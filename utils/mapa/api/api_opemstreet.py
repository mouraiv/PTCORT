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

    def obter_uf(estado: str, pais: str = None) -> str:
        """Converte o nome completo do estado para sigla UF, tratando casos internacionais
        
        Args:
            estado: Nome do estado/província
            pais: Nome do país (opcional)
            
        Returns:
            str: Sigla UF ou "--" para países não-Brasil ou dados inválidos
        """
        # Primeiro verifica se é um país não-Brasil
        if pais and pais.lower() != 'brasil' and pais.lower() != 'brazil':
            return "--"
        
        # Verifica estado vazio/nulo
        if not estado:
            return "--"
        
        try:
            # Dicionário completo com todas as variações de nomes
            estados_para_uf = {
                'acre': 'AC',
                'alagoas': 'AL',
                'amapá': 'AP', 'amapa': 'AP',
                'amazonas': 'AM',
                'bahia': 'BA',
                'ceará': 'CE', 'ceara': 'CE',
                'distrito federal': 'DF',
                'espírito santo': 'ES', 'espirito santo': 'ES',
                'goiás': 'GO', 'goias': 'GO',
                'maranhão': 'MA', 'maranhao': 'MA',
                'mato grosso': 'MT',
                'mato grosso do sul': 'MS',
                'minas gerais': 'MG',
                'pará': 'PA', 'para': 'PA',
                'paraíba': 'PB', 'paraiba': 'PB',
                'paraná': 'PR', 'parana': 'PR',
                'pernambuco': 'PE',
                'piauí': 'PI', 'piaui': 'PI',
                'rio de janeiro': 'RJ',
                'rio grande do norte': 'RN',
                'rio grande do sul': 'RS',
                'rondônia': 'RO', 'rondonia': 'RO',
                'roraima': 'RR',
                'santa catarina': 'SC',
                'são paulo': 'SP', 'sao paulo': 'SP',
                'sergipe': 'SE',
                'tocantins': 'TO'
            }
            
            # Normaliza o estado: remove espaços, acentos e coloca em minúsculas
            estado_formatado = estado.strip().lower()
            
            # Remove acentos (opcional, para maior robustez)
            estado_formatado = (estado_formatado
                            .replace('á', 'a').replace('â', 'a').replace('ã', 'a')
                            .replace('é', 'e').replace('ê', 'e')
                            .replace('í', 'i')
                            .replace('ó', 'o').replace('ô', 'o').replace('õ', 'o')
                            .replace('ú', 'u')
                            .replace('ç', 'c'))
            
            return estados_para_uf.get(estado_formatado, "--")
        
        except AttributeError:
            return "--"

    # 3. Preparar parâmetros para busca no Cep Aberto
    # Só envia cidade e bairro se existirem (pois são obrigatórios na API, mas a cidade pode estar em outras chaves)
    cidade = endereco.get('city') or endereco.get('town') or endereco.get('village')
    bairro = endereco.get('suburb') or endereco.get('neighbourhood')
    logradouro = endereco.get('road') or endereco.get('residential') or endereco.get('pedestrian')
    cep_opemstreet = endereco.get('postcode', '')

    #Trata retorno CEP
    if cep_opemstreet:
            cep_opemstreet = cep_opemstreet.replace("-", "")
    else:
        cep_opemstreet = "--"

    # Recuperar UF do estado
    uf = obter_uf(estado)

    if not cidade:
        raise Exception("Cidade não encontrada no resultado do Nominatim")

    cep_aberto_url = "https://www.cepaberto.com/api/v3/address"
    cep_aberto_headers = {'Authorization': f'Token token={cep_aberto_token}'}

    # Monta params, sem incluir None para evitar erro na API
    cep_aberto_params = {
        'logradouro': logradouro or '',
        'bairro': bairro or '',
        'cidade': cidade or '',
        'estado': uf or '',
    }

    cep_aberto_resp = requests.get(cep_aberto_url, headers=cep_aberto_headers, params=cep_aberto_params)
    if cep_aberto_resp.status_code == 200:
        cep_data = cep_aberto_resp.json()
        # Extrai os dados do CEP retornado
        cep_cep_aberto = cep_data.get('cep')
    else:
        cep_cep_aberto = None

    # 4. Consultar GeoCorp para dados mais completos
    def tratar_dados_geocorp(cep):
        _resultado = []

        dados_geocorp = consultar_cep("http://geocorp3.telemar:85/CEP.asp", cep)
        
        # 1. Dados GeoCorp (Correios + DBC_LOGRADOUROS)
        if dados_geocorp:
            # a) Correios
            if "CORREIOS" in dados_geocorp:
                lista_correios = []
                for dados in dados_geocorp["CORREIOS"]:
                    lista_correios.append([
                        f"{dados.get('TIPO', '')} {dados.get('LOGRADOURO', '')}".strip(),
                        dados.get("BAIRRO", ""),
                        dados.get("LOCALIDADE", ""),
                        dados.get("CEP", ""),
                        dados.get("UF", ""),
                        lat,
                        lon                      
                    ])
                if lista_correios:
                     _resultado.append({"cep_correios": lista_correios})

            # b) DBC LOGRADOUROS
            if "BDC_LOGRADOUROS" in dados_geocorp:
                lista_dbc = []
                for dados in dados_geocorp["BDC_LOGRADOUROS"]:
                    lista_dbc.append([
                        f"{dados.get('TIPO', '')} {dados.get('LOGRADOURO', '')}".strip(),
                        dados.get("BAIRRO", ""),
                        dados.get("LOCALIDADE", ""),
                        dados.get("CEP", ""),
                        dados.get("UF", ""),
                        lat,
                        lon 
                    ])
                if lista_dbc:
                     _resultado.append({"dbc_logradouro": lista_dbc})

            return _resultado
        else:
            print("⚠️ Nenhum dado retornado pelo GeoCorp.")

    # Criar resultado comparativo
    resultado_compare = tratar_dados_geocorp(cep_opemstreet) if cep_opemstreet else []
    
    # 1. Preparar dados OpenStreetMap com CEP original
    cep_osm = cep_cep_aberto  # valor default, caso OpenStreet não traga outro

    endereco_osm = [
        logradouro or "",
        bairro or "",
        cidade or "",
        cep_osm or "",
        uf or ""
    ]

    # 2. Verificar correspondência com GeoCorp (Correios ou DBC)
    cep_valido = None
    endereco_encontrado = False

    for item in resultado_compare:
        if "cep_correios" in item:
            for endereco in item["cep_correios"]:
                print(f"Verificando Correios: {endereco[0].lower().strip()} == {endereco_osm[0].lower().strip()}")
                if (endereco[0].lower().strip() == endereco_osm[0].lower().strip() and
                    endereco[1].lower().strip() == endereco_osm[1].lower().strip() and
                    endereco[2].lower().strip() == endereco_osm[2].lower().strip() and
                    endereco[4].lower().strip() == endereco_osm[4].lower().strip()):
                    
                    endereco_encontrado = True
                    break  # não precisa pegar o CEP aqui ainda

        if "dbc_logradouro" in item and not endereco_encontrado:
            for endereco in item["dbc_logradouro"]:
                print(f"Verificando DBC: {endereco[0].lower().strip()} == {endereco_osm[0].lower().strip()}")
                if (endereco[0].lower().strip() == endereco_osm[0].lower().strip() and
                    endereco[1].lower().strip() == endereco_osm[1].lower().strip() and
                    endereco[2].lower().strip() == endereco_osm[2].lower().strip() and
                    endereco[4].lower().strip() == endereco_osm[4].lower().strip()):
                    
                    endereco_encontrado = True
                    break

    print(f"Endereço encontrado: {endereco_encontrado}, cep_opem: {cep_opemstreet}, cep_aberto: {cep_cep_aberto}")

    # 3. Se o endereço foi encontrado, o CEP do OpenStreet é válido
    if endereco_encontrado:
        cep_valido = cep_opemstreet
    else:
        cep_valido = cep_cep_aberto  # fallback

    # Criar resultado unificado
    resultado_unificado = tratar_dados_geocorp(cep_valido) if cep_valido else []

    # 2. Dados OpenStreetMap + CepAberto
    try:
        dados_osm = {
            "logradouro": logradouro or "",
            "bairro": bairro or "",
            "municipio": cidade or "",
            "cep": cep_valido or "",
            "uf": uf or "",
            "latitude": lat,
            "longitude": lon
        }

        resultado_unificado.append({
            "opem_street": [[
                dados_osm.get("logradouro", ""),
                dados_osm.get("bairro", ""),
                dados_osm.get("municipio", ""),
                dados_osm.get("cep", ""),
                dados_osm.get("uf", ""),
                dados_osm.get("latitude", ""),
                dados_osm.get("longitude", "")
            ]]
        })
    except Exception as e:
        print(f"⚠️ Erro ao buscar via OpenStreetMap: {e}")

    return resultado_unificado
