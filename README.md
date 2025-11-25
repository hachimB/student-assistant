# Student Assistant RAG Chatbot

**RAG-powered student assistant** that answers questions using **official university documents** (regulations, timetables, exam calendars, procedures, FAQs, etc.).


## The classic LLM problem (ChatGPT-style chatbots)

They **hallucinate** when asked about specific documents they have never seen  
→ “When are the S1 resit exams in 2025?” → wrong or invented date  
They have a **limited context window** (8k–128k tokens max)
**Solution = RAG (Retrieval-Augmented Generation)**

## How RAG works – Simple flow
Student question
↓

Retrieval → semantic search in a vector database (FAISS/Chroma)
containing ALL university PDFs split into chunks with overlap
↓
Augmentation → the 3–5 most relevant text chunks are injected into the prompt
Example: "According to the official regulation (page 12): The resit exams take place..."
↓
Generation → the LLM answers only using real documents
→ 100 % accurate, no hallucination, sources cited


---


# Student-assistant
**Student Assistant RAG Chatbot**
→ Système RAG (Retrieval-Augmented Generation) pour répondre aux questions étudiants  
  à partir des documents officiels d'une école (règlements, emplois du temps, ...)
→ Pipeline complet : parsing PDF/docx → chunking + overlap → embeddings → recherche vectorielle → génération avec sources

## Problème classique des chatbots basés uniquement sur un LLM (comme ChatGPT)

Ils hallucinent (inventent des réponses fausses) quand la question porte sur des documents précis que le modèle n’a jamais vus (ex. : règlement intérieur UM5 2025, dates exactes d’examens…).
Ils ont une mémoire limitée (max 8k–128k tokens selon le modèle).
**Solution = RAG (Retrieval-Augmented Generation)**

## RAG = Retrieval-Augmented Generation
### Exemple de fonctionnement d'un système RAG

Question étudiant
       ↓
1. Retrieval (Recherche) → on va chercher dans une base de données vectorielle  
   les 3–5 morceaux de texte (chunks) les plus pertinents parmi TOUS les PDFs de l’école
       ↓
2. Augmentation → on injecte ces morceaux pertinents dans le prompt du LLM
   (ex. : « Voici l’extrait du règlement page 12 : … »)
       ↓
3. Generation → le LLM répond **en se basant uniquement sur les vrais documents**  
   → plus d’hallucinations, réponses 100 % fiables et sourcées
