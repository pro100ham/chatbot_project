#!/bin/bash

# Запускаємо Ollama у фоні
ollama serve &

# Очікуємо запуску Ollama
sleep 10

# Якщо модель ще не завантажена — качаємо
ollama list | grep llama3 || ollama pull llama3

# Запуск FastAPI
uvicorn main:app --host 0.0.0.0 --port 8000
