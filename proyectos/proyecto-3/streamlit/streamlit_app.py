import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import json
from typing import Dict, Any
import os

# Configure the app
st.set_page_config(
    page_title="Diabetes Readmission Predictor",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration
API_URL = os.getenv('API_URL', 'http://inference-api:8989')

# App title and description
st.title("🏥 Diabetes Readmission Prediction")
st.markdown("""
This application helps healthcare professionals predict the likelihood of patient readmission 
based on medical history and treatment information.
""")

# Function to load the model
def load_model():
    with st.spinner("Loading the model from MLflow..."):
        try:
            response = requests.post(f"{API_URL}/load_model/")
            data = response.json()
            return data
        except Exception as e:
            st.error(f"Failed to load model: {e}")
            return None

# Function to make prediction
def make_prediction(patient_data: Dict[str, Any]):
    with st.spinner("Generating prediction..."):
        try:
            response = requests.post(f"{API_URL}/predict/", json=patient_data)
            return response.json()
        except Exception as e:
            st.error(f"Prediction failed: {e}")
            return None

# Sidebar for model loading
with st.sidebar:
    st.header("Model Management")
    
    # Load model button
    if st.button("🔄 Load Model", type="primary", use_container_width=True):
        result = load_model()
        if result:
            st.success(result["message"])
            st.session_state["model_loaded"] = True
        else:
            st.error("Failed to load the model.")
            st.session_state["model_loaded"] = False
    
    # Display model status
    if "model_loaded" in st.session_state and st.session_state["model_loaded"]:
        st.success("✅ Model is loaded and ready")
    else:
        st.warning("⚠️ Model needs to be loaded before predictions")
    
    st.divider()
    st.markdown("### About")
    st.markdown("""
    Esta aplicación se conecta a un backend FastAPI que utiliza MLflow
    para gestionar y servir modelos de ML para la predicción de reingresos por diabetes.
    """)

# Create two columns for the form
col1, col2 = st.columns(2)

# Input form
with st.form("patient_data_form"):
    st.subheader("Patient Information")
    
    with col1:
        # Demographics
        race = st.selectbox(
            "Race",
            options=["Caucasian", "AfricanAmerican", "Asian", "Other", "?"]
        )
        
        gender = st.selectbox(
            "Gender",
            options=["Female", "Male", "Unknown/Invalid"]
        )
        
        age = st.selectbox(
            "Age Group",
            options=[
                "[0-10)", "[10-20)", "[20-30)", "[30-40)", "[40-50)",
                "[50-60)", "[60-70)", "[70-80)", "[80-90)", "[90-100)"
            ]
        )
        
        payer_code = st.selectbox(
            "Payer Code",
            options=[
                "?", "MC", "MD", "HM", "UN", "BC", "SP", "CP", "SI", "DM", "CM",
                "CH", "PO", "WC", "OT", "OG", "MP", "FR"
            ]
        )
        
        # Hospital visit data
        time_in_hospital = st.slider(
            "Time in Hospital (days)",
            min_value=1,
            max_value=14,
            value=3
        )
        
        num_lab_procedures = st.slider(
            "Number of Lab Procedures",
            min_value=1,
            max_value=132,
            value=45
        )
        
        num_procedures = st.slider(
            "Number of Procedures",
            min_value=0,
            max_value=6,
            value=1
        )
        
        num_medications = st.slider(
            "Number of Medications",
            min_value=1,
            max_value=81,
            value=16
        )
        
        number_diagnoses = st.slider(
            "Number of Diagnoses",
            min_value=1,
            max_value=16,
            value=7
        )
    
    with col2:
        # Previous visits
        number_outpatient = st.number_input(
            "Number of Outpatient Visits",
            min_value=0,
            max_value=42,
            value=0
        )
        
        number_emergency = st.number_input(
            "Number of Emergency Visits",
            min_value=0,
            max_value=76,
            value=0
        )
        
        number_inpatient = st.number_input(
            "Number of Inpatient Visits",
            min_value=0,
            max_value=21,
            value=0
        )
        
        # Medication information
        metformin = st.selectbox(
            "Metformin",
            options=["No", "Steady", "Up", "Down"]
        )
        
        glipizide = st.selectbox(
            "Glipizide",
            options=["No", "Steady", "Up", "Down"]
        )
        
        glyburide = st.selectbox(
            "Glyburide",
            options=["No", "Steady", "Up", "Down"]
        )
        
        insulin = st.selectbox(
            "Insulin",
            options=["No", "Steady", "Up", "Down"]
        )
        
        change = st.selectbox(
            "Medication Change",
            options=["No", "Ch"]
        )
        
        diabetesmed = st.selectbox(
            "Diabetes Medication",
            options=["No", "Yes"]
        )
    
    # Submit button
    submit_button = st.form_submit_button(
        label="🔍 Predict Readmission",
        type="primary",
        use_container_width=True
    )

# Process the form submission
if submit_button:
    if "model_loaded" not in st.session_state or not st.session_state["model_loaded"]:
        st.error("Please load the model first before making predictions.")
    else:
        # Collect form data
        patient_data = {
            "race": race,
            "gender": gender,
            "age": age,
            "time_in_hospital": time_in_hospital,
            "payer_code": payer_code,
            "num_lab_procedures": num_lab_procedures,
            "num_procedures": num_procedures,
            "num_medications": num_medications,
            "number_outpatient": number_outpatient,
            "number_emergency": number_emergency,
            "number_inpatient": number_inpatient,
            "number_diagnoses": number_diagnoses,
            "metformin": metformin,
            "glipizide": glipizide,
            "glyburide": glyburide,
            "insulin": insulin,
            "change": change,
            "diabetesmed": diabetesmed
        }
        
        # Make prediction
        prediction_result = make_prediction(patient_data)
        
        # Display results
        if prediction_result:
            st.divider()
            st.subheader("Prediction Result")
            
            result_cols = st.columns([2, 1])
            
            with result_cols[0]:
                # Show the prediction outcome
                prediction = prediction_result["prediction"]
                readmission_category = {
                    "<30": "Readmitted within 30 days",
                    ">30": "Readmitted after 30 days",
                    "NO": "Not readmitted"
                }.get(prediction, prediction)
                
                # Create color coding
                if prediction == "<30":
                    color = "red"
                    risk_level = "High Risk"
                elif prediction == ">30":
                    color = "orange"
                    risk_level = "Medium Risk"
                else:  # "NO"
                    color = "green"
                    risk_level = "Low Risk"
                
                st.markdown(f"""
                ### Patient is predicted to be:
                # <span style='color:{color};'>{readmission_category}</span>
                ## Risk Level: <span style='color:{color};'>{risk_level}</span>
                """, unsafe_allow_html=True)
                
                st.markdown(f"""
                **Model Information:**
                - Model Alias: {prediction_result.get('model_alias', 'champion')}
                - Model Version: {prediction_result.get('model_version', 'N/A')}
                """)
            
            with result_cols[1]:
                # Create a gauge chart for visualizing risk
                if prediction == "<30":
                    gauge_value = 85
                elif prediction == ">30":
                    gauge_value = 50
                else:  # "NO"
                    gauge_value = 15
                
                fig = px.pie(
                    values=[gauge_value, 100-gauge_value],
                    names=["Risk", ""],
                    hole=0.7,
                    color_discrete_sequence=[color, "#F0F2F6"]
                )
                
                fig.update_layout(
                    annotations=[dict(text=risk_level, x=0.5, y=0.5, font_size=20, showarrow=False)],
                    showlegend=False,
                    margin=dict(l=20, r=20, t=30, b=20),
                    height=250
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Prediction timestamp
                st.info("Prediction made on: " + pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"))

# Display history of predictions if available
if "predictions" in st.session_state and st.session_state["predictions"]:
    st.divider()
    st.subheader("Previous Predictions")
    
    for i, pred in enumerate(st.session_state["predictions"]):
        st.text(f"Patient {i+1}: {pred}")

# Footer
st.markdown("---")
st.markdown("Desarrollado por el grupo 3 | Proyecto 3: Machine Learning Operations")