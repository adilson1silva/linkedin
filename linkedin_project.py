from selenium import webdriver
from time import sleep
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

def login_linkedin(driver, username_str, password_str):
    """
    Realiza o login no LinkedIn.
    """
    driver.get('https://www.linkedin.com/login')
    driver.maximize_window()
    sleep(2)
    
    username = driver.find_element(By.ID, 'username')
    username.send_keys(username_str)
    sleep(2)
    
    password = driver.find_element(By.ID, 'password')
    password.send_keys(password_str)
    sleep(2)
    
    driver.find_element(By.XPATH, '//*[@id="organic-div"]/form/div[4]/button').click()
    sleep(2)

def apply_filter(driver):
    """
    Realiza a pesquisa de vagas e aplica os filtros desejados.
    """
    # Pesquisa
    search = driver.find_element(By.XPATH, '//*[@id="global-nav-typeahead"]/input')
    search.click()
    search.send_keys('system administrator')
    search.send_keys(Keys.ENTER)
    sleep(5)
    
    # Aplica filtro (candidatura simplificada)
    driver.find_element(By.XPATH, '//*[@id="search-reusables__filters-bar"]/ul/li[1]/button').click()
    sleep(5)
    driver.find_element(By.ID, 'searchFilter_applyWithLinkedin').click()
    sleep(2)

def main():
    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 10)
    
    # 1. Realiza o login
    login_linkedin(driver, 'inserir email', 'password')
    
    # 2. Executa a pesquisa e aplica os filtros
    apply_filter(driver)
    
    # 3. Extrai os links de cada vaga da lista
    job_cards = wait.until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li.scaffold-layout__list-item"))
    )
    job_links = []
    for card in job_cards:
        try:
            link_elem = card.find_element(By.TAG_NAME, "a")
            href = link_elem.get_attribute("href")
            if href and href not in job_links:
                job_links.append(href)
        except Exception as e:
            print("Erro ao extrair link do card:", e)
    print(f"Links coletados: {len(job_links)}")
    
    # 4. Itera pelos links e extrai os dados de cada vaga com BeautifulSoup
    all_jobs_data = []
    for index, link in enumerate(job_links, start=1):
        try:
            driver.get(link)
            sleep(3)  # Aguarda a página carregar
            
            # Aguarda os detalhes da vaga aparecerem
            wait.until(EC.visibility_of_element_located((By.ID, "job-details")))
            sleep(5)
            
            # Realiza o scroll para deixar o botão "Ver mais" visível
            driver.execute_script("window.scrollBy(0, 450);")
            sleep(5)
            
            # Tenta clicar no botão "Ver mais" para expandir a descrição completa
            try:
                see_more = driver.find_element(By.CLASS_NAME, 'artdeco-button__text')
                see_more.click()
                sleep(5)  # Aguarda a descrição ser expandida
            except Exception as e:
                print("Erro ao clicar no 'Ver mais':", e)
            
            # Obtém o HTML atualizado e usa o BeautifulSoup para extrair os dados
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            # Extrai o título da vaga (ajuste o seletor conforme necessário)
            title_elem = soup.select_one('.t-24.t-bold.inline')
            if title_elem:
                job_title = title_elem.get_text(strip=True)
            else:
                job_title = "Título não encontrado"
            
            # Extrai a descrição da vaga a partir do container com id "job-details"
            details_elem = soup.find(id="job-details")
            if details_elem:
                job_description = details_elem.get_text(strip=True)
            else:
                job_description = "Descrição não encontrada"
            
            # Obtém a URL atual
            job_url = driver.current_url
            
            # Armazena os dados
            all_jobs_data.append({
                "title": job_title,
                "description": job_description,
                "url": job_url
            })
            
            print(f"Vaga {index}")
            print("Título: ", job_title)
            print("URL: ", job_url)
            print("Descrição (início): ", job_description[:100], "...")
            print("-" * 60)
        except Exception as e:
            print(f"[ERRO] Não foi possível coletar dados da vaga {index}: {e}")
            continue
    
    # 5. Salva os dados em um arquivo TXT
    filename = "vagas.txt"
    with open(filename, "w", encoding="utf-8") as f:
        for i, job in enumerate(all_jobs_data, start=1):
            f.write(f"Vaga {i}\n")
            f.write(f"Título: {job['title']}\n")
            f.write(f"URL: {job['url']}\n")
            f.write("Descrição:\n")
            f.write(job['description'] + "\n")
            f.write("-" * 60 + "\n")
    
    print(f"\nDados de {len(all_jobs_data)} vagas salvos em '{filename}'.")
    driver.quit()

if __name__ == "__main__":
    main()
