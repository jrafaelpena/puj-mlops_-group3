import streamlit as st
import requests

API_URL = "http://inference-api:8989/predict/" 

st.set_page_config(page_title="Interfaz de Inferencia - Cobertura Forestal", layout="centered")

st.title("🌲 Inferencia - Modelo de Cobertura Forestal")
st.write("Complete los parámetros y presione el botón para obtener la predicción del modelo.")

with st.form(key='inference_form'):
    elevation = st.number_input("Elevation (m)", value=300, step=1)
    aspect = st.number_input("Aspect (°)", value=180, step=1)
    slope = st.number_input("Slope (°)", value=10, step=1)
    horizontal_distance_to_hydrology = st.number_input("Dist. horiz. a hidrología (m)", value=100, step=1)
    vertical_distance_to_hydrology = st.number_input("Dist. vert. a hidrología (m)", value=50, step=1)
    horizontal_distance_to_roadways = st.number_input("Dist. horiz. a carreteras (m)", value=200, step=1)
    hillshade_9am = st.number_input("Hillshade 9am (0-255)", min_value=0, max_value=255, value=150, step=1)
    hillshade_noon = st.number_input("Hillshade noon (0-255)", min_value=0, max_value=255, value=200, step=1)
    hillshade_3pm = st.number_input("Hillshade 3pm (0-255)", min_value=0, max_value=255, value=180, step=1)
    horizontal_distance_to_fire_points = st.number_input("Dist. horiz. a puntos de incendio (m)", value=300, step=1)
    
    submit_button = st.form_submit_button(label="🔍 Realizar Inferencia")

if submit_button:
    payload = {
        "features": [
            elevation, aspect, slope, horizontal_distance_to_hydrology,
            vertical_distance_to_hydrology, horizontal_distance_to_roadways,
            hillshade_9am, hillshade_noon, hillshade_3pm,
            horizontal_distance_to_fire_points
        ]
    }
    
    try:
        response = requests.post(API_URL, json=payload, timeout=10)
        if response.status_code == 200:
            result = response.json()
            st.success("✅ ¡Inferencia exitosa!")
            st.write("**Predicción:**", result["prediction"][0])
        else:
            st.error(f"❌ Error en la inferencia. Código de respuesta: {response.status_code}")
            st.write(response.text)
    except Exception as e:
        st.error(f"🚫 No se pudo conectar con la API. Error: {e}")

