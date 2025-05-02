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
MODEL_NAME = "mistral"

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
def load_model_on_startup():
    client.postCall(MODEL_NAME)

# Головна сторінка
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/ask", response_class=HTMLResponse)
async def ask(request: Request, question: str):
    answer = client.ask(question)
    return StreamingResponse(content={"answer": str(answer)})

@app.get("/ask-stream")
async def ask_stream(question: str):
    logger.info(f"Stream started for question: {question}")

    def event_stream():
        start_time = time.time()
        try:
            content = ""

            for chunk in client.ask_stream(question):
                try:
                    data = json.loads(chunk)
                    current_content = data.get("message", {}).get("content", "")
                    
                    if current_content:
                        content += current_content
                        yield f"data: {current_content}\n\n"

                except json.JSONDecodeError:
                    logger.error("JSON decoding error in chunk response")
                    continue
            
            end_time = time.time()
            response_time = end_time - start_time
            logger.info(f"Total response time for question '{question}': {response_time:.2f} seconds")
        except GeneratorExit:
            pass
        finally:
            end_time = time.time()
            logging.info(f"Total response time: {end_time - start_time:.2f} seconds")
    return StreamingResponse(event_stream(), media_type="text/event-stream")