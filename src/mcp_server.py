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
from unified_research_service import unified_research_service, ResearchStrategy

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
            name="start_research",
            description="Start research with specified strategy: simple (1-2 min), fast (2-3 min), async (5-10 min), or deep (20-30 min)",
            inputSchema={
                "type": "object",
                "properties": {
                    "story_id": {
                        "type": "string",
                        "description": "Azure DevOps story ID"
                    },
                    "strategy": {
                        "type": "string",
                        "enum": ["simple", "fast", "async", "deep"],
                        "description": "Research strategy: simple=debug/test, fast=templates, async=structured research, deep=AI agents"
                    },
                    "custom_prompt": {
                        "type": "string",
                        "description": "Custom research prompt (required for deep strategy)"
                    },
                    "research_types": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": ["technical", "market", "risk", "stakeholder"]
                        },
                        "description": "Research types for async strategy (default: technical, market)"
                    }
                },
                "required": ["story_id", "strategy"]
            }
        ),
        Tool(
            name="check_research_status",
            description="Check status of any research job",
            inputSchema={
                "type": "object",
                "properties": {
                    "job_id": {
                        "type": "string",
                        "description": "Research job ID"
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
            name="get_research_results",
            description="Get complete results for a completed research job",
            inputSchema={
                "type": "object",
                "properties": {
                    "job_id": {
                        "type": "string",
                        "description": "Research job ID"
                    }
                },
                "required": ["job_id"]
            }
        ),
        Tool(
            name="generate_document",
            description="Generate and store a project kickoff document in Azure Blob Storage or attach to ADO story",
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
                    },
                    "attach_to_ado": {
                        "type": "boolean",
                        "description": "If true, attach document to ADO story instead of just storing in blob"
                    },
                    "story_id": {
                        "type": "string",
                        "description": "ADO story ID (required if attach_to_ado is true)"
                    }
                },
                "required": ["content"]
            }
        ),
        Tool(
            name="attach_file_to_ado_story",
            description="Upload a file attachment directly to an Azure DevOps user story",
            inputSchema={
                "type": "object",
                "properties": {
                    "story_id": {
                        "type": "string",
                        "description": "The ID of the Azure DevOps user story"
                    },
                    "file_content": {
                        "type": "string",
                        "description": "Base64 encoded file content"
                    },
                    "filename": {
                        "type": "string",
                        "description": "Name of the file to attach"
                    },
                    "comment": {
                        "type": "string",
                        "description": "Optional comment for the attachment"
                    }
                },
                "required": ["story_id", "file_content", "filename"]
            }
        ),
        Tool(
            name="list_research_documents",
            description="List all research documents in the blob storage container",
            inputSchema={
                "type": "object",
                "properties": {
                    "storage_container": {
                        "type": "string",
                        "description": "Azure storage container name (default: projects)"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="download_research_document",
            description="Download a research document from blob storage",
            inputSchema={
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "Name of the file to download"
                    },
                    "storage_container": {
                        "type": "string",
                        "description": "Azure storage container name (default: projects)"
                    }
                },
                "required": ["filename"]
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
    
    elif name == "start_research":
        story_id = arguments.get("story_id")
        strategy = arguments.get("strategy")
        custom_prompt = arguments.get("custom_prompt")
        research_types = arguments.get("research_types")
        
        if not story_id or not strategy:
            return [TextContent(type="text", text="Error: story_id and strategy are required")]
        
        # Validate strategy-specific requirements
        if strategy == "deep" and not custom_prompt:
            return [TextContent(type="text", text="Error: custom_prompt is required for deep research strategy")]
        
        try:
            strategy_enum = ResearchStrategy(strategy)
            job_id = unified_research_service.start_research(
                story_id=story_id,
                strategy=strategy_enum,
                custom_prompt=custom_prompt,
                research_types=research_types
            )
            
            duration_msgs = {
                "simple": "1-2 minutes (debug/test mode)",
                "fast": "2-3 minutes (template-based)", 
                "async": "5-10 minutes (structured research)",
                "deep": "20-30 minutes (AI agents with Bing grounding)"
            }
            
            return [TextContent(type="text", text=f"Started {strategy} research job: {job_id}\n\nEstimated duration: {duration_msgs[strategy]}\n\nUse 'check_research_status' with this job_id to monitor progress.")]
        
        except ValueError:
            return [TextContent(type="text", text="Error: Invalid strategy. Must be one of: simple, fast, async, deep")]
        except Exception as e:
            return [TextContent(type="text", text=f"Error starting research: {str(e)}")]
    
    elif name == "check_research_status":
        job_id = arguments.get("job_id")
        if not job_id:
            return [TextContent(type="text", text="Error: job_id is required")]
        
        status = unified_research_service.get_status(job_id)
        return [TextContent(type="text", text=json.dumps(status, indent=2))]
    
    elif name == "list_research_jobs":
        jobs = unified_research_service.list_jobs()
        return [TextContent(type="text", text=json.dumps(jobs, indent=2))]
    
    elif name == "get_research_results":
        job_id = arguments.get("job_id")
        if not job_id:
            return [TextContent(type="text", text="Error: job_id is required")]
        
        results = unified_research_service.get_results(job_id)
        if results is None:
            return [TextContent(type="text", text="Error: Job not found or not completed yet")]
        
        return [TextContent(type="text", text=json.dumps(results, indent=2))]
    
    elif name == "generate_document":
        content = arguments.get("content")
        document_type = arguments.get("document_type", "word")
        storage_container = arguments.get("storage_container", "projects")
        attach_to_ado = arguments.get("attach_to_ado", False)
        story_id = arguments.get("story_id")
        if not content:
            return [TextContent(type="text", text="Error: content is required")]
        
        result = doc_tool.generate_document(content, document_type, storage_container, attach_to_ado, story_id)
        return [TextContent(type="text", text=result)]
    
    elif name == "attach_file_to_ado_story":
        story_id = arguments.get("story_id")
        file_content = arguments.get("file_content")
        filename = arguments.get("filename")
        comment = arguments.get("comment")
        
        if not all([story_id, file_content, filename]):
            return [TextContent(type="text", text="Error: story_id, file_content, and filename are required")]
        
        try:
            import base64
            file_bytes = base64.b64decode(file_content)
            result = ado_tool.upload_attachment_to_story(story_id, file_bytes, filename, comment)
            return [TextContent(type="text", text=result)]
        except Exception as e:
            return [TextContent(type="text", text=f"Error processing file attachment: {str(e)}")]
    
    elif name == "list_research_documents":
        storage_container = arguments.get("storage_container", "projects")
        result = doc_tool.list_documents(storage_container)
        return [TextContent(type="text", text=result)]
    
    elif name == "download_research_document":
        filename = arguments.get("filename")
        storage_container = arguments.get("storage_container", "projects")
        if not filename:
            return [TextContent(type="text", text="Error: filename is required")]
        
        result = doc_tool.download_document(filename, storage_container)
        return [TextContent(type="text", text=result)]
    
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