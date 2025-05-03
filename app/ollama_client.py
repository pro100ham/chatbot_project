import requests
from sentence_transformers import SentenceTransformer
import faiss
import os
from dotenv import load_dotenv

load_dotenv()

class OllamaClient:
    def __init__(self, text_path="app/documents/university_texts.txt"):

        env_mode = os.getenv("ACTIVE_ENV", "local")

        if env_mode == "docker":
            self.url = os.getenv("DOCKER_OLLAMA_URL") + "/chat"
        else:
            self.url = os.getenv("LOCAL_OLLAMA_URL") + "/chat"
            
        if not self.url:
            raise ValueError("Ollama URL is not defined. Check your .env configuration.")
            
        with open(text_path, encoding="utf-8") as f:
            self.chunks = f.read().split("\n\n")

        self.model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
        self.embeddings = self.model.encode(self.chunks, convert_to_numpy=True)

        self.dimension = self.embeddings.shape[1]
        self.index = faiss.IndexFlatL2(self.dimension)
        self.index.add(self.embeddings)

    def retrieve_context(self, question: str, top_k: int = 1) -> str:
        question_vector = self.model.encode([question], convert_to_numpy=True)
        distances, indices = self.index.search(question_vector, top_k)
        context_chunks = [self.chunks[i] for i in indices[0]]
        return "\n".join(context_chunks)

    def ask(self, question: str):
        context = self.retrieve_context(question)
        prompt = f"Контекст:\n{context}\n\nПитання: {question}\nВідповідь:"

        payload = {
            "model": "mistral",
            "messages": [{"role": "user", "content": prompt}],
            "stream": False
        }

        response = requests.post(self.url, json=payload)
        response.raise_for_status()
        return response.json()["message"]["content"]

    def ask_stream(self, question: str):
        context = self.retrieve_context(question)
        prompt = f"Контекст:\n{context}\n\nПитання: {question}\nВідповідь:"

        payload = {
            "model": "mistral",
            "messages": [{"role": "user", "content": prompt}],
            "stream": True
        }

        response = requests.post(self.url, json=payload, stream=True)
        response.raise_for_status()

        for line in response.iter_lines():
            if line:
                yield line.decode("utf-8")
                
    def postCall(self, model_name: str):
        try:
            payload = {"name": model_name}
            response = requests.post(f"{self.url}/pull", json=payload)
            response.raise_for_status()
            print(f"✅ Model '{model_name}' pulled successfully")
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to pull model '{model_name}': {e}")