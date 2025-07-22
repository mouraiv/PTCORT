from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import os

from utils.mapa.api.api_opemstreet import buscar_endereco_por_coordenadas

# Caminho absoluto para a pasta 'html' (um nível acima de 'server')
template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../html/"))

# Criação do servidor Flask
server_api = Flask(__name__, template_folder=template_dir)
CORS(server_api)

# Variável global para armazenar os dados recebidos
dados_salvos = []
dados_salvos_click = []

@server_api.route('/')
def index():
    return render_template("map.html")  # Não precisa colocar o caminho completo, só o nome

from flask import request, jsonify

@server_api.route("/enderecos", methods=["POST"])
def receber_enderecos():
    global dados_salvos

    # Extrair parâmetros do JSON enviado
    dados = request.get_json()
    lat = dados.get("lat")
    lon = dados.get("lon")

    if lat is None or lon is None:
        return jsonify({"erro": "Parâmetros 'lat' e 'lon' são obrigatórios."}), 400

    # Configurações
    api_osm_url = "https://nominatim.openstreetmap.org/reverse"
    cep_aberto_token = "d40efb650d1963b7546a6df9ebde4943"

    # Chamada
    dados_enderecos = buscar_endereco_por_coordenadas(
        api_osm_url,
        lat,
        lon,
        cep_aberto_token
    )

    dados_salvos = dados_enderecos
    return jsonify({"mensagem": "Dados recebidos com sucesso!"})

@server_api.route("/enderecos", methods=["GET"])
def enviar_enderecos():
    dados_formatados = []

    for item in dados_salvos:
        novo_item = {}
        for chave, valor in item.items():
            nova_lista = []
            for sublista in valor:
                nova_sublista = []
                for i, v in enumerate(sublista):
                    if isinstance(v, str):
                        if i == len(sublista) - 1:  # último campo = UF
                            nova_sublista.append(v.upper())
                        else:
                            nova_sublista.append(v.title())
                    else:
                        nova_sublista.append(v)
                nova_lista.append(nova_sublista)
            novo_item[chave] = nova_lista
        dados_formatados.append(novo_item)

    return jsonify(dados_formatados)

@server_api.route("/enderecos/click", methods=["POST"])
def receber_enderecos_click():
    global dados_salvos_click
    dados_salvos_click = request.get_json()
    return jsonify({"mensagem": "Linha recebida com sucesso!"})

@server_api.route("/enderecos/click", methods=["GET"])
def enviar_enderecos_click():
    return jsonify(dados_salvos_click)

if __name__ == "__main__":
    server_api.run(threaded=True, debug=True)
