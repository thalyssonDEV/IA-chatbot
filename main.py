import os
import io
import base64
import logging
import uuid
import time
from typing import Optional

import google.generativeai as genai
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv
from PIL import Image

# --- Configuração do Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# --- Armazenamento de Sessão em Memória ---
# Este dicionário irá guardar as sessões de chat.
# Formato: { "session_id": (history_object, last_access_timestamp) }
chat_sessions = {}
SESSION_EXPIRATION_SECONDS = 1800  # 30 minutos

# --- Configuração da API do Gemini ---
model = None
try:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("A variável de ambiente GEMINI_API_KEY não foi encontrada no arquivo .env")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name="gemini-2.5-flash")
    logging.info("Modelo Gemini inicializado e pronto para uso.")
except Exception as e:
    logging.critical(f"Falha crítica ao inicializar a API do Gemini: {e}")

# --- Configuração do FastAPI ---
app = FastAPI()

class ChatRequest(BaseModel):
    text: Optional[str] = ""
    image_base64: Optional[str] = None
    language: Optional[str] = "Português (Brasil)"
    session_id: Optional[str] = None

# Monta o diretório de imagens estáticas
app.mount("/images", StaticFiles(directory="images"), name="images")

@app.get("/")
async def read_index():
    """Serve a página principal do chat."""
    return FileResponse('templates/index.html')

@app.post("/chat")
async def chat(request: ChatRequest):
    """Processa as requisições de chat, gerenciando o histórico em memória."""
    if not model:
        raise HTTPException(status_code=503, detail="O serviço de IA não está disponível.")

    if not request.text and not request.image_base64:
        raise HTTPException(status_code=400, detail="É necessário enviar texto ou imagem.")

    try:
        session_id = request.session_id
        history = []

        # --- Lógica de gerenciamento de sessão em memória ---
        if session_id and session_id in chat_sessions:
            saved_history, last_access = chat_sessions[session_id]
            # Verifica se a sessão expirou
            if time.time() - last_access < SESSION_EXPIRATION_SECONDS:
                logging.info(f"Continuando sessão de chat existente: {session_id}")
                history = saved_history
            else:
                logging.info(f"Sessão {session_id} expirada. Iniciando nova.")
                del chat_sessions[session_id]
                session_id = None  # Força a criação de uma nova sessão

        if not session_id:
            session_id = str(uuid.uuid4())
            logging.info(f"Iniciando nova sessão de chat: {session_id}")

        convo = model.start_chat(history=history)
        prompt_parts = []

        # Adiciona a imagem ao prompt, se existir
        if request.image_base64:
            try:
                image_data = base64.b64decode(request.image_base64)
                img = Image.open(io.BytesIO(image_data))
                prompt_parts.append(img)
            except Exception as e:
                logging.error(f"Erro ao processar imagem em base64: {e}")
                raise HTTPException(status_code=400, detail="Formato de imagem inválido ou corrompido.")

        # Adiciona o texto ao prompt, incluindo o idioma e um prompt padrão para imagens
        prompt_text = request.text
        if not prompt_text and request.image_base64:
            prompt_text = "Descreva esta imagem."
        
        full_prompt = f"Responda em {request.language}. {prompt_text}"
        prompt_parts.append(full_prompt)

        # --- Lógica de envio unificada e com memória ---
        logging.info(f"Enviando prompt stateful para a sessão {session_id}.")
        response_from_api = convo.send_message(prompt_parts)

        # --- Salva o histórico atualizado na memória ---
        chat_sessions[session_id] = (convo.history, time.time())
        logging.info(f"Histórico da sessão {session_id} salvo/atualizado na memória.")

        if not response_from_api.text:
            logging.warning(f"Resposta da API para a sessão {session_id} está vazia. Feedback: {response_from_api.prompt_feedback}")
            raise HTTPException(status_code=500, detail="A API não retornou uma resposta de texto válida.")

        return {"response": response_from_api.text, "session_id": session_id}

    except Exception as e:
        logging.critical(f"Erro inesperado no endpoint /chat: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Ocorreu um erro interno inesperado no servidor.")