"""
Gestionnaire de conversations avec persistance

Stocke les conversations en JSON (simple pour MVP)
En production : utiliser une vraie DB (PostgreSQL, MongoDB)
"""

import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import uuid

CONVERSATIONS_DIR = Path("data/conversations")

class ConversationManager:
    """
    Gère la création, sauvegarde et chargement des conversations
    """
    
    def __init__(self):
        """Initialise le gestionnaire"""
        
        # Créer dossier si nécessaire
        CONVERSATIONS_DIR.mkdir(parents=True, exist_ok=True)
    
    
    def create_conversation(self) -> str:
        """
        Crée une nouvelle conversation
        
        Returns:
            ID de la conversation créée
        """
        
        conv_id = f"conv_{uuid.uuid4().hex[:12]}"
        
        conversation = {
            'id': conv_id,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'messages': [],
            'metadata': {
                'message_count': 0
            }
        }
        
        self._save_conversation(conv_id, conversation)
        
        return conv_id
    
    
    def add_message(
        self, 
        conv_id: str, 
        role: str, 
        content: str,
        sources: List[Dict] = None
    ):
        """
        Ajoute un message à une conversation
        
        Args:
            conv_id: ID de la conversation
            role: 'user' ou 'assistant'
            content: Contenu du message
            sources: Sources (si assistant)
        """
        
        conversation = self.load_conversation(conv_id)
        
        if conversation is None:
            # Créer si n'existe pas
            self.create_conversation()
            conversation = self.load_conversation(conv_id)
        
        message = {
            'id': f"msg_{uuid.uuid4().hex[:8]}",
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat(),
            'sources': sources or []
        }
        
        conversation['messages'].append(message)
        conversation['updated_at'] = datetime.now().isoformat()
        conversation['metadata']['message_count'] = len(conversation['messages'])
        
        self._save_conversation(conv_id, conversation)
    
    
    def load_conversation(self, conv_id: str) -> Optional[Dict]:
        """
        Charge une conversation
        
        Args:
            conv_id: ID de la conversation
        
        Returns:
            Données de la conversation ou None
        """
        
        file_path = CONVERSATIONS_DIR / f"{conv_id}.json"
        
        if not file_path.exists():
            return None
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    
    def list_conversations(self) -> List[Dict]:
        """
        Liste toutes les conversations
        
        Returns:
            Liste des métadonnées de conversations
        """
        
        conversations = []
        
        for file_path in CONVERSATIONS_DIR.glob("conv_*.json"):
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # Extraire métadonnées uniquement
                conversations.append({
                    'id': data['id'],
                    'created_at': data['created_at'],
                    'updated_at': data['updated_at'],
                    'message_count': data['metadata']['message_count'],
                    'preview': data['messages'][0]['content'][:50] + "..." if data['messages'] else ""
                })
        
        # Trier par date (plus récent d'abord)
        conversations.sort(key=lambda x: x['updated_at'], reverse=True)
        
        return conversations
    
    
    def delete_conversation(self, conv_id: str) -> bool:
        """
        Supprime une conversation
        
        Args:
            conv_id: ID de la conversation
        
        Returns:
            True si supprimé, False sinon
        """
        
        file_path = CONVERSATIONS_DIR / f"{conv_id}.json"
        
        if file_path.exists():
            file_path.unlink()
            return True
        
        return False
    
    
    def _save_conversation(self, conv_id: str, data: Dict):
        """
        Sauvegarde une conversation
        
        Args:
            conv_id: ID de la conversation
            data: Données à sauvegarder
        """
        
        file_path = CONVERSATIONS_DIR / f"{conv_id}.json"
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


# Instance globale
conversation_manager = ConversationManager()