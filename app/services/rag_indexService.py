import os
import json
import textwrap
import faiss
from sentence_transformers import SentenceTransformer

class RAGIndex:
    def __init__(self, text_path= "university_texts.txt", index_path="app/documents/rag_index.faiss", chunks_path="app/documents/rag_chunks.json", chunk_size=500):
        self.text_path = text_path
        self.index_path = index_path
        self.chunks_path = chunks_path
        self.chunk_size = chunk_size
        self.model = SentenceTransformer("intfloat/multilingual-e5-small")
        self.chunks = []
        self.embeddings = None
        self.index = None

    def prepare_chunks(self):
        if not os.path.exists(self.text_path):
            raise FileNotFoundError(f"❌ Файл не знайдено: {self.text_path}")

        with open(self.text_path, encoding="utf-8") as f:
            raw_text = f.read()

        if not raw_text.strip():
            raise ValueError("⚠️ Файл порожній або не містить тексту")

        raw_chunks = textwrap.wrap(
            raw_text,
            width=self.chunk_size,
            break_long_words=False,
            break_on_hyphens=False
        )
        self.chunks = [chunk.strip() for chunk in raw_chunks if len(chunk.strip()) > 50]
        print(f"✅ Розбито на {len(self.chunks)} чанків")

    def build_index(self):
        if not self.chunks:
            raise RuntimeError("❌ Немає чанків для індексації")
        self.embeddings = self.model.encode(self.chunks, convert_to_numpy=True)
        dimension = self.embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(self.embeddings)
        print(f"✅ Створено FAISS-індекс з розмірністю {dimension}")

    def save(self):
        faiss.write_index(self.index, self.index_path)
        with open(self.chunks_path, "w", encoding="utf-8") as f:
            json.dump(self.chunks, f, ensure_ascii=False, indent=2)
        print(f"📦 Збережено:\n- індекс → {self.index_path}\n- чанки → {self.chunks_path}")

    def run(self):
        self.prepare_chunks()
        self.build_index()
        self.save()
        return len(self.chunks)
