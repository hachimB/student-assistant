"""
Script d'indexation des documents dans ChromaDB

Processus :
1. Charger les chunks
2. Générer embeddings avec SentenceTransformers
3. Stocker dans ChromaDB avec métadonnées
4. Tester la recherche
"""

import json
from pathlib import Path
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from tqdm import tqdm  # Barre de progression
import time

# ============================================
# CONFIGURATION
# ============================================

CHROMA_DB_PATH = "data/chroma_db"
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
COLLECTION_NAME = "student_documents"

# ============================================
# INDEXATION
# ============================================

def index_documents():
    """
    Indexe tous les chunks dans ChromaDB
    """
    
    print("🗄️ INDEXATION DES DOCUMENTS DANS CHROMADB\n")
    print("=" * 60)
    
    # 1. Charger les chunks
    chunks_file = Path("data/processed/chunked_documents.json")
    
    if not chunks_file.exists():
        print("❌ ERREUR : chunked_documents.json manquant")
        print("   Lancez d'abord : python scripts/chunk_documents.py")
        return False
    
    print(f"📂 Chargement des chunks...")
    with open(chunks_file, 'r', encoding='utf-8') as f:
        chunks = json.load(f)
    
    print(f"✅ {len(chunks)} chunks chargés\n")
    
    # 2. Initialiser le modèle d'embeddings
    print(f"🤖 Chargement du modèle : {EMBEDDING_MODEL}")
    print("   (Première fois : téléchargement ~120MB, ~1-2 minutes)")
    
    model = SentenceTransformer(EMBEDDING_MODEL)
    print("✅ Modèle chargé\n")
    
    # 3. Initialiser ChromaDB
    print(f"🗄️ Initialisation ChromaDB : {CHROMA_DB_PATH}")
    
    # Créer le dossier si nécessaire
    Path(CHROMA_DB_PATH).mkdir(parents=True, exist_ok=True)
    
    # Client ChromaDB (stockage local)
    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    
    # Supprimer la collection si elle existe déjà (réindexation propre)
    try:
        client.delete_collection(name=COLLECTION_NAME)
        print("   Collection existante supprimée")
    except:
        pass
    
    # Créer nouvelle collection
    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"description": "Documents étudiants UM5"}
    )
    
    print(f"✅ Collection '{COLLECTION_NAME}' créée\n")
    
    # 4. Générer embeddings et indexer
    print("🔄 Génération des embeddings et indexation...")
    print(f"   (Traitement par batch de 32 chunks)")
    
    batch_size = 32  # Traiter 32 chunks à la fois
    total_batches = (len(chunks) + batch_size - 1) // batch_size
    
    start_time = time.time()
    
    for batch_idx in tqdm(range(0, len(chunks), batch_size), 
                          total=total_batches,
                          desc="Indexation"):
        
        # Batch de chunks
        batch_chunks = chunks[batch_idx:batch_idx + batch_size]
        
        # Extraire les textes
        texts = [chunk['text'] for chunk in batch_chunks]
        
        # Générer embeddings (batch)
        embeddings = model.encode(texts, show_progress_bar=False)
        
        # Préparer pour ChromaDB
        ids = [chunk['metadata']['chunk_id'] for chunk in batch_chunks]
        metadatas = [chunk['metadata'] for chunk in batch_chunks]
        
        # Ajouter à ChromaDB
        collection.add(
            embeddings=embeddings.tolist(),
            documents=texts,
            metadatas=metadatas,
            ids=ids
        )
    
    elapsed = time.time() - start_time
    
    print(f"\n✅ Indexation terminée en {elapsed:.1f}s")
    print(f"   Vitesse : {len(chunks) / elapsed:.1f} chunks/seconde\n")
    
    # 5. Vérification
    print("🔍 Vérification de l'index...")
    count = collection.count()
    print(f"✅ {count} chunks indexés dans ChromaDB\n")
    
    # 6. Test de recherche
    print("=" * 60)
    print("🧪 TEST DE RECHERCHE\n")
    
    test_queries = [
        "Quand commence le semestre d'hiver ?",
        "Règles sur les absences",
        "Comment s'inscrire ?"
    ]
    
    for query in test_queries:
        print(f"❓ Question : {query}")
        
        # Générer embedding de la question
        query_embedding = model.encode([query])[0]
        
        # Rechercher dans ChromaDB
        results = collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=3  # Top 3 résultats
        )
        
        print(f"   📄 Top 3 résultats :")
        for i, (doc, meta, distance) in enumerate(zip(
            results['documents'][0],
            results['metadatas'][0],
            results['distances'][0]
        )):
            print(f"\n   {i+1}. Source : {meta['source'][:40]}...")
            print(f"      Catégorie : {meta['category']}")
            print(f"      Score : {1 - distance:.3f}")  # Similarité
            print(f"      Extrait : {doc[:100]}...")
        
        print()
    
    print("=" * 60)
    print("\n🎉 Indexation réussie ! Vector DB prête à l'emploi.")
    
    return True


# ============================================
# STATISTIQUES INDEX
# ============================================

def show_index_stats():
    """
    Affiche les statistiques de l'index
    """
    
    print("\n📊 STATISTIQUES DE L'INDEX\n")
    
    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    
    try:
        collection = client.get_collection(name=COLLECTION_NAME)
        
        count = collection.count()
        print(f"Total chunks indexés : {count}")
        
        # Peek quelques documents
        sample = collection.peek(limit=5)
        
        print(f"\nÉchantillon (5 premiers chunks) :")
        for i, (doc_id, meta) in enumerate(zip(sample['ids'], sample['metadatas'])):
            print(f"   {i+1}. ID: {doc_id}")
            print(f"      Source: {meta['source'][:50]}...")
            print(f"      Catégorie: {meta['category']}")
        
    except Exception as e:
        print(f"❌ Erreur : {e}")


# ============================================
# MAIN
# ============================================

if __name__ == "__main__":
    # Indexer
    success = index_documents()
    
    if success:
        # Afficher stats
        show_index_stats()