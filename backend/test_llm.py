"""Test du LLM avec HuggingFace Inference API (GRATUIT) - CORRIGÉ"""

import os
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

load_dotenv()

def test_llm():
    api_key = os.getenv("HUGGINGFACE_API_KEY")
    
    if not api_key:
        print("❌ Token HuggingFace manquant dans .env")
        return False
    
    # Modèle Instruct → mieux avec chat
    model = "mistralai/Mistral-7B-Instruct-v0.2"
    
    print(f"🤖 Modèle LLM : {model}")
    print("🔄 Test de génération de texte via chat...\n")
    
    try:
        client = InferenceClient(token=api_key)
        
        messages = [
            {"role": "user", "content": "Tu es un assistant pour étudiants. Quand commence le semestre d'hiver ? Réponds en une phrase courte."}
        ]
        
        print(f"📝 Prompt envoyé :\n   {messages[0]['content']}\n")
        
        # Utilise chat_completion au lieu de text_generation
        response = client.chat_completion(
            messages=messages,
            model=model,
            max_tokens=100,
            temperature=0.7,
        )
        
        answer = response.choices[0].message.content
        print(f"✅ Réponse générée :\n   {answer}\n")
        print("🎉 Test LLM réussi avec chat_completion !")
        return True
        
    except Exception as e:
        print(f"❌ ERREUR : {e}")
        if "rate limit" in str(e).lower():
            print("\n⏳ Rate limit atteint → attends 1-2 min")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("TEST LLM HUGGINGFACE (GRATUIT) - FIXÉ")
    print("=" * 50 + "\n")
    test_llm()