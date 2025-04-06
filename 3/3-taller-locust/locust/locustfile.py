from locust import HttpUser, task, between

class UsuarioDeCarga(HttpUser):
    wait_time = between(1, 2.5)

    @task
    def hacer_inferencia(self):
        payload = {
            "features": [3000, 45, 10, 100, 50, 200, 220, 230, 180, 300]
        }
        response = self.client.post("/predict/", json=payload)
        if response.status_code != 200:
            print("❌ Error en la inferencia:", response.text)
