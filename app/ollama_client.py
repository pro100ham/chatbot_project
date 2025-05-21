from transformers import AutoTokenizer
from sentence_transformers import SentenceTransformer
from fastapi import logger
import requests
import textwrap
import faiss
import os
import hashlib
import json
import re
from dotenv import load_dotenv

load_dotenv()

class OllamaClient:
    def __init__(self, text_path="app/documents/university_texts.txt"):
        env_mode = os.getenv("ACTIVE_ENV", "local")
        self.MODEL_NAME = os.getenv("MODEL_NAME", "mistral")
        self.FORMAT_HINT = (
            "Відформатуй результат у HTML (використовуй <p>, <ul>, <li>, <strong>, якщо доречно, до 100 слів. Не використовуй ```html)"
        )
        self.INSTRUCTION_FOR_ACTION = (
                "Якщо питання стосується проблем або запитів, які вимагають дій від адміністрації, "
                "в кінці своєї відповіді просто встав фразу '▶ Створити тікет'. Але тільки коли це доречно до запиту користувача"
                "Це означає, що користувачу буде показано форму для відправки запиту. "
                "Не описуй процес створення тікету, просто дай лаконічну відповідь та покажи, що готовий передати звернення.\n"
        )

        if env_mode == "docker":
            self.url = os.getenv("DOCKER_OLLAMA_URL") + "/generate"
        else:
            self.url = os.getenv("LOCAL_OLLAMA_URL") + "/generate"

        if not self.url:
            raise ValueError("Ollama URL is not defined. Check your .env configuration.")

        with open(text_path, encoding="utf-8") as f:
            raw_text = f.read()
        wrapped_chunks = textwrap.wrap(
            raw_text, width=500, break_long_words=False, break_on_hyphens=False
        )
        self.chunks = [f"[Розділ {i+1}]\n{chunk}" for i, chunk in enumerate(wrapped_chunks)]

        self.model = SentenceTransformer("intfloat/multilingual-e5-small")
        self.embeddings = self.model.encode(self.chunks, convert_to_numpy=True)

        self.tokenizer = AutoTokenizer.from_pretrained("EleutherAI/gpt-neox-20b")
        self.dimension = self.embeddings.shape[1]
        self.index = faiss.IndexFlatL2(self.dimension)
        self.index.add(self.embeddings)

        self.cache = {}

    def hash_question(self, question: str) -> str:
        return hashlib.sha256(question.encode("utf-8")).hexdigest()

    def retrieve_context(self, question: str, top_k: int = 6, max_tokens: int = 3500) -> str:
        question_vector = self.model.encode([question], convert_to_numpy=True)
        distances, indices = self.index.search(question_vector, top_k)

        context_chunks = [self.chunks[i] for i in indices[0] if i != -1]

        print(f"[DEBUG] Distances: {distances}")
        print(f"[DEBUG] Indices: {indices}")
        print(f"[DEBUG] Retrieved {len(context_chunks)} context chunks")

        for i, chunk in enumerate(context_chunks):
            print(f"[CONTEXT {i+1}] >>> {chunk[:150]}...")

        context = "\n\n".join(context_chunks)
        context = self.truncate_by_tokens(context, max_tokens)

        print(f"[DEBUG] Final context length (chars): {len(context)}")
        return context

    def truncate_by_tokens(self, prompt: str, max_tokens: int = 4000) -> str:
        tokens = self.tokenizer.encode(prompt, add_special_tokens=False, truncation=True, max_length=max_tokens)
        return self.tokenizer.decode(tokens[:max_tokens], skip_special_tokens=True)

    def build_prompt(self, context: str, question: str, stream: bool = False) -> str:
        prompt = (
            "Ти — розумний україномовний асистент УКУ. Відповідай на запитання, використовуючи наведений контекст.\n"
            "Якщо питання стосується проблем або запитів, які вимагають дій від адміністрації, \n"
            "Не вигадуй інформацію, якщо її немає у контексті.\n\n"
            f"Контекст:\n{context}\n\n"
            f"Питання: {question}\n"
        )
        
        prompt += f"\n\n{self.INSTRUCTION_FOR_ACTION}"
        
        if stream:
            prompt += f"Стиль відповіді: {self.FORMAT_HINT}\n"
        return prompt + "Відповідь:"

    def ask(self, question: str):
        q_hash = self.hash_question(question)
        if q_hash in self.cache:
            print("[CACHE HIT] Returning cached answer.")
            return self.cache[q_hash]

        context = self.retrieve_context(question)
        prompt = self.build_prompt(context, question, stream=False)
        prompt = self.truncate_by_tokens(prompt, max_tokens=2048)

        payload = {
            "model": self.MODEL_NAME,
            "prompt": prompt,
            "stream": False
        }

        response = requests.post(self.url, json=payload)
        response.raise_for_status()
        answer = response.json()["response"]
        self.cache[q_hash] = answer
        return answer

    def ask_stream(self, question: str):
        context = self.retrieve_context(question)
        prompt = self.build_prompt(context, question, stream=True)
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
            MODEL_NAME = os.getenv("MODEL_NAME", "mistral")

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
            f"Основна мова спілкування це українська та англійська. "
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
