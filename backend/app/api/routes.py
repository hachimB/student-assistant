"""
Routes API FastAPI

Endpoints :
- POST /api/v1/ask : Poser une question
- GET /api/v1/history/{session_id} : Récupérer historique
- POST /api/v1/feedback : Donner feedback
- GET /api/v1/health : Vérifier santé API
- GET /api/v1/categories : Liste catégories
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict
import uuid
from datetime import datetime

from ..models.schemas import (
    QuestionRequest, QuestionResponse, 
    FeedbackRequest, HistoryResponse,
    HealthResponse, Source
)
from ..services.rag_service import RAGService
from ..core.conversation_manager import conversation_manager

# ============================================
# ROUTER
# ============================================

router = APIRouter(prefix="/api/v1", tags=["RAG"])

# Instance globale du service RAG (chargé au démarrage)
rag_service: RAGService = None

# Stockage sessions (en mémoire pour simplicité - en prod : Redis/DB)
sessions: Dict[str, RAGService] = {}


# ============================================
# DEPENDENCY : Obtenir ou créer service RAG
# ============================================

def get_rag_service(session_id: str = None) -> RAGService:
    """
    Retourne le service RAG pour une session
    
    Si session_id fourni : retourne service avec historique
    Sinon : retourne service global sans historique
    """
    
    global rag_service
    
    if session_id:
        # Service avec mémoire de session
        if session_id not in sessions:
            sessions[session_id] = RAGService()
        return sessions[session_id]
    else:
        # Service global sans mémoire
        if rag_service is None:
            rag_service = RAGService()
        return rag_service


# ============================================
# ENDPOINTS
# ============================================

@router.post("/ask", response_model=QuestionResponse)
async def ask_question(request: QuestionRequest):
    """
    Pose une question au RAG
    """
    
    try:
        # Créer conversation si besoin
        if request.session_id and not conversation_manager.load_conversation(request.session_id):
            conversation_manager.create_conversation()
        
        # Obtenir service RAG
        rag = get_rag_service(request.session_id)
        
        # Sauvegarder question
        if request.session_id:
            conversation_manager.add_message(
                request.session_id,
                role='user',
                content=request.question
            )
        
        # Poser la question
        result = rag.ask(
            question=request.question,
            n_results=request.n_results,
            use_history=request.use_history
        )
        
        # Générer ID
        question_id = f"q_{uuid.uuid4().hex[:12]}"
        
        # Formater sources
        sources = [
            Source(
                source=s['source'],
                category=s['category'],
                score=s['score']
            )
            for s in result['sources']
        ]
        
        # Sauvegarder réponse
        if request.session_id:
            conversation_manager.add_message(
                request.session_id,
                role='assistant',
                content=result['answer'],
                sources=[s.dict() for s in sources]
            )
        
        # Construire réponse
        response = QuestionResponse(
            question_id=question_id,
            question=result['question'],
            answer=result['answer'],
            sources=sources,
            session_id=request.session_id,
            reformulated_query=result.get('reformulated_query'),
            metadata={
                'timestamp': datetime.now().isoformat(),
                'n_documents_used': len(sources),
                'is_greeting': result.get('is_greeting', False)
            }
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur : {str(e)}"
        )


@router.get("/history/{session_id}", response_model=HistoryResponse)
async def get_history(session_id: str):
    """
    Récupère l'historique d'une session
    
    - **session_id** : ID de la session
    
    Retourne tous les échanges de la conversation.
    """
    
    if session_id not in sessions:
        raise HTTPException(
            status_code=404,
            detail=f"Session '{session_id}' introuvable"
        )
    
    rag = sessions[session_id]
    
    history_items = [
        {
            'question': item['question'],
            'answer': item['answer'],
            'timestamp': datetime.now().isoformat()  # À améliorer
        }
        for item in rag.conversation_history
    ]
    
    return HistoryResponse(
        session_id=session_id,
        history=history_items,
        count=len(history_items)
    )


@router.delete("/history/{session_id}")
async def clear_history(session_id: str):
    """
    Efface l'historique d'une session
    
    - **session_id** : ID de la session
    """
    
    if session_id not in sessions:
        raise HTTPException(
            status_code=404,
            detail=f"Session '{session_id}' introuvable"
        )
    
    sessions[session_id].clear_history()
    
    return {"message": f"Historique de la session '{session_id}' effacé"}


@router.post("/feedback")
async def submit_feedback(feedback: FeedbackRequest):
    """
    Enregistre un feedback sur une réponse
    
    - **question_id** : ID de la question évaluée
    - **rating** : -1 (👎), 0 (neutre), 1 (👍)
    - **comment** : Commentaire optionnel
    
    TODO : Stocker dans base de données pour analyse
    """
    
    # Pour l'instant, juste logger
    print(f"📊 Feedback reçu : Q={feedback.question_id}, Rating={feedback.rating}")
    
    if feedback.comment:
        print(f"   Commentaire : {feedback.comment}")
    
    # En production : sauvegarder dans DB
    # db.save_feedback(feedback)
    
    return {
        "message": "Feedback enregistré",
        "question_id": feedback.question_id
    }


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Vérifie la santé de l'API
    
    Retourne le statut des composants (modèles, ChromaDB).
    """
    
    try:
        global rag_service
        
        # Vérifier que le service peut être initialisé
        if rag_service is None:
            rag_service = RAGService()
        
        # Tester ChromaDB
        count = rag_service.collection.count()
        
        return HealthResponse(
            status="healthy",
            version="1.0.0",
            models_loaded=True,
            chroma_connected=count > 0
        )
        
    except Exception as e:
        return HealthResponse(
            status="unhealthy",
            version="1.0.0",
            models_loaded=False,
            chroma_connected=False
        )


