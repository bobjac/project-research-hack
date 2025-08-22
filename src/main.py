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


# Create an Azure AI Client from an endpoint, copied from your Azure AI Foundry project.
# You need to login to Azure subscription via Azure CLI and set the environment variables
project_endpoint = os.environ["PROJECT_ENDPOINT"]  # Ensure the PROJECT_ENDPOINT environment variable is set

# Create an AIProjectClient instance
project_client = AIProjectClient(
    endpoint=project_endpoint,
    credential=DefaultAzureCredential(),  # Use Azure Default Credential for authentication
)

code_interpreter = CodeInterpreterTool()

conn_id = "/subscriptions/31e9f9a0-9fd2-4294-a0a3-0101246d9700/resourceGroups/ResearchHack/providers/Microsoft.CognitiveServices/accounts/research-hack/projects/hackProject/connections/ProjectResearchHack"
bing = BingGroundingTool(connection_id=conn_id)

ado_tool = AzureDevOpsTool(
    organization="gpsuscodewith",  
    project="Code-With Engagement Portfolio"  
)

def fetch_and_print_new_agent_response(
    thread_id: str,
    agents_client: AgentsClient,
    last_message_id: Optional[str] = None,
) -> Optional[str]:
    response = agents_client.messages.get_last_message_by_role(
        thread_id=thread_id,
        role=MessageRole.AGENT,
    )
    if not response or response.id == last_message_id:
        return last_message_id  # No new content

    print("\nAgent response:")
    print("\n".join(t.text.value for t in response.text_messages))

    for ann in response.url_citation_annotations:
        print(f"URL Citation: [{ann.url_citation.title}]({ann.url_citation.url})")

    return response.id

def _format_custom_prompt(project_context: dict, story_details: str) -> str:
        """Format custom prompt with project context."""
        formatted = f"""
# Deep Research Request

## Project Context
**Project:** {project_context['project_name']}
**Story ID:** {project_context['story_id']}

## Research Instructions
I would like you to create a research briefing for a potential upcoming project that can be consumed by the system architect.
 
I would like you to identify the likely project scope based off the data provided.  It will most likely be related to Agentic AI.
 
You should use the following as guidance:
1.  Check the product description from the provided information to understand what the product does and predict what they may want to do with it using AI.  Ideas as welcome.
2.  Look at their job postings to get an undertsanding of their tech stack.  If you cannot determine or if there are multiple indications, please provide proposed guidance for the 3 most popular tech stacks.
3.  After you predict how agents might be added to their system, please provide a proposed architecture based on the tech stack(s)
4.  Ensure that you proposed architecure takes into account the delivery date.  We would not want to propose a technical solution that is too immature or in alpha.
5.  Make a prediction as to how the customer would like to extend the solution.  Please consider:
      - Extending the code in the proposed solution
      - Extending the solution to include low-code or visual extensions for non-developers
      - Extend the observability of the solution
6.  Please provide all resources that you are using for your predictions including the dates.  I want to make sure we are basing the proposed solution on the latest information
 
This solution should be for Microsoft Azure.  When creating the proposed solution, we are only interested in an Azure Solution.  No other cloud provider should be considered.
 
## Project Details
{story_details}

"""
        return formatted

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

def capture_ado_story_details(messages) -> str:
    """Extract ADO story details from agent messages."""
    story_details = ""
    for message in messages:
        if message.role == "agent":
            # Handle different content formats
            if hasattr(message, 'content') and message.content:
                if isinstance(message.content, str):
                    content_text = message.content
                elif isinstance(message.content, list):
                    # Handle list format where each item has 'text' property
                    content_parts = []
                    for item in message.content:
                        if isinstance(item, dict) and 'text' in item:
                            if isinstance(item['text'], dict) and 'value' in item['text']:
                                content_parts.append(item['text']['value'])
                            else:
                                content_parts.append(str(item['text']))
                        else:
                            content_parts.append(str(item))
                    content_text = "\n".join(content_parts)
                else:
                    content_text = str(message.content)
                
                if ("**Story" in content_text or "**Title:**" in content_text) and "State:" in content_text:
                    story_details = content_text
                    break
            elif hasattr(message, 'text_messages'):
                # Handle ThreadMessage format
                content_text = "\n".join([t.text.value for t in message.text_messages])
                if ("**Story" in content_text or "**Title:**" in content_text) and "State:" in content_text:
                    story_details = content_text
                    break
    return story_details

def create_research_summary(
        message : ThreadMessage,
        filepath: str = "research_summary.md"
) -> None:
    if not message:
        print("No message content provided, cannot create research summary.")
        return

    with open(filepath, "w", encoding="utf-8") as fp:
        # Write text summary
        text_summary = "\n\n".join([t.text.value.strip() for t in message.text_messages])
        fp.write(text_summary)

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

