from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.runnables.config import RunnableConfig
import uuid

from langfuse import get_client, observe
from langfuse import Langfuse
from langfuse.langchain import CallbackHandler
from langchain_core.prompts import PromptTemplate, MessagesPlaceholder, ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage

MCP_CLIENT = {
    "EA Forum MCP": {
        "url": "http://localhost:8010/mcp/",
        "transport": "streamable_http"
    }
}

class EffectiveAltruismChat:
    def __init__(self):
        self.mcp = MultiServerMCPClient(connections=MCP_CLIENT) # type: ignore

        self.memory = InMemorySaver()

        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-001",
            temperature=0.7,
            #max_tokens=300
        )

        self.langfuse = Langfuse()
    
    @observe()
    async def response(self, message:str, thread_id:uuid.UUID):
        self.tools = await self.mcp.get_tools()

        cb = CallbackHandler()

        self.langfuse_prompt = self.langfuse.get_prompt("prod")

        self.system_prompt = ChatPromptTemplate.from_messages([
            ("system", self.langfuse_prompt.get_langchain_prompt()),
            ("placeholder", "{messages}"),
            ("placeholder", "{agent_scratchpad}")
            ]
        )

        self.system_prompt.metadata = {"langfuse_prompt":self.langfuse_prompt}

        self.agent = create_react_agent(
            self.llm,
            self.tools,
            checkpointer=self.memory,
            #prompt=self.system_prompt,
            prompt=self.langfuse_prompt.get_langchain_prompt()
        )

        self.langfuse.update_current_trace(session_id=str(thread_id))
        self.langfuse.update_current_trace(input=message)

        result = await self.agent.ainvoke(
            {"messages":message},
            config={
                "thread_id":str(thread_id),
                "callbacks":[cb]
                }  # type: ignore
            )

        self.langfuse.update_current_trace(output=result.get("messages")[-1].content) # type: ignore
        #self.langfuse.update_current_trace(output=result)
        
        return result