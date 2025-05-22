from rag_indexService import RAGIndex

if __name__ == "__main__":
    rag = RAGIndex("app/documents/university_texts.txt")
    count = rag.run()
    print(f"🔢 Збережено {count} чанків")
