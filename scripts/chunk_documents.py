"""
Script de nettoyage et chunking des documents

Processus :
1. Charger les documents extraits
2. Nettoyer le texte
3. Découper en chunks intelligents
4. Sauvegarder avec métadonnées enrichies
"""

import json
from pathlib import Path
import re
from typing import List, Dict

# ============================================
# NETTOYAGE DU TEXTE
# ============================================

def clean_text(text: str) -> str:
    """
    Nettoie le texte extrait
    
    Pourquoi nettoyer ?
    - PDFs peuvent avoir espaces bizarres
    - Sauts de ligne excessifs
    - Caractères spéciaux inutiles
    
    Opérations :
    1. Remplacer multiples espaces par un seul
    2. Remplacer multiples sauts de ligne par max 2
    3. Supprimer espaces en début/fin de lignes
    4. Normaliser tirets et guillemets
    """
    
    # Remplacer espaces multiples par un seul
    text = re.sub(r' +', ' ', text)
    
    # Remplacer plus de 2 sauts de ligne par exactement 2
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Supprimer espaces en début/fin de chaque ligne
    lines = [line.strip() for line in text.split('\n')]
    text = '\n'.join(lines)
    
    # Normaliser tirets (remplacer tirets bizarres par tiret standard)
    text = text.replace('—', '-').replace('–', '-')
    
    # Supprimer espaces avant ponctuation
    text = re.sub(r'\s+([.,;:!?])', r'\1', text)
    
    return text.strip()


# ============================================
# CHUNKING INTELLIGENT
# ============================================

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 100) -> List[str]:
    """
    Découpe le texte en chunks avec overlap
    
    Args:
        text: Texte à découper
        chunk_size: Nombre de MOTS par chunk (pas caractères)
        overlap: Nombre de MOTS qui se chevauchent
    
    Pourquoi découper par MOTS et pas CARACTÈRES ?
    - Plus naturel (ne coupe pas au milieu d'un mot)
    - Plus prévisible (500 mots ≈ 1 page)
    
    Exemple avec chunk_size=4, overlap=2 :
    Texte: "A B C D E F G H"
    Chunk 1: "A B C D"
    Chunk 2: "C D E F"  ← overlap avec chunk 1
    Chunk 3: "E F G H"  ← overlap avec chunk 2
    """
    
    # Séparer en mots
    words = text.split()
    
    # Si texte trop court, retourner tel quel
    if len(words) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(words):
        # Prendre chunk_size mots à partir de start
        end = start + chunk_size
        chunk_words = words[start:end]
        
        # Reconstituer le texte du chunk
        chunk = ' '.join(chunk_words)
        chunks.append(chunk)
        
        # Avancer avec overlap
        # Si on a chunk_size=500 et overlap=100
        # On avance de 500-100 = 400 mots
        start += (chunk_size - overlap)
    
    return chunks


# ============================================
# TRAITEMENT COMPLET
# ============================================

