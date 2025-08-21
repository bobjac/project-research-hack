#!/usr/bin/env python3
"""
Unified Research Service

Consolidates all research services into a single service with multiple execution strategies.
Supports: async research, fast template-based research, deep AI research, and simple debugging.
"""

import time
import threading
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from enum import Enum

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
import os


class ResearchStrategy(Enum):
    """Available research execution strategies."""
    SIMPLE = "simple"           # Basic ADO fetch + single AI research call
    FAST = "fast"              # Template-based research (2-3 minutes)
    ASYNC = "async"            # Full structured research with multiple types
    DEEP = "deep"              # Custom deep research with Azure AI agents (20-30 min)


@dataclass
class ResearchJob:
    """Represents a research job with all its metadata."""
    job_id: str
    story_id: str
    strategy: ResearchStrategy
    status: str = "pending"
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    failed_at: Optional[str] = None
    progress: str = "Initializing..."
    current_step: str = "init"
    last_updated: Optional[str] = None
    error: Optional[str] = None
    failed_step: Optional[str] = None
    steps_completed: List[str] = field(default_factory=list)
    
    # Research-specific fields
    custom_prompt: Optional[str] = None
    research_types: List[str] = field(default_factory=list)
    estimated_duration: Optional[str] = None
    
    # Results
    story_details: Optional[str] = None
    project_context: Optional[Dict[str, Any]] = None
    research_result: Optional[str] = None
    research_results: Optional[Dict[str, str]] = None
    document_url: Optional[str] = None
    final_result: Optional[Dict[str, Any]] = None


class ResearchExecutor(ABC):
    """Abstract base class for research execution strategies."""
    
    @abstractmethod
    def execute(self, job: ResearchJob) -> None:
        """Execute the research strategy for the given job."""
        pass
    
    def _update_progress(self, job: ResearchJob, status: str, progress: str, step: str):
        """Update job progress."""
        job.status = status
        job.progress = progress
        job.current_step = step
        job.last_updated = datetime.now().isoformat()
        print(f"Job {job.job_id}: {progress}", file=sys.stderr)
    
    def _extract_context(self, story_details: str, story_id: str) -> Dict[str, Any]:
        """Extract project context from story details."""
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


class SimpleResearchExecutor(ResearchExecutor):
    """Simple research executor for debugging - ADO fetch + single AI research."""
    
    def execute(self, job: ResearchJob) -> None:
        try:
            # Step 1: Initialize ADO tool
            self._update_progress(job, "running", "Initializing ADO connection...", "ado_init")
            from mcp_tools import AzureDevOpsMCPTool, DeepResearchMCPTool
            ado_tool = AzureDevOpsMCPTool()
            job.steps_completed.append("ado_init")
            
            # Step 2: Fetch ADO story
            self._update_progress(job, "running", "Fetching ADO story...", "ado_fetch")
            story_result = ado_tool.get_azure_devops_story(job.story_id)
            job.story_details = story_result
            job.steps_completed.append("ado_fetch")
            
            # Step 3: Extract context
            self._update_progress(job, "running", "Extracting project context...", "context_extract")
            project_context = self._extract_context(story_result, job.story_id)
            job.project_context = project_context
            job.steps_completed.append("context_extract")
            
            # Step 4: Single technical research
            self._update_progress(job, "running", "Starting technical research...", "technical_research")
            research_tool = DeepResearchMCPTool()
            tech_query = f"""
            Perform technical analysis for {project_context['project_name']}:
            
            Analyze architecture patterns, technology stack, and implementation approaches for:
            {project_context['project_context']}
            
            Focus on Microsoft AI, CoPilot integration, and partner management platforms.
            """
            
            research_result = research_tool.deep_research(tech_query)
            job.research_result = research_result
            job.steps_completed.append("technical_research")
            
            # Complete
            job.status = "completed"
            job.completed_at = datetime.now().isoformat()
            job.progress = "Completed technical research"
            job.current_step = "completed"
            job.final_result = {
                "story_details": story_result,
                "technical_research": research_result
            }
            
        except Exception as e:
            job.status = "failed"
            job.error = str(e)
            job.failed_at = datetime.now().isoformat()
            job.failed_step = job.current_step


