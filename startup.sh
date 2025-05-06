#!/bin/bash

# Запускаємо Ollama у фоні
ollama serve &

# Очікуємо запуску Ollama
sleep 10

# Запуск FastAPI
uvicorn main:app --host 0.0.0.0 --port 8000
