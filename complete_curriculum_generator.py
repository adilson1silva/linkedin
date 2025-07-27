from dotenv import load_dotenv
import os
load_dotenv()
import openai
import re
from pathlib import Path

# === Configura a tua chave da API ===
# SUBSTITUI PELA TUA CHAVE REAL DA OPENAI

#client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
openai.api_key = os.getenv("OPENAI_API_KEY")


# === Lê os dados do perfil pessoal ===
# Certifica-te que o ficheiro meus_dados.txt está no mesmo diretório
with open("meus_dados.txt", "r", encoding="utf-8") as f:
    perfil_pessoal = f.read()

# === Lê e processa as vagas ===
# Certifica-te que o ficheiro vagas.txt está no mesmo diretório
with open("vagas.txt", "r", encoding="utf-8") as f:
    conteudo_vagas = f.read()

# Split by '------------------------------------------------------------' as observed in vagas.txt
blocos_vagas = re.split(r"-{50,}", conteudo_vagas)
blocos_vagas = [b.strip() for b in blocos_vagas if b.strip()]

# === Cria diretório de saída ===
output_dir = Path("curriculos_gerados")
output_dir.mkdir(exist_ok=True)

# === Loop para gerar cada currículo ===
for idx, vaga_texto in enumerate(blocos_vagas, 1):
    print(f"Processando vaga {idx}...")
    
    # Extrai informações da vaga
    titulo = re.search(r"T[ií]tulo:\s*(.*)", vaga_texto)
    url = re.search(r"URL:\s*(.*)", vaga_texto)
    descricao = re.search(r"Descri[cç][aã]o:\s*(.*)", vaga_texto, re.DOTALL)

    titulo = titulo.group(1).strip() if titulo else "Título não especificado"
    
    # Extrai nome da empresa (simplificado)
    empresa = f"Empresa_Vaga_{idx}"
    if "SECURIX" in vaga_texto:
        empresa = "SECURIX"
    elif "HCLTech" in vaga_texto:
        empresa = "HCLTech"
    elif "SAP" in vaga_texto:
        empresa = "SAP_Company"
    
    descricao = descricao.group(1).strip() if descricao else "Descrição não especificada"

    # Prompt para o ChatGPT
    prompt = f"""
Crie um currículo altamente profissional e personalizado com base neste perfil pessoal:

{perfil_pessoal}

Agora adapte este currículo para a seguinte vaga:
Título: {titulo}
Empresa: {empresa}
Descrição:
{descricao}

O currículo deve ser:
- Direto e profissional
- Adaptado especificamente à vaga
- Escrito em português
- Bem estruturado com secções claras
- Destacar as competências mais relevantes para a posição
"""

    try:
        # Chama a API do ChatGPT
        response = client.chat.completions.create(
            model="gpt-4",  # Podes usar "gpt-3.5-turbo" se preferires (mais barato)
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6,
            max_tokens=2000
        )

        cv = response.choices[0].message.content

        # Guarda o currículo num ficheiro
        filename = output_dir / f"CV_{idx}_{empresa.replace(' ', '_')}.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"CURRÍCULO PARA: {titulo} - {empresa}\n")
            f.write("="*60 + "\n\n")
            f.write(cv)

        print(f"[✔] Currículo gerado para: {titulo} - {empresa}")
        
    except Exception as e:
        print(f"[✗] Erro ao gerar currículo para {titulo}: {e}")
        continue

print("\n✅ Processo concluído! Verifica a pasta 'curriculos_gerados' para os resultados.")

