# server.py
from flask import Flask, request, jsonify
from flask_cors import CORS

server_api = Flask(__name__)
CORS(server_api)

# Variável global para armazenar o JSON
dados_salvos = []

@server_api.route("/enderecos", methods=["POST"])
def receber_enderecos():
    global dados_salvos
    dados_salvos = request.get_json()
    print("JSON recebido via POST:", dados_salvos)
    return jsonify({"mensagem": "Dados recebidos com sucesso!"})

@server_api.route("/enderecos", methods=["GET"])
def enviar_enderecos():
    return jsonify(dados_salvos)
