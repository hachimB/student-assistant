"""
Application FastAPI principale

Point d'entrée de l'API
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.routes import router
from .services.rag_service import get_embedding_model

# ============================================
# APPLICATION
# ============================================

app = FastAPI(
    title="Student Assistant RAG API",
    description="API pour l'assistant virtuel des étudiants UM5",
    version="1.0.0",
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc"  # ReDoc
)

# ============================================
# CORS (pour permettre requêtes depuis frontend)
# ============================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En prod : spécifier domaines autorisés
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# ROUTES
# ============================================

# Inclure les routes API
app.include_router(router)

# Route racine
@app.get("/")
async def root():
    """Page d'accueil de l'API"""
    return {
        "message": "Student Assistant RAG API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/v1/health"
    }


# ============================================
# EVENTS
# ============================================

@app.on_event("startup")
async def startup_event():
    """Exécuté au démarrage de l'API"""
    print("🚀 API démarrée")
    print("📦 Pré-chargement du modèle d'embeddings...")
    
    # Charger le modèle UNE FOIS au démarrage
    get_embedding_model()
    
    print("✅ Modèle prêt - API opérationnelle")
    print("📚 Documentation : http://localhost:8000/docs")


@app.on_event("shutdown")
async def shutdown_event():
    """Exécuté à l'arrêt de l'API"""
    print("👋 API arrêtée")