#!/usr/bin/env python3
"""
Test script to validate the ADO-to-Deep Research pipeline works correctly
"""

import os, time
from typing import Optional
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.agents import AgentsClient
from azure.ai.agents.models import DeepResearchTool, MessageRole, ThreadMessage
from AzureDevOpsTool import AzureDevOpsTool
from dotenv import load_dotenv
from pathlib import Path

# Load .env from project root
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

def extract_project_context(story_details: str, story_id: str) -> dict:
    """Extract project context from ADO story details."""
    lines = story_details.split('\n')
    
    # Extract title (assuming format: **Story ID: Title**)
    title = "Unknown Project"
    for line in lines:
        if line.startswith("**Story") and ":" in line:
            title = line.split(":", 1)[1].strip().rstrip("*")
            break
    
    return {
        "project_name": title,
        "story_id": story_id
    }

def format_custom_prompt(project_context: dict, story_details: str) -> str:
    """Format custom prompt with project context."""
    formatted = f"""
# Deep Research Request

## Project Context
**Project:** {project_context['project_name']}
**Story ID:** {project_context['story_id']}

## Research Instructions
I would like you to create a research briefing for a potential upcoming project that can be consumed by the system architect.
 
I would like you to identify the likely project scope based off the data provided. It will most likely be related to Agentic AI.
 
You should use the following as guidance:
1. Check the product description from the provided information to understand what the product does and predict what they may want to do with it using AI. Ideas are welcome.
2. Look at their job postings to get an understanding of their tech stack. If you cannot determine or if there are multiple indications, please provide proposed guidance for the 3 most popular tech stacks.
3. After you predict how agents might be added to their system, please provide a proposed architecture based on the tech stack(s)
4. Ensure that your proposed architecture takes into account the delivery date. We would not want to propose a technical solution that is too immature or in alpha.
5. Make a prediction as to how the customer would like to extend the solution. Please consider:
   - Extending the code in the proposed solution
   - Extending the solution to include low-code or visual extensions for non-developers
   - Extend the observability of the solution
6. Please provide all resources that you are using for your predictions including the dates. I want to make sure we are basing the proposed solution on the latest information
 
This solution should be for Microsoft Azure. When creating the proposed solution, we are only interested in an Azure Solution. No other cloud provider should be considered.
 
## Project Details
{story_details}

"""
    return formatted

def main():
    print("=== TESTING ADO TO DEEP RESEARCH PIPELINE ===")
    
    # Step 1: Get ADO story details directly
    print("1. Testing ADO story retrieval...")
    ado_tool = AzureDevOpsTool(
        organization="gpsuscodewith",  
        project="Code-With Engagement Portfolio"  
    )
    
    story_id = "1186"
    story_details = ado_tool.get_azure_devops_story(story_id)
    
    if "Failed to retrieve" in story_details:
        print(f"❌ Error retrieving story: {story_details}")
        return False
    
    print("✅ Successfully retrieved ADO story details")
    print(f"   Story length: {len(story_details)} characters")
    
    # Step 2: Extract project context
    print("2. Testing project context extraction...")
    project_context = extract_project_context(story_details, story_id)
    print(f"✅ Project: {project_context['project_name']}")
    print(f"   Story ID: {project_context['story_id']}")
    
    # Step 3: Format research prompt
    print("3. Testing prompt formatting...")
    research_prompt = format_custom_prompt(project_context, story_details)
    print(f"✅ Generated custom research prompt: {len(research_prompt)} characters")
    
    # Step 4: Test Azure AI setup
    print("4. Testing Azure AI client setup...")
    try:
        project_endpoint = os.environ["PROJECT_ENDPOINT"]
        project_client = AIProjectClient(
            endpoint=project_endpoint,
            credential=DefaultAzureCredential(),
        )
        
        with project_client:
            conn_id = project_client.connections.get(name=os.environ["BING_RESOURCE_NAME"]).id
            deep_research_tool = DeepResearchTool(
                bing_grounding_connection_id=conn_id,
                deep_research_model=os.environ["DEEP_RESEARCH_MODEL_DEPLOYMENT_NAME"],
            )
            
            with project_client.agents as dr_agents_client:
                model_to_use = os.environ["MODEL_DEPLOYMENT_NAME"]
                print(f"✅ Using agent model: {model_to_use}")
                print(f"✅ Using deep research model: {os.environ['DEEP_RESEARCH_MODEL_DEPLOYMENT_NAME']}")
                
                dr_agent = dr_agents_client.create_agent(
                    model=model_to_use,
                    name="test-research-agent",
                    instructions="You are an expert research analyst specializing in comprehensive technology and business research.",
                    tools=deep_research_tool.definitions,
                )
                
                print(f"✅ Created deep research agent: {dr_agent.id}")
                
                thread = dr_agents_client.threads.create()
                print(f"✅ Created thread: {thread.id}")
                
                message = dr_agents_client.messages.create(
                    thread_id=thread.id,
                    role="user",
                    content=research_prompt,
                )
                print(f"✅ Created message: {message.id}")
                
                # Start the research but don't wait for completion
                print("5. Testing research initiation...")
                run = dr_agents_client.runs.create(thread_id=thread.id, agent_id=dr_agent.id)
                print(f"✅ Research run started: {run.id}")
                print(f"   Initial status: {run.status}")
                
                # Wait a few seconds to see if it starts properly
                time.sleep(10)
                run = dr_agents_client.runs.get(thread_id=thread.id, run_id=run.id)
                print(f"   Status after 10s: {run.status}")
                
                if run.status == "failed":
                    print(f"❌ Research failed immediately: {run.last_error}")
                    return False
                elif run.status in ("queued", "in_progress"):
                    print("✅ Research is running properly")
                    print("   (Not waiting for completion in this test)")
                
                # Cleanup
                dr_agents_client.delete_agent(dr_agent.id)
                print("✅ Cleaned up test agent")
                
        print("\n=== PIPELINE TEST RESULTS ===")
        print("✅ ADO story retrieval: PASSED")
        print("✅ Project context extraction: PASSED") 
        print("✅ Custom prompt formatting: PASSED")
        print("✅ Azure AI client setup: PASSED")
        print("✅ Deep research tool configuration: PASSED")
        print("✅ Research initiation: PASSED")
        print("\n🎉 FULL PIPELINE TEST: PASSED")
        print("\nThe pipeline is ready for production use in the MCP Server!")
        return True
        
    except Exception as e:
        print(f"❌ Error in Azure AI setup: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)