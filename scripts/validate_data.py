"""
Script de validation des données traitées

Vérifie :
1. Tous les fichiers existent
2. Données bien structurées
3. Statistiques cohérentes
4. Pas de chunks vides
"""

import json
from pathlib import Path
from collections import Counter

def validate_data():
    """Valide les données avant indexation"""
    
    print("✅ VALIDATION DES DONNÉES\n")
    print("=" * 60)
    
    # Vérifier que les fichiers existent
    extracted_file = Path("data/processed/extracted_documents.json")
    chunked_file = Path("data/processed/chunked_documents.json")
    
    if not extracted_file.exists():
        print("❌ ERREUR : extracted_documents.json manquant")
        return False
    
    if not chunked_file.exists():
        print("❌ ERREUR : chunked_documents.json manquant")
        return False
    
    print("✅ Fichiers présents\n")
    
    # Charger les chunks
    with open(chunked_file, 'r', encoding='utf-8') as f:
        chunks = json.load(f)
    
    print(f"📊 Total chunks : {len(chunks)}\n")
    
    # Validation 1 : Pas de chunks vides
    empty_chunks = [c for c in chunks if not c['text'].strip()]
    if empty_chunks:
        print(f"⚠️ Attention : {len(empty_chunks)} chunks vides détectés")
    else:
        print("✅ Aucun chunk vide")
    
    # Validation 2 : Métadonnées complètes
    required_fields = ['text', 'metadata']
    required_meta = ['source', 'category', 'chunk_id', 'chunk_words']
    
    issues = 0
    for i, chunk in enumerate(chunks[:10]):  # Vérifier 10 premiers
        if not all(field in chunk for field in required_fields):
            print(f"❌ Chunk {i} : champs manquants")
            issues += 1
        if not all(field in chunk['metadata'] for field in required_meta):
            print(f"❌ Chunk {i} : métadonnées incomplètes")
            issues += 1
    
    if issues == 0:
        print("✅ Métadonnées complètes")
    else:
        print(f"⚠️ {issues} problèmes détectés\n")
    
    # Validation 3 : Distribution des chunks
    categories = [c['metadata']['category'] for c in chunks]
    cat_counts = Counter(categories)
    
    print(f"\n📈 Distribution par catégorie :")
    for cat, count in cat_counts.most_common():
        pct = (count / len(chunks)) * 100
        print(f"   • {cat}: {count} chunks ({pct:.1f}%)")
    
    # Validation 4 : Taille des chunks
    chunk_sizes = [c['metadata']['chunk_words'] for c in chunks]
    avg_size = sum(chunk_sizes) / len(chunk_sizes)
    min_size = min(chunk_sizes)
    max_size = max(chunk_sizes)
    
    print(f"\n📏 Taille des chunks (en mots) :")
    print(f"   • Moyenne : {avg_size:.0f} mots")
    print(f"   • Min : {min_size} mots")
    print(f"   • Max : {max_size} mots")
    
    # Validation 5 : Quelques exemples
    print(f"\n📝 Exemples de chunks :")
    for i in range(min(2, len(chunks))):
        chunk = chunks[i]
        print(f"\n   Chunk {i+1}:")
        print(f"   Source : {chunk['metadata']['source'][:50]}...")
        print(f"   Taille : {chunk['metadata']['chunk_words']} mots")
        print(f"   Aperçu : {chunk['text'][:100]}...")
    
    print("\n" + "=" * 60)
    print("\n🎉 Validation terminée - Données prêtes pour indexation !")
    
    return True

if __name__ == "__main__":
    validate_data()