with project_client:
    # Create an agent with the Bing Grounding tool
    agent = project_client.agents.create_agent(
        model=os.environ["MODEL_DEPLOYMENT_NAME"],  # Model deployment name
        name="my-agent",  # Name of the agent
        instructions="You are a helpful agent that can answer questions and retrieve Azure DevOps stories.",  # Instructions for the agent
        tools=ado_tool.definitions,  # Attach the tools
    )
    print(f"Created agent, ID: {agent.id}")

    # Create a thread for communication
    thread = project_client.agents.threads.create()
    print(f"Created thread, ID: {thread.id}")
    
    # Add a message to the thread
    message = project_client.agents.messages.create(
        thread_id=thread.id,
        role="user",  # Role of the message sender
        content="Can you fetch the details of ADO story 1198",  # Message content
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
    
    # Fetch and capture ADO story details instead of just printing
    messages = project_client.agents.messages.list(thread_id=thread.id)
    
    # Debug: Print message structure to understand format
    messages_list = list(messages)  # Convert ItemPaged to list
    print(f"Found {len(messages_list)} messages")
    for i, msg in enumerate(messages_list):
        print(f"Message {i}: Role={msg.role}, Type={type(msg.content)}")
        if hasattr(msg, 'content') and msg.content:
            print(f"  Content preview: {str(msg.content)[:200]}...")
    
    story_details = capture_ado_story_details(messages_list)
    
    if not story_details:
        print("Could not extract story details from agent response")
        # Fallback: use any agent message content
        for msg in messages_list:
            if msg.role == "agent" and msg.content:
                story_details = str(msg.content)
                print(f"Using fallback content: {story_details[:100]}...")
                break
        if not story_details:
            story_details = "Story details could not be retrieved"
    else:
        print("Successfully captured ADO story details")
    
    # Delete the agent when done
    project_client.agents.delete_agent(agent.id)
    print("Deleted agent")

    print("Creating a Deep Research agent...")
    
    # Extract project context from the captured story details
    story_id = "1198"  # The story ID we requested
    project_context = extract_project_context(story_details, story_id)
    
    # Format the custom prompt with the captured story details
    research_prompt = _format_custom_prompt(project_context, story_details)
    print(f"Generated research prompt for: {project_context['project_name']}")

    conn_id = project_client.connections.get(name=os.environ["BING_RESOURCE_NAME"]).id
    # Initialize a Deep Research tool with Bing Connection ID and Deep Research model deployment name
    deep_research_tool = DeepResearchTool(
        bing_grounding_connection_id=conn_id,
        deep_research_model=os.environ["DEEP_RESEARCH_MODEL_DEPLOYMENT_NAME"],
    )

    with project_client.agents as dr_agents_client:
         # Create a new agent that has the Deep Research tool attached.
        # NOTE: To add Deep Research to an existing agent, fetch it with `get_agent(agent_id)` and then,
        # update the agent with the Deep Research tool.
        # Use deep research model if available, otherwise fallback to regular model
        model_to_use = os.environ.get("DEEP_RESEARCH_MODEL_DEPLOYMENT_NAME", os.environ["MODEL_DEPLOYMENT_NAME"])
        print(f"Using model: {model_to_use}")
        
        dr_agent = dr_agents_client.create_agent(
            model=model_to_use,
            name="my-dr-agent",
            instructions="You are an expert research analyst specializing in comprehensive technology and business research. Conduct thorough analysis using the deep research tool to gather current information from authoritative sources. Always provide detailed, well-structured responses with specific citations and actionable recommendations.",
            tools=deep_research_tool.definitions,
        )

        # [END create_agent_with_deep_research_tool]
        print(f"Created deep research agent, ID: {dr_agent.id}")

        # Create thread for communication
        thread = dr_agents_client.threads.create()
        print(f"Created thread, ID: {thread.id}")

        # Create message to thread using the formatted prompt
        message = dr_agents_client.messages.create(
            thread_id=thread.id,
            role="user",
            content=research_prompt,  # Use the formatted prompt instead of hardcoded content
        )
        print(f"Created message, ID: {message.id}")

        print(f"Start processing the message... this may take a few minutes to finish. Be patient!")
        # Poll the run as long as run status is queued or in progress
        run = dr_agents_client.runs.create(thread_id=thread.id, agent_id=dr_agent.id)
        last_message_id = None
        while run.status in ("queued", "in_progress"):
            time.sleep(1)
            run = dr_agents_client.runs.get(thread_id=thread.id, run_id=run.id)

            last_message_id = fetch_and_print_new_agent_response(
                thread_id=thread.id,
                agents_client=dr_agents_client,
                last_message_id=last_message_id,
            )
            print(f"Run status: {run.status}")

        print(f"Run finished with status: {run.status}, ID: {run.id}")

        if run.status == "failed":
            print(f"Run failed: {run.last_error}")

        # Fetch the final message from the agent in the thread and create a research summary
        final_message = dr_agents_client.messages.get_last_message_by_role(
            thread_id=thread.id, role=MessageRole.AGENT
        )
        if final_message:
            create_research_summary(final_message)

        # Clean-up and delete the agent once the run is finished.
        # NOTE: Comment out this line if you plan to reuse the agent later.
        dr_agents_client.delete_agent(dr_agent.id)
        print("Deleted agent")