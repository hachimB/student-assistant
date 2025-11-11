"""Test de connexion à HuggingFace"""

import os
from dotenv import load_dotenv
from huggingface_hub import HfApi, login

load_dotenv()

def test_huggingface_connection():
    """Teste si le token HuggingFace fonctionne"""
    
    # Vérifier que le token existe
    api_key = os.getenv("HUGGINGFACE_API_KEY")
    
    if not api_key:
        print("❌ ERREUR : HUGGINGFACE_API_KEY non trouvée dans .env")
        return False
    
    if api_key == "your_huggingface_token_here":
        print("❌ ERREUR : Remplacez le token dans .env par votre vrai token")
        return False
    
    print(f"✅ Token HuggingFace trouvé : {api_key[:15]}...")
    
    # Tester la connexion
    try:
        print("\n🔄 Test de connexion à HuggingFace...")
        
        # Login
        login(token=api_key)
        
        # Test API
        api = HfApi()
        user_info = api.whoami(token=api_key)
        
        print(f"✅ Connexion réussie !")
        print(f"   - Utilisateur : {user_info['name']}")
        print(f"   - Type : {user_info.get('type', 'user')}")
        
        return True
        
    except Exception as e:
        print(f"❌ ERREUR de connexion : {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("TEST DE CONNEXION HUGGINGFACE")
    print("=" * 50 + "\n")
    
    success = test_huggingface_connection()
    
    if success:
        print("\n🎉 Configuration HuggingFace OK !")
    else:
        print("\n⚠️ Problème de configuration. Vérifiez votre token.")