# 🤖 ChatBot Project

Цей проєкт — це чат-бот на базі FastAPI, який використовує Ollama для обробки запитів з використанням LLM-моделей (наприклад, Mistral). Проєкт легко розгортається через Docker Compose та може бути задеплоєний на Azure Virtual Machine.

## ⚙️ Структура проєкту

```
chatbot_project/
│
├── main.py               # Головний FastAPI додаток
├── startup.sh            # Скрипт запуску FastAPI
├── .env                  # Змінні середовища
├── requirements.txt      # Python-залежності
├── Dockerfile            # Docker-образ FastAPI
├── docker-compose.yml    # Compose файл (FastAPI + Ollama)
└── app/                  # (опціонально) додаткові модулі
```

## 🚀 Швидкий старт (локально через Docker)

### 1. Встанови Docker та Docker Compose

- [Docker Desktop](https://www.docker.com/products/docker-desktop)

### 2. Склонуй проєкт:

```bash
git clone https://github.com/pro100ham/chatbot_project.git
cd chatbot_project
```

### 3. Створи `.env` файл

```env
OLLAMA_HOST=http://localhost:11434
```

### 4. Запусти проєкт:

```bash
docker-compose up --build
```

Після запуску доступ до FastAPI:  
📍 [http://localhost:8000/docs](http://localhost:8000/docs)

---

## ☁️ Деплой на Azure VM

### 1. Підключись до VM по SSH

```bash
ssh -i your_key.pem azureuser@<your-vm-ip>
```

### 2. Встанови Docker та Docker Compose

```bash
sudo apt update
sudo apt install -y docker.io docker-compose
sudo usermod -aG docker $USER
```

Вийди і знову зайди в SSH для оновлення прав.

### 3. Скопіюй проєкт на VM

```bash
scp -r -i your_key.pem ./chatbot_project azureuser@<your-vm-ip>:/home/azureuser/
```

### 4. Запусти на сервері

```bash
cd chatbot_project
docker-compose up --build -d
```

### 5. Перевір

Перевір, чи працює FastAPI:  
📍 `http://<your-vm-ip>:8000`

---

## 🧠 Модель Ollama

Усередині контейнера `ollama` автоматично завантажується модель:

```yaml
command: >
  sh -c "ollama pull mistral && ollama serve"
```
якщо ні -> http://localhost:11434/api/pull

Ви можете змінити модель, оновивши цю команду у `docker-compose.yml`.

---

## 🔗 Корисні посилання

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Ollama](https://ollama.com/)
- [Docker Docs](https://docs.docker.com/)
- [Azure VM Docs](https://learn.microsoft.com/en-us/azure/virtual-machines/)

---

## 🛠 TODO

- [ ] Додати авторизацію
- [ ] Підключити базу даних
- [ ] Додати фронтенд-інтерфейс

---

## 📄 Ліцензія

MIT License © 2025