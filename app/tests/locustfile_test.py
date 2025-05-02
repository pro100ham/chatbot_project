from locust import HttpUser, task, between

class ChatBotUser(HttpUser):
    wait_time = between(1, 2)  # Очікування між запитами (в секундах)

    @task
    def ask_question(self):
        question = "Привіт, як справи?"
        with self.client.get(f"/ask-stream?question={question}", stream=True, catch_response=True) as response:
            if response.status_code == 200:
                try:
                    # Прочитати перші кілька стрімів
                    for i, line in enumerate(response.iter_lines()):
                        if b"data:" in line:
                            break  # Достатньо для перевірки
                        if i > 10:
                            break
                    response.success()
                except Exception as e:
                    response.failure(f"Streaming failed: {str(e)}")
            else:
                response.failure(f"Unexpected status code: {response.status_code}")
