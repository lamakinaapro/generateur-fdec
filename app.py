import streamlit as st
from openai import OpenAI
import json
from datetime import datetime
from fpdf import FPDF

# 1. Configuration de l'interface
st.set_page_config(page_title="Système de Qualité", layout="wide")

# --- CSS PERSONNALISÉ POUR FORCER LE STYLE LOGICIEL INDUSTRIEL (ERP) ---
st.markdown("""
<style>
    /* Forcer le thème clair et la police d'entreprise (type Windows/Microsoft) */
    .stApp {
        background-color: #F4F6F9 !important; /* Gris très clair logiciel */
    }
    .stApp, p, h1, h2, h3, h4, h5, h6, span, label, div {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif !important;
        color: #2C3E50 !important; /* Texte gris/bleu très foncé */
    }
    
    /* Masquer l'en-tête et le pied de page Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Styliser les champs de texte pour faire "formulaire strict" */
    .stTextInput>div>div>input, .stTextArea>div>div>textarea {
        background-color: #FFFFFF !important;
        border: 1px solid #CED4DA !important;
        border-radius: 3px !important;
        color: #333333 !important;
    }
    
    /* Styliser le bouton (Bleu classique industriel) */
    .stButton>button {
        width: 100%;
        border-radius: 3px !important;
        background-color: #0056B3 !important; 
        color: #FFFFFF !important;
        padding: 10px 15px !important;
        font-size: 14px !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        border: none !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
    }
    .stButton>button:hover {
        background-color: #004494 !important;
        color: #FFFFFF !important;
    }
    
    /* Styliser la barre latérale (Sidebar) */
    [data-testid="stSidebar"] {
        background-color: #1A252F !important; /* Bleu nuit presque noir */
    }
    [data-testid="stSidebar"] * {
        color: #ECF0F1 !important; /* Texte clair sur fond sombre */
    }
    
    /* Ligne de séparation discrète */
    hr {
        border-top: 1px solid #DEE2E6 !important;
        margin-top: 10px;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# --- BARRE LATÉRALE (Menu du logiciel) ---
with st.sidebar:
    st.markdown("### INFORMATIONS SESSION")
    st.write("Utilisateur : J. Dupont")
    st.write("Profil : Chef d'équipe")
    st.write("Terminal : Poste-C3-Atelier")
    st.write("Statut Réseau : Connecté")
    st.divider()
    st.markdown("### MODULES BPF")
    st.markdown("- **Déclaration Déviation (En cours)**")
    st.markdown("- Suivi des CAPA")
    st.markdown("- Historique des lots")
    st.markdown("- Audit Trail")
    st.divider()
    st.caption("Système Documentaire QA - v2.1.4")

# --- EN-TÊTE PROFESSIONNEL ---
col_titre, col_date = st.columns([4, 1])
with col_titre:
    st.markdown("<h3 style='color: #0056B3 !important; margin-bottom: 0;'>SYSTÈME QUALITÉ : GESTION DES DÉVIATIONS</h3>", unsafe_allow_html=True)
    st.markdown("<p style='font-size: 14px; color: #7F8C8D !important;'>Module d'enregistrement informatisé selon référentiel BPF</p>", unsafe_allow_html=True)
with col_date:
    st.write("") # Espace d'alignement
    st.markdown(f"<div style='text-align: right; font-size: 14px; color: #7F8C8D !important;'>Date du jour : {datetime.now().strftime('%d/%m/%Y')}</div>", unsafe_allow_html=True)
st.divider()

# 2. Formulaire de saisie terrain
st.markdown("<h5 style='color: #2C3E50 !important;'>FORMULAIRE DE DÉCLARATION (FDEC)</h5>", unsafe_allow_html=True)

# Conteneur blanc avec une fine bordure pour bien délimiter la zone de saisie
with st.container(border=True):
    col1, col2 = st.columns(2)
    with col1:
        atelier = st.text_input("Secteur / Atelier :", placeholder="Ex: Pesée Cabine C3")
    with col2:
        lot = st.text_input("Produit et N° de Lot :", placeholder="Ex: Fervex Lot 8849-A")

    description = st.text_area(
        "Description factuelle de l'événement (Saisie stricte des faits) :", 
        height=150,
        placeholder="Décrivez l'incident rencontré..."
    )

st.write("") # Petit espace avant le bouton

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
                
                # Récupération des données brutes
                texte_ia = response.choices[0].message.content
                data = json.loads(texte_ia)
                
                # ---------------------------------------------------------
                # BOUCLIER ANTI-PLANTAGE (Nettoyage extrême à 100%)
                # ---------------------------------------------------------
                def nettoyage_extreme(valeur):
                    # Si l'IA a fait une liste, on la transforme en texte
                    if isinstance(valeur, list):
                        valeur = "\n".join([f"- {str(item)}" for item in valeur])
                    
                    valeur = str(valeur)
                    
                    # 1. Remplacement manuel des caractères classiques
                    valeur = valeur.replace("’", "'").replace("‘", "'").replace("œ", "oe").replace("€", " euros")
                    valeur = valeur.replace("‑", "-").replace("–", "-").replace("—", "-")
                    valeur = valeur.replace("«", '"').replace("»", '"').replace("…", "...")
                    valeur = valeur.replace(" ", " ").replace(" ", " ") # Remplace tous les espaces invisibles bizarres par un espace normal
                    
                    # 2. Le filtre absolu : tout caractère non supporté par la police PDF sera remplacé par "?" au lieu de faire planter l'app
                    return valeur.encode('latin-1', errors='replace').decode('latin-1')

                # On applique le bouclier à TOUTES les données de l'IA
                for cle in data:
                    data[cle] = nettoyage_extreme(data[cle])
                
                # ---------------------------------------------------------
                # GÉNERATEUR PDF AVANCÉ
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
                        self.multi_cell(0, 5, str(body))
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
