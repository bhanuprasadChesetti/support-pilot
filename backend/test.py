from PIL.Image import logger
import asyncio
import os
from dotenv import load_dotenv
import logging
# 1. Load environment variables BEFORE importing your app modules
load_dotenv() 


from app.config import settings
from app.logger import setup_logging

setup_logging()

logger = logging.getLogger(__name__)



from app.core.workflows.rag.service import rag
from app.core.workflows.rag.ingestion.service import load_documents
from app.core.workflows.rag.vector_db.service import create_collection

def save_graph_image():
    print(f"Inspecting workflow structure for: {rag}")
    
    try:
        # 2. Extract the graph schema and draw it as Mermaid PNG bytes
        # By default, this uses the public Mermaid.Ink API to render the chart
        print("Generating graph structural image...")
        image_bytes = rag.get_graph().draw_mermaid_png()
        
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




async def main():
    print("Initializing RAG service...")
    
    try:
        # 3. Call the service with a safety timeout
        print("Sending query...")
        results = await asyncio.wait_for(
            rag.ainvoke({"query": "Kubernetes Job Hierarchy", "top_k": 5}), 
            timeout=15.0
        )
        print("\n--- Results ---")
        logger.info(results)
        print(results['context'])
        
    except asyncio.TimeoutError:
        print("\n[ERROR]: The request timed out.")
        print("Ensure your Vector DB (Milvus/Qdrant/Pinecone) or LLM API is accessible.")
    except Exception as e:
        print(f"\n[ERROR]: An unexpected error occurred: {e}")

if __name__ == "__main__":


    create_collection()

    load_documents(target_directory='/Volumes/Stark/fight/Repos/AI/marathon/data_cleaned/kubernetes')

    asyncio.run(main())
