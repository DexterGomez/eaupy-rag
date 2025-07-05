from langchain_core.chat_history import BaseChatMessageHistory
from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from typing import List

class PersistentChatMessageHistory(BaseChatMessageHistory, BaseModel):
    """Chat message history that actually persists messages"""
    messages: List[BaseMessage] = Field(default_factory=list)
    
    def add_message(self, message: BaseMessage) -> None:
        """Add a message to the chat history."""
        self.messages.append(message)
        print(f"Added message: {message.type} - {message.content[:50]}...")
    
    def add_user_message(self, message: str) -> None:
        """Add a user message to the history"""
        self.add_message(HumanMessage(content=message))
    
    def add_ai_message(self, message: str) -> None:
        """Add an AI message to the history"""
        self.add_message(AIMessage(content=message))
    
    def clear(self) -> None:
        """Clear the history"""
        self.messages = []