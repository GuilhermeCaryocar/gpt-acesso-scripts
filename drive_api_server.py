from flask import Flask, request, jsonify
import os
import io
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload
from google.auth.transport.requests import Request

app = Flask(__name__)

# Escopos necessários
SCOPES = ['https://www.googleapis.com/auth/drive']
CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'token.json'

def get_drive_service():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
    return build('drive', 'v3', credentials=creds)

@app.route('/listar-scripts', methods=['GET'])
def listar_scripts():
    service = get_drive_service()
    query = (
        "name contains '.ps1' or name contains '.py' or name contains '.sh'"
    )
    results = service.files().list(
        q=query,
        fields="files(id, name, mimeType)",
        corpora="user",
        includeItemsFromAllDrives=True,
        supportsAllDrives=True
    ).execute()
    arquivos = results.get('files', [])
    return jsonify(arquivos)

@app.route('/ler-script', methods=['GET'])
def ler_script():
    nome = request.args.get('nome')
    if not nome:
        return 'Parâmetro "nome" é obrigatório', 400

    service = get_drive_service()
    query = f"name='{nome}'"
    result = service.files().list(q=query, fields="files(id, name)").execute()
    arquivos = result.get('files', [])
    if not arquivos:
        return 'Arquivo não encontrado', 404

    file_id = arquivos[0]['id']
    request_drive = service.files().get_media(fileId=file_id)
    buf = io.BytesIO()
    downloader = MediaIoBaseDownload(buf, request_drive)
    done = False
    while not done:
        status, done = downloader.next_chunk()
    buf.seek(0)
    return buf.read().decode('utf-8')

@app.route('/salvar-script', methods=['POST'])
def salvar_script():
    data = request.json
    nome = data.get('nome')
    conteudo = data.get('conteudo')

    if not nome or not conteudo:
        return 'Campos "nome" e "conteudo" são obrigatórios', 400

    service = get_drive_service()
    result = service.files().list(q=f"name='{nome}'", fields="files(id, name)").execute()
    arquivos = result.get('files', [])

    conteudo_io = io.BytesIO(conteudo.encode('utf-8'))
    media = MediaIoBaseUpload(conteudo_io, mimetype='text/plain', resumable=True)

    if arquivos:
        file_id = arquivos[0]['id']
        atualizado = service.files().update(fileId=file_id, media_body=media).execute()
    else:
        metadata = {'name': nome, 'mimeType': 'text/plain'}
        novo = service.files().create(body=metadata, media_body=media).execute()

    return jsonify({'status': 'salvo', 'nome': nome})

if __name__ == '__main__':
    app.run(port=5000)
