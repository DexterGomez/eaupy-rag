from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.graph import StateGraph, MessagesState, START
from langgraph.prebuilt import ToolNode, tools_condition
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.memory import MemorySaver

from langfuse import Langfuse, observe
from langfuse.langchain import CallbackHandler
from typing import Any

MCP_CLIENT = {
    "EA Forum MCP": {
        "url": "http://localhost:8010/mcp/",
        "transport": "streamable_http"
    }
}

class EffectiveAltruismChat:
    def __init__(self):

        #self.model = init_chat_model("gemini-2.0-flash", model_provider="google_genai")
        #self.model = init_chat_model("gpt-4o-mini", model_provider="openai")
        self.model = init_chat_model('gpt-4.1-nano', model_provider='openai')
        #self.model = init_chat_model('gpt-4.1-mini', model_provider='openai')

        self.memory = MemorySaver()
        self.graph = None
        self.model_with_tools = None
        
        self.langfuse = Langfuse()

        self.langfuse_prompt = self.langfuse.get_prompt("base")

        self.client = MultiServerMCPClient(MCP_CLIENT)
        
    async def _initialize(self):
        if self.graph:
            return
        
        tools = await self.client.get_tools()
        self.model_with_tools = self.model.bind_tools(tools)

        workflow = StateGraph(MessagesState)
        workflow.add_node('call_model',self.call_model)
        workflow.add_node('tools',ToolNode(tools))
        workflow.add_edge(START, 'call_model')
        workflow.add_conditional_edges(
            'call_model',
            tools_condition
        )
        workflow.add_edge('tools','call_model')

        langfuse_handler = CallbackHandler()

        self.graph = workflow.compile(checkpointer=self.memory).with_config(
            {
                "callbacks": [langfuse_handler], 
                #'metadata':{'prompt_version':self.langfuse_prompt.version, 'prompt_name':self.langfuse_prompt.name}
            }
        )
    
    async def call_model(self, state: MessagesState):
        system_prompt = self.langfuse_prompt.get_langchain_prompt()

        response = await self.model_with_tools.ainvoke([system_prompt] + state['messages'])

        return {'messages':response}

    @observe()
    async def response(self, message:str, thread_id:str) -> dict[str, Any] | Any:

        self.langfuse.update_current_trace(session_id=thread_id)
        self.langfuse.update_current_trace(input=message)

        await self._initialize()

        config = {'configurable': {'thread_id': thread_id}, }


        result = await self.graph.ainvoke(
            {'messages': message}, config
        )

        self.langfuse.update_current_trace(output=result.get("messages")[-1].content)

        return result

    @observe(as_type='generation')
    async def astream_response(self, message:str, thread_id:str):

        await self._initialize()

        config = {'configurable': {'thread_id': thread_id}}

        response = ''
        
        with self.langfuse.start_as_current_span(name='EAchat') as root_span:
            
            root_span.update_trace(input=message)
            root_span.update_trace(session_id=thread_id)

            async for msg, meta in self.graph.astream({'messages':message}, config, stream_mode='messages'):
                response += msg.content
                yield msg, meta

            root_span.update_trace(output=response)