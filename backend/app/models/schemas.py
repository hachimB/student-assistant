"""
Schémas Pydantic pour validation des requêtes/réponses API

Pydantic :
- Valide automatiquement les types de données
- Génère la documentation Swagger
- Convertit JSON ↔ Python objects
"""

from typing import List, Optional
from pydantic import BaseModel, Field

# ============================================
# REQUÊTES (Input)
# ============================================

class QuestionRequest(BaseModel):
    """
    Requête pour poser une question
    
    Exemple JSON :
    {
        "question": "Quand commence le semestre ?",
        "session_id": "user123",
        "n_results": 3,
        "use_history": true
    }
    """
    
    question: str = Field(
        ...,  # Requis
        min_length=3,
        max_length=500,
        description="Question de l'étudiant",
        examples=["Quand commence le semestre d'hiver ?"]
    )
    
    session_id: Optional[str] = Field(
        None,
        description="ID de session pour historique conversationnel",
        examples=["user_abc123"]
    )
    
    n_results: int = Field(
        default=3,
        ge=1,  # >= 1
        le=10,  # <= 10
        description="Nombre de documents à récupérer"
    )
    
    use_history: bool = Field(
        default=True,
        description="Utiliser l'historique conversationnel"
    )
    
    category_filter: Optional[str] = Field(
        None,
        description="Filtrer par catégorie",
        examples=["emploi_temps", "reglements"]
    )


class FeedbackRequest(BaseModel):
    """
    Requête pour donner un feedback sur une réponse
    
    Exemple JSON :
    {
        "question_id": "q_12345",
        "rating": 1,
        "comment": "Très utile !"
    }
    """
    
    question_id: str = Field(
        ...,
        description="ID de la question évaluée"
    )
    
    rating: int = Field(
        ...,
        ge=-1,  # -1 (pouce bas), 0 (neutre), 1 (pouce haut)
        le=1,
        description="Note : -1 (👎), 0 (neutre), 1 (👍)"
    )
    
    comment: Optional[str] = Field(
        None,
        max_length=500,
        description="Commentaire optionnel"
    )


# ============================================
# RÉPONSES (Output)
# ============================================

class Source(BaseModel):
    """
    Informations sur une source citée
    """
    
    source: str = Field(description="Nom du document source")
    category: str = Field(description="Catégorie du document")
    score: float = Field(description="Score de pertinence (0-1)")
    excerpt: Optional[str] = Field(None, description="Extrait du document")


class QuestionResponse(BaseModel):
    """
    Réponse à une question
    
    Exemple JSON :
    {
        "question_id": "q_12345",
        "question": "Quand commence le semestre ?",
        "answer": "Le semestre commence le 18 septembre 2024...",
        "sources": [...],
        "session_id": "user123",
        "reformulated_query": "...",
        "metadata": {...}
    }
    """
    
    question_id: str = Field(description="ID unique de la question")
    question: str = Field(description="Question posée")
    answer: str = Field(description="Réponse générée")
    sources: List[Source] = Field(description="Sources utilisées")
    
    session_id: Optional[str] = Field(None, description="ID de session")
    reformulated_query: Optional[str] = Field(None, description="Question reformulée")
    
    metadata: dict = Field(
        default_factory=dict,
        description="Métadonnées additionnelles"
    )


class HistoryItem(BaseModel):
    """
    Un échange dans l'historique
    """
    
    question: str
    answer: str
    timestamp: str


class HistoryResponse(BaseModel):
    """
    Historique d'une session
    """
    
    session_id: str
    history: List[HistoryItem]
    count: int


class HealthResponse(BaseModel):
    """
    Statut de santé de l'API
    """
    
    status: str = Field(description="'healthy' ou 'unhealthy'")
    version: str = Field(description="Version de l'API")
    models_loaded: bool = Field(description="Modèles chargés")
    chroma_connected: bool = Field(description="ChromaDB connecté")


class StatsResponse(BaseModel):
    """
    Statistiques de l'API
    """
    
    total_questions: int
    total_sessions: int
    avg_response_time: float
    top_categories: dict