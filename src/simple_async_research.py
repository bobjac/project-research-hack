#!/usr/bin/env python3
"""
Simple Async Research Service - Isolates each step for debugging
"""

import time
import threading
import sys
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

class SimpleAsyncResearch:
    def __init__(self):
        self.jobs = {}
    
    def start_research(self, story_id: str) -> str:
        """Start background research with step-by-step progress tracking."""
        job_id = f"research-{story_id}-{int(time.time())}"
        
        self.jobs[job_id] = {
            "status": "started",
            "story_id": story_id,
            "started_at": datetime.now().isoformat(),
            "progress": "Initializing...",
            "steps_completed": [],
            "current_step": "init"
        }
        
        # Start in background thread
        thread = threading.Thread(target=self._run_step_by_step, args=(job_id, story_id))
        thread.daemon = True
        thread.start()
        
        return job_id
    
    def _run_step_by_step(self, job_id: str, story_id: str):
        """Run research step by step with detailed progress."""
        try:
            # Step 1: Test basic imports
            self._update_progress(job_id, "running", "Testing imports...", "imports")
            time.sleep(0.5)
            
            # Step 2: Initialize ADO tool only
            self._update_progress(job_id, "running", "Initializing ADO connection...", "ado_init")
            from mcp_tools import AzureDevOpsMCPTool
            ado_tool = AzureDevOpsMCPTool()
            self.jobs[job_id]["steps_completed"].append("ado_init")
            
            # Step 3: Fetch ADO story  
            self._update_progress(job_id, "running", "Fetching ADO story...", "ado_fetch")
            story_result = ado_tool.get_azure_devops_story(story_id)
            self.jobs[job_id]["steps_completed"].append("ado_fetch")
            self.jobs[job_id]["story_details"] = story_result
            
            # Step 4: Initialize research tools
            self._update_progress(job_id, "running", "Initializing research tools...", "research_init")
            from mcp_tools import DeepResearchMCPTool
            research_tool = DeepResearchMCPTool()
            self.jobs[job_id]["steps_completed"].append("research_init")
            
            # Step 5: Extract project context
            self._update_progress(job_id, "running", "Extracting project context...", "context_extract")
            project_context = self._extract_simple_context(story_result, story_id)
            self.jobs[job_id]["steps_completed"].append("context_extract")
            self.jobs[job_id]["project_context"] = project_context
            
            # Step 6: Perform ONE technical research (not multiple types)
            self._update_progress(job_id, "running", "Starting technical research...", "technical_research")
            tech_query = f"""
            Perform technical analysis for {project_context['project_name']}:
            
            Analyze architecture patterns, technology stack, and implementation approaches for:
            {project_context['project_context']}
            
            Focus on Microsoft AI, CoPilot integration, and partner management platforms.
            """
            
            research_result = research_tool.deep_research(tech_query)
            self.jobs[job_id]["steps_completed"].append("technical_research")
            
            # Complete with research results
            self.jobs[job_id].update({
                "status": "completed",
                "completed_at": datetime.now().isoformat(),
                "progress": "Completed technical research",
                "current_step": "completed",
                "research_result": research_result,
                "final_result": {
                    "story_details": story_result,
                    "technical_research": research_result
                }
            })
            
        except Exception as e:
            self.jobs[job_id].update({
                "status": "failed", 
                "error": str(e),
                "failed_at": datetime.now().isoformat(),
                "failed_step": self.jobs[job_id].get("current_step", "unknown")
            })
    
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
    
    def _extract_simple_context(self, story_details: str, story_id: str) -> dict:
        """Extract basic project context from story details."""
        lines = story_details.split('\n')
        
        # Extract title
        title = "Unknown Project"
        for line in lines:
            if line.startswith("**Story") and ":" in line:
                title = line.split(":", 1)[1].strip().rstrip("*")
                break
        
        # Extract description
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

# Create global instance
simple_research = SimpleAsyncResearch()