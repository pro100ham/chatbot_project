from transformers import AutoTokenizer
from fastapi import logger
import requests
from sentence_transformers import SentenceTransformer
import faiss
import os
from dotenv import load_dotenv


load_dotenv()

class OllamaClient:
    def __init__(self, text_path="app/documents/university_texts.txt"):
        env_mode = os.getenv("ACTIVE_ENV", "local")
        self.MODEL_NAME = os.getenv("MODEL_NAME", "phi:2")
        self.FORMAT_HINT =  "Відформатуй результат у HTML (використовуй <p>, <ul>, <li>, <strong>, якщо доречно, до 100 слів"
        
        if env_mode == "docker":
            self.url = os.getenv("DOCKER_OLLAMA_URL") + "/generate"
        else:
            self.url = os.getenv("LOCAL_OLLAMA_URL") + "/generate"
            
        if not self.url:
            raise ValueError("Ollama URL is not defined. Check your .env configuration.")
            
        with open(text_path, encoding="utf-8") as f:
            self.chunks = f.read().split("\n\n")

        self.tokenizer = AutoTokenizer.from_pretrained("EleutherAI/gpt-neox-20b")
        self.model = SentenceTransformer("intfloat/multilingual-e5-small")
        self.embeddings = self.model.encode(self.chunks, convert_to_numpy=True)

        self.dimension = self.embeddings.shape[1]
        self.index = faiss.IndexFlatL2(self.dimension)
        self.index.add(self.embeddings)

    def retrieve_context(self, question: str, top_k: int = 8, max_tokens: int = 3500) -> str:
        question_vector = self.model.encode([question], convert_to_numpy=True)
        distances, indices = self.index.search(question_vector, top_k)

        # НЕ фільтруємо, просто беремо top_k chunks
        context_chunks = [self.chunks[i] for i in indices[0] if i != -1]

        print(f"[DEBUG] Distances: {distances}")
        print(f"[DEBUG] Indices: {indices}")
        print(f"[DEBUG] Retrieved {len(context_chunks)} context chunks")

        context = "\n\n".join(context_chunks)
        context = self.truncate_by_tokens(context, max_tokens)

        print(f"[DEBUG] Final context length (chars): {len(context)}")
        return context

    def truncate_by_tokens(self, prompt: str, max_tokens: int = 4000) -> str:
        tokens = self.tokenizer.encode(prompt, add_special_tokens=False, truncation=True, max_length=4000)
        if len(tokens) <= max_tokens:
            return prompt
        truncated_tokens = tokens[:max_tokens]
        return self.tokenizer.decode(truncated_tokens, skip_special_tokens=True)

    def ask(self, question: str):
        context = self.retrieve_context(question)
        prompt = f"Контекст:\n{context}\n\nПитання: {question}\nВідповідь:"
        prompt = self.truncate_by_tokens(prompt, max_tokens=2048)

        payload = {
            "model": self.MODEL_NAME,
            "prompt": prompt,
            "stream": False
        }

        response = requests.post(self.url, json=payload)
        response.raise_for_status()
        return response.json()["response"]

    def ask_stream(self, question: str):
        context = self.retrieve_context(question)
        #prompt = f"Контекст:\n{context}\n\nПитання: {question}\nВідповідь ({self.FORMAT_HINT})"
        prompt = (
            "Ти — розумний україномовний асистент УКУ. Відповідай на запитання, використовуючи наведений контекст.\n"
            "Використовуй виключно інформацію з блоку 'Контекст'. Не вигадуй, якщо не знаєш.\n\n"
            f"Контекст:\n{context}\n\n"
            f"Питання: {question}\n"
            f"Стиль відповіді: {self.FORMAT_HINT}\n"
            "Відповідь:"
        )
        print(prompt)
        prompt = self.truncate_by_tokens(prompt, max_tokens=2048)   

        payload = {
            "model": self.MODEL_NAME,
            "prompt": prompt,
            "stream": True
        }

        with requests.post(self.url, json=payload, stream=True) as response:
            response.raise_for_status()
            for line in response.iter_lines(decode_unicode=True):
                if not line.strip():
                    continue
                yield line
                
    def postCall(self):
        try:
            env_mode = os.getenv("ACTIVE_ENV", "local")
            MODEL_NAME = os.getenv("MODEL_NAME", "phi:2")

            payload = {"name": MODEL_NAME}

            if env_mode == "docker":
                url = os.getenv("DOCKER_OLLAMA_URL") + "/pull"
            else:
                url = os.getenv("LOCAL_OLLAMA_URL") + "/pull"
                
            response = requests.post(url, json=payload)
            response.raise_for_status()
            print(f"✅ Model '{MODEL_NAME}' pulled successfully")
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to pull model '{MODEL_NAME}': {e}")
             
    def preSessionConfiguration(self):
        prompt = (
            f"Ти онлайн асистент Українського Католицького Університету. "
            f"Основна мова спілкування це українська та англіська. "
            f"Відповідай коротко, чітко та ввічливо, максимум 3 речення. "
            f"Тебе звати Оленка (жіноче ім'я). Ти допомагаєш користувачам дізнатись більше про університет.\n\n"
            f"Привітайся і запропонуй допомогу."
        )

        payload = {
            "model": self.MODEL_NAME,
            "prompt": prompt,
            "stream": True
        }

        with requests.post(self.url, json=payload, stream=True) as response:
            response.raise_for_status()
            for line in response.iter_lines(decode_unicode=True):
                if not line.strip():
                    continue
                yield line

    def build_prompt(self, context: str, question: str, stream: bool = False) -> str:
        base_prompt = (
            "Ти — розумний україномовний асистент УКУ. Відповідай на запитання, використовуючи наведений контекст.\n"
            "Якщо інформації в контексті недостатньо — скажи про це прямо.\n\n"
            f"Контекст:\n{context}\n\n"
            f"Питання: {question}\n"
        )
        if stream:
            base_prompt += f"Стиль відповіді: {self.FORMAT_HINT}\n"
        return base_prompt + "Відповідь:"