@router.get("/categories")
async def get_categories():
    """
    Liste les catégories de documents disponibles
    
    Retourne : emploi_temps, reglements, procedures, faqs, notes
    """
    
    categories = [
        {"id": "emploi_temps", "name": "Emplois du temps", "description": "Calendriers et horaires"},
        {"id": "reglements", "name": "Règlements", "description": "Règles et chartes"},
        {"id": "procedures", "name": "Procédures", "description": "Démarches administratives"},
        {"id": "faqs", "name": "FAQs", "description": "Questions fréquentes"},
        {"id": "notes", "name": "Notes", "description": "Système de notation"}
    ]
    
    return {"categories": categories}



@router.post("/conversations", status_code=201)
async def create_conversation():
    """
    Crée une nouvelle conversation
    
    Retourne l'ID de la conversation créée.
    """
    
    conv_id = conversation_manager.create_conversation()
    
    return {
        "conversation_id": conv_id,
        "message": "Nouvelle conversation créée"
    }


@router.get("/conversations")
async def list_conversations():
    """
    Liste toutes les conversations
    
    Retourne la liste avec métadonnées (ID, date, aperçu).
    """
    
    conversations = conversation_manager.list_conversations()
    
    return {
        "conversations": conversations,
        "count": len(conversations)
    }


@router.get("/conversations/{conv_id}")
async def get_conversation(conv_id: str):
    """
    Récupère une conversation complète
    
    - **conv_id**: ID de la conversation
    
    Retourne tous les messages de la conversation.
    """
    
    conversation = conversation_manager.load_conversation(conv_id)
    
    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail=f"Conversation '{conv_id}' introuvable"
        )
    
    return conversation


@router.delete("/conversations/{conv_id}")
async def delete_conversation(conv_id: str):
    """
    Supprime une conversation
    
    - **conv_id**: ID de la conversation
    """
    
    success = conversation_manager.delete_conversation(conv_id)
    
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"Conversation '{conv_id}' introuvable"
        )
    
    # Supprimer aussi de la session en mémoire
    if conv_id in sessions:
        del sessions[conv_id]
    
    return {"message": f"Conversation '{conv_id}' supprimée"}