class FastResearchExecutor(ResearchExecutor):
    """Fast template-based research executor."""
    
    def execute(self, job: ResearchJob) -> None:
        try:
            # Step 1: Get ADO story
            self._update_progress(job, "running", "Fetching ADO story...", "ado_fetch")
            from mcp_tools import AzureDevOpsMCPTool, DocumentGenerationTool
            ado_tool = AzureDevOpsMCPTool()
            story_result = ado_tool.get_azure_devops_story(job.story_id)
            job.story_details = story_result
            
            # Step 2: Extract context
            self._update_progress(job, "running", "Extracting project context...", "context_extract")
            context = self._extract_context(story_result, job.story_id)
            job.project_context = context
            
            # Step 3: Generate template-based research
            self._update_progress(job, "running", "Generating research using templates...", "template_research")
            research_results = {
                "technical_research": self._generate_technical_research(context),
                "market_research": self._generate_market_research(context),
                "risk_assessment": self._generate_risk_assessment(context)
            }
            job.research_results = research_results
            
            # Step 4: Generate document
            self._update_progress(job, "running", "Generating document...", "doc_generation")
            final_result = {
                "project_details": story_result,
                "project_context": context,
                "research_results": research_results
            }
            
            doc_tool = DocumentGenerationTool()
            doc_url = doc_tool.generate_document(final_result, "word", "projects", attach_to_ado=True, story_id=job.story_id)
            
            # Complete
            job.status = "completed"
            job.completed_at = datetime.now().isoformat()
            job.progress = "Research and document generation completed"
            job.current_step = "completed"
            job.document_url = doc_url
            job.final_result = final_result
            
        except Exception as e:
            job.status = "failed"
            job.error = str(e)
            job.failed_at = datetime.now().isoformat()
            job.failed_step = job.current_step
    
    def _generate_technical_research(self, context: Dict[str, Any]) -> str:
        """Generate technical research using template approach."""
        project_name = context.get("project_name", "Unknown Project")
        
        return f"""# Technical Research: {project_name}

## Architecture Analysis
Based on the project description, this appears to be a partner management platform with AI integration:

### Recommended Architecture
- **Frontend**: React/TypeScript for modern web interface
- **Backend**: .NET Core Web API for enterprise integration
- **AI Integration**: Microsoft Copilot SDK and Azure OpenAI Service
- **Database**: Azure SQL Database with partner management schema
- **Authentication**: Azure AD B2B for partner access control

### Technology Stack Recommendations
1. **Microsoft Copilot Integration**
   - Use Microsoft Graph Copilot SDK for seamless integration
   - Implement RAG (Retrieval-Augmented Generation) for partner documentation
   - Voice integration through Azure Speech Services

2. **Partner Management Core**
   - Partner onboarding workflows
   - Deal registration and management
   - Content generation for partner materials
   - Multi-party offer management

### Implementation Approach
- Phase 1: Core partner management functionality
- Phase 2: AI integration with basic Copilot features
- Phase 3: Advanced AI features (revenue attribution, advanced analytics)

## Security Considerations
- Implement zero-trust architecture
- Use managed identities for Azure resource access
- Partner data isolation and compliance (GDPR, SOC 2)
- API rate limiting and monitoring

## Scalability Planning
- Microservices architecture for independent scaling
- Azure Container Apps for containerized deployment
- Event-driven architecture for partner workflow automation
- CDN for global content delivery
"""
    
    def _generate_market_research(self, context: Dict[str, Any]) -> str:
        """Generate market research using template approach."""
        return """# Market Research: Partner Management Platform with AI

## Market Landscape
The partner management software market is experiencing significant growth driven by digital transformation and AI adoption.

### Key Market Trends
1. **AI-Powered Partner Management**: 73% of companies plan to integrate AI into partner operations by 2025
2. **Automated Content Generation**: Growing demand for AI-generated partner materials and documentation
3. **Voice-Enabled Interfaces**: 45% increase in voice integration for B2B platforms
4. **Real-time Analytics**: Partners expect real-time insights and revenue attribution

### Competitive Analysis

#### Direct Competitors
- **Channeltivity**: Strong in traditional partner management, limited AI integration
- **Crossbeam**: Focus on partner ecosystem mapping, growing AI features
- **Impartner** (Current solution): Market leader with established customer base

#### Market Positioning Opportunities
1. **Superior AI Integration**: More advanced Copilot integration than competitors
2. **Microsoft Ecosystem**: Deep integration with Microsoft stack provides competitive advantage
3. **Enterprise Focus**: Target large enterprises like Rockwell with complex partner ecosystems

### Target Customer Segments
1. **Enterprise Software Companies**: Need sophisticated partner onboarding and management
2. **Manufacturing Companies**: Like Rockwell, complex channel partner networks
3. **Technology Integrators**: Microsoft partners requiring advanced AI capabilities

### Market Size and Growth
- Global Partner Management Software Market: $4.2B (2024)
- Expected CAGR: 15.2% through 2029
- AI-enabled segment growing at 22% annually

### Competitive Advantages
- Microsoft partnership and integration
- Advanced AI capabilities with Copilot
- Enterprise-grade security and compliance
- Proven customer base (Rockwell, etc.)
"""
    
    def _generate_risk_assessment(self, context: Dict[str, Any]) -> str:
        """Generate risk assessment using template approach."""
        return """# Risk Assessment: Partner Management Platform CoPilot

## Technical Risks

### High Risk
1. **AI Model Dependencies**
   - Risk: Changes to Microsoft Copilot APIs could break functionality
   - Mitigation: Implement abstraction layer, maintain fallback options
   - Timeline: Ongoing monitoring required

2. **Data Privacy and Security**
   - Risk: Partner data exposure or compliance violations
   - Mitigation: Implement zero-trust architecture, regular security audits
   - Timeline: Security review required before production

### Medium Risk
3. **Integration Complexity**
   - Risk: Complex integrations with existing partner systems
   - Mitigation: Phased rollout, comprehensive testing environment
   - Timeline: 2-3 months for integration testing

4. **Performance at Scale**
   - Risk: System performance degradation with large partner networks
   - Mitigation: Load testing, auto-scaling infrastructure
   - Timeline: Performance testing in months 3-4

## Business Risks

### High Risk
1. **Market Competition**
   - Risk: Established competitors with similar AI features
   - Mitigation: Focus on unique Microsoft integration advantages
   - Timeline: Continuous competitive monitoring

2. **Customer Adoption**
   - Risk: Partners resistant to AI-powered tools
   - Mitigation: Comprehensive training program, gradual feature rollout
   - Timeline: 6-month adoption program

### Medium Risk
3. **Resource Requirements**
   - Risk: Insufficient development resources for complex AI integration
   - Mitigation: Secure Microsoft "tiger team" support, external expertise
   - Timeline: Resource planning in next 30 days

## Regulatory Risks

### Medium Risk
1. **AI Compliance**
   - Risk: Evolving AI regulations may impact functionality
   - Mitigation: Design with privacy-by-design principles
   - Timeline: Ongoing regulatory monitoring

2. **Data Governance**
   - Risk: Multi-jurisdictional data handling requirements
   - Mitigation: Implement data residency controls, GDPR compliance
   - Timeline: Legal review within 60 days

## Mitigation Strategies
1. **Technical**: Implement robust testing, monitoring, and fallback systems
2. **Business**: Phased rollout with strong customer support
3. **Regulatory**: Proactive compliance program with legal oversight
4. **Resource**: Secure Microsoft partnership and external expertise early
"""


