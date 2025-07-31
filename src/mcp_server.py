#!/usr/bin/env python3
"""
Azure DevOps and Deep Research MCP Server

An MCP server that provides Azure DevOps integration and deep research capabilities
using Azure AI agents.
"""

import asyncio
import json
from typing import Any, Sequence
from mcp import server
from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp_tools import AzureDevOpsMCPTool, DeepResearchMCPTool, ProjectKickoffTool, DocumentGenerationTool
from async_research_service import research_service
from simple_async_research import simple_research
from fast_research_service import fast_research
from robust_deep_research import robust_deep_research

# Initialize tools
ado_tool = AzureDevOpsMCPTool()
research_tool = DeepResearchMCPTool()
kickoff_tool = ProjectKickoffTool()
doc_tool = DocumentGenerationTool()

# Create MCP server
mcp_server = Server("azure-research-server")

@mcp_server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="get_azure_devops_story",
            description="Get a user story's title, description, state, dates, and assignee from Azure DevOps",
            inputSchema={
                "type": "object",
                "properties": {
                    "story_id": {
                        "type": "string",
                        "description": "The ID of the Azure DevOps user story to retrieve"
                    }
                },
                "required": ["story_id"]
            }
        ),
        Tool(
            name="deep_research",
            description="Perform comprehensive research on a topic using Azure AI agents with Bing grounding",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The research question or topic to investigate"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="structured_research",
            description="Perform structured research using predefined templates (technical, market, risk, stakeholder)",
            inputSchema={
                "type": "object",
                "properties": {
                    "research_type": {
                        "type": "string",
                        "description": "Type of research to perform",
                        "enum": ["technical", "market", "risk", "stakeholder"]
                    },
                    "project_context": {
                        "type": "object",
                        "description": "Project context information",
                        "properties": {
                            "project_name": {"type": "string"},
                            "project_context": {"type": "string"},
                            "technology_stack": {"type": "string"},
                            "domain": {"type": "string"},
                            "industry": {"type": "string"},
                            "timeline": {"type": "string"},
                            "organization": {"type": "string"}
                        },
                        "required": ["project_name", "project_context"]
                    }
                },
                "required": ["research_type", "project_context"]
            }
        ),
        Tool(
            name="research_project_kickoff",
            description="Perform comprehensive project kickoff research by combining ADO story details with structured research",
            inputSchema={
                "type": "object",
                "properties": {
                    "story_id": {
                        "type": "string",
                        "description": "Azure DevOps story ID"
                    },
                    "research_types": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": ["technical", "market", "risk", "stakeholder"]
                        },
                        "description": "List of research types to perform (default: all types)"
                    }
                },
                "required": ["story_id"]
            }
        ),
        Tool(
            name="start_async_research",
            description="Start long-running project kickoff research in background (returns job ID for status checking)",
            inputSchema={
                "type": "object",
                "properties": {
                    "story_id": {
                        "type": "string",
                        "description": "Azure DevOps story ID"
                    },
                    "research_types": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": ["technical", "market", "risk", "stakeholder"]
                        },
                        "description": "List of research types (default: technical, market for speed)"
                    }
                },
                "required": ["story_id"]
            }
        ),
        Tool(
            name="check_research_status",
            description="Check status of background research job",
            inputSchema={
                "type": "object",
                "properties": {
                    "job_id": {
                        "type": "string",
                        "description": "Research job ID returned from start_async_research"
                    }
                },
                "required": ["job_id"]
            }
        ),
        Tool(
            name="list_research_jobs",
            description="List all research jobs and their status",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="test_async_research",
            description="Test simple async research (ADO fetch only) to debug issues",
            inputSchema={
                "type": "object",
                "properties": {
                    "story_id": {
                        "type": "string",
                        "description": "Azure DevOps story ID"
                    }
                },
                "required": ["story_id"]
            }
        ),
        Tool(
            name="check_test_status",
            description="Check status of test async research",
            inputSchema={
                "type": "object",
                "properties": {
                    "job_id": {
                        "type": "string",
                        "description": "Test job ID"
                    }
                },
                "required": ["job_id"]
            }
        ),
        Tool(
            name="fast_project_research",
            description="Fast project kickoff research using template-based approach (completes in 2-3 minutes)",
            inputSchema={
                "type": "object",
                "properties": {
                    "story_id": {
                        "type": "string",
                        "description": "Azure DevOps story ID"
                    }
                },
                "required": ["story_id"]
            }
        ),
        Tool(
            name="check_fast_status",
            description="Check status of fast research job",
            inputSchema={
                "type": "object",
                "properties": {
                    "job_id": {
                        "type": "string",
                        "description": "Fast research job ID"
                    }
                },
                "required": ["job_id"]
            }
        ),
        Tool(
            name="start_custom_deep_research",
            description="Start custom deep research with Azure AI agents (20-30 minutes) using your own prompt template",
            inputSchema={
                "type": "object",
                "properties": {
                    "story_id": {
                        "type": "string",
                        "description": "Azure DevOps story ID for project context"
                    },
                    "custom_prompt": {
                        "type": "string",
                        "description": "Your custom research prompt template (will be combined with project context)"
                    }
                },
                "required": ["story_id", "custom_prompt"]
            }
        ),
        Tool(
            name="check_deep_research_status",
            description="Check status of custom deep research job",
            inputSchema={
                "type": "object",
                "properties": {
                    "job_id": {
                        "type": "string",
                        "description": "Deep research job ID"
                    }
                },
                "required": ["job_id"]
            }
        ),
        Tool(
            name="generate_document",
            description="Generate and store a project kickoff document in Azure Blob Storage",
            inputSchema={
                "type": "object",
                "properties": {
                    "content": {
                        "type": "object",
                        "description": "Research content and project details"
                    },
                    "document_type": {
                        "type": "string",
                        "enum": ["word", "markdown"],
                        "description": "Type of document to generate (default: word)"
                    },
                    "storage_container": {
                        "type": "string",
                        "description": "Azure storage container name (default: projects)"
                    }
                },
                "required": ["content"]
            }
        )
    ]

