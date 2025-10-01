#!/usr/bin/env python3
"""
Robust Deep Research Service - Handles 30+ minute Azure AI agent operations
"""

import os
import sys
import time
import threading
from datetime import datetime
from pathlib import Path

# Load environment
sys.path.append(str(Path(__file__).parent))

try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / '.env'
    load_dotenv(dotenv_path=env_path)
except ImportError:
    pass

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.agents.models import DeepResearchTool, MessageRole

class RobustDeepResearch:
    def __init__(self):
        self.jobs = {}
        self._init_azure_components()
    
    def _init_azure_components(self):
        """Initialize Azure components once at startup."""
        print("🚀 Initializing Azure AI components...", file=sys.stderr)
        
        self.project_endpoint = os.environ["PROJECT_ENDPOINT"]
        self.model_deployment = os.environ["MODEL_DEPLOYMENT_NAME"] 
        self.deep_research_model = os.environ["DEEP_RESEARCH_MODEL_DEPLOYMENT_NAME"]
        self.bing_resource_name = os.environ["BING_RESOURCE_NAME"]
        
        # Initialize project client
        self.project_client = AIProjectClient(
            endpoint=self.project_endpoint,
            credential=DefaultAzureCredential(),
        )
        
        # Get Bing connection ID
        self.conn_id = self.project_client.connections.get(name=self.bing_resource_name).id
        print(f"✅ Azure AI components initialized", file=sys.stderr)
    
    def start_deep_research(self, story_id: str, custom_prompt: str) -> str:
        """Start long-running deep research with custom prompt."""
        job_id = f"deep-research-{story_id}-{int(time.time())}"
        
        self.jobs[job_id] = {
            "status": "started",
            "story_id": story_id,
            "custom_prompt": custom_prompt,
            "started_at": datetime.now().isoformat(),
            "progress": "Initializing deep research...",
            "current_step": "init",
            "estimated_duration": "20-30 minutes"
        }
        
        # Start in background thread
        thread = threading.Thread(target=self._run_deep_research, args=(job_id, story_id, custom_prompt))
        thread.daemon = True
        thread.start()
        
        return job_id
    
    def _run_deep_research(self, job_id: str, story_id: str, custom_prompt: str):
        """Execute the actual deep research."""
        try:
            # Step 1: Get ADO story context
            self._update_progress(job_id, "running", "Fetching project context from ADO...", "ado_fetch")
            from mcp_tools import AzureDevOpsMCPTool
            ado_tool = AzureDevOpsMCPTool()
            story_details = ado_tool.get_azure_devops_story(story_id)
            
            # Step 2: Prepare research context
            self._update_progress(job_id, "running", "Preparing research context...", "context_prep")
            project_context = self._extract_context(story_details, story_id)
            
            # Step 3: Format the custom prompt with context
            formatted_prompt = self._format_custom_prompt(custom_prompt, project_context, story_details)
            
            # Step 4: Execute deep research with Azure AI agents
            self._update_progress(job_id, "running", "Starting Azure AI deep research (this may take 20-30 minutes)...", "deep_research")
            
            # Create deep research tool
            deep_research_tool = DeepResearchTool(
                bing_grounding_connection_id=self.conn_id,
                deep_research_model=self.deep_research_model,
            )
            
            # Create agents client context
            with self.project_client.agents as agents_client:
                self._update_progress(job_id, "running", "Creating AI research agent...", "agent_creation")
                
                # Create agent
                agent = agents_client.create_agent(
                    model=self.model_deployment,
                    name=f"deep-research-agent-{job_id}",
                    instructions="You are an expert research analyst. Provide comprehensive, detailed analysis with citations and specific recommendations. Use the deep research tool to gather current information from multiple sources.",
                    tools=deep_research_tool.definitions,
                )
                
                # Create thread
                thread = agents_client.threads.create()
                
                # Send research query
                self._update_progress(job_id, "running", "Executing deep research query...", "research_execution")
                message = agents_client.messages.create(
                    thread_id=thread.id,
                    role="user", 
                    content=formatted_prompt,
                )
                
                # Start run
                run = agents_client.runs.create(thread_id=thread.id, agent_id=agent.id)
                
                # Monitor progress with detailed updates
                last_message_id = None
                iteration = 0
                
                while run.status in ("queued", "in_progress"):
                    iteration += 1
                    elapsed_minutes = iteration * 0.5  # Update every 30 seconds
                    
                    self._update_progress(
                        job_id, 
                        "running", 
                        f"Deep research in progress... ({elapsed_minutes:.1f} minutes elapsed)", 
                        "research_execution"
                    )
                    
                    time.sleep(30)  # Check every 30 seconds
                    
                    try:
                        run = agents_client.runs.get(thread_id=thread.id, run_id=run.id)
                        
                        # Check for new messages
                        try:
                            response = agents_client.messages.get_last_message_by_role(
                                thread_id=thread.id,
                                role=MessageRole.AGENT,
                            )
                            if response and response.id != last_message_id:
                                print(f"🔄 New research progress for job {job_id}", file=sys.stderr)
                                last_message_id = response.id
                        except:
                            pass  # Continue even if message check fails
                            
                    except Exception as e:
                        print(f"⚠️ Progress check error (continuing): {e}", file=sys.stderr)
                        continue
                
                # Handle completion
                if run.status == "failed":
                    error_msg = f"Research failed: {run.last_error}"
                    self.jobs[job_id].update({
                        "status": "failed",
                        "error": error_msg,
                        "failed_at": datetime.now().isoformat()
                    })
                    return
                
                # Get final results
                self._update_progress(job_id, "running", "Collecting research results...", "results_collection")
                final_message = agents_client.messages.get_last_message_by_role(
                    thread_id=thread.id, 
                    role=MessageRole.AGENT
                )
                
                if final_message:
                    # Format results
                    research_text = "\n\n".join([t.text.value.strip() for t in final_message.text_messages])
                    
                    # Add citations
                    if final_message.url_citation_annotations:
                        research_text += "\n\n## References and Citations\n"
                        seen_urls = set()
                        for ann in final_message.url_citation_annotations:
                            url = ann.url_citation.url
                            title = ann.url_citation.title or url
                            if url not in seen_urls:
                                research_text += f"- [{title}]({url})\n"
                                seen_urls.add(url)
                    
                    # Generate document
                    self._update_progress(job_id, "running", "Generating final document...", "doc_generation")
                    
                    final_result = {
                        "project_details": story_details,
                        "project_context": project_context,
                        "custom_prompt": custom_prompt,
                        "research_results": {
                            "deep_research": research_text
                        }
                    }
                    
                    # Create document
                    from mcp_tools import DocumentGenerationTool
                    doc_tool = DocumentGenerationTool()
                    doc_url = doc_tool.generate_document(final_result, "markdown", "projects", attach_to_ado=True, story_id=story_id)

                    
                    # Complete successfully
                    self.jobs[job_id].update({
                        "status": "completed",
                        "completed_at": datetime.now().isoformat(),
                        "progress": "Deep research completed successfully",
                        "current_step": "completed",
                        "document_url": doc_url,
                        "research_result": research_text,
                        "final_result": final_result
                    })
                    
                    print(f"✅ Deep research completed for job {job_id}", file=sys.stderr)
                else:
                    raise Exception("No research results returned from agent")
                
                # Cleanup
                try:
                    agents_client.delete_agent(agent.id)
                except:
                    pass  # Don't fail if cleanup fails
        
        except Exception as e:
            print(f"❌ Deep research failed for job {job_id}: {e}", file=sys.stderr)
            self.jobs[job_id].update({
                "status": "failed",
                "error": str(e),
                "failed_at": datetime.now().isoformat(),
                "failed_step": self.jobs[job_id].get("current_step", "unknown")
            })
    
    def _format_custom_prompt(self, custom_prompt: str, project_context: dict, story_details: str) -> str:
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
6.  Make a prediction of any objects the customer might have to the proposed solution and provide counter arguments to the predicted objections.
7.  Make a prediction of any questions the customer might ask about the solution and provide answers to the predicted questions.
8.  Please provide all resources that you are using for your predictions including the dates.  I want to make sure we are basing the proposed solution on the latest information.
9. Make detailed recommendations on how to secure the proposed solution.
10. Make detailed recommendations on performance and scalability of the proposed solution.

