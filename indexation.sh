# 1. Extraction
echo "📄 Extraction des documents..."
uv run python scripts/parse_documents.py

# 2. Nettoyage et chunking
echo "🧹 Nettoyage et chunking..."
uv run python scripts/chunk_documents.py

# 3. Indexation vectorielle
echo "🗄️ Indexation dans ChromaDB..."
uv run python scripts/index_documents.py