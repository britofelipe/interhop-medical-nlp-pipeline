import streamlit as st
import requests
import os

# Backend URL from environment variable
BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")

st.set_page_config(page_title="InterHop - Analyse d'Ordonnances", layout="wide")

st.title("🏥 Analyse Automatique d'Ordonnances")
st.markdown("---")

# Sidebar for navigation
st.sidebar.header("Navigation")
page = st.sidebar.radio("Aller vers:", ["Accueil", "Validation", "Statistiques"])

if page == "Accueil":
    st.subheader("Charger un document")
    st.info("Ce système est open-source et développé pour InterHop.org.")
    
    # Simple check to see if backend is online
    try:
        response = requests.get(f"{BACKEND_URL}/health")
        if response.status_code == 200:
            st.success("Système connecté au serveur d'analyse.")
        else:
            st.error("Erreur de connexion au serveur.")
    except:
        st.error("Le serveur backend est inaccessible.")
        