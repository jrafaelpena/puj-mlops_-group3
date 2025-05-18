from locust import HttpUser, task, between
import random
import logging

class IrisAPILoadTester(HttpUser):
    """
    Sends one random prediction request per simulated user every second.
    """
    wait_time = between(1, 1)          # exactly 1 s, meets teacher spec
    model_loaded = False               # shared among greenlets

    def on_start(self):
        """
        Runs once per simulated user when it starts: ensure model is loaded.
        """
        if not IrisAPILoadTester.model_loaded:
            with self.client.post("/load_model/", catch_response=True) as resp:
                if resp.status_code == 200:
                    IrisAPILoadTester.model_loaded = True
                    logging.info("✅ Model loaded.")
                    resp.success()
                else:
                    resp.failure(f"Failed to load model: {resp.text}")

    # ------------------------------------------------------------------

    def generate_random_iris(self):
        """
        Returns a dict with valid random Iris measurements (0–10 cm).
        """
        return {
            "sepal_length": round(random.uniform(0.0, 10.0), 2),
            "sepal_width" : round(random.uniform(0.0, 10.0), 2),
            "petal_length": round(random.uniform(0.0, 10.0), 2),
            "petal_width" : round(random.uniform(0.0, 10.0), 2),
        }

    @task
    def make_prediction(self):
        """
        Sends one prediction request with a random sample.
        """
        payload = self.generate_random_iris()
        with self.client.post("/predict/", json=payload, catch_response=True) as resp:
            if resp.status_code == 200:
                pred = resp.json()
                logging.debug(f"✅ {payload} → {pred['species']} ({pred['prediction']})")
                resp.success()
            elif "Modelo no cargado" in resp.text:
                resp.failure("Model not loaded")
            else:
                resp.failure(f"Unexpected error {resp.status_code}: {resp.text}")