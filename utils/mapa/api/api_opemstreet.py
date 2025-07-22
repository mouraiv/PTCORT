import requests

from utils.mapa.api.api_geocorp import consultar_cep

def buscar_endereco_por_coordenadas(api, lat, lon, cep_aberto_token):
    """
    Faz uma requisição à API Nominatim do OpenStreetMap para obter endereço
    e consulta o CEP mais preciso no Cep Aberto via estado, cidade, bairro e logradouro.
    """
    # 1. Consulta ao Nominatim (OpenStreetMap)
    params_osm = {
        'lat': lat,
        'lon': lon,
        'format': 'json',
        'addressdetails': 1,
        'accept-language': 'pt-BR'
    }

    headers_osm = {
        'User-Agent': 'PythonReverseGeocoder/1.0 (seu-email@dominio.com)'
    }

    response = requests.get(api, params=params_osm, headers=headers_osm)
    if response.status_code != 200:
        raise Exception("API [OpenStreet] indisponível")

    data = response.json()
    endereco = data.get('address', {})

    # 2. Tratamento do estado para obter a sigla UF via db_instance
    estado = endereco.get('state')

    def obter_uf(estado: str) -> str:
        estados_para_uf = {
            'Acre': 'AC',
            'Alagoas': 'AL',
            'Amapá': 'AP',
            'Amazonas': 'AM',
            'Bahia': 'BA',
            'Ceará': 'CE',
            'Distrito Federal': 'DF',
            'Espírito Santo': 'ES',
            'Goiás': 'GO',
            'Maranhão': 'MA',
            'Mato Grosso': 'MT',
            'Mato Grosso do Sul': 'MS',
            'Minas Gerais': 'MG',
            'Pará': 'PA',
            'Paraíba': 'PB',
            'Paraná': 'PR',
            'Pernambuco': 'PE',
            'Piauí': 'PI',
            'Rio de Janeiro': 'RJ',
            'Rio Grande do Norte': 'RN',
            'Rio Grande do Sul': 'RS',
            'Rondônia': 'RO',
            'Roraima': 'RR',
            'Santa Catarina': 'SC',
            'São Paulo': 'SP',
            'Sergipe': 'SE',
            'Tocantins': 'TO'
        }

        # Remove espaços extras
        estado_formatado = estado.strip()
        
        # Procura pelo estado no dicionário (comparação case insensitive)
        for nome_estado, uf in estados_para_uf.items():
            if nome_estado.casefold() == estado_formatado.casefold():
                return uf
        
        return None  # Retorna None se não encontrar

    # 3. Preparar parâmetros para busca no Cep Aberto
    # Só envia cidade e bairro se existirem (pois são obrigatórios na API, mas a cidade pode estar em outras chaves)
    cidade = endereco.get('city') or endereco.get('town') or endereco.get('village')
    bairro = endereco.get('suburb') or endereco.get('neighbourhood')
    logradouro = endereco.get('road') or endereco.get('residential') or endereco.get('pedestrian')

    if not cidade:
        raise Exception("Cidade não encontrada no resultado do Nominatim")

    cep_aberto_url = "https://www.cepaberto.com/api/v3/nearest"
    cep_aberto_headers = {'Authorization': f'Token token={cep_aberto_token}'}

    # Monta params, sem incluir None para evitar erro na API
    cep_aberto_params = {'lat': lat, 'lng': lon}

    cep_aberto_resp = requests.get(cep_aberto_url, headers=cep_aberto_headers, params=cep_aberto_params)
    if cep_aberto_resp.status_code == 200:
        cep_data = cep_aberto_resp.json()
        cep = cep_data.get('cep')
    else:
        cep = None
    
    dados_geocorp = consultar_cep("http://geocorp3.telemar:85/CEP.asp",cep)

    #Criar resultado unificado
    resultado_unificado = []

    # 1. Dados GeoCorp (Correios + DBC_LOGRADOUROS)
    if dados_geocorp:
        # a) Correios
        if "CORREIOS" in dados_geocorp:
            dados = dados_geocorp["CORREIOS"]
            resultado_unificado.append({
                "cep_correios": [[
                    f"{dados.get('TIPO', '')} {dados.get('LOGRADOURO', '')}".strip(),
                    dados.get("BAIRRO", ""),
                    dados.get("LOCALIDADE", ""),
                    dados.get("CEP", ""),
                    dados.get("UF", "")
                ]]
            })

        # b) DBC LOGRADOURO
        if "BDC_LOGRADOUROS" in dados_geocorp:
            dados = dados_geocorp["BDC_LOGRADOUROS"]
            resultado_unificado.append({
                "dbc_logradouro": [[
                    f"{dados.get('TIPO', '')} {dados.get('LOGRADOURO', '')}".strip(),
                    dados.get("BAIRRO", ""),
                    dados.get("LOCALIDADE", ""),
                    dados.get("CEP", ""),
                    dados.get("UF", "")
                ]]
            })
    else:
        print("⚠️ Nenhum dado retornado pelo GeoCorp.")

    # Recuperar UF do estado
    uf = obter_uf(estado)

    # 2. Dados OpenStreetMap + CepAberto
    try:
        dados_osm = {
            "logradouro": logradouro or "",
            "bairro": bairro or "",
            "municipio": cidade or "",
            "cep": cep or "",
            "uf": uf or ""
        }
        
        resultado_unificado.append({
            "opem_street": [[
                dados_osm.get("logradouro", ""),
                dados_osm.get("bairro", ""),
                dados_osm.get("municipio", ""),
                dados_osm.get("cep", ""),
                dados_osm.get("uf", "")
            ]]
        })
    except Exception as e:
        print(f"⚠️ Erro ao buscar via OpenStreetMap: {e}")

    return resultado_unificado