@mcp_server.call_tool()
async def handle_call_tool(name: str, arguments: dict[str, Any] | None) -> list[TextContent]:
    """Handle tool execution."""
    if not arguments:
        arguments = {}
    
    if name == "get_azure_devops_story":
        story_id = arguments.get("story_id")
        if not story_id:
            return [TextContent(type="text", text="Error: story_id is required")]
        
        result = ado_tool.get_azure_devops_story(story_id)
        return [TextContent(type="text", text=result)]
    
    elif name == "deep_research":
        query = arguments.get("query")
        if not query:
            return [TextContent(type="text", text="Error: query is required")]
        
        result = research_tool.deep_research(query)
        return [TextContent(type="text", text=result)]
    
    elif name == "structured_research":
        research_type = arguments.get("research_type")
        project_context = arguments.get("project_context")
        if not research_type or not project_context:
            return [TextContent(type="text", text="Error: research_type and project_context are required")]
        
        result = research_tool.structured_research(research_type, project_context)
        return [TextContent(type="text", text=result)]
    
    elif name == "research_project_kickoff":
        story_id = arguments.get("story_id")
        research_types = arguments.get("research_types")
        if not story_id:
            return [TextContent(type="text", text="Error: story_id is required")]
        
        result = kickoff_tool.research_project_kickoff(story_id, research_types)
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    elif name == "generate_document":
        content = arguments.get("content")
        document_type = arguments.get("document_type", "word")
        storage_container = arguments.get("storage_container", "projects")
        if not content:
            return [TextContent(type="text", text="Error: content is required")]
        
        result = doc_tool.generate_document(content, document_type, storage_container)
        return [TextContent(type="text", text=result)]
    
    elif name == "start_async_research":
        story_id = arguments.get("story_id")
        research_types = arguments.get("research_types", ["technical", "market"])
        if not story_id:
            return [TextContent(type="text", text="Error: story_id is required")]
        
        job_id = research_service.start_research(story_id, research_types)
        return [TextContent(type="text", text=f"Started background research job: {job_id}\nUse 'check_research_status' with this job_id to monitor progress.")]
    
    elif name == "check_research_status":
        job_id = arguments.get("job_id")
        if not job_id:
            return [TextContent(type="text", text="Error: job_id is required")]
        
        status = research_service.get_status(job_id)
        return [TextContent(type="text", text=json.dumps(status, indent=2))]
    
    elif name == "list_research_jobs":
        jobs = research_service.list_jobs()
        return [TextContent(type="text", text=json.dumps(jobs, indent=2))]
    
    elif name == "test_async_research":
        story_id = arguments.get("story_id")
        if not story_id:
            return [TextContent(type="text", text="Error: story_id is required")]
        
        job_id = simple_research.start_research(story_id)
        return [TextContent(type="text", text=f"Started test research job: {job_id}")]
    
    elif name == "check_test_status":
        job_id = arguments.get("job_id")
        if not job_id:
            return [TextContent(type="text", text="Error: job_id is required")]
        
        status = simple_research.get_status(job_id)
        return [TextContent(type="text", text=json.dumps(status, indent=2))]
    
    elif name == "fast_project_research":
        story_id = arguments.get("story_id")
        if not story_id:
            return [TextContent(type="text", text="Error: story_id is required")]
        
        job_id = fast_research.start_research(story_id)
        return [TextContent(type="text", text=f"Started fast research job: {job_id}\nThis should complete in 2-3 minutes with template-based research and document generation.")]
    
    elif name == "check_fast_status":
        job_id = arguments.get("job_id")
        if not job_id:
            return [TextContent(type="text", text="Error: job_id is required")]
        
        status = fast_research.get_status(job_id)
        return [TextContent(type="text", text=json.dumps(status, indent=2))]
    
    elif name == "start_custom_deep_research":
        story_id = arguments.get("story_id")
        custom_prompt = arguments.get("custom_prompt")
        if not story_id or not custom_prompt:
            return [TextContent(type="text", text="Error: both story_id and custom_prompt are required")]
        
        job_id = robust_deep_research.start_deep_research(story_id, custom_prompt)
        return [TextContent(type="text", text=f"Started custom deep research job: {job_id}\n\nThis will use Azure AI agents with Bing grounding and is expected to take 20-30 minutes. Use 'check_deep_research_status' to monitor progress.\n\nYour custom prompt will be combined with the project context from ADO story {story_id}.")]
    
    elif name == "check_deep_research_status":
        job_id = arguments.get("job_id")
        if not job_id:
            return [TextContent(type="text", text="Error: job_id is required")]
        
        status = robust_deep_research.get_status(job_id)
        return [TextContent(type="text", text=json.dumps(status, indent=2))]
    
    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]

async def main():
    """Run the MCP server."""
    from mcp.server.stdio import stdio_server
    
    async with stdio_server() as (read_stream, write_stream):
        await mcp_server.run(
            read_stream, 
            write_stream,
            mcp_server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())