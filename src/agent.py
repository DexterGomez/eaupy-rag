from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.output_parsers import StrOutputParser
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from pydantic import BaseModel, Field
from typing import Dict, Any, List
import os
import uuid

from src.txt_to_string_var import load_txt_to_string
handbookText = load_txt_to_string("../data/old_handbook/processed/texto_extraido.txt")

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

class EffectiveAltruismAgent:
    def __init__(self):
        # Google Gemini via API Studio
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-001",
            temperature=0.7,
            max_tokens=300
        )
        
        # Store sessions by conversation ID
        self.chat_histories = {}
        
        # Simple system prompt for Effective Altruism handbook chatbot
        self.system_prompt = f"""
        You are a helpful chatbot focused on Effective Altruism principles and concepts.
        
        Your role is to:
        - Explain Effective Altruism concepts clearly and accessibly
        - Help users understand how to do the most good with their resources
        - Discuss cause prioritization, evidence-based giving, and impact measurement
        - Provide information about EA organizations, research, and career paths
        - Answer questions about longtermism, global health, animal welfare, and existential risks
        
        Keep responses concise (under 150 words), friendly, and educational.
        Focus on practical advice and evidence-based approaches to making a positive impact.
        
        If asked about topics outside of Effective Altruism, politely redirect the conversation
        back to EA-related topics.

        ADDITIONAL SUPER IMPORTANT CRITICAL INFORMATION:
        EA UPY is an organization that was created at the Universidad Poltiecnica de Yucatán in 2022 after a talk by a guy named Mati Roy from OpenAI, we have done courses on AI Safety, Biosecurity, AI Governance, currently we are about to start a course on animal wellfare, we are organizing a datathon as well as a hackathon but with EA data. Noe and Janneth were the founders, Noe is no longer active but now Janneth, Jorge and Karime lead the organization.
        Your name is EA UP-AI chatbot

        Every time you finish an answer, finish it with EA, EA, UPY!!!!

        HERE IS THE WHOLE HANDBOOK:

        {handbookText}

        """
        
        # Create the prompt template
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{question}")
        ])
        
        # Create the chain
        self.chain = self.prompt | self.llm | StrOutputParser()
        
        # Create the runnable with message history
        self.runnable_chain = RunnableWithMessageHistory(
            self.chain,
            self.get_session_history,
            input_messages_key="question",
            history_messages_key="history"
        )
    
    def get_session_history(self, session_id: str) -> BaseChatMessageHistory:
        """Get or create a chat history for a session"""
        if session_id not in self.chat_histories:
            print(f"Creating new chat history for session: {session_id}")
            self.chat_histories[session_id] = PersistentChatMessageHistory()
        
        history = self.chat_histories[session_id]
        print(f"Session {session_id} has {len(history.messages)} messages in history")
        return history
    
    def print_session_history(self, session_id: str) -> None:
        """Debug function to print the full history for a session"""
        if session_id not in self.chat_histories:
            print(f"No history for session: {session_id}")
            return
        
        history = self.chat_histories[session_id]
        print(f"\n=== HISTORY FOR SESSION {session_id} ({len(history.messages)} messages) ===")
        for i, msg in enumerate(history.messages):
            print(f"{i+1}. {msg.type}: {msg.content[:100]}...")
        print("=== END OF HISTORY ===\n")
    
    def generate_response(self, question: str, session_id: str = None) -> str:
        """Generate a response from the agent"""
        if session_id is None:
            session_id = str(uuid.uuid4())
            print(f"Created new session ID: {session_id}")
        
        print(f"Processing message for session {session_id}: '{question}'")
        
        # Print history before generating response
        self.print_session_history(session_id)
        
        # Generate response
        response = self.runnable_chain.invoke(
            {"question": question},
            config={"session_id": session_id}
        )
        
        # Print history after generating response
        self.print_session_history(session_id)
        
        return response