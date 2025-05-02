from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

# Зчитування тексту
with open("university_texts.txt", encoding="utf-8") as f:
    chunks = f.read().split("\n\n")

# Векторизація
embeddings = model.encode(chunks, convert_to_numpy=True)

# FAISS індекс
dimension = embeddings.shape[1]
index = faiss.IndexFlatL2(dimension)
index.add(embeddings)

# Збереження
faiss.write_index(index, "university_faiss.index")