from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from app.ollama_client import OllamaClient
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import logging
import json
import time

app = FastAPI()
app.mount("/static", StaticFiles(directory="app/static"), name="static")

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

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

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/ask", response_class=JSONResponse)
async def ask(request: Request, question: str):
    answer = client.ask(question)
    return JSONResponse(content={"answer": str(answer)})

@app.get("/intro")
async def intro():
     return StreamingResponse(
        stream_ollama_response(client.preSessionConfiguration)(),
        media_type="text/event-stream"
    )


@app.get("/ask-stream")
async def ask_stream(question: str):
    return StreamingResponse(
        stream_ollama_response(client.ask_stream, question)(),
        media_type="text/event-stream"
    )

def stream_ollama_response(generator_func, *args):
    def stream():
        for chunk in generator_func(*args):
            try:
                if isinstance(chunk, bytes):
                    chunk = chunk.decode("utf-8")

                data = json.loads(chunk)
                response_piece = data.get("response")
                if response_piece:
                    yield f"data: {response_piece}\n\n"
                if data.get("done"):
                    break
            except Exception as e:
                logger.error(f"Chunk parse error: {e}")
                continue
    return stream
