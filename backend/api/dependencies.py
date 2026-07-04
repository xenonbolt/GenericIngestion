from memory.mongo_memory import MongoMemoryManager
from memory.token_manager import TokenManager
from agents.chatbot import ChatbotAgent

memory_manager = MongoMemoryManager()
token_manager = TokenManager()
chatbot = ChatbotAgent(memory_manager, token_manager)