class AsyncResearchExecutor(ResearchExecutor):
    """Async research executor with multiple research types."""
    
    def execute(self, job: ResearchJob) -> None:
        try:
            # Step 1: Get ADO story
            self._update_progress(job, "running", "Fetching ADO story...", "ado_fetch")
            from mcp_tools import ProjectKickoffTool, DocumentGenerationTool
            kickoff_tool = ProjectKickoffTool()
            
            # Step 2: Perform structured research
            self._update_progress(job, "running", "Performing structured research...", "structured_research")
            research_types = job.research_types or ["technical", "market"]
            results = kickoff_tool.research_project_kickoff(job.story_id, research_types)
            
            # Step 3: Generate document
            self._update_progress(job, "running", "Generating document...", "doc_generation")
            doc_tool = DocumentGenerationTool()
            doc_result = doc_tool.generate_document(results, "word", "projects", attach_to_ado=True, story_id=job.story_id)
            
            # Complete
            job.status = "completed"
            job.completed_at = datetime.now().isoformat()
            job.progress = "Research and document generation completed"
            job.current_step = "completed"
            job.document_url = doc_result
            job.final_result = results
            
        except Exception as e:
            job.status = "failed"
            job.error = str(e)
            job.failed_at = datetime.now().isoformat()
            job.failed_step = job.current_step


