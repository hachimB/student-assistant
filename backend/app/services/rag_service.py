"""
Service RAG (Retrieval-Augmented Generation)

Architecture :
Question → Embedding → ChromaDB → Top K chunks → Prompt + LLM → Réponse
"""

import os
from pathlib import Path
from typing import List, Dict, Optional
import warnings
warnings.filterwarnings('ignore')

from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
from huggingface_hub import InferenceClient
from dotenv import load_dotenv

load_dotenv()

# ============================================
# CONFIGURATION
# ============================================

CHROMA_DB_PATH = "data/chroma_db"
COLLECTION_NAME = "student_documents"
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
LLM_MODEL = "mistralai/Mistral-7B-Instruct-v0.2"
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")

# ============================================
# SINGLETON : Modèle d'embeddings global
# ============================================

_embedding_model = None  # Variable globale

def get_embedding_model():
    """
    Retourne le modèle d'embeddings (chargé une seule fois)
    Pattern Singleton
    """
    global _embedding_model
    
    if _embedding_model is None:
        print("📦 Chargement modèle embeddings (une seule fois)...")
        
        _embedding_model = SentenceTransformer(
            EMBEDDING_MODEL,
            device='cpu',
            cache_folder=os.path.expanduser("~/.cache/huggingface/")
        )
        
        print("✅ Modèle embeddings chargé et prêt")
    
    return _embedding_model

# ============================================
# SERVICE RAG
# ============================================

