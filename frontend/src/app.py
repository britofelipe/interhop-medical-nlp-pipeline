import streamlit as st
import pandas as pd
from api import check_health, upload_document, poll_status, get_results, validate_results
from utils import convert_to_fhir

# --- CONFIGURATION ---
st.set_page_config(page_title="InterHop - Analyse d'Ordonnances", layout="wide", page_icon="🏥")

# --- SESSION STATE INITIALIZATION ---
if "document_id" not in st.session_state:
    st.session_state.document_id = None
if "extracted_data" not in st.session_state:
    st.session_state.extracted_data = None
if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None

# --- SIDEBAR ---
st.sidebar.title("InterHop OCR")
st.sidebar.info("Projet OpenSource pour la structuration de données de santé.")

# Health Check Indicator
if check_health():
    st.sidebar.success("🟢 API Connectée")
else:
    st.sidebar.error("🔴 API Déconnectée")

page = st.sidebar.radio("Navigation", ["Accueil", "Validation", "Statistiques"])

# --- PAGE: ACCUEIL (Upload) ---
if page == "Accueil":
    st.title("🏥 Analyse Automatique d'Ordonnances")
    st.markdown("---")
    st.write("Bienvenue. Chargez une ordonnance (PDF ou Image) pour démarrer l'extraction.")

    uploaded_file = st.file_uploader("Choisir un fichier", type=["png", "jpg", "jpeg", "pdf"])

    if uploaded_file is not None:
        if st.button("🚀 Traiter l'ordonnance", type="primary"):
            with st.spinner("Envoi du fichier..."):
                try:
                    # 1. Upload
                    doc_info = upload_document(
                        uploaded_file.getvalue(), 
                        uploaded_file.name, 
                        uploaded_file.type
                    )
                    st.session_state.document_id = doc_info["id"]
                    st.session_state.uploaded_file = uploaded_file # Save for display later
                    
                    # 2. Wait for processing
                    with st.spinner("Analyse IA en cours (OCR + Extraction)..."):
                        poll_status(doc_info["id"])
                        
                    # 3. Get Results
                    results = get_results(doc_info["id"])
                    st.session_state.extracted_data = results.get("structured_json", {})
                    
                    st.success("Analyse terminée ! Allez dans l'onglet 'Validation'.")
                    
                except Exception as e:
                    st.error(f"Erreur lors du traitement: {e}")

# --- PAGE: VALIDATION (Review) ---
elif page == "Validation":
    st.title("✅ Validation et Correction")
    
    if not st.session_state.extracted_data:
        st.warning("Aucune donnée à valider. Veuillez d'abord charger un document dans 'Accueil'.")
    else:
        # Split Screen Layout
        col1, col2 = st.columns([1, 1.5]) # Left narrow (Image), Right wide (Data)

        with col1:
            st.subheader("Document Original")
            if st.session_state.uploaded_file:
                # If image, show it. If PDF, just show info (displaying PDF in streamlit is complex without plugins)
                if st.session_state.uploaded_file.type in ["application/pdf"]:
                    st.info("📄 Aperçu PDF (Page 1)")
                    # For MVP, we don't render PDF to avoid extra dependencies, 
                    # but normally we would use an iframe or convert first page to image.
                else:
                    st.image(st.session_state.uploaded_file, width='stretch')
            else:
                st.info("Image non disponible")

        with col2:
            st.subheader("Données Extraites (IA)")
            
            data = st.session_state.extracted_data

            # 1. Header Info (Patient/Doctor)
            c1, c2 = st.columns(2)
            new_doctor = c1.text_input("Médecin", value=data.get("doctor", ""))
            new_patient = c2.text_input("Patient", value=data.get("patient", ""))

            # 2. Medicines (Data Editor)
            st.markdown("### 💊 Médicaments Identifiés")
            st.info("Vous pouvez modifier, ajouter ou supprimer des lignes directement dans le tableau.")
            
            meds_df = pd.DataFrame(data.get("medicines", []))
            
            # Configure columns for better UX
            column_config = {
                "drug_name": st.column_config.TextColumn("Médicament", required=True),
                "dosage": st.column_config.TextColumn("Dosage"),
                "raw_instruction": st.column_config.TextColumn("Instructions"),
            }

            edited_df = st.data_editor(meds_df, num_rows="dynamic", column_config=column_config, use_container_width=True)

            # 3. Action Buttons
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
                        validate_results(st.session_state.document_id, updated_data)
                        st.session_state.extracted_data = updated_data # Update local state
                        st.toast("Validation enregistrée avec succès !", icon="✅")
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

# --- PAGE: STATISTIQUES ---
elif page == "Statistiques":
    st.title("📊 Tableau de Bord")
    st.info("Cette section affichera les métriques de performance (WER, Précision) calculées par le module de benchmark.")
    
    # Simple placeholder for now
    st.metric(label="Documents Traités", value="12")
    st.metric(label="Précision Moyenne (IA)", value="85.4%")