import streamlit as st
import google.generativeai as genai
import json
from datetime import datetime
from fpdf import FPDF

# 1. Configuration de l'interface
st.set_page_config(page_title="Générateur FDEC", page_icon="📄")
st.title("📄 Assistant FDEC - Production & QA")
st.markdown("Module de saisie rapide d'incidents (Pesée, Ligne, MOP) et génération de déviations BPF.")
st.divider()

# 2. Formulaire de saisie terrain
col1, col2 = st.columns(2)
with col1:
    atelier = st.text_input("Secteur / Atelier", placeholder="Ex: Atelier Pesée Cabine C3")
with col2:
    lot = st.text_input("Produit & N° de Lot", placeholder="Ex: Fervex Lot 8849-A")

description = st.text_area(
    "Description factuelle de l'incident (Texte ou dictée vocale)", 
    height=150,
    placeholder="Ex: Lors de la phase d'introduction du PA, la balance a dérivé de 1.5g. Le conteneur a été isolé."
)

# 3. Moteur de génération IA et PDF
if st.button("🚀 Générer la FDEC Officielle"):
    if not atelier or not description:
        st.error("Les champs 'Atelier' et 'Description' sont obligatoires.")
    else:
        with st.spinner("Analyse métier BPF et structuration du document en cours..."):
            try:
                # Récupération SECRÈTE de la clé API (Invisible pour l'utilisateur)
                api_key = st.secrets["GEMINI_API_KEY"]
                genai.configure(api_key=api_key)
                
                system_prompt = """Tu es un expert QA Pharmaceutique BPF. 
                Prends le récit d'incident brut et structure-le en un rapport professionnel. 
                Réponds UNIQUEMENT au format JSON avec ces 5 clés exactes :
                "description_factuelle", "mesures_conservatoires", "criticite" (doit être MINEURE, MAJEURE ou CRITIQUE), "justification_criticite", "capa" (pistes d'investigation)."""
                
                model = genai.GenerativeModel(
                    'gemini-1.5-flash',
                    system_instruction=system_prompt,
                    generation_config={"response_mime_type": "application/json"}
                )
                
                user_prompt = f"Atelier: {atelier}\nLot: {lot}\nIncident: {description}"
                
                response = model.generate_content(user_prompt)
                data = json.loads(response.text)
                
                class PDF(FPDF):
                    def header(self):
                        self.set_font("helvetica", "B", 14)
                        self.set_fill_color(26, 54, 93)
                        self.set_text_color(255, 255, 255)
                        self.cell(0, 10, "FICHE DE DECLARATION D'EVENEMENT (FDEC)", border=0, ln=1, align="C", fill=True)
                        self.set_text_color(0, 0, 0)
                        self.set_font("helvetica", "I", 10)
                        self.cell(0, 10, "Document Confidentiel - Norme BPF / GMP", border=0, ln=1, align="C")
                        self.ln(5)
                        
                    def chapter_title(self, title):
                        self.set_font("helvetica", "B", 11)
                        self.set_fill_color(237, 242, 247)
                        self.cell(0, 8, title, border=1, ln=1, align="L", fill=True)
                        self.ln(2)
                        
                    def chapter_body(self, body):
                        self.set_font("helvetica", "", 10)
                        self.multi_cell(0, 6, body)
                        self.ln(4)

                pdf = PDF()
                pdf.add_page()
                
                pdf.set_font("helvetica", "B", 10)
                date_str = datetime.now().strftime("%d/%m/%Y à %H:%M")
                pdf.cell(0, 6, f"Date de l'événement : {date_str}", ln=1)
                pdf.cell(0, 6, f"Secteur / Atelier : {atelier}", ln=1)
                pdf.cell(0, 6, f"Produit / N° de Lot : {lot}", ln=1)
                pdf.ln(5)
                
                pdf.chapter_title("1. DESCRIPTION FACTUELLE")
                pdf.chapter_body(data.get("description_factuelle", ""))
                
                pdf.chapter_title("2. MESURES CONSERVATOIRES IMMÉDIATES")
                pdf.chapter_body(data.get("mesures_conservatoires", ""))
                
                pdf.chapter_title("3. ÉVALUATION DE LA CRITICITÉ BPF")
                pdf.set_font("helvetica", "B", 10)
                pdf.cell(0, 6, f"Niveau retenu : {data.get('criticite', '')}", ln=1)
                pdf.chapter_body(f"Justification : {data.get('justification_criticite', '')}")
                
                pdf.chapter_title("4. PISTES D'INVESTIGATION (CAPA)")
                pdf.chapter_body(data.get("capa", ""))
                
                pdf.ln(10)
                pdf.set_font("helvetica", "B", 10)
                pdf.cell(95, 20, "Visa Chef d'Atelier / Déclarant :", border=1)
                pdf.cell(95, 20, "Visa Assurance Qualité (QA) :", border=1, ln=1)
                
                pdf_bytes = bytes(pdf.output())
                
                st.success("✅ FDEC générée, structurée et prête pour l'Assurance Qualité.")
                
                st.download_button(
                    label="📥 Télécharger la FDEC (Format PDF)",
                    data=pdf_bytes,
                    file_name=f"FDEC_Automatique_{lot.replace(' ', '_')}.pdf",
                    mime="application/pdf"
                )
                
            except Exception as e:
                st.error(f"Une erreur inattendue est survenue : {e}")
