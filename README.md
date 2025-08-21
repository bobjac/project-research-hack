# Project Research Hack

An Azure AI Agent project that integrates with Azure DevOps to retrieve and analyze user stories. This project can be run as a standalone script or as an MCP (Model Context Protocol) server for integration with Claude Code and other MCP clients.

## Features

- **Azure AI Agent**: Creates intelligent agents using Azure AI Foundry
- **Azure DevOps Integration**: Custom tool to fetch user story details from Azure DevOps
- **Deep Research**: Comprehensive research capabilities using Azure AI agents with Bing grounding
- **MCP Server**: Can be used as an MCP server for integration with Claude Code and other MCP clients
- **Standalone Mode**: Can also be run as a standalone Python script

## Prerequisites

- Python 3.8 or higher
- Azure subscription with access to Azure AI services
- Azure DevOps organization and Personal Access Token (PAT)
- Azure CLI installed and configured

## Project Structure

```
project-research-hack/
├── src/
│   ├── main.py              # Standalone application entry point
│   ├── mcp_server.py        # MCP server entry point
│   ├── mcp_tools.py         # MCP tool implementations
│   └── AzureDevOpsTool.py   # Original Azure DevOps integration tool
├── requirements.txt         # Python dependencies
├── mcp_config.json          # MCP server configuration
├── .env                     # Environment variables (create from template)
└── README.md               # This file
```

## Setup Instructions

### 1. Clone the Repository

```bash
git clone <repository-url>
cd project-research-hack
```

### 2. Create Python Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root with the following variables:

```bash
# Azure AI Project Configuration
PROJECT_ENDPOINT=https://your-project.services.ai.azure.com/api/projects/your-project
MODEL_DEPLOYMENT_NAME=your-model-deployment-name
DEEP_RESEARCH_MODEL_DEPLOYMENT_NAME=your-deep-research-model-deployment-name
BING_RESOURCE_NAME=your-bing-resource-name

# Azure DevOps Configuration
ADO_PAT=your-azure-devops-personal-access-token
```

#### Getting the Required Values:

1. **PROJECT_ENDPOINT**: 
   - Go to Azure AI Foundry portal
   - Navigate to your project
   - Copy the project endpoint URL

2. **MODEL_DEPLOYMENT_NAME**: 
   - In Azure AI Foundry, go to your model deployments
   - Copy the deployment name (e.g., "gpt-4", "gpt-35-turbo")

3. **ADO_PAT**: 
   - Go to Azure DevOps → User Settings → Personal Access Tokens
   - Create a new token with "Work Items (Read)" permissions
   - Copy the generated token

### 5. Azure Authentication

Ensure you're logged into Azure CLI:

```bash
az login
```

## Running the Project

### As an MCP Server (Recommended)

To use with Claude Code or other MCP clients:

```bash
# Make sure virtual environment is activated
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate     # On Windows

# Run the MCP server
cd src
python mcp_server.py
```

Configure your MCP client to connect to this server using the provided `mcp_config.json`.

### As a Standalone Script

```bash
# Make sure virtual environment is activated
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate     # On Windows

# Run the main application
cd src
python main.py
```

### Available MCP Tools

When running as an MCP server, the following tools are available:

1. **get_azure_devops_story**: Fetch detailed information about Azure DevOps user stories
2. **deep_research**: Perform comprehensive research on any topic using Azure AI agents with Bing grounding

### What the Standalone Application Does

1. **Creates an Azure AI Agent** with custom Azure DevOps integration
2. **Establishes a conversation thread** for communication
3. **Sends a test query** to fetch Azure DevOps story details
4. **Processes the response** using the AI agent
5. **Displays the results** and cleans up resources
6. **Performs deep research** on quantum computing and saves results

### Customizing the Query

Edit the query in `src/main.py` at line 52:

```python
content="Can you fetch the details of ADO story 1198"  # Change the story ID
```

### Customizing Azure DevOps Configuration

Update the organization and project settings in `src/main.py` at lines 29-32:

```python
ado_tool = AzureDevOpsTool(
    organization="your-organization",  
    project="Your Project Name"  
)
```

## Troubleshooting

### Common Issues

1. **Authentication Errors**: Ensure you're logged into Azure CLI and have proper permissions
2. **Missing Environment Variables**: Double-check your `.env` file configuration
3. **Azure DevOps Access**: Verify your PAT has the correct permissions and hasn't expired
4. **Model Deployment**: Ensure your model deployment is active in Azure AI Foundry

### Error Messages

- `ADO_PAT environment variable is not set`: Create/update your `.env` file with the PAT
- `Authentication failed`: Run `az login` and ensure proper Azure permissions
- `Model not found`: Verify your MODEL_DEPLOYMENT_NAME in the `.env` file

## Development

### Project Components

- **main.py**: Entry point that orchestrates the AI agent workflow
- **AzureDevOpsTool.py**: Custom tool class that integrates with Azure DevOps REST API

### Adding New Features

1. Create new tool classes similar to `AzureDevOpsTool`
2. Register tools with the agent in `main.py`
3. Update environment variables as needed

## License

[Add your license information here]