This solution should be for Microsoft Azure.  When creating the proposed solution, we are only interested in an Azure Solution.  No other cloud provider should be considered.
 
## Project Details
{story_details}

"""
        return formatted
    
    def _extract_context(self, story_details: str, story_id: str) -> dict:
        """Extract project context."""
        lines = story_details.split('\n')
        
        title = "Unknown Project"
        for line in lines:
            if line.startswith("**Story") and ":" in line:
                title = line.split(":", 1)[1].strip().rstrip("*")
                break
        
        description = ""
        in_description = False
        for line in lines:
            if "**Description:**" in line:
                in_description = True
                continue
            if in_description:
                description += line + " "
        
        return {
            "project_name": title,
            "project_context": description.strip() or f"Azure DevOps Story {story_id}",
            "story_id": story_id
        }
    
    def _update_progress(self, job_id: str, status: str, progress: str, step: str):
        """Update job progress."""
        self.jobs[job_id].update({
            "status": status,
            "progress": progress,
            "current_step": step,
            "last_updated": datetime.now().isoformat()
        })
        print(f"Job {job_id}: {progress}", file=sys.stderr)
    
    def get_status(self, job_id: str) -> dict:
        """Get job status."""
        return self.jobs.get(job_id, {"status": "not_found"})
    
    def list_jobs(self) -> dict:
        """List all jobs."""
        return self.jobs

# Create global instance
robust_deep_research = RobustDeepResearch()