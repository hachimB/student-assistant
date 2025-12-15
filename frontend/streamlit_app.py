"""
Interface Streamlit pour l'Assistant RAG Étudiant

Interface conversationnelle intuitive
"""

import streamlit as st
import requests
import uuid
from datetime import datetime

# ============================================
# CONFIGURATION
# ============================================

API_URL = "http://localhost:8000"

st.set_page_config(
    page_title="Assistant UM5",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# STYLES CSS
# ============================================

st.markdown("""
<style>
    /* Style personnalisé */
    .main-header {
        font-size: 2.5rem;
        color: #1f4788;
        text-align: center;
        margin-bottom: 1rem;
    }
    
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    /* AMÉLIORÉ : Meilleur contraste pour les sources */
    .source-box {
        background-color: #e8eaf6;  /* Bleu très clair */
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f4788;
        margin: 0.5rem 0;
        color: #1a1a1a;  /* Texte noir pour bon contraste */
    }
    
    .source-box strong {
        color: #1f4788;  /* Titre en bleu foncé */
        font-size: 1.05rem;
    }
    
    /* Style pour les métadonnées */
    .source-meta {
        color: #424242;
        font-size: 0.9rem;
        margin-top: 0.3rem;
    }
    
    .feedback-section {
        margin-top: 1rem;
        padding: 1rem;
        background-color: #f8f9fa;
        border-radius: 0.5rem;
    }
    
    /* Style pour l'expander */
    .streamlit-expanderHeader {
        background-color: #f0f2f6;
        border-radius: 0.5rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# SESSION STATE (pour mémoire)
# ============================================

if 'session_id' not in st.session_state:
    st.session_state.session_id = f"user_{uuid.uuid4().hex[:8]}"

if 'messages' not in st.session_state:
    st.session_state.messages = []

if 'last_sources' not in st.session_state:
    st.session_state.last_sources = []

# ============================================
# SIDEBAR
# ============================================
with st.sidebar:
    st.markdown("### 🎓 Assistant UM5")
    st.markdown("---")
    
    # NOUVEAU : Gestion conversations
    st.markdown("**💬 Conversations**")
    
    # Charger liste conversations
    try:
        response = requests.get(f"{API_URL}/api/v1/conversations")
        if response.status_code == 200:
            conversations = response.json()['conversations']
            
            # Dropdown pour sélectionner conversation
            if conversations:
                conv_options = {
                    conv['id']: f"{conv['preview']} ({conv['message_count']} msgs)"
                    for conv in conversations
                }
                
                # Ajouter option "Nouvelle"
                conv_options["new"] = "➕ Nouvelle conversation"
                
                selected = st.selectbox(
                    "Sélectionner",
                    options=list(conv_options.keys()),
                    format_func=lambda x: conv_options[x],
                    index=0 if st.session_state.session_id not in conv_options else list(conv_options.keys()).index(st.session_state.session_id)
                )
                
                # Si "Nouvelle" sélectionnée
                if selected == "new":
                    if st.button("Créer", use_container_width=True):
                        # Créer nouvelle conversation
                        resp = requests.post(f"{API_URL}/api/v1/conversations")
                        if resp.status_code == 201:
                            new_id = resp.json()['conversation_id']
                            st.session_state.session_id = new_id
                            st.session_state.messages = []
                            st.rerun()
                
                # Si conversation existante sélectionnée
                elif selected != st.session_state.session_id:
                    # Charger conversation
                    resp = requests.get(f"{API_URL}/api/v1/conversations/{selected}")
                    if resp.status_code == 200:
                        conv_data = resp.json()
                        st.session_state.session_id = selected
                        
                        # Charger messages
                        st.session_state.messages = [
                            {
                                'role': msg['role'],
                                'content': msg['content'],
                                'sources': msg.get('sources', [])
                            }
                            for msg in conv_data['messages']
                        ]
                        
                        st.rerun()
            
            else:
                st.info("Aucune conversation")
                
                if st.button("➕ Créer première conversation", use_container_width=True):
                    resp = requests.post(f"{API_URL}/api/v1/conversations")
                    if resp.status_code == 201:
                        new_id = resp.json()['conversation_id']
                        st.session_state.session_id = new_id
                        st.session_state.messages = []
                        st.rerun()
    
    except Exception as e:
        st.error(f"Erreur chargement conversations : {e}")
    
    # Bouton supprimer conversation actuelle
    if st.session_state.session_id and st.button("🗑️ Supprimer conversation", use_container_width=True):
        try:
            resp = requests.delete(f"{API_URL}/api/v1/conversations/{st.session_state.session_id}")
            if resp.status_code == 200:
                st.session_state.session_id = f"user_{uuid.uuid4().hex[:8]}"
                st.session_state.messages = []
                st.success("Conversation supprimée")
                st.rerun()
        except Exception as e:
            st.error(f"Erreur suppression : {e}")
    
        st.markdown("---")
    st.markdown("**Paramètres de l'assistant**")

    # === NOMBRE DE SOURCES À RETOURNER ===
    n_results = st.slider(
        "Nombre de sources utilisées",
        min_value=1,
        max_value=10,
        value=5,
        step=1,
        help="Plus de sources = réponse plus précise, mais plus lente"
    )

    # === UTILISATION DE L'HISTORIQUE ===
    use_history = st.checkbox(
        "Utiliser l'historique de la conversation",
        value=True,
        help="Si désactivé, l'assistant oublie les messages précédents"
    )
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666; font-size: 0.8rem;'>
        Université Mohammed V de Rabat<br>
        Version 1.0.0
        </div>
        """,
        unsafe_allow_html=True
    )

# ============================================
# MAIN CONTENT
# ============================================

# Header
st.markdown("<h1 class='main-header'>🎓 Assistant Virtuel UM5</h1>", unsafe_allow_html=True)
st.markdown(
    "<p class='sub-header'>Posez vos questions sur les emplois du temps, règlements et procédures</p>",
    unsafe_allow_html=True
)

# Zone de chat
st.markdown("---")

# Afficher l'historique des messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        # Afficher sources si c'est une réponse de l'assistant
        if message["role"] == "assistant" and "sources" in message:
            sources = message['sources']
            # Afficher sources
            with st.expander("📚 Sources consultées", expanded=True):
                if sources:
                    for i, source in enumerate(sources, 1):
                        # Tronquer le nom si trop long
                        source_name = source['source']
                        if len(source_name) > 60:
                            source_name = source_name[:57] + "..."
                        
                        st.markdown(f"""
                        <div class='source-box'>
                            <strong>{i}. {source_name}</strong><br>
                            <div class='source-meta'>
                                📁 Catégorie : <strong>{source['category']}</strong><br>
                                📊 Pertinence : <strong>{source['score']:.1%}</strong>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("Aucune source consultée (question générale)")

# Zone de saisie
if prompt := st.chat_input("Posez votre question..."):
    
    # Ajouter message utilisateur
    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })
    
    # Afficher message utilisateur
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Appel API
    with st.chat_message("assistant"):
        with st.spinner("🤔 Je réfléchis..."):
            try:
                # Requête à l'API
                response = requests.post(
                    f"{API_URL}/api/v1/ask",
                    json={
                        "question": prompt,
                        "session_id": st.session_state.session_id,
                        "n_results": n_results,
                        "use_history": use_history
                    },
                    timeout=60  # 60 secondes max
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    answer = data['answer']
                    sources = data['sources']
                    
                    # Afficher réponse
                    st.markdown(answer)
                    
                    # Stocker sources
                    st.session_state.last_sources = sources
                    
                    # Ajouter à l'historique
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": answer,
                        "sources": sources
                    })
                    
                    
                    # Afficher sources
                    with st.expander("📚 Sources consultées", expanded=True):
                        if sources:
                            for i, source in enumerate(sources, 1):
                                # Tronquer le nom si trop long
                                source_name = source['source']
                                if len(source_name) > 60:
                                    source_name = source_name[:57] + "..."
                                
                                st.markdown(f"""
                                <div class='source-box'>
                                    <strong>{i}. {source_name}</strong><br>
                                    <div class='source-meta'>
                                        📁 Catégorie : <strong>{source['category']}</strong><br>
                                        📊 Pertinence : <strong>{source['score']:.1%}</strong>
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)
                        else:
                            st.info("Aucune source consultée (question générale)")
                    
                    # Section feedback
                    # st.markdown("<div class='feedback-section'>", unsafe_allow_html=True)
                    st.markdown("**Cette réponse vous a-t-elle été utile ?**")
                    
                    col1, col2, col3 = st.columns([1, 1, 4])
                    
                    with col1:
                        if st.button("👍 Oui", key=f"up_{data['question_id']}"):
                            requests.post(
                                f"{API_URL}/api/v1/feedback",
                                json={
                                    "question_id": data['question_id'],
                                    "rating": 1
                                }
                            )
                            st.success("Merci pour votre retour !")
                    
                    with col2:
                        if st.button("👎 Non", key=f"down_{data['question_id']}"):
                            requests.post(
                                f"{API_URL}/api/v1/feedback",
                                json={
                                    "question_id": data['question_id'],
                                    "rating": -1
                                }
                            )
                            st.info("Merci, nous allons améliorer !")
                    
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                else:
                    st.error(f"Erreur API : {response.status_code}")
                    st.json(response.json())
                    
            except requests.exceptions.Timeout:
                st.error("⏱️ Délai d'attente dépassé. Veuillez réessayer.")
            except requests.exceptions.ConnectionError:
                st.error("🔌 Impossible de se connecter à l'API. Vérifiez que le serveur est démarré.")
            except Exception as e:
                st.error(f"❌ Erreur : {str(e)}")

# ============================================
# SECTION EXEMPLES (si pas de messages)
# ============================================

if len(st.session_state.messages) == 0:
    st.markdown("### 💡 Exemples de questions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **📅 Emplois du temps**
        - Quand commence le semestre d'hiver ?
        - Quel est le calendrier académique 2024-2025 ?
        - Quand sont les examens ?
        """)
        
        st.markdown("""
        **📋 Règlements**
        - Quelles sont les règles d'absence à l'ENSIAS ?
        - Quelle est la charte de l'UM5 ?
        """)
    
    with col2:
        st.markdown("""
        **📝 Procédures**
        - Comment s'inscrire à l'UM5 pour 2025-2026 ?
        - Quelle est la procédure d'inscription ?
        """)
        
        st.markdown("""
        **❓ Questions générales**
        - Où trouver mon emploi du temps ?
        - Comment contacter l'administration ?
        """)

# ============================================
# FOOTER
# ============================================

st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #999; font-size: 0.9rem; margin-top: 2rem;'>
    ℹ️ Cet assistant se base sur les documents officiels de l'UM5. 
    Pour des questions spécifiques, contactez votre administration.
    </div>
    """,
    unsafe_allow_html=True
)