import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from functools import lru_cache

@lru_cache(maxsize=100)
def consultar_cep(api, cep):
    """
    Consulta um CEP no sistema interno da Telemar (GeoCorp) e retorna os dados em formato dicionário.
    """
        
    url = f"{api}"
    
    # Configurar sessão com retentativas
    session = requests.Session()
    retries = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[500, 502, 503, 504]
    )
    session.mount('http://', HTTPAdapter(max_retries=retries))
    
    try:
        response = session.post(url, data={"CEP": cep}, timeout=10)
        response.raise_for_status()

        if f"INFORMAÇÕES SOBRE O CEP:&nbsp;{cep}" not in response.text:
            return None

        soup = BeautifulSoup(response.text, 'html.parser')
        resultado = {}

        # === BDC_LOGRADOUROS ===
        bdc_header = soup.find('td', bgcolor="#8175A7")
        if bdc_header:
            resultado['BDC_LOGRADOUROS'] = []
            for row in bdc_header.find_parent('table').find_all('tr'):
                cells = row.find_all('td')
                if len(cells) >= 9 and cep in row.get_text():
                    resultado['BDC_LOGRADOUROS'].append({
                        'UF': cells[0].get_text(strip=True),
                        'LOCALIDADE': cells[1].get_text(strip=True),
                        'TIPO': cells[2].get_text(strip=True),
                        'TITULO': cells[3].get_text(strip=True),
                        'LOGRADOURO': cells[4].get_text(strip=True),
                        'BAIRRO': cells[5].get_text(strip=True),
                        'CEP': cells[6].get_text(strip=True).replace('-', '').strip(),
                        'COD_LOCALIDADE': cells[7].get_text(strip=True),
                        'COD_LOGRADOURO': cells[8].get_text(strip=True)
                    })

        # === CORREIOS ===
        correios_header = soup.find('td', bgcolor="#009AA2")
        if correios_header:
            resultado['CORREIOS'] = []
            tr_inicio = correios_header.find_parent('tr')
            trs = tr_inicio.find_next_siblings('tr')

            for row in trs:
                cells = row.find_all('td')
                # Encerra se encontrar nova seção ou linha fora do padrão
                if not cells or (cells[0].has_attr('bgcolor') and cells[0]['bgcolor'] != "#009AA2"):
                    break
                if len(cells) >= 8 and cep in row.get_text():
                    resultado['CORREIOS'].append({
                        'UF': cells[0].get_text(strip=True),
                        'LOCALIDADE': cells[1].get_text(strip=True),
                        'TIPO': cells[2].get_text(strip=True),
                        'TITULO': cells[3].get_text(strip=True),
                        'LOGRADOURO': cells[4].get_text(strip=True),
                        'BAIRRO': cells[5].get_text(strip=True),
                        'CEP': cells[6].get_text(strip=True).replace('-', '').strip(),
                        'COMPLEMENTO': cells[7].get_text(strip=True)
                    })

        return resultado if resultado else None

    except requests.exceptions.RequestException as e:
        print(f"Erro na requisição para CEP {cep}: {e}")
        return "500"
    except Exception as e:
        print(f"Erro inesperado ao processar CEP {cep}: {e}")
        return None
