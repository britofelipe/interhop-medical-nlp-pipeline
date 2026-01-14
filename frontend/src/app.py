import streamlit as st
import pandas as pd
import time
from api import (
    check_health, 
    upload_document, 
    poll_status, 
    get_results, 
    validate_results, 
    get_document_list, 
    get_document_file_bytes,
    get_document_status_simple
)
from utils import convert_to_fhir
import requests
import os

BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")

# --- CONFIGURATION ---
st.set_page_config(page_title="InterHop - Analyse d'Ordonnances", layout="wide", page_icon="🏥")

# --- SESSION STATE INITIALIZATION ---
if "selected_doc_id" not in st.session_state:
    st.session_state.selected_doc_id = None
# We don't need 'uploaded_file' in session state anymore for global access, 
# as we will fetch images from the backend on demand.

# --- SIDEBAR ---
st.sidebar.title("ToobibOrdo")
st.sidebar.info("Projet OpenSource pour la structuration de données de santé.")

# Health Check Indicator
if check_health():
    st.sidebar.success("🟢 API Connectée")
else:
    st.sidebar.error("🔴 API Déconnectée")

# Updated Navigation
page = st.sidebar.radio("Navigation", ["Bibliothèque", "Validation", "Statistiques"])

st.sidebar.markdown("---")

# Helper function to switch tabs/pages
def go_to_validation(doc_id):
    st.session_state.selected_doc_id = doc_id
    # We don't need to manually switch 'page' variable here because Streamlit reruns 
    # and the user needs to click the sidebar, or we use st.switch_page (if multipage)
    # For this single-file app, we just notify the user or use a slight hack if we want auto-redirect.
    # Ideally, the user clicks "Validation" in sidebar, but we can help them:
    st.toast(f"Document {doc_id} sélectionné. Allez dans l'onglet Validation.", icon="🚀")

# --- PAGE: BIBLIOTHÈQUE (New Home) ---
if page == "Bibliothèque":
    st.title("📂 Bibliothèque de Documents")

    # --- POLLING (Auto-Refresh) ---
    if st.session_state.get("last_uploaded_id"):
        curr_status = get_document_status_simple(st.session_state.last_uploaded_id)
        
        if curr_status == "completed":
             st.toast("Document traité avec succès ! Prêt pour validation.", icon="✅")
             st.session_state.last_uploaded_id = None
             # st.balloons() # Optional
             
        elif curr_status == "failed":
             st.toast("❌ Échec du traitement du document.", icon="❌")
             st.session_state.last_uploaded_id = None
             
        elif curr_status in ["pending", "processing"]:
             # Wait and auto-reload
             time.sleep(2) 
             st.rerun()
             
    # ZONE A: UPLOAD (Collapsible)
    with st.expander("➕ Nouveau Document (Upload)", expanded=True):
        st.write("Chargez une ou plusieurs ordonnances.")
        uploaded_files = st.file_uploader(
            "Choisir des fichiers", 
            type=["png", "jpg", "jpeg", "pdf"], 
            accept_multiple_files=True
        )
        
        if uploaded_files:
            if st.button("🚀 Envoyer Tout", type="primary"):
                progress_bar = st.progress(0)
                total = len(uploaded_files)
                
                for idx, uploaded_file in enumerate(uploaded_files):
                    try:
                        # 1. Upload
                        doc_info = upload_document(
                            uploaded_file.getvalue(), 
                            uploaded_file.name, 
                            uploaded_file.type
                        )
                        # 2. Track last one for polling
                        st.session_state.last_uploaded_id = doc_info['id']
                        
                        # Update progress
                        progress_bar.progress((idx + 1) / total)
                        time.sleep(0.1) # UI feel
                        
                    except Exception as e:
                        st.error(f"Erreur avec {uploaded_file.name}: {e}")
                
                st.toast(f"{total} documents envoyés!", icon="🚀")
                time.sleep(1) 
                st.rerun()

    st.markdown("---")

    # ZONE B: DASHBOARD (Tabs for Validated vs To Do)
    tab1, tab2 = st.tabs(["📥 À Valider (Inbox)", "✅ Archives (Validés)"])

    def render_doc_table(validated_status, button_label):
        """Helper to render the list and selection logic"""
        try:
            docs = get_document_list(validated=validated_status)
        except Exception as e:
            st.error(f"Erreur de chargement: {e}")
            return

        if not docs:
            st.info("Aucun document trouvé dans cette catégorie.")
            return

        # Prepare Data for Table
        table_data = []
        for d in docs:
            # Status Mapping with semantic icons
            raw_status = d.get("status", "pending")
            status_map = {
                "pending": "⏳ En attente",
                "processing": "⚙️ Analyse IA...",
                "completed": "✅ Prêt",
                "failed": "❌ Erreur"
            }
            display_status = status_map.get(raw_status, raw_status)

            table_data.append({
                "ID": d["id"],
                "Fichier": d["filename"],
                "Date": d["upload_timestamp"],
                "Statut": display_status
            })
        
        df = pd.DataFrame(table_data)

        # Layout: List on Left, Preview on Right
        col_list, col_preview = st.columns([2, 1])

        with col_list:
            st.dataframe(
                df, 
                column_config={
                    "ID": st.column_config.TextColumn("ID", width="small"),
                    "Date": st.column_config.DatetimeColumn("Date", format="DD/MM/YYYY HH:mm"),
                    "Statut": st.column_config.TextColumn("État"),
                },
                use_container_width=True, 
                hide_index=True
            )
            
            # Selection Mechanism
            # Using selectbox as a stable selector
            selected_id = st.selectbox(
                "🔍 Sélectionner un document pour voir les détails:", 
                options=[d["ID"] for d in table_data],
                format_func=lambda x: next((d["Fichier"] for d in table_data if d["ID"] == x), x),
                key=f"sel_{validated_status}"
            )

        with col_preview:
            if selected_id:
                st.subheader("Aperçu")
                try:
                    # Fetch Image Bytes from Backend
                    file_bytes, content_type = get_document_file_bytes(selected_id)
                    
                    if "pdf" in content_type:
                        st.info("📄 Document PDF")
                        st.caption("(La prévisualisation PDF n'est pas disponible, ouvrez pour valider)")
                    else:
                        st.image(file_bytes, use_container_width=True)
                    
                    st.markdown("---")
                    # Action Button
                    if st.button(f"{button_label}", key=f"btn_{selected_id}", type="primary"):
                        go_to_validation(selected_id)
                        
                except Exception as e:
                    st.error(f"Impossible de charger l'image: {e}")

    # Render Tabs
    with tab1:
        render_doc_table(False, "✏️ Ouvrir pour Correction")
    
    with tab2:
        render_doc_table(True, "👀 Voir / Revalider")


