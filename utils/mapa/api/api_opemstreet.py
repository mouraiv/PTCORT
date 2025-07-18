import requests

def buscar_endereco_por_coordenadas(api, lat, lon, db_instance_uf, cep_aberto_token):
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
    if not estado:
        raise Exception("Estado não encontrado no resultado do Nominatim")

    if db_instance_uf is not None:
        valor_uf = db_instance_uf #db_instance.obter_uf_brev_roteiro(estado.upper())
        uf = valor_uf or ""
    else:
        uf = ""

    # 3. Preparar parâmetros para busca no Cep Aberto
    # Só envia cidade e bairro se existirem (pois são obrigatórios na API, mas a cidade pode estar em outras chaves)
    cidade = endereco.get('city') or endereco.get('town') or endereco.get('village')
    bairro = endereco.get('suburb') or endereco.get('neighbourhood')
    logradouro = endereco.get('road') or endereco.get('residential') or endereco.get('pedestrian')

    if not cidade:
        raise Exception("Cidade não encontrada no resultado do Nominatim")

    cep_aberto_url = "https://www.cepaberto.com/api/v3/address"
    cep_aberto_headers = {'Authorization': f'Token token={cep_aberto_token}'}

    # Monta params, sem incluir None para evitar erro na API
    cep_aberto_params = {
        'estado': uf,
        'cidade': cidade,
    }
    if bairro:
        cep_aberto_params['bairro'] = bairro
    if logradouro:
        cep_aberto_params['logradouro'] = logradouro

    print(cep_aberto_params)

    cep_aberto_resp = requests.get(cep_aberto_url, headers=cep_aberto_headers, params=cep_aberto_params)
    if cep_aberto_resp.status_code == 200:
        cep_data = cep_aberto_resp.json()
        cep = cep_data.get('cep')
        print(cep)
    else:
        cep = None
        print(cep_aberto_resp.json())

    return {
        'cep': cep,
        'logradouro': logradouro,
        'bairro': bairro,
        'municipio': cidade,
        'localidade': estado,
        'uf': uf
    }