def process_documents(input_file: str, output_file: str):
    """
    Charge, nettoie et chunk tous les documents
    """
    
    print("🧹 NETTOYAGE ET CHUNKING DES DOCUMENTS\n")
    print("=" * 60)
    
    # 1. Charger les documents extraits
    print(f"\n📂 Chargement depuis : {input_file}")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        documents = json.load(f)
    
    print(f"✅ {len(documents)} documents chargés\n")
    
    # 2. Traiter chaque document
    all_chunks = []
    stats = {
        'total_docs': len(documents),
        'total_chunks': 0,
        'total_chars_before': 0,
        'total_chars_after': 0,
        'by_category': {}
    }
    
    for doc_idx, doc in enumerate(documents, 1):
        source = doc['metadata']['source']
        category = doc['metadata']['category']
        original_text = doc['text']
        
        print(f"[{doc_idx}/{len(documents)}] 🔄 {source}")
        
        # Stats avant
        chars_before = len(original_text)
        stats['total_chars_before'] += chars_before
        
        # Nettoyer
        cleaned_text = clean_text(original_text)
        chars_after = len(cleaned_text)
        stats['total_chars_after'] += chars_after
        
        print(f"   Nettoyage : {chars_before:,} → {chars_after:,} caractères")
        
        # Chunker
        chunks = chunk_text(
            cleaned_text,
            chunk_size=500,  # 500 mots par chunk
            overlap=100       # 100 mots d'overlap
        )
        
        print(f"   Chunking : {len(chunks)} chunk(s) créé(s)")
        
        # Créer un objet pour chaque chunk
        for chunk_idx, chunk_context in enumerate(chunks):
            chunk_obj = {
                'text': chunk_context,
                'metadata': {
                    # Métadonnées du document original
                    'source': source,
                    'category': category,
                    'doc_path': doc['metadata']['path'],
                    
                    # Métadonnées du chunk
                    'chunk_id': f"{doc_idx}_{chunk_idx}",
                    'chunk_index': chunk_idx,
                    'total_chunks': len(chunks),
                    
                    # Stats
                    'chunk_chars': len(chunk_context),
                    'chunk_words': len(chunk_context.split()),
                }
            }
            
            all_chunks.append(chunk_obj)
        
        # Stats par catégorie
        if category not in stats['by_category']:
            stats['by_category'][category] = {'docs': 0, 'chunks': 0}
        stats['by_category'][category]['docs'] += 1
        stats['by_category'][category]['chunks'] += len(chunks)
        
        stats['total_chunks'] += len(chunks)
    
    # 3. Sauvegarder
    print("\n" + "=" * 60)
    print(f"\n💾 Sauvegarde dans : {output_file}")
    
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=2)
    
    # 4. Afficher statistiques
    print("\n📊 STATISTIQUES FINALES\n")
    print(f"Documents traités : {stats['total_docs']}")
    print(f"Chunks créés : {stats['total_chunks']}")
    print(f"Moyenne chunks/doc : {stats['total_chunks'] / stats['total_docs']:.1f}")
    print(f"\nCaractères avant nettoyage : {stats['total_chars_before']:,}")
    print(f"Caractères après nettoyage : {stats['total_chars_after']:,}")
    print(f"Réduction : {(1 - stats['total_chars_after']/stats['total_chars_before']) * 100:.1f}%")
    
    print(f"\nPar catégorie :")
    for cat, data in stats['by_category'].items():
        print(f"   • {cat}:")
        print(f"      - Documents : {data['docs']}")
        print(f"      - Chunks : {data['chunks']}")
        print(f"      - Moyenne : {data['chunks']/data['docs']:.1f} chunks/doc")
    
    print("\n🎉 Traitement terminé avec succès !")


# ============================================
# VISUALISATION (optionnel)
# ============================================

def preview_chunks(chunks_file: str, num_examples: int = 3):
    """
    Affiche quelques exemples de chunks pour vérification
    """
    
    print("\n" + "=" * 60)
    print("APERÇU DES CHUNKS\n")
    
    with open(chunks_file, 'r', encoding='utf-8') as f:
        chunks = json.load(f)
    
    for i in range(min(num_examples, len(chunks))):
        chunk = chunks[i]
        text = chunk['text']
        meta = chunk['metadata']
        
        print(f"\n📄 Chunk {i+1}/{len(chunks)}")
        print(f"Source : {meta['source']}")
        print(f"Catégorie : {meta['category']}")
        print(f"Position : {meta['chunk_index'] + 1}/{meta['total_chunks']}")
        print(f"Taille : {meta['chunk_words']} mots")
        print(f"\nTexte (200 premiers caractères) :")
        print("-" * 60)
        print(text[:200] + "...")
        print("-" * 60)


# ============================================
# MAIN
# ============================================

if __name__ == "__main__":
    # Chemins
    input_file = "data/processed/extracted_documents.json"
    output_file = "data/processed/chunked_documents.json"
    
    # Vérifier que le fichier d'entrée existe
    if not Path(input_file).exists():
        print(f"❌ ERREUR : {input_file} n'existe pas")
        print("   Lancez d'abord : python scripts/parse_documents.py")
        exit(1)
    
    # Traiter
    process_documents(input_file, output_file)
    
    # Aperçu
    preview_chunks(output_file, num_examples=2)