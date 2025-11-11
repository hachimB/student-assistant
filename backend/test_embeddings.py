"""Test des embeddings avec Sentence Transformers (GRATUIT)"""

import os
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

load_dotenv()

def test_embeddings():
    """Teste la génération d'embeddings avec modèle gratuit"""
    
    # Modèle multilingue (français + anglais) - téléchargé localement
    model_name = os.getenv("EMBEDDING_MODEL", 
                          "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    
    print(f"📦 Chargement du modèle : {model_name}")
    print("⏳ Premier chargement peut prendre 1-2 minutes (téléchargement)...\n")
    
    try:
        # Charger le modèle (téléchargé une seule fois)
        model = SentenceTransformer(model_name)
        
        print("✅ Modèle chargé !\n")
        
        # Texte test
        test_texts = [
            "Quand commence le semestre d'hiver ?",
            "Quel est le règlement concernant les absences ?",
            "Comment consulter mes notes ?"
        ]
        
        print("📝 Textes tests :")
        for i, text in enumerate(test_texts, 1):
            print(f"   {i}. {text}")
        
        print("\n🔄 Génération des embeddings...")
        
        # Générer embeddings
        embeddings = model.encode(test_texts)
        
        print(f"✅ Embeddings générés !")
        print(f"   - Nombre de textes : {len(embeddings)}")
        print(f"   - Dimension vecteur : {len(embeddings[0])}")
        print(f"   - Premiers 5 valeurs (texte 1) : {embeddings[0][:5]}")
        
        # Test de similarité
        from sentence_transformers.util import cos_sim
        
        similarity = cos_sim(embeddings[0], embeddings[1])[0][0].item()
        print(f"\n🔍 Similarité texte 1 vs texte 2 : {similarity:.4f}")
        
        print("\n💡 Le modèle est maintenant en cache local (pas de re-téléchargement)")
        
        return True
        
    except Exception as e:
        print(f"❌ ERREUR : {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("TEST EMBEDDINGS AVEC SENTENCE TRANSFORMERS (GRATUIT)")
    print("=" * 60 + "\n")
    
    test_embeddings()