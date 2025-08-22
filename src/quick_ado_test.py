#!/usr/bin/env python3
"""
Quick test of the ADO extraction fix
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

import os
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.agents.models import MessageRole
from AzureDevOpsTool import AzureDevOpsTool
from dotenv import load_dotenv

# Load environment
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Import the fixed capture function from main.py
from main import capture_ado_story_details

def quick_test():
    """Quick test of ADO extraction"""
    print("=== QUICK ADO EXTRACTION TEST ===")
    
    # Create client and tool
    project_client = AIProjectClient(
        endpoint=os.environ["PROJECT_ENDPOINT"],
        credential=DefaultAzureCredential(),
    )
    
    ado_tool = AzureDevOpsTool()

    with project_client:
        # Create agent and get story details
        agent = project_client.agents.create_agent(
            model=os.environ["MODEL_DEPLOYMENT_NAME"],
            name="quick-test-agent",
            instructions="You are a helpful agent.",
            tools=ado_tool.definitions,
        )
        
        thread = project_client.agents.threads.create()
        
        message = project_client.agents.messages.create(
            thread_id=thread.id,
            role="user",
            content="Can you fetch the details of ADO story 1198",
        )
        
        project_client.agents.enable_auto_function_calls([
            ado_tool.get_azure_devops_story
        ])
        
        run = project_client.agents.runs.create_and_process(thread_id=thread.id, agent_id=agent.id)
        print(f"Run status: {run.status}")
        
        if run.status == "completed":
            # Test the extraction
            messages = list(project_client.agents.messages.list(thread_id=thread.id))
            story_details = capture_ado_story_details(messages)
            
            if story_details and len(story_details) > 100:
                print(f"✅ SUCCESS: Extracted {len(story_details)} characters")
                print(f"Sample: {story_details[:200]}...")
                
                # Test that it contains the expected content
                if "Impartner" in story_details and "Planning" in story_details:
                    print("✅ Content verification passed")
                    return True
                else:
                    print("❌ Content verification failed")
                    return False
            else:
                print(f"❌ FAILED: No story details extracted")
                return False
        else:
            print(f"❌ Run failed: {run.status}")
            return False
        
        # Cleanup
        project_client.agents.delete_agent(agent.id)

if __name__ == "__main__":
    success = quick_test()
    print(f"\n{'SUCCESS' if success else 'FAILED'}: ADO extraction test")
    exit(0 if success else 1)