import chainlit as cl
from dotenv import load_dotenv
from src.agent import EffectiveAltruismChat
from typing import cast
import uuid

load_dotenv()

@cl.on_chat_start
async def start_chat():
    session_id = uuid.uuid4()
    agent = EffectiveAltruismChat()
    cl.user_session.set("session_id", session_id)
    cl.user_session.set("agent", agent)

@cl.on_message
async def process_message(message: cl.Message):
    """Function that processes each user message"""

    msg = message.content

    session_id = cast(uuid.UUID, cl.user_session.get("session_id"))
    agent = cast(EffectiveAltruismChat, cl.user_session.get("agent"))
    
    response = await agent.response(message=msg, thread_id=session_id)

    await cl.Message(
        response.get("messages")[-1].content # type: ignore
    ).send()