# --- PAGE: VALIDATION (Review) ---
elif page == "Validation":
    st.title("✅ Validation et Correction")
    
    # 1. Check if a document is selected
    if not st.session_state.selected_doc_id:
        st.warning("⚠️ Aucun document sélectionné.")
        st.info("Veuillez aller dans l'onglet **Bibliothèque** et sélectionner un document à corriger.")
        st.stop() # Stop execution here

    doc_id = st.session_state.selected_doc_id
    
    # 2. Load Data (Live from Backend)
    try:
        with st.spinner("Chargement du document..."):
            results = get_results(doc_id)
            file_bytes, content_type = get_document_file_bytes(doc_id)
            extracted_data = results.get("structured_json", {}) or {}

        # 3. Split Screen Layout
        col1, col2 = st.columns([1, 1.5]) 

        with col1:
            st.subheader("Document Original")
            if "pdf" in content_type:
                st.info("📄 Document PDF")
                # Optional: Add download button for PDF
                st.download_button("Télécharger le PDF", file_bytes, file_name="document.pdf")
            else:
                st.image(file_bytes, use_container_width=True)

        with col2:
            st.subheader("Extraction & Correction")

            # Header Info
            c1, c2 = st.columns(2)
            new_doctor = c1.text_input("Médecin", value=extracted_data.get("doctor", ""))
            new_patient = c2.text_input("Patient", value=extracted_data.get("patient", ""))

            # Medicines (Data Editor)
            st.markdown("### 💊 Médicaments Identifiés")
            
            meds_df = pd.DataFrame(extracted_data.get("medicines", []))
            
            column_config = {
                "drug_name": st.column_config.TextColumn("Médicament", required=True),
                "dosage": st.column_config.TextColumn("Dosage"),
                "raw_instruction": st.column_config.TextColumn("Instructions"),
            }

            edited_df = st.data_editor(
                meds_df, 
                num_rows="dynamic", 
                column_config=column_config, 
                use_container_width=True,
                key="editor"
            )

            # Action Buttons
            st.markdown("---")
            col_actions1, col_actions2 = st.columns(2)
            
            with col_actions1:
                if st.button("💾 Valider les corrections", type="primary"):
                    # Reconstruct JSON
                    updated_data = {
                        "doctor": new_doctor,
                        "patient": new_patient,
                        "medicines": edited_df.to_dict(orient="records")
                    }
                    
                    try:
                        validate_results(doc_id, updated_data)
                        
                        # UX Improvements
                        st.toast("Validation enregistrée avec succès !", icon="✅")
                        st.success("✅ Document validé et sauvegardé dans la base de données!")
                        st.balloons()
                        
                    except Exception as e:
                        st.error(f"Erreur de sauvegarde: {e}")

            with col_actions2:
                # FHIR Export
                updated_data = {
                    "doctor": new_doctor,
                    "patient": new_patient,
                    "medicines": edited_df.to_dict(orient="records")
                }
                fhir_json = convert_to_fhir(updated_data)
                st.download_button(
                    label="⬇️ Exporter en FHIR (JSON)",
                    data=fhir_json,
                    file_name="ordonnance_fhir.json",
                    mime="application/json"
                )

    except Exception as e:
        st.error(f"Erreur lors du chargement des données: {e}")
        if "404" in str(e):
             st.warning("Le document n'a peut-être pas fini d'être traité. Réessayez dans quelques instants.")


# --- PAGE: STATISTIQUES ---
elif page == "Statistiques":
    st.title("📊 Tableau de Bord de Performance")
    st.markdown("Comparaison entre l'extraction **IA** et la validation **Humaine**.")

    if st.button("🔄 Actualiser les données"):
        st.rerun()

    try:
        resp = requests.get(f"{BACKEND_URL}/statistics/global")
        if resp.status_code == 200:
            stats = resp.json()
            
            if stats.get("count", 0) == 0:
                st.warning("Pas assez de documents validés pour calculer les statistiques.")
            else:
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Docs Validés", stats["count"])
                col2.metric("Précision", f"{stats['avg_precision']*100:.1f}%")
                col3.metric("Rappel", f"{stats['avg_recall']*100:.1f}%")
                col4.metric("Score F1", f"{stats['avg_f1']*100:.1f}%")
                
                st.markdown("---")
                st.success(f"L'IA a correctement identifié {stats['avg_recall']*100:.0f}% des médicaments finaux.")
                
        else:
            st.error("Erreur lors de la récupération des statistiques.")
    except Exception as e:
        st.error(f"Erreur de connexion: {e}")