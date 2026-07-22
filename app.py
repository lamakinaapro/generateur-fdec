import streamlit as st
from openai import OpenAI
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
        with st.spinner("Analyse métier BPF et génération du document PDF en cours..."):
            try:
                # Connexion à l'API gratuite Groq
                api_key = st.secrets["GROQ_API_KEY"]
                client = OpenAI(
                    base_url="https://api.groq.com/openai/v1",
                    api_key=api_key
                )
                
                prompt_complet = f"""Tu es un expert QA Pharmaceutique BPF. 
                Structure ce récit d'incident. 
                Réponds UNIQUEMENT au format JSON valide, sans aucune balise Markdown.
                Les 5 clés exactes du JSON sont : "description_factuelle", "mesures_conservatoires", "criticite", "justification_criticite", "capa".

                --- DONNÉES DE L'INCIDENT ---
                Atelier: {atelier}
                Lot: {lot}
                Incident: {description}
                """
                
                # Appel du modèle stable Mixtral sur Groq
                response = client.chat.completions.create(
                    model="openai/gpt-oss-120b",
                    messages=[
                        {"role": "user", "content": prompt_complet}
                    ],
                    response_format={"type": "json_object"}
                )
                
                # Récupération des données et nettoyage des caractères spéciaux
                texte_ia = response.choices[0].message.content
                texte_ia = texte_ia.replace("’", "'").replace("œ", "oe").replace("€", " euros")
                data = json.loads(texte_ia)
                
                # ---------------------------------------------------------
                # GÉNERATEUR PDF AVANCÉ (Reproduction de la charte graphique)
                # ---------------------------------------------------------
                class PDF(FPDF):
                    def header(self):
                        # Tableau d'en-tête (3 cellules côte à côte)
                        self.set_font("helvetica", "B", 14)
                        self.set_fill_color(247, 250, 252) # Gris très clair
                        self.set_text_color(26, 54, 93) # Bleu foncé UPSA
                        
                        # Case 1 : Logo / Nom
                        self.cell(40, 16, "UPSA", border=1, align="C", fill=True)
                        
                        # Case 2 : Titre central (Sur deux lignes)
                        x = self.get_x()
                        y = self.get_y()
                        self.cell(100, 8, "FICHE DE DECLARATION D'EVENEMENT", border="LTR", align="C")
                        self.set_xy(x, y + 8)
                        self.set_font("helvetica", "", 9)
                        self.set_text_color(74, 85, 104)
                        self.cell(100, 8, "Système de Gestion des Déviations BPF / GMP", border="LBR", align="C")
                        
                        # Case 3 : Métadonnées
                        self.set_xy(x + 100, y)
                        self.set_font("helvetica", "", 8)
                        self.set_text_color(0, 0, 0)
                        date_str = datetime.now().strftime("%d/%m/%Y")
                        meta_text = f"Réf: FDEC-2026-AUTO\nVersion: 2.0\nDate: {date_str}\nStatut: En cours QA"
                        self.multi_cell(50, 4, meta_text, border=1, align="L", fill=True)
                        self.ln(6)

                    def footer(self):
                        # Pied de page BPF
                        self.set_y(-15)
                        self.set_font("helvetica", "I", 8)
                        self.set_text_color(100, 100, 100)
                        self.cell(0, 10, f"UPSA - Document Confidentiel BPF / GMP - Page {self.page_no()}/{{nb}}", 0, 0, "C")
                        
                    def section_title(self, number, title):
                        # En-têtes de sections sur fond bleu foncé
                        self.set_font("helvetica", "B", 10)
                        self.set_fill_color(26, 54, 93)
                        self.set_text_color(255, 255, 255)
                        self.cell(0, 7, f"{number}. {title.upper()}", border=1, ln=1, fill=True)
                        self.set_text_color(0, 0, 0)
                        self.ln(2)
                        
                    def section_body(self, body):
                        self.set_font("helvetica", "", 9.5)
                        self.multi_cell(0, 5, body)
                        self.ln(4)

                pdf = PDF()
                pdf.alias_nb_pages()
                pdf.add_page()
                
                # Tableau d'informations du contexte (Grisé pour les titres)
                pdf.set_font("helvetica", "B", 9)
                pdf.set_fill_color(237, 242, 247)
                
                # Ligne 1
                pdf.cell(35, 7, "Secteur / Atelier :", border=1, fill=True)
                pdf.set_font("helvetica", "", 9)
                pdf.cell(60, 7, atelier, border=1)
                pdf.set_font("helvetica", "B", 9)
                pdf.cell(40, 7, "Date & Heure :", border=1, fill=True)
                pdf.set_font("helvetica", "", 9)
                pdf.cell(55, 7, datetime.now().strftime("%d/%m/%Y à %H:%M"), border=1, ln=1)
                
                # Ligne 2
                pdf.set_font("helvetica", "B", 9)
                pdf.cell(35, 7, "Produit / Lot :", border=1, fill=True)
                pdf.set_font("helvetica", "", 9)
                pdf.cell(60, 7, lot, border=1)
                pdf.set_font("helvetica", "B", 9)
                pdf.cell(40, 7, "Émetteur :", border=1, fill=True)
                pdf.set_font("helvetica", "", 9)
                pdf.cell(55, 7, "Opérateur Terrain (Auto)", border=1, ln=1)
                pdf.ln(6)
                
                # Contenu structuré par l'IA
                pdf.section_title("1", "DESCRIPTION FACTUELLE DE L'ÉVÉNEMENT")
                pdf.section_body(data.get("description_factuelle", ""))
                
                pdf.section_title("2", "MESURES CONSERVATOIRES ET IMMÉDIATES PRISES")
                pdf.section_body(data.get("mesures_conservatoires", ""))
                
                pdf.section_title("3", "ÉVALUATION INITIALE DE LA CRITICITÉ BPF")
                pdf.set_font("helvetica", "B", 10)
                pdf.cell(0, 6, f"Niveau retenu : {str(data.get('criticite', '')).upper()}", ln=1)
                pdf.section_body(f"Justification : {data.get('justification_criticite', '')}")
                
                pdf.section_title("4", "PISTES D'INVESTIGATION & ACTIONS CORRECTIVES (CAPA)")
                pdf.section_body(data.get("capa", ""))
                
                # Tableau des signatures BPF (3 colonnes)
                pdf.ln(5)
                pdf.section_title("5", "APPROBATIONS & VISAS BPF")
                
                pdf.set_font("helvetica", "B", 9)
                pdf.set_fill_color(237, 242, 247)
                pdf.cell(63, 6, "Déclarant (Opérateur/Chef)", border=1, align="C", fill=True)
                pdf.cell(64, 6, "Responsable Production", border=1, align="C", fill=True)
                pdf.cell(63, 6, "Assurance Qualité (QA)", border=1, ln=1, align="C", fill=True)
                
                pdf.set_font("helvetica", "", 9)
                x = pdf.get_x()
                y = pdf.get_y()
                
                date_sign = datetime.now().strftime('%d/%m/%Y')
                pdf.multi_cell(63, 6, f"Nom: J. Dupont\nDate: {date_sign}\nVisa: Signé électroniquement", border=1)
                
                pdf.set_xy(x + 63, y)
                pdf.multi_cell(64, 6, f"Nom:\nDate:\nVisa:", border=1)
                
                pdf.set_xy(x + 127, y)
                pdf.multi_cell(63, 6, f"Nom:\nDate:\nVisa:", border=1)
                
                # Export du PDF
                pdf_bytes = bytes(pdf.output())
                
                st.success("✅ FDEC générée avec succès (Format Officiel UPSA).")
                
                st.download_button(
                    label="📥 Télécharger la FDEC (Format PDF)",
                    data=pdf_bytes,
                    file_name=f"FDEC_Automatique_{lot.replace(' ', '_')}.pdf",
                    mime="application/pdf"
                )
                
            except Exception as e:
                st.error(f"Erreur technique : {e}")
