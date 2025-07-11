import chainlit as cl
from src.agent import EffectiveAltruismChat
from typing import cast
import uuid

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

    final_answer = cl.Message(content='')

    async for agent_msg, meta in agent.astream_response(msg, str(session_id)):
        
        if agent_msg.content and meta['langgraph_node'] == 'call_model':
            final_answer.language = None
            await final_answer.stream_token(agent_msg.content)
    
    await final_answer.send()