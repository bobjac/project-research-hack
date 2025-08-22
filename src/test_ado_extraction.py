#!/usr/bin/env python3
"""
Test ADO extraction functionality from main.py
"""

import os, time
from typing import Optional
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.agents import AgentsClient
from azure.ai.agents.models import CodeInterpreterTool, BingGroundingTool, DeepResearchTool, MessageRole, ThreadMessage
from AzureDevOpsTool import AzureDevOpsTool
from dotenv import load_dotenv
from pathlib import Path

# Load .env from project root
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

def capture_ado_story_details(messages) -> str:
    """Extract ADO story details from agent messages."""
    story_details = ""
    print(f"=== CAPTURE_ADO_STORY_DETAILS DEBUG ===")
    print(f"Processing {len(messages)} messages")
    
    for i, message in enumerate(messages):
        print(f"Message {i}: Role={message.role}")
        if message.role == "agent" or message.role == MessageRole.AGENT:
            print(f"  Processing agent message {i}")
            print(f"  Has content attr: {hasattr(message, 'content')}")
            if hasattr(message, 'content'):
                print(f"  Content exists: {bool(message.content)}")
                print(f"  Content type: {type(message.content)}")
            
            # Handle different content formats
            if hasattr(message, 'content') and message.content:
                print(f"  Content processing - type: {type(message.content)}")
                if isinstance(message.content, str):
                    content_text = message.content
                    print(f"    String content: {len(content_text)} chars")
                elif isinstance(message.content, list):
                    print(f"    List content with {len(message.content)} items")
                    # Handle list format where each item has 'text' property
                    content_parts = []
                    for j, item in enumerate(message.content):
                        print(f"      Item {j}: {type(item)}")
                        if isinstance(item, dict):
                            print(f"        Keys: {list(item.keys())}")
                            if 'text' in item:
                                if isinstance(item['text'], dict) and 'value' in item['text']:
                                    content_parts.append(item['text']['value'])
                                    print(f"        Added text value: {len(item['text']['value'])} chars")
                                else:
                                    content_parts.append(str(item['text']))
                        else:
                            content_parts.append(str(item))
                    content_text = "\n".join(content_parts)
                    print(f"    Joined content: {len(content_text)} chars")
                else:
                    content_text = str(message.content)
                    print(f"    Stringified content: {len(content_text)} chars")
                
                # Debug the content we're checking  
                has_story = ("**Story" in content_text or "**Title:**" in content_text or 
                           "### **Title:**" in content_text or "Title:" in content_text)
                has_state = ("State:" in content_text or "**State:**" in content_text or 
                           "### **State:**" in content_text)
                print(f"  Checking agent message: has_story={has_story}, has_state={has_state}")
                if len(content_text) > 100:
                    print(f"  Content sample: {content_text[:200]}...")
                
                if has_story and has_state:
                    story_details = content_text
                    print(f"  ✅ Found ADO story details! Length: {len(content_text)} characters")
                    break
                else:
                    print(f"  ❌ No match - continuing to next message")
                    
            elif hasattr(message, 'text_messages'):
                # Handle ThreadMessage format
                print(f"  Trying text_messages format")
                content_text = "\n".join([t.text.value for t in message.text_messages])
                has_story = ("**Story" in content_text or "**Title:**" in content_text or 
                           "### **Title:**" in content_text or "Title:" in content_text)
                has_state = ("State:" in content_text or "**State:**" in content_text or 
                           "### **State:**" in content_text)
                print(f"  Checking ThreadMessage: has_story={has_story}, has_state={has_state}")
                if len(content_text) > 100:
                    print(f"  Content sample: {content_text[:200]}...")
                
                if has_story and has_state:
                    story_details = content_text
                    print(f"  ✅ Found ADO story details in ThreadMessage! Length: {len(content_text)} characters")
                    break
            else:
                print(f"  No content or text_messages found")
                
    print(f"=== FINAL RESULT ===")
    if story_details:
        print(f"✅ Successfully extracted story details: {len(story_details)} characters")
        print(f"First 300 chars: {story_details[:300]}...")
    else:
        print(f"❌ Failed to extract story details")
    
    return story_details

def test_ado_extraction():
    """Test just the ADO extraction part"""
    
    print("=== TESTING ADO EXTRACTION FROM MAIN.PY ===")
    
    # Create an Azure AI Client
    project_endpoint = os.environ["PROJECT_ENDPOINT"]
    project_client = AIProjectClient(
        endpoint=project_endpoint,
        credential=DefaultAzureCredential(),
    )

    ado_tool = AzureDevOpsTool(
        organization="gpsuscodewith",  
        project="Code-With Engagement Portfolio"  
    )

    with project_client:
        # Create an agent with the ADO tool
        agent = project_client.agents.create_agent(
            model=os.environ["MODEL_DEPLOYMENT_NAME"],
            name="ado-test-agent",
            instructions="You are a helpful agent that can answer questions and retrieve Azure DevOps stories.",
            tools=ado_tool.definitions,
        )
        print(f"Created agent, ID: {agent.id}")

        # Create a thread for communication
        thread = project_client.agents.threads.create()
        print(f"Created thread, ID: {thread.id}")
        
        # Add a message to the thread
        message = project_client.agents.messages.create(
            thread_id=thread.id,
            role="user",
            content="Can you fetch the details of ADO story 1198",
        )
        print(f"Created message, ID: {message['id']}")
        
        project_client.agents.enable_auto_function_calls([
            ado_tool.get_azure_devops_story
        ])

        # Create and process an agent run
        run = project_client.agents.runs.create_and_process(thread_id=thread.id, agent_id=agent.id)
        print(f"Run finished with status: {run.status}")
        
        # Check if the run failed
        if run.status == "failed":
            print(f"Run failed: {run.last_error}")
        
        # Fetch messages and test extraction
        messages = project_client.agents.messages.list(thread_id=thread.id)
        
        # Debug: Print message structure to understand format
        messages_list = list(messages)
        print(f"\nFound {len(messages_list)} messages")
        for i, msg in enumerate(messages_list):
            print(f"Message {i}: Role={msg.role}, Type={type(msg.content)}")
            if hasattr(msg, 'content') and msg.content:
                print(f"  Content preview: {str(msg.content)[:200]}...")
                
        print("\n=== TESTING STORY EXTRACTION ===")
        story_details = capture_ado_story_details(messages_list)
        
        if story_details:
            print(f"\n🎉 SUCCESS: ADO extraction working!")
            print(f"Extracted {len(story_details)} characters")
        else:
            print(f"\n❌ FAILED: ADO extraction not working")
            
        # Clean up
        project_client.agents.delete_agent(agent.id)
        print("Deleted agent")

if __name__ == "__main__":
    test_ado_extraction()