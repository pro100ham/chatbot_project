from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.ollama_client import OllamaClient
from fastapi.staticfiles import StaticFiles
import logging
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Request
from fastapi.responses import StreamingResponse
import json
import time

app = FastAPI()
app.mount("/static", StaticFiles(directory="app/static"), name="static")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

templates = Jinja2Templates(directory="app/templates")
client = OllamaClient()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],
)

@app.on_event("startup")
async def load_model_on_startup():
    client.postCall()

@app.on_event("shutdown")
def shutdown_event():
    logger.info("Application shutdown")

# Головна сторінка
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/ask", response_class=HTMLResponse)
async def ask(request: Request, question: str):
    answer = client.ask(question)
    return StreamingResponse(content={"answer": str(answer)})

# @app.get("/ask-stream")
# async def ask_stream(question: str):
#     def event_stream():
#         start_time = time.time()
#         buffer = ""
#         for chunk in client.ask_stream(question):
#             try:
#                 buffer += chunk
#                 data = json.loads(chunk.decode("utf-8"))
#                 response_piece = data.get("response")
#                 if response_piece:
#                     yield f"data: {response_piece}\n\n"
#                 if data.get("done"):
#                     break
#             except Exception as e:
#                 logger.error(f"Chunk decode or parse error: {e}")
#                 continue
#     end_time = time.time()
#     return StreamingResponse(event_stream(), media_type="text/event-stream")

@app.get("/ask-stream")
async def ask_stream(question: str):
    def event_stream():
        for chunk in client.ask_stream(question):
            try:
                # Якщо chunk — це вже рядок (str), не декодуємо
                data = json.loads(chunk)
                response_piece = data.get("response")
                if response_piece:
                    yield f"data: {response_piece}\n\n"
                if data.get("done"):
                    break
            except Exception as e:
                logger.error(f"Chunk decode or parse error: {e}")
                continue

    return StreamingResponse(event_stream(), media_type="text/event-stream")
