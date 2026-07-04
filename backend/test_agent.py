import asyncio
from agents.chatbot import ChatbotAgent
from memory.mongo_memory import MongoMemoryManager
from memory.token_manager import TokenManager

async def main():
    memory = MongoMemoryManager("mongodb://localhost:27017")
    token = TokenManager()
    agent = ChatbotAgent(memory, token)
    res = await agent.invoke("test", "test_user", "Hello")
    print("RESULT:", res)

asyncio.run(main())
