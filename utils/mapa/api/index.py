from utils.mapa.api.api_geocorp import consultar_cep
from utils.mapa.api.api_opemstreet import buscar_endereco_por_coordenadas

def unificar_enderecos(api_geocorp_url, api_osm_url, cep, lat, lon, db_instance, cep_aberto_token):

    resultado_unificado = []

    # 1. Dados GeoCorp (Correios + DBC_LOGRADOUROS)
    dados_geocorp = consultar_cep(api_geocorp_url, cep)
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

    # 2. Dados OpenStreetMap + CepAberto
    try:
        dados_osm = buscar_endereco_por_coordenadas(api_osm_url, lat, lon, db_instance, cep_aberto_token)
        resultado_unificado.append({
            "opem_street": [[
                dados_osm.get("logradouro", ""),
                dados_osm.get("bairro", ""),
                dados_osm.get("municipio", ""),
                dados_osm.get("cep", "") or "",
                dados_osm.get("uf", "")
            ]]
        })
    except Exception as e:
        print(f"⚠️ Erro ao buscar via OpenStreetMap: {e}")

    return resultado_unificado
