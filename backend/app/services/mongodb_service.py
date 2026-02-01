from pymongo import MongoClient
from datetime import datetime
import os
from typing import List, Dict, Optional

class MongoDBService:
    """
    MongoDB Atlas service for storing chat history between user and AI.
    This is a test implementation for caching conversation data.
    """
    
    def __init__(self):
        # MongoDB Atlas connection string (you'll need to set this in .env)
        self.connection_string = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
        self.db_name = 'drivecode'
        self.collection_name = 'chat_history'
        
        try:
            self.client = MongoClient(self.connection_string)
            self.db = self.client[self.db_name]
            self.collection = self.db[self.collection_name]
            print("✅ MongoDB connected successfully")
        except Exception as e:
            print(f"❌ MongoDB connection failed: {e}")
            self.client = None
    
    def save_chat_message(self, user_id: str, repo_name: str, role: str, content: str, metadata: Optional[Dict] = None) -> bool:
        """
        Save a single chat message to MongoDB.
        
        Args:
            user_id: GitHub user ID or session ID
            repo_name: Repository name for context
            role: 'user' or 'assistant'
            content: Message content
            metadata: Optional additional data (intent, file_path, pr_url, etc.)
        
        Returns:
            bool: True if saved successfully
        """
        if not self.client:
            print("⚠️ MongoDB not connected, message not saved")
            return False
        
        try:
            message = {
                'user_id': user_id,
                'repo_name': repo_name,
                'role': role,
                'content': content,
                'timestamp': datetime.utcnow(),
                'metadata': metadata or {}
            }
            
            result = self.collection.insert_one(message)
            print(f"💾 Chat message saved: {result.inserted_id}")
            return True
        except Exception as e:
            print(f"❌ Error saving message: {e}")
            return False
    
    def save_conversation(self, user_id: str, repo_name: str, messages: List[Dict]) -> bool:
        """
        Save multiple chat messages as a conversation.
        
        Args:
            user_id: GitHub user ID or session ID
            repo_name: Repository name
            messages: List of message dicts with 'role' and 'content'
        
        Returns:
            bool: True if saved successfully
        """
        if not self.client:
            print("⚠️ MongoDB not connected, conversation not saved")
            return False
        
        try:
            conversation = {
                'user_id': user_id,
                'repo_name': repo_name,
                'messages': messages,
                'timestamp': datetime.utcnow(),
                'message_count': len(messages)
            }
            
            result = self.collection.insert_one(conversation)
            print(f"💾 Conversation saved: {result.inserted_id}")
            return True
        except Exception as e:
            print(f"❌ Error saving conversation: {e}")
            return False
    
    def get_recent_chats(self, user_id: str, limit: int = 10) -> List[Dict]:
        """
        Get recent chat messages for a user.
        
        Args:
            user_id: GitHub user ID or session ID
            limit: Maximum number of messages to retrieve
        
        Returns:
            List of recent chat messages
        """
        if not self.client:
            print("⚠️ MongoDB not connected, returning cached data")
            return self._get_cached_chats()
        
        try:
            chats = list(self.collection.find(
                {'user_id': user_id}
            ).sort('timestamp', -1).limit(limit))
            
            # Clean up MongoDB _id for JSON serialization
            for chat in chats:
                chat['_id'] = str(chat['_id'])
                if 'timestamp' in chat:
                    chat['timestamp'] = chat['timestamp'].isoformat()
            
            print(f"📖 Retrieved {len(chats)} recent chats")
            return chats
        except Exception as e:
            print(f"❌ Error retrieving chats: {e}")
            return self._get_cached_chats()
    
    def get_conversation_history(self, user_id: str, repo_name: str, limit: int = 50) -> List[Dict]:
        """
        Get conversation history for a specific user and repository.
        
        Args:
            user_id: GitHub user ID
            repo_name: Repository name
            limit: Maximum number of messages
        
        Returns:
            List of messages in chronological order
        """
        if not self.client:
            print("⚠️ MongoDB not connected, returning cached data")
            return self._get_cached_chats()
        
        try:
            messages = list(self.collection.find(
                {'user_id': user_id, 'repo_name': repo_name}
            ).sort('timestamp', 1).limit(limit))
            
            # Clean up for JSON serialization
            for msg in messages:
                msg['_id'] = str(msg['_id'])
                if 'timestamp' in msg:
                    msg['timestamp'] = msg['timestamp'].isoformat()
            
            print(f"📖 Retrieved {len(messages)} messages for {repo_name}")
            return messages
        except Exception as e:
            print(f"❌ Error retrieving conversation: {e}")
            return self._get_cached_chats()
    
    def delete_old_chats(self, days: int = 30) -> int:
        """
        Delete chat messages older than specified days.
        
        Args:
            days: Number of days to keep
        
        Returns:
            Number of deleted messages
        """
        if not self.client:
            print("⚠️ MongoDB not connected")
            return 0
        
        try:
            from datetime import timedelta
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            result = self.collection.delete_many({
                'timestamp': {'$lt': cutoff_date}
            })
            
            print(f"🗑️ Deleted {result.deleted_count} old messages")
            return result.deleted_count
        except Exception as e:
            print(f"❌ Error deleting old chats: {e}")
            return 0
    
    def _get_cached_chats(self) -> List[Dict]:
        """
        Return cached/mock chat data for testing when MongoDB is not connected.
        This simulates saved conversations.
        """
        return [
            {
                '_id': 'cached_001',
                'user_id': 'test_user',
                'repo_name': 'AirOxygenC/DriveCode',
                'role': 'user',
                'content': 'Create a function to validate email addresses',
                'timestamp': '2026-02-01T12:00:00',
                'metadata': {
                    'intent': 'Create email validation function',
                    'file_path': 'utils/validators.py'
                }
            },
            {
                '_id': 'cached_002',
                'user_id': 'test_user',
                'repo_name': 'AirOxygenC/DriveCode',
                'role': 'assistant',
                'content': 'I understand. Creating email validation function in utils/validators.py',
                'timestamp': '2026-02-01T12:00:05',
                'metadata': {
                    'intent': 'Create email validation function',
                    'status': 'analyzing'
                }
            },
            {
                '_id': 'cached_003',
                'user_id': 'test_user',
                'repo_name': 'AirOxygenC/DriveCode',
                'role': 'assistant',
                'content': 'Pull request created successfully! Would you like me to merge it?',
                'timestamp': '2026-02-01T12:00:30',
                'metadata': {
                    'pr_url': 'https://github.com/AirOxygenC/DriveCode/pull/42',
                    'status': 'completed'
                }
            },
            {
                '_id': 'cached_004',
                'user_id': 'test_user',
                'repo_name': 'AirOxygenC/DriveCode',
                'role': 'user',
                'content': 'Add a dark mode toggle to the settings page',
                'timestamp': '2026-02-01T12:15:00',
                'metadata': {
                    'intent': 'Add dark mode toggle',
                    'file_path': 'frontend/components/settings.tsx'
                }
            },
            {
                '_id': 'cached_005',
                'user_id': 'test_user',
                'repo_name': 'AirOxygenC/DriveCode',
                'role': 'assistant',
                'content': 'I understand. Adding dark mode toggle to settings page',
                'timestamp': '2026-02-01T12:15:05',
                'metadata': {
                    'intent': 'Add dark mode toggle',
                    'status': 'generating'
                }
            }
        ]
    
    def get_stats(self, user_id: str) -> Dict:
        """
        Get statistics about user's chat history.
        
        Args:
            user_id: GitHub user ID
        
        Returns:
            Dict with statistics
        """
        if not self.client:
            return {
                'total_messages': 5,
                'total_conversations': 2,
                'repositories': ['AirOxygenC/DriveCode'],
                'source': 'cached'
            }
        
        try:
            total_messages = self.collection.count_documents({'user_id': user_id})
            
            repos = self.collection.distinct('repo_name', {'user_id': user_id})
            
            return {
                'total_messages': total_messages,
                'repositories': repos,
                'source': 'mongodb'
            }
        except Exception as e:
            print(f"❌ Error getting stats: {e}")
            return {}
    
    def close(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            print("📪 MongoDB connection closed")
