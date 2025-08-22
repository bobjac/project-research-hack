#!/usr/bin/env python3
"""
Simplified main.py that integrates ADO story details with deep research
without the problematic agent-based ADO retrieval.
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
 
Please provide optimal solution based on the findings and provide an alternative Microsoft Azure-only solution as well.
 
## Project Details
{story_details}

"""
    return formatted

def extract_final_report_from_message(content: str) -> str:
    """Extract the final research report from the message content."""
    lines = content.split('\n')
    
    # Look for the final report marker
    final_report_start = None
    for i, line in enumerate(lines):
        if line.startswith('Final Report: #') or 'Final Report:' in line:
            final_report_start = i
            break
    
    if final_report_start is None:
        print("⚠️ Could not find 'Final Report:' marker, using full content")
        return content
    
    # Extract everything from the final report onwards
    report_lines = lines[final_report_start:]
    
    # Remove the "Final Report: " prefix from the first line
    if report_lines[0].startswith('Final Report: '):
        report_lines[0] = report_lines[0].replace('Final Report: ', '')
    
    # Join the lines back together
    final_report = '\n'.join(report_lines)
    
    return final_report

def create_research_summary(message: ThreadMessage, filepath: str = "research_summary.md") -> None:
    """Create a research summary from the message."""
    if not message:
        print("No message content provided, cannot create research summary.")
        return

    with open(filepath, "w", encoding="utf-8") as fp:
        # Write text summary with proper extraction
        text_summary = "\n\n".join([t.text.value.strip() for t in message.text_messages])
        
        # Extract just the final report section
        final_report = extract_final_report_from_message(text_summary)
        fp.write(final_report)

        # Write unique URL citations, if present
        if message.url_citation_annotations:
            fp.write("\n\n## References\n")
            seen_urls = set()
            for ann in message.url_citation_annotations:
                url = ann.url_citation.url
                title = ann.url_citation.title or url
                if url not in seen_urls:
                    fp.write(f"- [{title}]({url})\n")
                    seen_urls.add(url)

    print(f"Research summary written to '{filepath}'.")

def main():
    # Step 1: Get ADO story details directly
    print("Fetching ADO story details...")
    ado_tool = AzureDevOpsTool(
        organization="gpsuscodewith",  
        project="Code-With Engagement Portfolio"  
    )
    
    story_id = "1198"
    story_details = ado_tool.get_azure_devops_story(story_id)
    
    if "Failed to retrieve" in story_details:
        print(f"Error retrieving story: {story_details}")
        return
    
    print("✅ Successfully retrieved ADO story details")
    
    # Step 2: Extract project context
    project_context = extract_project_context(story_details, story_id)
    print(f"Project: {project_context['project_name']}")
    
    # Step 3: Format research prompt
    research_prompt = format_custom_prompt(project_context, story_details)
    print("✅ Generated custom research prompt")
    
    # Step 4: Run deep research
    print("Starting deep research (this may take 20-30 minutes)...")
    
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
            # Use regular model for agent (per Microsoft docs)
            model_to_use = os.environ["MODEL_DEPLOYMENT_NAME"]
            print(f"Using agent model: {model_to_use}")
            print(f"Using deep research model in tool: {os.environ['DEEP_RESEARCH_MODEL_DEPLOYMENT_NAME']}")
            
            dr_agent = dr_agents_client.create_agent(
                model=model_to_use,
                name="research-agent",
                instructions="You are an expert research analyst specializing in comprehensive technology and business research. Conduct thorough analysis using the deep research tool to gather current information from authoritative sources. Always provide detailed, well-structured responses with specific citations and actionable recommendations.",
                tools=deep_research_tool.definitions,
            )

            print(f"Created deep research agent, ID: {dr_agent.id}")

            thread = dr_agents_client.threads.create()
            print(f"Created thread, ID: {thread.id}")

            message = dr_agents_client.messages.create(
                thread_id=thread.id,
                role="user",
                content=research_prompt,
            )
            print(f"Created message, ID: {message.id}")

            print("Processing research request...")
            run = dr_agents_client.runs.create(thread_id=thread.id, agent_id=dr_agent.id)
            
            start_time = time.time()
            check_count = 0
            while run.status in ("queued", "in_progress"):
                time.sleep(5)  # Check every 5 seconds for more responsive feedback
                run = dr_agents_client.runs.get(thread_id=thread.id, run_id=run.id)
                check_count += 1
                elapsed = int(time.time() - start_time)
                
                if check_count % 6 == 0:  # Print update every 30 seconds
                    print(f"Status: {run.status} - Elapsed: {elapsed//60}m {elapsed%60}s")
                
                # Check for new messages every minute
                if check_count % 12 == 0:  # Every 60 seconds
                    try:
                        latest_msg = dr_agents_client.messages.get_last_message_by_role(
                            thread_id=thread.id, role=MessageRole.AGENT
                        )
                        if latest_msg and hasattr(latest_msg, 'text_messages') and latest_msg.text_messages:
                            preview = latest_msg.text_messages[0].text.value[:100]
                            print(f"Latest response preview: {preview}...")
                    except:
                        pass  # Continue if message check fails

            print(f"Research finished with status: {run.status}")

            if run.status == "failed":
                print(f"Research failed!")
                print(f"Error: {run.last_error}")
                print(f"Run object: {vars(run)}")  # Print all run object properties
                
                # Try to get more detailed error information
                if hasattr(run, 'last_error') and run.last_error:
                    error = run.last_error
                    if isinstance(error, dict):
                        print(f"Error code: {error.get('code', 'unknown')}")
                        print(f"Error message: {error.get('message', 'no message')}")
                        if 'details' in error:
                            print(f"Error details: {error['details']}")
                    else:
                        print(f"Error (raw): {error}")
            else:
                # Get final results
                final_message = dr_agents_client.messages.get_last_message_by_role(
                    thread_id=thread.id, role=MessageRole.AGENT
                )
                if final_message:
                    # Create research summary
                    filename = f"research_summary_{story_id}_{project_context['project_name'].replace(' ', '_').replace(':', '')}.md"
                    create_research_summary(final_message, filename)
                    print("✅ Research completed and saved!")
                else:
                    print("No research results returned")

            # Cleanup
            dr_agents_client.delete_agent(dr_agent.id)
            print("Deleted agent")

if __name__ == "__main__":
    main()