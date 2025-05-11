from locust import HttpUser, task, between
import logging
import random
import json

class DiabetesAPILoadTester(HttpUser):
    wait_time = between(1, 2.5)
    model_loaded = False  # Class-level flag (not thread-safe in distributed tests)

    # Possible field values
    race_options = ["Caucasian", "AfricanAmerican", "?", "Other", "Asian"]
    gender_options = ["Female", "Male", "Unknown/Invalid"]
    age_options = ["[0-10)", "[10-20)", "[20-30)", "[30-40)", "[40-50)", 
                   "[50-60)", "[60-70)", "[70-80)", "[80-90)", "[90-100)"]
    payer_code_options = [
        "?", "MC", "MD", "HM", "UN", "BC", "SP", "CP", "SI", "DM", "CM",
        "CH", "PO", "WC", "OT", "OG", "MP", "FR"
    ]
    medication_status = ["No", "Steady", "Up", "Down"]
    change_options = ["No", "Ch"]
    diabetes_med_options = ["No", "Yes"]

    def on_start(self):
        """
        Se llama cuando cada usuario simulado va a hacer su solicitud.
        """
        if not DiabetesAPILoadTester.model_loaded:
            with self.client.post("/load_model/", catch_response=True) as response:
                if response.status_code == 200:
                    DiabetesAPILoadTester.model_loaded = True
                    logging.info("✅ Model loaded successfully.")
                    response.success()
                else:
                    logging.error(f"❌ Failed to load model: {response.status_code} - {response.text}")
                    response.failure("Failed to load model")

    def generate_random_patient(self):
        """
        Generate un paciente sintético aleatorio.
        """
        return {
            "race": random.choice(self.race_options),
            "gender": random.choice(self.gender_options),
            "age": random.choice(self.age_options),
            "time_in_hospital": random.randint(1, 14),
            "payer_code": random.choice(self.payer_code_options),
            "num_lab_procedures": random.randint(1, 132),
            "num_procedures": random.randint(0, 6),
            "num_medications": random.randint(1, 81),
            "number_outpatient": random.randint(0, 42),
            "number_emergency": random.randint(0, 76),
            "number_inpatient": random.randint(0, 21),
            "number_diagnoses": random.randint(1, 16),
            "metformin": random.choice(self.medication_status),
            "glipizide": random.choice(self.medication_status),
            "glyburide": random.choice(self.medication_status),
            "insulin": random.choice(self.medication_status),
            "change": random.choice(self.change_options),
            "diabetesmed": random.choice(self.diabetes_med_options)
        }

    @task
    def make_prediction(self):
        """
        Genera solicitudes de predicción con pacientes sintéticos distintos
        """
        payload = self.generate_random_patient()

        try:
            with self.client.post("/predict/", json=payload, catch_response=True) as response:
                if response.status_code == 200:
                    result = response.json()
                    logging.info(f"✅ Prediction: {result['prediction']}")
                    response.success()
                elif "Modelo no cargado" in response.text or "model not loaded" in response.text.lower():
                    logging.warning("⚠️ Model not loaded.")
                    response.failure("Model not loaded")
                else:
                    logging.error(f"❌ Prediction error: {response.status_code} - {response.text}")
                    response.failure(f"Prediction failed: {response.status_code}")
        except json.JSONDecodeError:
            logging.error("❌ Invalid JSON in response")
        except Exception as e:
            logging.error(f"❌ Request exception: {str(e)}")