#!/usr/bin/env python3
"""
Async Research Service

Handles long-running research operations in the background,
storing results in Azure Blob Storage for later retrieval.
"""

import asyncio
import time
from datetime import datetime
from pathlib import Path

# Add the project root to the path so we can import mcp_tools
import sys
sys.path.append(str(Path(__file__).parent))

try:
    from dotenv import load_dotenv
    # Load environment
    env_path = Path(__file__).parent.parent / '.env'
    load_dotenv(dotenv_path=env_path)
except ImportError:
    print("Warning: python-dotenv not available, using system environment", file=sys.stderr)

from mcp_tools import ProjectKickoffTool, DocumentGenerationTool

class AsyncResearchService:
    def __init__(self):
        self.kickoff_tool = ProjectKickoffTool()
        self.doc_tool = DocumentGenerationTool()
        self.status_storage = {}  # In production, use Azure Table Storage or Redis
    
    def start_research(self, story_id: str, research_types: list = None) -> str:
        """Start background research and return job ID."""
        job_id = f"research-{story_id}-{int(time.time())}"
        
        # Initialize status
        self.status_storage[job_id] = {
            "status": "started",
            "story_id": story_id,
            "research_types": research_types or ["technical", "market"],
            "started_at": datetime.now().isoformat(),
            "progress": "Initializing research..."
        }
        
        # Start background task in thread immediately (don't wait for completion)
        import threading
        thread = threading.Thread(target=self._run_research_sync, args=(job_id, story_id, research_types))
        thread.daemon = True
        thread.start()
        
        return job_id
    
    def _run_research_sync(self, job_id: str, story_id: str, research_types: list):
        """Synchronous wrapper for research."""
        try:
            print(f"Background research started for job {job_id}", file=sys.stderr)
            
            # Update status
            self.status_storage[job_id]["status"] = "running"
            self.status_storage[job_id]["progress"] = "Fetching ADO story..."
            
            # Add small delay to ensure MCP call returns first
            time.sleep(0.5)
            
            # Perform research
            results = self.kickoff_tool.research_project_kickoff(story_id, research_types)
            
            self.status_storage[job_id]["progress"] = "Generating document..."
            
            # Generate document  
            doc_result = self.doc_tool.generate_document(results, "word", "projects", attach_to_ado=True, story_id=story_id)
            
            # Update final status
            self.status_storage[job_id].update({
                "status": "completed",
                "completed_at": datetime.now().isoformat(),
                "document_url": doc_result,
                "results": results
            })
            
            print(f"Background research completed for job {job_id}", file=sys.stderr)
            
        except Exception as e:
            print(f"Background research failed for job {job_id}: {e}", file=sys.stderr)
            self.status_storage[job_id].update({
                "status": "failed",
                "error": str(e),
                "failed_at": datetime.now().isoformat()
            })
    
    async def _run_research(self, job_id: str, story_id: str, research_types: list):
        """Run the actual research in background."""
        try:
            # Update status
            self.status_storage[job_id]["status"] = "running"
            self.status_storage[job_id]["progress"] = "Fetching ADO story..."
            
            # Perform research
            results = self.kickoff_tool.research_project_kickoff(story_id, research_types)
            
            self.status_storage[job_id]["progress"] = "Generating document..."
            
            # Generate document
            doc_result = self.doc_tool.generate_document(results, "word", "projects", attach_to_ado=True, story_id=story_id)
            
            # Update final status
            self.status_storage[job_id].update({
                "status": "completed",
                "completed_at": datetime.now().isoformat(),
                "document_url": doc_result,
                "results": results
            })
            
        except Exception as e:
            self.status_storage[job_id].update({
                "status": "failed",
                "error": str(e),
                "failed_at": datetime.now().isoformat()
            })
    
    def get_status(self, job_id: str) -> dict:
        """Get research job status."""
        return self.status_storage.get(job_id, {"status": "not_found"})
    
    def list_jobs(self) -> dict:
        """List all research jobs."""
        return self.status_storage

# Global service instance
research_service = AsyncResearchService()

if __name__ == "__main__":
    # Test the service
    job_id = research_service.start_research("1198", ["technical"])
    print(f"Started research job: {job_id}")
    
    # Keep checking status
    while True:
        status = research_service.get_status(job_id)
        print(f"Status: {status['status']} - {status.get('progress', '')}")
        
        if status['status'] in ['completed', 'failed']:
            if status['status'] == 'completed':
                print(f"Document URL: {status['document_url']}")
            break
        
        time.sleep(5)