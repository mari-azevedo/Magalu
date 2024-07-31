import time
import random
import requests as http_cliente
import pandas as pd
from bs4 import BeautifulSoup
import os
from email.message import EmailMessage
import ssl
import smtplib
from testa_proxy import funciona

# URL base
url_base = "https://www.magazineluiza.com.br/busca/notebooks/?from=submit&page="

# Lista de proxies para contornar o CAPTCHA
proxies = funciona()

print('proxies',len(proxies))
def obterHTML(url, proxy):

    try:
        requisicao = http_cliente.get(url, proxies={"http": proxy, "https": proxy}, timeout=20)
        requisicao.raise_for_status()  # Levanta um erro se a requisição falhar
        return BeautifulSoup(requisicao.text, 'html.parser')
    except http_cliente.RequestException as e:
        print(f"Erro ao acessar {url} com proxy {proxy}: {e}")
        return None

def pegar_itens_do_site(soup):
    notebooks = []
    if soup:
        # Seleciona os elementos que contém as informações dos notebooks
        itens = soup.select('li.sc-fTyFcS.iTkWie') 
        for item in itens:
            nome_elem = item.select_one('h2.sc-elxqWl.kWTxnF')
            nome = nome_elem.get_text(strip=True) if nome_elem else "Título não encontrado"

            aval_elem = item.select_one('span.sc-epqpcT.jdMYPv')
            aval = aval_elem.get_text(strip=True) if aval_elem else "Avaliações não encontradas"

            link_elem = item.select_one('a')['href']
            link = f"https://www.magazineluiza.com.br{link_elem}" if link_elem else "Link não encontrado"

            notebooks.append({
                'PRODUTO': nome,
                'QTD_AVAL': aval,
                'URL': link
            })
    return notebooks

def extrair_dados():
    numero_pag = 1
    notebooks = []
    while proxies: 
        url = f"{url_base}{numero_pag}"
        proxy = random.choice(proxies)
        proxies.remove(proxy) 
        print(f"Raspando página: {url} usando proxy: {proxy}")

        soup = obterHTML(url, proxy)
        if soup is None and len(proxies)!= 1:
            print(f"Erro ao raspar a página {url}.")
            continue

        notebooks_atuais = pegar_itens_do_site(soup)

        if not notebooks_atuais:
            if soup.title and soup.title.string == "Radware Bot Manager Captcha":
                print("Site fora do ar, CAPTCHA ativo para esse proxy!") #log para quando o captcha é ativado pela magalu
                continue
                #break
            else:
                print(f"Nenhum item encontrado na página {numero_pag}. Parando a raspagem.")
                break

        notebooks.extend(notebooks_atuais)
        print(f"Encontrados {len(notebooks_atuais)} itens na página {numero_pag}.")
        numero_pag += 1

        # Pausa de 15 a 30 segundos entre as requisições para não sobrecarregar o servidor
        time.sleep(random.randint(15, 30))

    return notebooks

try:
    notebooks = extrair_dados()

    if notebooks:
        notebooks_df = pd.DataFrame(notebooks)
        print(notebooks_df)
    else:
        print("Nenhum notebook com avaliações encontrado.")
except Exception as e:
    print(f"Ocorreu um erro: {e}")
    
#Tirando do DF os itens sem avaliação
sem_avaliacao = notebooks_df[notebooks_df['QTD_AVAL'] == 'Avaliações não encontradas']
notebooks_df = notebooks_df[notebooks_df['QTD_AVAL'] != 'Avaliações não encontradas']

#deixando apenas a quantidade de avaliação
notebooks_df['QTD_AVAL'] = notebooks_df['QTD_AVAL'].str.extract(r'\((.*?)\)')

#transformando de string para inteiro
notebooks_df['QTD_AVAL'] = notebooks_df['QTD_AVAL'].astype(int)

# Separando entre 'piores' and 'melhores'
piores = notebooks_df[notebooks_df['QTD_AVAL'] < 100]
melhores = notebooks_df[notebooks_df['QTD_AVAL'] >= 100]

# Certificando que a pasta Output existe
output_dir = 'Output'
os.makedirs(output_dir, exist_ok=True)

# Exportando Excel
excel_path = os.path.join(output_dir, 'notebooks.xlsx')
with pd.ExcelWriter(excel_path) as writer:
    piores.to_excel(writer, sheet_name='Piores', index=False)
    melhores.to_excel(writer, sheet_name='Melhores', index=False)

# Email Configurações
meu_email = "" 
senha_gerada = "" 
destinatario_email = ""
assunto = "Relatório Notebooks"
body = "Olá, aqui está o seu relatório dos notebooks extraídos da Magazine Luiza.\n\nAtenciosamente,\nRobô"

em = EmailMessage()
em['From'] = meu_email
em['To'] = destinatario_email
em['Subject'] = assunto
em.set_content(body)

# Incluido o excel como anexo
with open(excel_path, 'rb') as file:
    em.add_attachment(file.read(), maintype='application', subtype='vnd.openxmlformats-officedocument.spreadsheetml.sheet', filename='notebooks.xlsx')

# enviando e-mail
context = ssl.create_default_context()

with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
    smtp.login(meu_email, senha_gerada)
    smtp.send_message(em)

print("E-mail enviado com sucesso!")
