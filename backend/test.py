from PIL.Image import logger
import asyncio
import os
from dotenv import load_dotenv
import logging
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage,ToolCall,ToolMessage

# 1. Load environment variables BEFORE importing your app modules
load_dotenv() 


from app.config import settings
from app.logger import setup_logging

setup_logging()

logger = logging.getLogger(__name__)






def save_graph_image(graph):
    print(f"Inspecting workflow structure for: {graph}")
    
    try:
        # 2. Extract the graph schema and draw it as Mermaid PNG bytes
        # By default, this uses the public Mermaid.Ink API to render the chart
        print("Generating graph structural image...")
        image_bytes = graph.get_graph().draw_mermaid_png()
        
        # 3. Write the image payload out to your disk
        output_filename = "rag_workflow_graph.png"
        with open(output_filename, "wb") as f:
            f.write(image_bytes)
            
        print(f"✅ Success! Workflow state diagram saved to: {os.path.abspath(output_filename)}")
        
    except AttributeError:
        print("[ERROR]: The 'rag' object doesn't appear to be a compiled LangGraph/Runnable workflow.")
        print("Ensure it was created using `workflow.compile()` before export.")
    except Exception as e:
        print(f"[ERROR]: Failed to generate graph visual: {e}")
        print("Tip: If the default Mermaid API fails, you might need to install: pip pyppeteer")




async def rag():
    print("Initializing RAG service...")
    from app.core.workflows.rag.service import rag,query_enhancement
    from app.core.agents.react import get_react_agent
    
    try:
        # 3. Call the service with a safety timeout
        print("Sending query...")
        results = await rag.ainvoke({"query": "How does Kubernetes manage application deployment and scaling, how does it provide service discovery and load balancing between Pods, and how does it recover when Pods or containers fail?", "top_k": 2})
        # results = query_enhancement({"query": "What is a Kubernetes Deployment and how does it manage the desired number of pod replicas?", "top_k": 5})
        print("\n--- Results ---")
        # logger.info(results)
        print(results['context'])
        
    except asyncio.TimeoutError:
        print("\n[ERROR]: The request timed out.")
        print("Ensure your Vector DB (Milvus/Qdrant/Pinecone) or LLM API is accessible.")
    except Exception as e:
        print(f"\n[ERROR]: An unexpected error occurred: {e}")


def load_docs():    
    from app.core.workflows.rag.ingestion.service import load_documents
    from app.core.workflows.rag.vector_db.service import create_collection
    documents = load_documents('/Volumes/Stark/fight/Repos/AI/support-pilot/backend/app/data'
    ,chunk_size=1500
    ,chunk_overlap=200
    )
    


import json

def print_agent_trace(results: dict):
    """
    Dynamically tracks and pretty-prints the step-by-step 
    execution of the ReAct agent.
    """
    messages = results.get("messages", [])
    
    print("\n" + "="*60)
    print("🚀 AGENT EXECUTION TRACE")
    print("="*60)
    
    for idx, msg in enumerate(messages):
        # Handle the different message types or dictionary formats
        # Supports both class instances and dictionary representations
        msg_type = getattr(msg, 'type', msg.get('type', '')) if isinstance(msg, dict) else getattr(msg, 'type', '')
        if not msg_type and isinstance(msg, dict):
            # Check for alternative role/type naming conventions
            msg_type = msg.get('role', '') 
        
        content = getattr(msg, 'content', '') if not isinstance(msg, dict) else msg.get('content', '')
        tool_calls = getattr(msg, 'additional_kwargs', {}).get('tool_calls', []) if not isinstance(msg, dict) else msg.get('additional_kwargs', {}).get('tool_calls', [])
        
        # 1. User Input
        if msg_type in ('human', 'user'):
            print(f"\n👤 [User Query]: {content}")
            
        # 2. AI Model thinking / deciding to call a tool
        elif msg_type == 'ai':
            # If the AI decided to execute tools
            if tool_calls:
                for call in tool_calls:
                    func = call.get('function', {})
                    name = func.get('name')
                    args = func.get('arguments')
                    print(f"\n🤖 [Agent Decision]: Calling Tool -> '{name}'")
                    print(f"   📥 Arguments: {args}")
            # If it's the final answer from the AI
            elif content:
                print(f"\n🎯 [Final Answer]:\n{content}")
                
        # 3. Tool Execution Results
        elif msg_type == 'tool':
            tool_name = getattr(msg, 'name', 'Unknown Tool') if not isinstance(msg, dict) else msg.get('name', 'Unknown Tool')
            print(f"   📤 [Tool Output] ({tool_name}):")
            
            # Try to pretty-print JSON payload if the tool output is text JSON
            try:
                parsed_json = json.loads(content)
                formatted_json = json.dumps(parsed_json, indent=4)
                # Indent lines for clear terminal reading
                for line in formatted_json.split('\n'):
                    print(f"      {line}")
            except (json.JSONDecodeError, TypeError):
                print(f"      {content}")
                
    print("\n" + "="*60 + "\n")

async def react_agent():
    from app.core.agents.react import get_react_agent
    from app.core.tools.ecommerce import get_order_details, get_shipment_status, get_customer_profile
    from app.core.tools.rag import create_search_knowledge_tool
    from app.core.llm.factory import LLMFactory
    
    tools = [
        get_order_details,
        get_shipment_status,
        get_customer_profile,
        create_search_knowledge_tool(top_k=2)
    ]


    llm = LLMFactory.get_model()
    
    agent = get_react_agent(llm, tools)
    
    results = await agent.ainvoke({
        "messages": [
            {
                "role": "user",
                "content": "I received a damaged product. What is the reporting time limit, what evidence do I need to provide, whether I can get a replacement or refund, who pays the return shipping cost, and what happens if the same product is out of stock? Also, how does this differ from the normal return policy?"
            }
        ]
    })

    print_agent_trace(results)




if __name__ == "__main__":


    asyncio.run(react_agent())
   