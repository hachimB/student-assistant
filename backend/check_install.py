"""Script pour vérifier que toutes les dépendances sont installées"""

def check_imports():
    packages = {
        'langchain': 'LangChain',
        'openai': 'OpenAI',
        'fastapi': 'FastAPI',
        'streamlit': 'Streamlit',
        'chromadb': 'ChromaDB',
        'pypdf': 'PyPDF',
        'docx': 'python-docx',
        'sqlalchemy': 'SQLAlchemy',
    }
    
    print("🔍 Vérification des installations...\n")
    
    all_ok = True
    for package, name in packages.items():
        try:
            __import__(package)
            print(f"✅ {name}")
        except ImportError:
            print(f"❌ {name} - NON INSTALLÉ")
            all_ok = False
    
    if all_ok:
        print("\n🎉 Toutes les dépendances sont installées !")
    else:
        print("\n⚠️ Certains packages manquent. Relancez: uv sync")

if __name__ == "__main__":
    check_imports()