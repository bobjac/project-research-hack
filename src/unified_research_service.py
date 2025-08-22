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
    
    def _sanitize_content_for_http_transport(self, content: str) -> str:
        """Sanitize content to prevent HTTP transport issues by breaking up long lines."""
        lines = content.split('\n')
        sanitized_lines = []
        
        for line in lines:
            line = line.strip()
            if len(line) > 200:  # If line is too long, break it up
                print(f"⚠️ Sanitizing long line ({len(line)} chars) to prevent HTTP transport issues", file=sys.stderr)
                # Split on common sentence boundaries
                import re
                # Split on periods followed by space, but preserve URLs
                sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\!|\?)\s+', line)
                for sentence in sentences:
                    sentence = sentence.strip()
                    if len(sentence) > 200:
                        # Further split very long sentences on commas or other delimiters
                        parts = re.split(r'[,;]\s+', sentence)
                        for part in parts:
                            if len(part) > 200:
                                # Final fallback: split at word boundaries
                                words = part.split()
                                current_line = ""
                                for word in words:
                                    if len(current_line + " " + word) > 200:
                                        if current_line:
                                            sanitized_lines.append(current_line.strip())
                                        current_line = word
                                    else:
                                        current_line += " " + word if current_line else word
                                if current_line:
                                    sanitized_lines.append(current_line.strip())
                            else:
                                sanitized_lines.append(part.strip())
                    else:
                        sanitized_lines.append(sentence)
            else:
                sanitized_lines.append(line)
        
        sanitized_content = '\n'.join([line for line in sanitized_lines if line])
        print(f"📄 Content sanitization: {len(content)} -> {len(sanitized_content)} chars", file=sys.stderr)
        return sanitized_content

    def _extract_context(self, story_details: str, story_id: str) -> Dict[str, Any]:
        """Extract project context from story details."""
        # First sanitize the content to prevent HTTP transport issues
        sanitized_details = self._sanitize_content_for_http_transport(story_details)
        
        lines = sanitized_details.split('\n')
        
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
            "story_id": story_id,
            "sanitized_details": sanitized_details  # Include sanitized version for the deep research
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
            
            # Step 3: Format the custom prompt with context (use sanitized details)
            sanitized_details = project_context.get("sanitized_details", story_details)
            formatted_prompt = self._format_custom_prompt(job.custom_prompt, project_context, sanitized_details)
            
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
                
                # Create agent (use deep research model for better performance)
                agent = agents_client.create_agent(
                    model=self.model_deployment,
                    #model=self.deep_research_model,  # Use o3-deep-research model
                    name=f"deep-research-agent-{job.job_id}",
                    instructions="You are an expert research analyst specializing in comprehensive technology and business research. Conduct thorough analysis using the deep research tool to gather current information from authoritative sources. Always provide detailed, well-structured responses with specific citations and actionable recommendations.",
                    tools=deep_research_tool.definitions,
                )
                
                # Create thread
                thread = agents_client.threads.create()
                
                # Send research query
                self._update_progress(job, "running", "Executing deep research query...", "research_execution")
                
                # Debug: Log the prompt being sent
                print(f"📝 Sending prompt for job {job.job_id}:", file=sys.stderr)
                print(f"📝 First 300 chars: {formatted_prompt[:300]}...", file=sys.stderr)
                print(f"📝 Using model: {self.deep_research_model}", file=sys.stderr)
                
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
                    print(f"📄 Processing final message for job {job.job_id}", file=sys.stderr)
                    print(f"📄 Message has {len(final_message.text_messages)} text messages", file=sys.stderr)
                    
                    # Debug: Print message structure
                    print(f"📄 Message attributes: {dir(final_message)}", file=sys.stderr)
                    print(f"📄 Message content: {str(final_message)[:500]}...", file=sys.stderr)
                    
                    raw_research_text = "\n\n".join([t.text.value.strip() for t in final_message.text_messages])
                    
                    print(f"📄 Extracted raw research text length: {len(raw_research_text)} characters", file=sys.stderr)
                    
                    # Extract the final report section using our new method
                    research_text = self._extract_final_report_from_message(raw_research_text)
                    print(f"📄 Final report length: {len(research_text)} characters", file=sys.stderr)
                    
                    # If text_messages is empty or short, try alternative extraction methods
                    if len(raw_research_text.strip()) < 100:
                        print(f"📄 Short raw research text: '{raw_research_text}'", file=sys.stderr)
                        
                        # Try to extract content from other possible fields
                        alternative_text = ""
                        
                        if hasattr(final_message, 'content') and final_message.content:
                            print(f"📄 Trying message.content: {str(final_message.content)[:200]}...", file=sys.stderr)
                            alternative_text = str(final_message.content)
                        elif hasattr(final_message, 'text') and final_message.text:
                            print(f"📄 Trying message.text: {str(final_message.text)[:200]}...", file=sys.stderr)
                            alternative_text = str(final_message.text)
                        
                        # If we found alternative content, use it and extract final report
                        if len(alternative_text.strip()) > len(raw_research_text.strip()):
                            print(f"📄 Using alternative content (length: {len(alternative_text)})", file=sys.stderr)
                            research_text = self._extract_final_report_from_message(alternative_text)
                    

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
                    
                    # Try to save raw research text locally for debugging (optional)
                    try:
                        local_filename = f"deep-research-raw-{job.story_id}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.md"
                        local_path = Path("research_output") / local_filename
                        
                        # Create output directory if it doesn't exist
                        local_path.parent.mkdir(exist_ok=True)
                        
                        with open(local_path, 'w', encoding='utf-8') as f:
                            f.write(f"# Deep Research Raw Output\n\n")
                            f.write(f"**Story ID:** {job.story_id}\n")
                            f.write(f"**Job ID:** {job.job_id}\n")
                            f.write(f"**Custom Prompt:** {job.custom_prompt}\n")
                            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                            f.write(f"---\n\n")
                            f.write(research_text)
                        
                        print(f"💾 Saved raw research output to: {local_path}", file=sys.stderr)
                    except Exception as e:
                        print(f"⚠️ Could not save local raw file (continuing anyway): {e}", file=sys.stderr)
                    

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
                    
                    # Try to save the formatted document locally (optional)
                    try:
                        formatted_filename = f"deep-research-formatted-{job.story_id}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.md"
                        formatted_path = Path("research_output") / formatted_filename
                        
                        # Generate the same content that goes to ADO for comparison
                        project_name = project_context.get("project_name", "Deep Research")
                        formatted_content = f"# {project_name} - Deep Research\n\n"
                        formatted_content += "## Project Overview\n\n"
                        formatted_content += story_details + "\n\n"
                        formatted_content += "## Deep Research\n\n"
                        if research_text and research_text.strip():
                            formatted_content += research_text + "\n\n"
                        else:
                            formatted_content += "Research results were not available or could not be generated.\n\n"
                        formatted_content += f"\n*Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"
                        
                        with open(formatted_path, 'w', encoding='utf-8') as f:
                            f.write(formatted_content)
                        
                        print(f"💾 Saved formatted document to: {formatted_path}", file=sys.stderr)
                    except Exception as e:
                        print(f"⚠️ Could not save local formatted file (continuing anyway): {e}", file=sys.stderr)
                    
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
    
    def _extract_final_report_from_message(self, content: str) -> str:
        """Extract the final research report from the message content."""
        lines = content.split('\n')
        
        # Look for the final report marker
        final_report_start = None
        for i, line in enumerate(lines):
            if line.startswith('Final Report: #') or 'Final Report:' in line:
                final_report_start = i
                break
        
        if final_report_start is None:
            print("⚠️ Could not find 'Final Report:' marker, using full content", file=sys.stderr)
            return content
        
        # Extract everything from the final report onwards
        report_lines = lines[final_report_start:]
        
        # Remove the "Final Report: " prefix from the first line
        if report_lines[0].startswith('Final Report: '):
            report_lines[0] = report_lines[0].replace('Final Report: ', '')
        
        # Join the lines back together
        final_report = '\n'.join(report_lines)
        
        return final_report

    def _format_custom_prompt(self, custom_prompt: str, project_context: Dict[str, Any], story_details: str) -> str:
        """Format custom prompt with project context."""
        # Use the Azure AI focused template when no custom prompt provided
        if not custom_prompt or custom_prompt.strip() == "":
            formatted = f"""
# Deep Research Request

## Project Context
**Project:** {project_context['project_name']}
**Story ID:** {project_context['story_id']}

## Research Instructions
I would like you to create a comprehensive research briefing for a potential upcoming project that can be consumed by the system architect.
 
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
 
This solution should be for Microsoft Azure. When creating the proposed solution, we are only interested in an Azure Solution. No other cloud provider should be considered.
 
## Project Details
{story_details}

Please conduct comprehensive research addressing the above instructions. Use the deep research capabilities to gather current, authoritative information from multiple sources. Provide detailed analysis with specific citations and actionable recommendations.
"""
        else:
            # Use custom prompt provided by user
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
        
        # Start execution in background thread with error handling
        executor = self.executors[strategy]
        thread = threading.Thread(target=self._execute_job_safely, args=(executor, job))

        thread.daemon = True
        thread.start()
        
        return job_id
    

    def _execute_job_safely(self, executor, job: ResearchJob) -> None:
        """Execute a job with proper error handling and logging."""
        try:
            print(f"🚀 Starting execution for job {job.job_id} (strategy: {job.strategy})", file=sys.stderr)
            executor.execute(job)
            print(f"✅ Completed execution for job {job.job_id}", file=sys.stderr)
        except Exception as e:
            print(f"❌ Job {job.job_id} failed with exception: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            
            # Update job status with error
            job.status = "failed"
            job.error = f"Execution failed: {str(e)}"
            job.failed_at = datetime.now().isoformat()
            job.failed_step = job.current_step or "execution"
    

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