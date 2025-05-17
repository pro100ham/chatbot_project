import os
import requests

class CRMClient:
    def forward_to_crm(self, question: str, answer: str, user_email: str = "anonymous@bot.ua") -> dict:
        crm_url = os.getenv("CRM_ENDPOINT_URL")
        api_key = os.getenv("CRM_API_KEY")

        payload = {
            "subject": "Запит через чат-бот",
            "description": f"Користувач запитав:\n{question}\n\nВідповідь:\n{answer}",
            "user_email": user_email,
            "priority": "normal"
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

        try:
            response = requests.post(crm_url, json=payload, headers=headers)
            response.raise_for_status()
            print("[CRM] Тікет успішно створено")
            return response.json()
        except requests.RequestException as e:
            print(f"[CRM] Помилка надсилання тікету: {e}")
            return {"error": str(e)}