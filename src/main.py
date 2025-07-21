import os
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.agents.models import CodeInterpreterTool
from azure.ai.agents.models import BingGroundingTool
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
    
    # Fetch and log all messages
    messages = project_client.agents.messages.list(thread_id=thread.id)
    for message in messages:
        print(f"Role: {message.role}, Content: {message.content}")
    
    # Delete the agent when done
    project_client.agents.delete_agent(agent.id)
    print("Deleted agent")