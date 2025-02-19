import os
import json
import csv
import requests
from datetime import datetime
import matplotlib.pyplot as plt
from flask import Flask, request, send_from_directory
from twilio.twiml.messaging_response import MessagingResponse, Message

app = Flask(__name__)

STATIC_DIR = 'static/'
categorias_aguardando = {}

def carregar_categorias():
    try:
        with open('categorias.json', 'r') as file:
            categorias = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        categorias = []
    return categorias

def salvar_categorias(categorias):
    with open('categorias.json', 'w') as file:
        json.dump(categorias, file)

def carregar_gastos():
    try:
        with open('gastos.csv', 'r', newline='') as file:
            reader = csv.reader(file)
            gastos = list(reader)
    except FileNotFoundError:
        gastos = []
    return gastos

def salvar_gasto(categoria, valor):
    gastos = carregar_gastos()

    categoria_encontrada = False
    for i, gasto in enumerate(gastos):
        if gasto[0].lower() == categoria.lower():
            gastos[i][1] = str(float(gastos[i][1]) + valor)
            categoria_encontrada = True
            break
    
    if not categoria_encontrada:
        gastos.append([categoria, str(valor)])

    with open('gastos.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(gastos)

def gerar_relatorio():
    gastos = carregar_gastos()

    categorias = []
    valores = []
    for gasto in gastos:
        categorias.append(gasto[0])
        valores.append(float(gasto[1]))

    plt.figure(figsize=(10, 6))
    plt.bar(categorias, valores, color='skyblue')
    plt.xlabel('Categorias')
    plt.ylabel('Gastos (R$)')
    plt.title('Gastos por Categoria')

    # Salva o gráfico na pasta 'static'
    data_hora = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    nome_arquivo = f"relatorio_{data_hora}.png"
    caminho_arquivo = os.path.join(STATIC_DIR, nome_arquivo)
    plt.tight_layout()
    plt.savefig(caminho_arquivo)

    return nome_arquivo


def processar_gasto(msg, sender):
    categorias = carregar_categorias()

    for categoria in categorias:
        if categoria in msg.lower():
            try:
                valor = float(msg.split()[1])
                salvar_gasto(categoria, valor)
                return f"Gasto de R${valor} em {categoria.capitalize()} registrado com sucesso!"
            except ValueError:
                return "Desculpe, não entendi o valor. Tente novamente."

    return perguntar_adicionar_categoria(msg, sender)

def perguntar_adicionar_categoria(msg, sender):
    nova_categoria = msg.split()[0].lower()

    if nova_categoria not in categorias_aguardando:
        categorias_aguardando[sender] = nova_categoria
        return f"A categoria '{nova_categoria}' não foi reconhecida. Deseja adicioná-la? (S/N)"

    return "Já estamos esperando uma resposta. Por favor, clique em 's' ou 'n'."

def adicionar_categoria(sender):
    nova_categoria = categorias_aguardando.get(sender)
    if nova_categoria:
        categorias = carregar_categorias()

        categorias.append(nova_categoria)
        salvar_categorias(categorias)

        del categorias_aguardando[sender]
        return f"A categoria '{nova_categoria}' foi adicionada com sucesso! Agora, você pode registrar um gasto nesta categoria."

    return "Houve um erro ao adicionar a categoria."

def obter_url_ngrok():
    response = requests.get('http://localhost:4040/api/tunnels')
    data = response.json()
    return data['tunnels'][0]['public_url']


@app.route("/webhook", methods=["POST"])
def webhook():
    msg = request.form.get("Body") 
    sender = request.form.get("From")

    print(f"Mensagem recebida de {sender}: {msg}")

    if sender in categorias_aguardando:
        if msg.strip().lower() == "s":
            resposta = adicionar_categoria(sender)
        elif msg.strip().lower() == "n":
            resposta = f"A categoria '{categorias_aguardando[sender]}' não foi adicionada."
            del categorias_aguardando[sender]
        else:
            resposta = "Responda com 's' ou 'n' para adicionar a categoria."
    elif msg.strip().lower() == "relatorio":
        nome_arquivo = gerar_relatorio()

        url_arquivo = f"{obter_url_ngrok()}/static/{nome_arquivo}"

        resp = MessagingResponse()
        resp.message("Aqui está o seu relatório de gastos!")
        resp.message().media(url_arquivo)

        return str(resp)
    else:
        resposta = processar_gasto(msg, sender)

    resp = MessagingResponse()
    resp.message(resposta)

    return str(resp)

@app.route('/static/<filename>')
def serve_static(filename):
    return send_from_directory(STATIC_DIR, filename)

if __name__ == "__main__":
    app.run(debug=True)
