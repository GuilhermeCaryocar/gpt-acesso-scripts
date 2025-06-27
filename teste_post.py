import requests

url = 'http://127.0.0.1:5000/salvar-script'
dados = {
    'nome': 'subido_pelo_api.ps1',
    'conteudo': 'Write-Output "Este script foi criado via API."'
}
resposta = requests.post(url, json=dados)

print(resposta.status_code)
print(resposta.text)