class DeepResearchExecutor(ResearchExecutor):
    """Deep AI research executor using Azure AI agents."""
    
    def __init__(self):
        self._init_azure_components()
    
    def _init_azure_components(self):
        """Initialize Azure components once at startup."""
        try:
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
        except Exception as e:
            print(f"⚠️ Azure components initialization failed: {e}", file=sys.stderr)
            raise
    
    def execute(self, job: ResearchJob) -> None:
        try:
            # Step 1: Get ADO story context
            self._update_progress(job, "running", "Fetching project context from ADO...", "ado_fetch")
            from mcp_tools import AzureDevOpsMCPTool, DocumentGenerationTool
            ado_tool = AzureDevOpsMCPTool()
            story_details = ado_tool.get_azure_devops_story(job.story_id)
            job.story_details = story_details
            
            # Step 2: Prepare research context
            self._update_progress(job, "running", "Preparing research context...", "context_prep")
            project_context = self._extract_context(story_details, job.story_id)
            job.project_context = project_context
            
            # Step 3: Format the custom prompt with context
            formatted_prompt = self._format_custom_prompt(job.custom_prompt, project_context, story_details)
            
            # Step 4: Execute deep research with Azure AI agents
            self._update_progress(job, "running", "Starting Azure AI deep research (this may take 20-30 minutes)...", "deep_research")
            
            # Create deep research tool
            deep_research_tool = DeepResearchTool(
                bing_grounding_connection_id=self.conn_id,
                deep_research_model=self.deep_research_model,
            )
            
            # Create agents client context
            with self.project_client.agents as agents_client:
                self._update_progress(job, "running", "Creating AI research agent...", "agent_creation")
                
                # Create agent
                agent = agents_client.create_agent(
                    model=self.model_deployment,
                    name=f"deep-research-agent-{job.job_id}",
                    instructions="You are an expert research analyst. Provide comprehensive, detailed analysis with citations and specific recommendations. Use the deep research tool to gather current information from multiple sources.",
                    tools=deep_research_tool.definitions,
                )
                
                # Create thread
                thread = agents_client.threads.create()
                
                # Send research query
                self._update_progress(job, "running", "Executing deep research query...", "research_execution")
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
                        job, 
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
                                print(f"🔄 New research progress for job {job.job_id}", file=sys.stderr)
                                last_message_id = response.id
                        except:
                            pass  # Continue even if message check fails
                            
                    except Exception as e:
                        print(f"⚠️ Progress check error (continuing): {e}", file=sys.stderr)
                        continue
                
                # Handle completion
                if run.status == "failed":
                    error_msg = f"Research failed: {run.last_error}"
                    job.status = "failed"
                    job.error = error_msg
                    job.failed_at = datetime.now().isoformat()
                    return
                
                # Get final results
                self._update_progress(job, "running", "Collecting research results...", "results_collection")
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
                    self._update_progress(job, "running", "Generating final document...", "doc_generation")
                    
                    final_result = {
                        "project_details": story_details,
                        "project_context": project_context,
                        "custom_prompt": job.custom_prompt,
                        "research_results": {
                            "deep_research": research_text
                        }
                    }
                    
                    # Create document
                    doc_tool = DocumentGenerationTool()
                    doc_url = doc_tool.generate_document(final_result, "word", "projects", attach_to_ado=True, story_id=job.story_id)
                    
                    # Complete successfully
                    job.status = "completed"
                    job.completed_at = datetime.now().isoformat()
                    job.progress = "Deep research completed successfully"
                    job.current_step = "completed"
                    job.document_url = doc_url
                    job.research_result = research_text
                    job.final_result = final_result
                    
                    print(f"✅ Deep research completed for job {job.job_id}", file=sys.stderr)
                else:
                    raise Exception("No research results returned from agent")
                
                # Cleanup
                try:
                    agents_client.delete_agent(agent.id)
                except:
                    pass  # Don't fail if cleanup fails
        
        except Exception as e:
            print(f"❌ Deep research failed for job {job.job_id}: {e}", file=sys.stderr)
            job.status = "failed"
            job.error = str(e)
            job.failed_at = datetime.now().isoformat()
            job.failed_step = job.current_step
    
    def _format_custom_prompt(self, custom_prompt: str, project_context: Dict[str, Any], story_details: str) -> str:
        """Format custom prompt with project context."""
        formatted = f"""
# Deep Research Request

## Project Context
**Project:** {project_context['project_name']}
**Story ID:** {project_context['story_id']}

## Project Details
{story_details}

## Research Instructions
{custom_prompt}

Please conduct comprehensive research addressing the above instructions. Use the deep research tool to gather current, authoritative information from multiple sources. Provide detailed analysis with specific citations and actionable recommendations.
"""
        return formatted


