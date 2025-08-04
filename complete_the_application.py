
import os
import re
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from pathlib import Path

# --- Configuration --- #
LINKEDIN_USERNAME = os.environ.get("LINKEDIN_USERNAME")
LINKEDIN_PASSWORD = os.environ.get("LINKEDIN_PASSWORD")

# Path to vagas.txt and generated CVs
VAGAS_FILE = "vagas.txt"
GENERATED_CVS_DIR = "curriculos_gerados"

# --- Helper Functions --- #
def get_job_data(vagas_file_path):
    job_data = []
    with open(vagas_file_path, "r", encoding="utf-8") as f:
        content = f.read()

    blocos_vagas = re.split(r"-{50,}", content)
    blocos_vagas = [b.strip() for b in blocos_vagas if b.strip()]

    for idx, vaga_texto in enumerate(blocos_vagas, 1):
        url_match = re.search(r"URL:\s*(.*)", vaga_texto)
        title_match = re.search(r"T[ií]tulo:\s*(.*)", vaga_texto)

        url = url_match.group(1).strip() if url_match else None
        title = title_match.group(1).strip() if title_match else f"Job_{idx}"

        # Attempt to extract company name from URL or description
        empresa = f"Empresa_Vaga_{idx}"
        if url:
            match = re.search(r"linkedin.com/jobs/view/.*?/(.*?)/", url)
            if match:
                empresa = match.group(1).replace("-", " ").title()
        
        # Fallback to description for company name if not found in URL
        if empresa == f"Empresa_Vaga_{idx}":
            company_match = re.search(r"(About Us|Über uns|À propos du poste|Unser Kunde)\s*([A-Za-z0-9\s,.-]+)", vaga_texto)
            if company_match:
                empresa = company_match.group(2).strip().split(" ")[0] # Take the first word as company name

        # Construct CV filename based on the naming convention from complete_curriculum_generator.py
        cv_filename = f"CV_{idx}_{empresa.replace(" ", "_")}.txt"
        cv_path = Path(GENERATED_CVS_DIR) / cv_filename

        if url and cv_path.exists():
            job_data.append({
                "url": url,
                "title": title,
                "company": empresa,
                "cv_path": str(cv_path)
            })
        else:
            print(f"Skipping job {idx}: URL or CV file not found. URL: {url}, CV Path: {cv_path}")
    return job_data

def linkedin_login(driver, username, password):
    driver.get("https://www.linkedin.com/login")
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "username"))).send_keys(username)
    driver.find_element(By.ID, "password").send_keys(password)
    driver.find_element(By.XPATH, "//button[@type=\'submit\']").click()
    try:
        WebDriverWait(driver, 10).until(EC.url_contains("feed")) # Wait for successful login
        print("Successfully logged into LinkedIn.")
        return True
    except TimeoutException:
        print("Failed to log in. Check your credentials.")
        return False

def apply_for_job(driver, job_url, cv_path):
    print(f"Navigating to job: {job_url}")
    driver.get(job_url)
    time.sleep(3) # Give page time to load

    try:
        # Check for Easy Apply button
        easy_apply_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(., \'Easy Apply\')] | //button[contains(., \'Candidatura simplificada\')]"))
        )
        easy_apply_button.click()
        print("Clicked Easy Apply button.")

        # --- Handle application steps --- #
        # This part is highly dependent on LinkedIn's application flow
        # It might involve multiple steps, attaching CVs, filling forms, etc.
        # For simplicity, we'll assume a basic flow and focus on CV upload if applicable.

        # Wait for the application modal to appear
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[role=\'dialog\']")))
        print("Application modal appeared.")

        # Look for a file input element to upload CV
        try:
            # Find all input elements of type file
            file_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type=\'file\']")
            uploaded = False
            for file_input in file_inputs:
                # Check if the input is for a resume/CV
                if "resume" in file_input.get_attribute("name").lower() or \
                   "cv" in file_input.get_attribute("name").lower() or \
                   "upload" in file_input.get_attribute("name").lower():
                    file_input.send_keys(cv_path)
                    print(f"Uploaded CV: {cv_path}")
                    uploaded = True
                    break
            if not uploaded:
                print("No specific CV upload field found or recognized.")

        except NoSuchElementException:
            print("No file upload element found in the application form.")

        # Try to click the 'Next' or 'Review' or 'Submit' button
        # This is a generic attempt and might need refinement based on actual LinkedIn forms
        try:
            next_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(., \'Next\')] | //button[contains(., \'Review\')] | //button[contains(., \'Submit\')] | //button[contains(., \'Próximo\')] | //button[contains(., \'Rever\')] | //button[contains(., \'Enviar\')]"))
            )
            next_button.click()
            print("Clicked Next/Review/Submit button.")
            time.sleep(2) # Wait for next step or submission

            # If there are multiple steps, you might need a loop here
            # For now, let's assume one click is enough or it's the final step
            # Check for a final submit button if the first click was 'Next' or 'Review'
            try:
                final_submit_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(., \'Submit application\')] | //button[contains(., \'Enviar candidatura\')]"))
                )
                final_submit_button.click()
                print("Clicked final Submit application button.")
                time.sleep(2)
            except TimeoutException:
                print("No final submit button found after initial click, assuming single step or already submitted.")

        except TimeoutException:
            print("No Next/Review/Submit button found or clickable. Manual intervention might be needed.")

        print(f"Successfully attempted to apply for: {job_url}")
        return True

    except TimeoutException:
        print(f"Easy Apply button not found or not clickable for {job_url}. Skipping.")
        return False
    except Exception as e:
        print(f"An error occurred while applying for {job_url}: {e}")
        return False

# --- Main Execution --- #
if __name__ == "__main__":
    if not LINKEDIN_USERNAME or not LINKEDIN_PASSWORD:
        print("Please set LINKEDIN_USERNAME and LINKEDIN_PASSWORD environment variables.")
        print("You can also hardcode them in the script for testing, but it's not recommended for security.")
        exit()

    # Setup WebDriver
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless") # Run in headless mode (without opening browser UI)
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    try:
        driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
    except Exception as e:
        print(f"Error setting up WebDriver: {e}")
        print("Please ensure you have Chrome installed and try again.")
        exit()

    # Ensure the generated_curriculos directory exists
    Path(GENERATED_CVS_DIR).mkdir(exist_ok=True)

    # Login to LinkedIn
    if not linkedin_login(driver, LINKEDIN_USERNAME, LINKEDIN_PASSWORD):
        driver.quit()
        exit()

    # Get job data from vagas.txt
    # Assuming vagas.txt is in the same directory as the script, or provide full path
    job_listings = get_job_data(VAGAS_FILE)

    if not job_listings:
        print("No job listings found with corresponding CVs. Please ensure vagas.txt is correctly formatted and CVs are generated.")
    else:
        for job in job_listings:
            print(f"\nAttempting to apply for: {job["title"]} at {job["company"]}")
            apply_for_job(driver, job["url"], job["cv_path"])
            time.sleep(5) # Wait before next application

    driver.quit()
    print("Automation complete.")


