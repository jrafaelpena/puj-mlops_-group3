import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
from typing import Dict, Any
import os
import numpy as np
from datetime import datetime

# Configure the app
st.set_page_config(
    page_title="House Price Predictor",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration
API_URL = os.getenv('API_URL', 'http://inference-api:8989')

# App title and description
st.title("🏠 House Price Prediction")
st.markdown("""
This application helps real estate professionals and home buyers predict house prices 
based on property characteristics and location information.
""")

# Sample data for examples
SAMPLE_HOUSES = [
    {"bed": 3, "bath": 2, "acre_lot": 0.25, "city": "clarks summit", "state": "pennsylvania", "zip_code": "18411", "house_size": 1684, "expected_price": 214000},
    {"bed": 3, "bath": 2, "acre_lot": 0.15, "city": "iowa city", "state": "iowa", "zip_code": "52240", "house_size": 1638, "expected_price": 239900},
    {"bed": 3, "bath": 3, "acre_lot": 0.17, "city": "phillips", "state": "wisconsin", "zip_code": "54555", "house_size": 2718, "expected_price": 204900},
    {"bed": 3, "bath": 2, "acre_lot": 0.2, "city": "addison", "state": "michigan", "zip_code": "49220", "house_size": 1792, "expected_price": 159900},
    {"bed": 4, "bath": 3, "acre_lot": 0.24, "city": "clarinda", "state": "iowa", "zip_code": "51632", "house_size": 1806, "expected_price": 249000},
    {"bed": 3, "bath": 2, "acre_lot": 0.2, "city": "troy", "state": "alabama", "zip_code": "36079", "house_size": 1775, "expected_price": 239000},
    {"bed": 3, "bath": 3, "acre_lot": 0.19, "city": "albuquerque", "state": "new mexico", "zip_code": "87120", "house_size": 2029, "expected_price": 290000},
    {"bed": 3, "bath": 2, "acre_lot": 0.14, "city": "round lake", "state": "illinois", "zip_code": "60073", "house_size": 1604, "expected_price": 244900},
    {"bed": 4, "bath": 2, "acre_lot": 0.03, "city": "philadelphia", "state": "pennsylvania", "zip_code": "19120", "house_size": 1716, "expected_price": 219500},
    {"bed": 3, "bath": 3, "acre_lot": 1.56, "city": "green township", "state": "new jersey", "zip_code": "07821", "house_size": 2948, "expected_price": 200000}
]

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
def make_prediction(house_data: Dict[str, Any]):
    with st.spinner("Generating prediction..."):
        try:
            response = requests.post(f"{API_URL}/predict/", json=house_data)
            return response.json()
        except Exception as e:
            st.error(f"Prediction failed: {e}")
            return None

# Function to format price
def format_price(price):
    return f"${price:,.0f}"

# Function to format datetime
def format_datetime(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S")

# Sidebar for model loading and examples
with st.sidebar:
    st.header("Model Management")
    
    # Load model button
    if st.button("🔄 Load Model", type="primary", use_container_width=True):
        result = load_model()
        if result:
            st.success(result["message"])
            st.session_state["model_loaded"] = True
            st.session_state["model_load_time"] = datetime.now()
            st.rerun()  # Refresh to show the updated timestamp
        else:
            st.error("Failed to load the model.")
            st.session_state["model_loaded"] = False
            if "model_load_time" in st.session_state:
                del st.session_state["model_load_time"]
    
    # Display model status
    if "model_loaded" in st.session_state and st.session_state["model_loaded"]:
        st.success("✅ Model is loaded and ready")
        
        # Display last load time if available
        if "model_load_time" in st.session_state:
            load_time = st.session_state["model_load_time"]
            st.info(f"📅 **Last loaded:** {format_datetime(load_time)}")
            
            # Calculate time since last load
            time_diff = datetime.now() - load_time
            hours = int(time_diff.total_seconds() // 3600)
            minutes = int((time_diff.total_seconds() % 3600) // 60)
            
            if hours > 0:
                time_since = f"{hours}h {minutes}m ago"
            else:
                time_since = f"{minutes}m ago"
            
            st.caption(f"⏱️ Loaded {time_since}")
    else:
        st.warning("⚠️ Model needs to be loaded before predictions")
    
    st.divider()
    
    # Sample houses section
    st.header("📊 Sample Properties")
    st.markdown("Try these example properties:")
    
    selected_sample = st.selectbox(
        "Choose a sample house:",
        options=range(len(SAMPLE_HOUSES)),
        format_func=lambda x: f"{SAMPLE_HOUSES[x]['city'].title()}, {SAMPLE_HOUSES[x]['state'].title()} - {SAMPLE_HOUSES[x]['bed']}bed/{SAMPLE_HOUSES[x]['bath']}bath",
        key="sample_selector"
    )
    
    if st.button("🏠 Load Sample Data", use_container_width=True):
        sample = SAMPLE_HOUSES[selected_sample]
        for key, value in sample.items():
            if key != "expected_price":
                st.session_state[f"form_{key}"] = value
        st.success("Sample data loaded!")
    
    st.divider()
    st.markdown("### About")
    st.markdown("""
    Esta aplicación se conecta a un backend FastAPI que utiliza MLflow
    para gestionar y servir modelos de ML para la predicción de precios de casas.
    """)

# Create two columns for the form
col1, col2 = st.columns(2)

# Input form
with st.form("house_data_form"):
    st.subheader("🏠 Property Information")
    
    with col1:
        # Property details
        bed = st.number_input(
            "Number of Bedrooms",
            min_value=1,
            max_value=190,
            value=st.session_state.get("form_bed", 3),
            help="Number of bedrooms in the house"
        )
        
        bath = st.number_input(
            "Number of Bathrooms",
            min_value=1,
            max_value=163,
            value=st.session_state.get("form_bath", 2),
            help="Number of bathrooms in the house"
        )
        
        house_size = st.number_input(
            "House Size (sq ft)",
            min_value=1500,
            max_value=1560780,
            value=st.session_state.get("form_house_size", 1656),
            help="Total house size in square feet"
        )
        
        acre_lot = st.number_input(
            "Lot Size (acres)",
            min_value=0.0,
            max_value=100000.0,
            value=st.session_state.get("form_acre_lot", 0.23),
            step=0.01,
            help="Lot size in acres"
        )
    
    with col2:
        # Location details
        city = st.text_input(
            "City",
            value=st.session_state.get("form_city", "pleasantville"),
            help="City where the house is located"
        ).lower()
        
        state = st.text_input(
            "State",
            value=st.session_state.get("form_state", "new jersey"),
            help="State where the house is located"
        ).lower()
        
        zip_code = st.text_input(
            "ZIP Code",
            value=str(st.session_state.get("form_zip_code", "8232")),
            help="ZIP code of the location (4-5 digits)",
            max_chars=5
        )
        
        # Add some spacing
        st.markdown("### Quick Property Stats")
        
        # Calculate some quick stats
        price_per_sqft_est = st.empty()
        if house_size > 0:
            estimated_price_per_sqft = 150  # rough estimate
            st.info(f"**Estimated price per sq ft:** ${estimated_price_per_sqft}")
            st.info(f"**Total estimated area:** {house_size:,} sq ft")
            st.info(f"**Lot size:** {acre_lot} acres")
    
    # Submit button
    submit_button = st.form_submit_button(
        label="💰 Predict House Price",
        type="primary",
        use_container_width=True
    )

# Process the form submission
if submit_button:
    if "model_loaded" not in st.session_state or not st.session_state["model_loaded"]:
        st.error("Please load the model first before making predictions.")
    else:
        # Validate ZIP code format
        if not zip_code.isdigit() or len(zip_code) < 4 or len(zip_code) > 5:
            st.error("Please enter a valid ZIP code (4-5 digits)")
        else:
            # Collect form data with correct data types
            house_data = {
                "bed": int(bed),
                "bath": int(bath),
                "acre_lot": float(acre_lot),  # Ensure float type
                "city": city.lower(),
                "state": state.lower(),
                "zip_code": str(zip_code),  # Ensure string type
                "house_size": int(house_size)
            }
            
            # Make prediction
            prediction_result = make_prediction(house_data)
            
            # Display results
            if prediction_result:
                st.divider()
                st.subheader("💰 Price Prediction Result")
                
                result_cols = st.columns([2, 1, 1])
                
                with result_cols[0]:
                    # Show the prediction outcome
                    predicted_price = prediction_result["predicted_price"]
                    
                    st.markdown(f"""
                    ### Predicted House Price:
                    # <span style='color:#1f77b4; font-size: 48px;'>{format_price(predicted_price)}</span>
                    """, unsafe_allow_html=True)
                    
                    # Price per square foot
                    price_per_sqft = predicted_price / house_size
                    st.markdown(f"""
                    **Price per Square Foot:** ${price_per_sqft:.2f}
                    """)
                    
                    st.markdown(f"""
                    **Model Information:**
                    - Model Alias: {prediction_result.get('model_alias', 'champion')}
                    - Model Version: {prediction_result.get('model_version', 'N/A')}
                    """)
                
                with result_cols[1]:
                    # Create a gauge chart for price range
                    # Determine price category
                    if predicted_price < 200000:
                        price_category = "Budget"
                        color = "#28a745"
                    elif predicted_price < 300000:
                        price_category = "Mid-Range"
                        color = "#ffc107"
                    elif predicted_price < 500000:
                        price_category = "Premium"
                        color = "#fd7e14"
                    else:
                        price_category = "Luxury"
                        color = "#dc3545"
                    
                    fig = go.Figure(go.Indicator(
                        mode = "gauge+number",
                        value = predicted_price/1000,  # Show in thousands
                        domain = {'x': [0, 1], 'y': [0, 1]},
                        title = {'text': "Price (in $K)"},
                        gauge = {
                            'axis': {'range': [None, 1000]},
                            'bar': {'color': color},
                            'steps': [
                                {'range': [0, 200], 'color': "lightgray"},
                                {'range': [200, 300], 'color': "gray"},
                                {'range': [300, 500], 'color': "darkgray"},
                                {'range': [500, 1000], 'color': "black"}
                            ],
                            'threshold': {
                                'line': {'color': "red", 'width': 4},
                                'thickness': 0.75,
                                'value': 400
                            }
                        }
                    ))
                    
                    fig.update_layout(height=250, margin=dict(l=20, r=20, t=30, b=20))
                    st.plotly_chart(fig, use_container_width=True)
                    
                    st.markdown(f"""
                    **Category:** <span style='color:{color}; font-weight: bold;'>{price_category}</span>
                    """, unsafe_allow_html=True)
                
                with result_cols[2]:
                    # Property summary
                    st.markdown("### Property Summary")
                    st.metric("Bedrooms", bed)
                    st.metric("Bathrooms", bath)
                    st.metric("House Size", f"{house_size:,} sq ft")
                    st.metric("Lot Size", f"{acre_lot} acres")
                    
                    # Prediction timestamp
                    st.info("Prediction made on: " + pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"))
                
                # Store prediction in session state
                if "predictions" not in st.session_state:
                    st.session_state["predictions"] = []
                
                prediction_summary = {
                    "timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "city": city.title(),
                    "state": state.title(),
                    "predicted_price": predicted_price,
                    "house_size": house_size,
                    "bed": bed,
                    "bath": bath
                }
                st.session_state["predictions"].append(prediction_summary)
                
                # Show comparison with similar properties if sample data is available
                st.divider()
                st.subheader("📊 Market Comparison")
                
                # Find similar properties from samples
                similar_properties = []
                for sample in SAMPLE_HOUSES:
                    if (abs(sample["bed"] - bed) <= 1 and 
                        abs(sample["bath"] - bath) <= 1 and
                        abs(sample["house_size"] - house_size) <= 500):
                        similar_properties.append(sample)
                
                if similar_properties:
                    comparison_data = []
                    for prop in similar_properties[:5]:  # Show max 5 similar properties
                        comparison_data.append({
                            "Property": f"{prop['city'].title()}, {prop['state'].title()}",
                            "Actual Price": prop["expected_price"],
                            "Bed/Bath": f"{prop['bed']}/{prop['bath']}",
                            "Size (sq ft)": prop["house_size"]
                        })
                    
                    # Add current prediction
                    comparison_data.append({
                        "Property": f"{city.title()}, {state.title()} (Predicted)",
                        "Actual Price": predicted_price,
                        "Bed/Bath": f"{bed}/{bath}",
                        "Size (sq ft)": house_size
                    })
                    
                    df_comparison = pd.DataFrame(comparison_data)
                    
                    # Create comparison chart
                    fig = px.bar(
                        df_comparison, 
                        x="Property", 
                        y="Actual Price",
                        title="Price Comparison with Similar Properties",
                        color="Actual Price",
                        color_continuous_scale="viridis"
                    )
                    fig.update_layout(xaxis_tickangle=-45, height=400)
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Show table
                    st.dataframe(df_comparison, use_container_width=True)
                else:
                    st.info("No similar properties found in sample data for comparison.")

# Display history of predictions if available
if "predictions" in st.session_state and st.session_state["predictions"]:
    st.divider()
    st.subheader("📈 Previous Predictions")
    
    # Create a DataFrame from predictions
    df_predictions = pd.DataFrame(st.session_state["predictions"])
    
    if len(df_predictions) > 0:
        # Show summary stats
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Predictions", len(df_predictions))
        with col2:
            st.metric("Average Price", format_price(df_predictions["predicted_price"].mean()))
        with col3:
            st.metric("Highest Price", format_price(df_predictions["predicted_price"].max()))
        with col4:
            st.metric("Lowest Price", format_price(df_predictions["predicted_price"].min()))
        
        # Show recent predictions table
        st.dataframe(
            df_predictions[["timestamp", "city", "state", "predicted_price", "house_size", "bed", "bath"]].tail(10),
            use_container_width=True
        )
        
        # Price trend chart if more than 2 predictions
        if len(df_predictions) > 2:
            fig = px.line(
                df_predictions.tail(10), 
                x="timestamp", 
                y="predicted_price",
                title="Recent Price Predictions Trend",
                markers=True
            )
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)

# Footer
st.markdown("---")
st.markdown("Desarrollado por el Grupo 3 | Proyecto 3: Machine Learning Operations")

# Add some custom CSS for better styling
st.markdown("""
<style>
.metric-card {
    background-color: #f0f2f6;
    padding: 1rem;
    border-radius: 0.5rem;
    margin: 0.5rem 0;
}
</style>
""", unsafe_allow_html=True)