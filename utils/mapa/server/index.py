import tempfile
from flask import Flask, render_template, send_file, jsonify, request
from flask_cors import CORS
import os

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

@server_api.route("/enderecos", methods=["POST"])
def receber_enderecos():
    global dados_salvos
    dados_salvos = request.get_json()
    return jsonify({"mensagem": "Dados recebidos com sucesso!"})

@server_api.route("/enderecos", methods=["GET"])
def enviar_enderecos():
    return jsonify(dados_salvos)

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