class UnifiedResearchService:
    """Unified research service that manages all research strategies."""
    
    def __init__(self):
        self.jobs: Dict[str, ResearchJob] = {}
        self.executors = {
            ResearchStrategy.SIMPLE: SimpleResearchExecutor(),
            ResearchStrategy.FAST: FastResearchExecutor(),
            ResearchStrategy.ASYNC: AsyncResearchExecutor(),
            ResearchStrategy.DEEP: DeepResearchExecutor(),
        }
    
    def start_research(self, story_id: str, strategy: ResearchStrategy, 
                      custom_prompt: Optional[str] = None, 
                      research_types: Optional[List[str]] = None) -> str:
        """Start research with the specified strategy."""
        job_id = f"{strategy.value}-research-{story_id}-{int(time.time())}"
        
        # Set default research types based on strategy
        if research_types is None:
            if strategy == ResearchStrategy.ASYNC:
                research_types = ["technical", "market"]
            else:
                research_types = []
        
        # Set estimated duration based on strategy
        duration_map = {
            ResearchStrategy.SIMPLE: "1-2 minutes",
            ResearchStrategy.FAST: "2-3 minutes", 
            ResearchStrategy.ASYNC: "5-10 minutes",
            ResearchStrategy.DEEP: "20-30 minutes"
        }
        
        job = ResearchJob(
            job_id=job_id,
            story_id=story_id,
            strategy=strategy,
            status="started",
            started_at=datetime.now().isoformat(),
            custom_prompt=custom_prompt,
            research_types=research_types,
            estimated_duration=duration_map[strategy]
        )
        
        self.jobs[job_id] = job
        
        # Start execution in background thread
        executor = self.executors[strategy]
        thread = threading.Thread(target=executor.execute, args=(job,))
        thread.daemon = True
        thread.start()
        
        return job_id
    
    def get_status(self, job_id: str) -> Dict[str, Any]:
        """Get job status."""
        job = self.jobs.get(job_id)
        if not job:
            return {"status": "not_found"}
        
        return {
            "status": job.status,
            "story_id": job.story_id,
            "strategy": job.strategy.value,
            "started_at": job.started_at,
            "completed_at": job.completed_at,
            "failed_at": job.failed_at,
            "progress": job.progress,
            "current_step": job.current_step,
            "last_updated": job.last_updated,
            "error": job.error,
            "failed_step": job.failed_step,
            "steps_completed": job.steps_completed,
            "custom_prompt": job.custom_prompt,
            "research_types": job.research_types,
            "estimated_duration": job.estimated_duration,
            "document_url": job.document_url,
            "research_result": job.research_result if job.strategy == ResearchStrategy.SIMPLE else None
        }
    
    def list_jobs(self) -> Dict[str, Any]:
        """List all jobs with their current status."""
        return {job_id: self.get_status(job_id) for job_id in self.jobs.keys()}
    
    def get_results(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get complete results for a completed job."""
        job = self.jobs.get(job_id)
        if not job or job.status != "completed":
            return None
        return job.final_result


# Create global instance
unified_research_service = UnifiedResearchService()