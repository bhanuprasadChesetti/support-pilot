from app.core import workflows
import logging
import asyncio
import os
import json
from dotenv import load_dotenv
import logging
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage,ToolCall,ToolMessage


# 1. Load environment variables BEFORE importing your app modules
load_dotenv() 



from app.core.workflows.registry import WORKFLOW_BLUEPRINTS


from app.logger import setup_logging

setup_logging(log_level=logging.DEBUG)

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




import logging
from contextlib import asynccontextmanager
from app.db.checkpointer import db_checkpointer
from app.core.workflows.registry import WORKFLOW_BLUEPRINTS


logger = logging.getLogger("test_runner")

@asynccontextmanager
async def compile_workflow(workflow):
    """
    Generator/Context Manager that setups the DB pool, 
    pre-compiles all workflows, yields them for testing, 
    and handles automatic cleanup at the end.
    """
    logger.info("🔌 [SETUP] Initializing checkpointer pool...")
    saver = await db_checkpointer.initialize()
    
    try:
        logger.info("⚙️ [SETUP] Pre-compiling workflow registry...")
        workflow_builder = WORKFLOW_BLUEPRINTS.get(workflow)
        if not workflow_builder:
            logger.error(f"❌ Workflow '{workflow}' not found in registry.")
            return
        compiled_workflow = workflow_builder.compile(checkpointer=saver)
        yield compiled_workflow
        
    finally:
        logger.info("🛑 [TEARDOWN] Cleaning up checkpointer pools...")
        await db_checkpointer.close()




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


async def test_order_issue_resolutor_v2_workflow():
    from app.core.workflows.order_issue_resolutor.order_issue_resolution import order_issue_resolutor
    result = await order_issue_resolutor.ainvoke({
        "user_query": "I bought an item yesterday but my order ID is 12345. The screen is cracked, can I get a refund?"
    })

    logger.debug(result)

    print(result['final_response'])


async def test_order_issue_resolutor_v3_workflow():
    from app.core.workflows.order_issue_resolutor.order_issue_resolution import order_issue_resolutor

    q1 = "Where is ORD-8821 right now?"
    q2 = "Can I return ORD-1104?"
    
    result = await order_issue_resolutor.ainvoke({
        "user_query": q2
    })

    logger.debug(result)

    print('=========================================')
    print(result['final_response'])
    print('=========================================')


async def test_order_issue_resolutor_action_planner(order_issue_resolutor):

    q1 = "Where is ORD-8821 right now?"
    q2 = "I want to cancel my order ORD-8821 and get a full refund of ₹1499."
    q3 = "I want to cancel my order ORD-4492 and get a full refund of $79.99. Customer id is CUST-202"


    # 1. Target your active thread
    # config = {"configurable": {"thread_id": "standalone-test-approval-planner"}}


    config = {"configurable": {"thread_id": "standalone-test-approval-testing"}}

    # Initial Run with Intentional Fail
    # result = await order_issue_resolutor.ainvoke({
    #     "user_query": q3
    # }, config=config)


    # # Inspect checkpoint
    # state = await order_issue_resolutor.aget_state(config)

    # print("Current state:", state.values)
    # print("Next:", state.next)


    # Resume same thread
    # result = await order_issue_resolutor.ainvoke(
    #     None,
    #     config=config
    # )

    # ================== approval =================
    # Requested approval
    # result = await order_issue_resolutor.ainvoke({
    #     "user_query": q3
    # }, config=config)

    # Resume same thread
    # result = await order_issue_resolutor.ainvoke(
    #     None,
    #     config=config
    # )

    # Customer Giving approval
    from langgraph.types import Command

    result = await order_issue_resolutor.ainvoke(
        Command(
            resume={
                "decision": "approved",
                "approver_id": "Manager-202",
                "reason": "I approve the Refund."
            }
        ),
        config=config,
    )
    logger.debug(result)

    print('=========================================')
    is_approval_needed = result.get('__interrupt__')

    if is_approval_needed:
        print('Approval Needed')
        print(result.get('approval_request', {}))
    else:
        print('No Approval Needed')
        print(result['final_response'])
    print('=========================================')


async def main():
    # Consume the generator cleanly using an async context block
    async with compile_workflow('order_issue_resolutor') as workflow:
        await test_order_issue_resolutor_action_planner(workflow)
        

if __name__ == "__main__":

    asyncio.run(main())
    # pass

