"""
Service RAG (Retrieval-Augmented Generation)

Architecture :
Question → Embedding → ChromaDB → Top K chunks → Prompt + LLM → Réponse
"""

import os
from pathlib import Path
from typing import List, Dict, Optional

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
        """Initialise le service RAG"""
        
        print("🚀 Initialisation du service RAG...")
        
        # 1. Modèle d'embeddings
        print(f"   📦 Chargement modèle embeddings...")
        self.embedding_model = SentenceTransformer(EMBEDDING_MODEL)
        
        # 2. ChromaDB
        print(f"   🗄️ Connexion ChromaDB...")
        self.chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        self.collection = self.chroma_client.get_collection(name=COLLECTION_NAME)
        
        # 3. LLM Client
        print(f"   🤖 Connexion HuggingFace API...")
        self.llm_client = InferenceClient(token=HUGGINGFACE_API_KEY)
        
        print("✅ Service RAG prêt !\n")
    
    
    def retrieve_documents(
        self, 
        query: str, 
        n_results: int = 3,
        category_filter: Optional[str] = None
    ) -> List[Dict]:
        """
        Recherche les documents pertinents
        
        Args:
            query: Question de l'utilisateur
            n_results: Nombre de résultats à retourner
            category_filter: Filtrer par catégorie (optionnel)
        
        Returns:
            Liste de documents avec métadonnées
        """
        
        # Générer embedding de la question
        query_embedding = self.embedding_model.encode([query])[0]
        
        # Rechercher dans ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=n_results,
            # where={"category": category_filter} if category_filter else None
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
                'score': 1 / (1 + abs(distance))  # Convertir distance en score 0-1
            })
        
        return documents
    
    
    def generate_prompt(
        self, 
        query: str, 
        documents: List[Dict]
    ) -> str:
        """
        Construit le prompt pour le LLM
        
        Structure :
        1. Instructions système
        2. Contexte (documents récupérés)
        3. Question
        4. Instructions de réponse
        """
        
        # Construire le contexte à partir des documents
        context = ""
        for i, doc in enumerate(documents, 1):
            source = doc['metadata']['source']
            category = doc['metadata']['category']
            text = doc['text']
            
            context += f"\n[Document {i}]\n"
            context += f"Source: {source}\n"
            context += f"Catégorie: {category}\n"
            context += f"Contenu: {text}\n"
            context += "-" * 60 + "\n"
        
        # Prompt complet
        prompt = f"""Tu es un assistant virtuel pour les étudiants de l'Université Mohammed V de Rabat (UM5).
        Ton rôle :
        - Répondre aux questions sur les emplois du temps, règlements, procédures et FAQ
        - Utiliser UNIQUEMENT les informations fournies dans le contexte
        - Citer les sources de tes informations
        - Être précis, bienveillant et professionnel
        Contexte disponible :
        {context}
        Question de l'étudiant : {query}
        Instructions pour ta réponse :
        1. Réponds en te basant UNIQUEMENT sur le contexte ci-dessus
        2. Si l'information n'est pas dans le contexte, dis "Je n'ai pas cette information dans ma base de connaissances"
        3. Cite la source (nom du document) pour chaque information
        4. Sois concis mais complet
        5. Utilise un ton professionnel mais accessible
        6. Si les questions sont poses en Francais, tu Dois repondre en Francais et non en Anglais.
        7. Tu ne reponds en anglais que si on te pose des question en anglais sinon reponds en Francais
        Réponse :"""

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
    
    
    def ask(
        self, 
        question: str,
        n_results: int = 3,
        category_filter: Optional[str] = None
    ) -> Dict:
        """
        Pipeline RAG complet
        
        C'est la fonction principale qui orchestre tout :
        1. Retrieval (recherche)
        2. Prompt generation
        3. Answer generation
        4. Source formatting
        
        Args:
            question: Question de l'utilisateur
            n_results: Nombre de documents à récupérer
            category_filter: Filtrer par catégorie
        
        Returns:
            Dict avec answer, sources, metadata
        """
        
        print(f"\n❓ Question : {question}")
        
        # 1. Retrieval
        print("   🔍 Recherche documents pertinents...")
        documents = self.retrieve_documents(
            query=question,
            n_results=n_results,
            category_filter=category_filter
        )
        
        print(f"   ✅ {len(documents)} documents trouvés")
        
        # 2. Generate prompt
        print("   📝 Construction du prompt...")
        prompt = self.generate_prompt(question, documents)
        
        # 3. Generate answer
        print("   ...Génération de la réponse...")
        answer = self.generate_answer(prompt)
        
        # 4. Format sources
        sources = [
            {
                'source': doc['metadata']['source'],
                'category': doc['metadata']['category'],
                'score': doc['score'],
                'excerpt': doc['text'][:200] + "..."
            }
            for doc in documents
        ]
        
        print("   ✅ Réponse générée\n")
        
        return {
            'question': question,
            'answer': answer,
            'sources': sources,
            'metadata': {
                'n_documents_used': len(documents),
                'model': LLM_MODEL
            }
        }


# ============================================
# FONCTION DE TEST
# ============================================

def test_rag_service():
    """Teste le service RAG avec des questions exemples"""
    
    print("=" * 70)
    print("TEST DU SERVICE RAG")
    print("=" * 70 + "\n")
    
    # Initialiser le service
    rag = RAGService()
    
    # Questions test
    test_questions = [
        "Quand commence le semestre d'hiver 2024-2025 ?",
        "Quelles sont les règles concernant les absences à l'ENSIAS ?",
        "Comment s'inscrire à l'UM5 pour 2025-2026 ?"
    ]
    
    # Tester chaque question
    for i, question in enumerate(test_questions, 1):
        print("=" * 70)
        print(f"TEST {i}/{len(test_questions)}")
        print("=" * 70)
        
        result = rag.ask(question)
        
        print(f"\n📌 QUESTION :")
        print(f"   {result['question']}")
        
        print(f"\n💬 RÉPONSE :")
        print(f"   {result['answer']}")
        
        print(f"\n📚 SOURCES ({len(result['sources'])}) :")
        for j, source in enumerate(result['sources'], 1):
            print(f"\n   {j}. {source['source']}")
            print(f"      Catégorie : {source['category']}")
            print(f"      Score : {source['score']:.3f}")
            print(f"      Extrait : {source['excerpt'][:100]}...")
        
        print("\n")


# ============================================
# MAIN
# ============================================

if __name__ == "__main__":
    test_rag_service()