class RAGService:
    """
    Service principal pour le RAG
    
    Responsabilités :
    1. Recherche de documents pertinents (retrieval)
    2. Génération de réponse avec contexte (generation)
    3. Citation des sources
    """
    
    def __init__(self):
        """Initialise le service RAG (réutilise le modèle global)"""
        
        print("🚀 Initialisation du service RAG...")
        
        # 1. Embeddings (réutilise modèle global)
        self.embedding_model = get_embedding_model()  # ← Utilise singleton
        
        # 2. ChromaDB
        print(f"   🗄️ Connexion ChromaDB...")
        self.chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        self.collection = self.chroma_client.get_collection(name=COLLECTION_NAME)
        
        # 3. LLM
        print(f"   🤖 Connexion HuggingFace API...")
        self.llm_client = InferenceClient(token=HUGGINGFACE_API_KEY)
        
        # 4. Mémoire
        self.conversation_history = []
        self.max_history = 5
        
        print("✅ Service RAG prêt !\n")
    

    def add_to_history(self, question: str, answer: str):
        """
        Ajoute un échange à l'historique
        
        Args:
            question: Question de l'utilisateur
            answer: Réponse de l'assistant
        """
        
        self.conversation_history.append({
            'question': question,
            'answer': answer
        })
        
        # Limiter la taille de l'historique
        if len(self.conversation_history) > self.max_history:
            self.conversation_history.pop(0)
    
    
    def get_conversation_context(self) -> str:
        """
        Construit le contexte conversationnel
        
        Returns:
            Historique formaté pour le prompt
        """
        
        if not self.conversation_history:
            return ""
        
        context = "\nHistorique de la conversation :\n"
        for i, exchange in enumerate(self.conversation_history, 1):
            context += f"\nÉchange {i}:\n"
            context += f"Étudiant: {exchange['question']}\n"
            context += f"Assistant: {exchange['answer']}\n"
        
        return context
    
    
    def clear_history(self):
        """Efface l'historique de conversation"""
        self.conversation_history = []
        print("🗑️ Historique effacé")
    
    
    def retrieve_documents(
    self, 
    query: str, 
    n_results: int = 3,
    category_filter: Optional[str] = None
) -> List[Dict]:
        """
        Recherche les documents pertinents
        
        AMÉLIORÉ : Détection automatique de catégorie
        """
        
        # Détecter automatiquement la catégorie si non fournie
        if not category_filter:
            category_filter = self._detect_category(query)
        
        # Générer embedding de la question
        query_embedding = self.embedding_model.encode([query])[0]
        
        # Préparer filtres ChromaDB
        where_filter = None
        if category_filter and category_filter != "all":
            where_filter = {"category": category_filter}
        
        # Rechercher dans ChromaDB
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=n_results * 2,  # Récupérer plus pour filtrer
                where=where_filter
            )
            
            # Formater les résultats
            documents = []
            for doc, meta, distance in zip(
                results['documents'][0],
                results['metadatas'][0],
                results['distances'][0]
            ):
                documents.append({
                    'text': doc,
                    'metadata': meta,
                    'score': 1 / (1 + abs(distance))
                })
            
            # Limiter au nombre demandé
            documents = documents[:n_results]
            
            return documents
            
        except Exception as e:
            print(f"⚠️ Erreur retrieval : {e}")
            # Fallback sans filtre
            results = self.collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=n_results
            )
            
            documents = []
            for doc, meta, distance in zip(
                results['documents'][0],
                results['metadatas'][0],
                results['distances'][0]
            ):
                documents.append({
                    'text': doc,
                    'metadata': meta,
                    'score': 1 / (1 + abs(distance))
                })
            
            return documents


    def _detect_category(self, query: str) -> Optional[str]:
        """
        Détecte automatiquement la catégorie d'une question
        
        Args:
            query: Question de l'utilisateur
        
        Returns:
            Catégorie détectée ou None
        """
        
        query_lower = query.lower()
        
        # Mots-clés par catégorie
        categories = {
            'emploi_temps': [
                'emploi du temps', 'calendrier', 'horaire', 'planning',
                'quand commence', 'début', 'fin semestre', 'vacances',
                'cours', 'séance', 'date examen', 'rentrée'
            ],
            'reglements': [
                'règlement', 'règle', 'charte', 'interdit', 'autorisé',
                'absence', 'retard', 'sanction', 'discipline',
                'droit', 'obligation', 'infraction'
            ],
            'procedures': [
                'inscription', 'comment', 'procédure', 'démarche',
                'documents', 'dossier', 'attestation', 'certificat',
                's\'inscrire', 'demande', 'formulaire'
            ],
            'faqs': [
                'faq', 'question fréquente', 'aide', 'information',
                'contact', 'où trouver', 'qui contacter'
            ]
        }
        
        # Compter matches par catégorie
        scores = {}
        for category, keywords in categories.items():
            score = sum(1 for keyword in keywords if keyword in query_lower)
            if score > 0:
                scores[category] = score
        
        # Retourner catégorie avec le plus de matches
        if scores:
            best_category = max(scores, key=scores.get)
            print(f"   🏷️ Catégorie détectée : {best_category}")
            return best_category
        
        return None
    
    
    def generate_prompt(
    self, 
    query: str, 
    documents: List[Dict],
    include_history: bool = True
) -> str:
        """
        Prompt RENFORCÉ contre hallucinations
        """
        
        # Contexte documentaire
        context = ""
        for i, doc in enumerate(documents, 1):
            source = doc['metadata']['source']
            text = doc['text']
            
            context += f"\n[Document {i} - {source}]\n{text}\n"
            context += "-" * 60 + "\n"
        
        # Historique
        history_context = ""
        if include_history and self.conversation_history:
            history_context = "\n\nÉchanges précédents :\n"
            for i, exchange in enumerate(self.conversation_history[-3:], 1):
                history_context += f"Q{i}: {exchange['question']}\n"
                history_context += f"R{i}: {exchange['answer'][:100]}...\n\n"
        
        # Prompt renforcé
        prompt = f"""Tu es un assistant de l'UM5. Tu dois être TRÈS PRUDENT et NE JAMAIS inventer d'informations.

    CONTEXTE :
    Tu as accès à des documents officiels limités.
    {history_context}

    DOCUMENTS DISPONIBLES :
    {context}

    ⚠️ RÈGLES CRITIQUES - À RESPECTER ABSOLUMENT :

    1. SALUTATIONS (bonjour, merci, ok, au revoir) :
    → Réponds poliment SANS utiliser les documents

    2. QUESTIONS NÉCESSITANT RECHERCHE :
    → Utilise UNIQUEMENT les informations EXPLICITES dans les documents ci-dessus
    → Si l'information N'EST PAS EXPLICITEMENT dans les documents, tu DOIS dire :
        "Je n'ai pas cette information dans ma base de connaissances. Je vous conseille de contacter [service concerné]."
    
    3. NE JAMAIS :
    ❌ Inventer des URLs, emails, numéros de téléphone
    ❌ Inventer des procédures non mentionnées
    ❌ Extrapoler ou déduire des informations
    ❌ Donner des infos générales si la question est spécifique
    
    4. STYLE :
    ✅ Concis (2-3 phrases max)
    ✅ Citer la source : "Selon [Document X]..."
    ✅ Si incomplet : "Les documents ne précisent pas... Je vous conseille de..."

    QUESTION :
    {query}

    RÉPONSE (prudente, précise, citée) :
    
    CONTACTS UTILES (à mentionner si info manquante) :
    - Service scolarité de votre faculté
    - Plateforme de préinscription : https://preinscription.um5.ac.ma
    - Site officiel UM5 : https://www.um5.ac.ma"""

        return prompt
        
    
    def generate_answer(
        self, 
        prompt: str, 
        max_tokens: int = 500,
        temperature: float = 0.7
    ) -> str:
        """
        Génère la réponse avec le LLM
        
        Args:
            prompt: Prompt complet avec contexte
            max_tokens: Longueur max de la réponse
            temperature: Créativité (0=déterministe, 1=créatif)
        
        Returns:
            Réponse générée par le LLM
        """
        
        try:
            # Appel API HuggingFace
            messages = [
                {"role": "user", "content": prompt}
            ]
            
            response = self.llm_client.chat_completion(
                messages=messages,
                model=LLM_MODEL,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            
            answer = response.choices[0].message.content
            return answer.strip()
            
        except Exception as e:
            return f"Erreur lors de la génération : {str(e)}"
    
    def reformulate_query(self, query: str) -> str:
        """
        Reformule la question en incluant le contexte conversationnel
        Exemple :
        Historique: "Quand commence le semestre d'automne ?"
        Question: "Et combien de temps dure-t-il ?"
        Reformulé: "Combien de temps dure le semestre d'automne ?"
        Args:
        query: Question actuelle (peut être vague)
        Returns:
        Question reformulée (plus explicite)
        """
    
        # Si pas d'historique ou question déjà explicite, retourner tel quel
        if not self.conversation_history:
            return query
    
        # Si question courte avec pronom (il, elle, ça, etc.)
        pronouns = ['il', 'elle', 'ça', 'cela', 'ils', 'elles']
        is_followup = any(pronoun in query.lower() for pronoun in pronouns)
        if not is_followup and len(query.split()) > 5:
            return query  # Question déjà explicite
    
        print(f"   🔄 Reformulation avec contexte...")
    
        # Construire prompt de reformulation
        last_exchange = self.conversation_history[-1]
        reformulation_prompt = f"""Tu dois reformuler une question de suivi pour la rendre explicite.
        Contexte de la conversation précédente :
        Question précédente : {last_exchange['question']}
        Réponse donnée : {last_exchange['answer'][:200]}
        Question de suivi (vague) : {query}
        Ta tâche : Reformuler cette question de suivi pour qu'elle soit explicite et autonome.
        Ne réponds PAS à la question, reformule-la seulement.
        Exemple :
        Contexte : "Quand commence le semestre d'automne ?"
        Question : "Et combien de temps dure-t-il ?"
        Reformulé : "Combien de temps dure le semestre d'automne ?"

        Reformulation (une seule phrase, sans explication) :"""

        try:
            messages = [{"role": "user", "content": reformulation_prompt}]
        
            response = self.llm_client.chat_completion(
                messages=messages,
                model=LLM_MODEL,
                max_tokens=50,
                temperature=0.3  # Bas pour être précis
            )
        
            reformulated = response.choices[0].message.content.strip()
            print(f"   ✅ Reformulé : {reformulated}")
        
            return reformulated
        
        except Exception as e:
            print(f"   ⚠️ Erreur reformulation, utilisation question originale")
            return query
        

    
    def is_greeting(self, question: str) -> bool:
        """
        Détecte si c'est une salutation OU formule de politesse
        (ne nécessitant pas de recherche documentaire)
        """
        
        # Salutations et formules de politesse
        simple_phrases = [
            # Salutations
            'bonjour', 'salut', 'hello', 'hi', 'hey', 'coucou', 'bonsoir',
            # Politesse
            'merci', 'thanks', 'thank you', 'd\'accord', 'ok', 'okay',
            'au revoir', 'bye', 'à bientôt', 'à plus',
            # Expressions courtes
            'oui', 'non', 'bien', 'super', 'cool', 'parfait', 'génial'
        ]
        
        question_lower = question.lower().strip()
        
        # Phrase courte (1-3 mots)
        if len(question_lower.split()) <= 3:
            return any(phrase in question_lower for phrase in simple_phrases)
        
        return False


    def handle_greeting(self, question: str) -> str:
        """
        Réponse adaptée selon le type de message
        """
        
        question_lower = question.lower().strip()
        
        # Merci / Remerciements
        if any(word in question_lower for word in ['merci', 'thanks', 'thank you']):
            responses = [
                "De rien ! 😊 N'hésitez pas si vous avez d'autres questions.",
                "Avec plaisir ! Je suis là pour vous aider.",
                "Heureux de vous aider ! Autre chose ?"
            ]
        
        # Au revoir
        elif any(word in question_lower for word in ['au revoir', 'bye', 'à bientôt', 'à plus']):
            responses = [
                "À bientôt ! Bonne journée ! 👋",
                "Au revoir ! N'hésitez pas à revenir si besoin.",
                "À plus tard ! Bonne continuation dans vos études ! 🎓"
            ]
        
        # Confirmations (ok, d'accord, etc.)
        elif any(word in question_lower for word in ['ok', 'okay', 'd\'accord', 'bien', 'parfait']):
            responses = [
                "Super ! Autre question ?",
                "Parfait ! Comment puis-je vous aider d'autre ?",
                "D'accord ! N'hésitez pas pour d'autres questions."
            ]
        
        # Salutations par défaut
        else:
            responses = [
                "Bonjour ! 👋 Je suis l'assistant virtuel de l'UM5. Comment puis-je vous aider ?",
                "Salut ! 😊 Posez-moi vos questions sur les emplois du temps, règlements et procédures.",
                "Bonjour ! Bienvenue ! Que souhaitez-vous savoir sur l'UM5 ?"
            ]
        
        import random
        return random.choice(responses)
    
    
    def ask(
        self, 
        question: str,
        n_results: int = 3,
        use_history: bool = True
    ) -> Dict:
        """
        Pipeline RAG complet avec gestion salutations
        """
        
        print(f"\n❓ Question : {question}")
        
        # 0. Détecter salutation
        if self.is_greeting(question):
            print("   👋 Message simple détecté (pas de recherche doc)")
            
            answer = self.handle_greeting(question)  # ← Passer la question
            
            return {
                'question': question,
                'answer': answer,
                'sources': [],
                'reformulated_query': None,
                'is_greeting': True
            }
        
        # 1. Reformuler si nécessaire
        search_query = question
        if use_history and self.conversation_history:
            search_query = self.reformulate_query(question)
        
        # 2. Retrieval
        print("   🔍 Recherche documents pertinents...")
        documents = self.retrieve_documents(query=search_query, n_results=n_results)
        print(f"   ✅ {len(documents)} documents trouvés")
        
        # 3. Generate prompt
        print("   📝 Construction du prompt...")
        prompt = self.generate_prompt(
            question,
            documents, 
            include_history=use_history
        )
        
        # 4. Generate answer
        print("   🤖 Génération de la réponse...")
        answer = self.generate_answer(prompt, max_tokens=200)  # Réduit pour concision
        
        # 5. Ajouter à l'historique
        if use_history:
            self.add_to_history(question, answer)
        
        # 6. Format sources
        sources = [
            {
                'source': doc['metadata']['source'],
                'category': doc['metadata']['category'],
                'score': doc['score']
            }
            for doc in documents
        ]
        
        print("   ✅ Réponse générée\n")
        
        return {
            'question': question,
            'answer': answer,
            'sources': sources,
            'reformulated_query': search_query if search_query != question else None,
            'is_greeting': False
        }

# ============================================
# FONCTION DE TEST
# ============================================

def test_conversation():
    """Teste une conversation multi-tours"""
    
    print("=" * 70)
    print("TEST CONVERSATION MULTI-TOURS")
    print("=" * 70 + "\n")
    
    rag = RAGService()
    
    # Conversation
    questions = [
        "Bonjour !"
        "Quand commence le semestre d'automne 2024 ?",
        "Et combien de temps dure-t-il ?",  # ← Référence à question précédente
        "Merci ! Maintenant, quelles sont les règles d'absence ?"
    ]
    
    for i, q in enumerate(questions, 1):
        print(f"\n{'='*70}")
        print(f"TOUR {i}")
        print(f"{'='*70}")
        
        result = rag.ask(q, use_history=True)
        
        print(f"\n❓ {result['question']}")
        print(f"\n💬 {result['answer']}")
        print(f"\n📚 Sources : {', '.join([s['source'][:30] for s in result['sources']])}")
    
    # Effacer historique
    print(f"\n{'='*70}")
    rag.clear_history()


if __name__ == "__main__":
    # Test simple
    # test_rag_service()
    
    # Test conversation
    test_conversation()


# ============================================
# MAIN
# ============================================

if __name__ == "__main__":
    test_conversation()