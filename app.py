import chainlit as cl
from src.agent import EffectiveAltruismAgent
import uuid

from dotenv import load_dotenv

load_dotenv()

# Initialize the agent once for the entire application
agent = EffectiveAltruismAgent()

@cl.on_chat_start
async def start_chat():
    """Function that runs when starting the chat"""
    # Create a unique session ID for each conversation
    session_id = str(uuid.uuid4())
    cl.user_session.set("session_id", session_id)
    print(f"=== NEW SESSION STARTED: {session_id} ===")
    
    # Welcome message
    await cl.Message(
        content="""# Hello! I'm your Effective Altruism Assistant! 🌍

I'm here to help you learn about Effective Altruism and how to make the biggest positive impact possible.

## What I can help you with:

- **EA Fundamentals** - Core principles and philosophy
- **Cause Prioritization** - Which problems should we focus on?
- **Effective Giving** - How to donate for maximum impact
- **Career Advice** - High-impact career paths
- **Organizations** - EA charities, research groups, and communities
- **Research Areas** - Global health, animal welfare, longtermism, AI safety

## Quick start
Just ask me anything about Effective Altruism! For example:
- "What is Effective Altruism?"
- "How should I choose which charity to donate to?"
- "What are the most important global problems?"

Let's explore how you can do the most good! 🚀
"""
    ).send()

@cl.on_message
async def process_message(message: cl.Message):
    """Function that processes each user message"""
    # Extract the question
    question = message.content

    # Retrieve the saved session ID
    session_id = cl.user_session.get("session_id")
    if not session_id:
        print("⚠️ NO SESSION ID FOUND - CREATING NEW ONE")
        session_id = str(uuid.uuid4())
        cl.user_session.set("session_id", session_id)

    print(f"Processing message for session: {session_id}")
    print(f"Question: '{question}'")

    # Create a message to show while generating the response
    response_message = cl.Message(content="")
    await response_message.send()

    try:
        # Generate response using the session ID
        response = agent.generate_response(question, session_id=session_id)

        # Simulate streaming for better user experience
        for i in range(0, len(response), 8):
            chunk = response[i:i+8]
            response_message.content += chunk
            await response_message.update()
            await cl.sleep(0.03)  # Small pause to simulate typing

    except Exception as e:
        error_msg = f"Error generating response: {str(e)}"
        print(f"❌  {error_msg}")
        response_message.content = "Sorry, an error occurred while processing your request. Please try again."
        await response_message.update()