import requests

def funciona():
    proxies_lista_url = "https://api.proxyscrape.com/v3/free-proxy-list/get?request=displayproxies&protocol=http&proxy_format=protocolipport&format=text&timeout=8611"

    response = requests.get(proxies_lista_url)
    proxies = response.text.split('\n')

    funciona = []
    contador = 0

    url = "https://www.magazineluiza.com.br"
    timeout = 10 

    for proxy in proxies:
        proxy = proxy.strip()
        if proxy: 
            try:
                response = requests.get(url, proxies={"http": proxy, "https": proxy}, timeout=timeout)
                response.raise_for_status()
                print(f"Proxy {proxy} funcionando!")
                funciona.append(proxy)
                contador += 1
                if contador == 8:
                    break
            except requests.RequestException as e:
                pass

    print("Proxies funcionando:", funciona)
    return funciona