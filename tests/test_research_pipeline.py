"""
Integration tests for the research pipeline functionality.
"""

import pytest
import time
from unified_research_service import ResearchStrategy


@pytest.mark.integration
@pytest.mark.research
@pytest.mark.slow
class TestResearchPipeline:
    """Test the complete research pipeline."""

    def test_pipeline_components(self, azure_credentials, test_story_ids, ado_tool):
        """Test individual pipeline components work correctly."""
        story_id = test_story_ids["working_story"]
        
        # Test 1: ADO story retrieval
        story_details = ado_tool.get_azure_devops_story(story_id)
        assert story_details is not None
        assert len(story_details) > 100
        
        # Test 2: Project context extraction
        from unified_research_service import ResearchExecutor
        executor = ResearchExecutor()
        project_context = executor._extract_context(story_details, story_id)
        
        assert project_context is not None
        assert "project_name" in project_context
        assert "story_id" in project_context
        assert project_context["story_id"] == story_id

    def test_content_sanitization(self, azure_credentials, test_story_ids, ado_tool):
        """Test content sanitization for HTTP transport."""
        story_id = test_story_ids["complex_story"]  # Story 1198 with long lines
        
        story_details = ado_tool.get_azure_devops_story(story_id)
        
        # Test sanitization
        from unified_research_service import ResearchExecutor
        executor = ResearchExecutor()
        
        sanitized_content = executor._sanitize_content_for_http_transport(story_details)
        
        # Verify no lines are too long
        lines = sanitized_content.split('\n')
        long_lines = [line for line in lines if len(line) > 200]
        
        assert len(long_lines) == 0, f"Found {len(long_lines)} lines longer than 200 characters"
        assert len(sanitized_content) > 100  # Content should still be substantial

    @pytest.mark.azure
    def test_simple_research_execution(self, azure_credentials, test_story_ids, unified_research_service):
        """Test simple research strategy execution."""
        story_id = test_story_ids["working_story"]
        
        # Start simple research (faster than deep research)
        job_id = unified_research_service.start_research(
            story_id=story_id,
            strategy=ResearchStrategy.SIMPLE,
            custom_prompt="Test research prompt"
        )
        
        assert job_id is not None
        assert "simple-research" in job_id
        
        # Monitor for completion (simple research should be fast)
        max_wait = 60  # 1 minute max
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            status = unified_research_service.get_status(job_id)
            
            if status["status"] == "completed":
                break
            elif status["status"] == "failed":
                pytest.fail(f"Research failed: {status.get('error', 'Unknown error')}")
            
            time.sleep(5)
        
        # Verify completion
        final_status = unified_research_service.get_status(job_id)
        assert final_status["status"] in ["completed", "running"], f"Unexpected status: {final_status['status']}"

    @pytest.mark.azure  
    @pytest.mark.slow
    def test_deep_research_initiation(self, azure_credentials, test_story_ids, unified_research_service):
        """Test deep research initiation (without waiting for completion)."""
        story_id = test_story_ids["working_story"]
        
        # Start deep research
        job_id = unified_research_service.start_research(
            story_id=story_id,
            strategy=ResearchStrategy.DEEP,
            custom_prompt=""  # Use default Azure AI focused prompt
        )
        
        assert job_id is not None
        assert "deep-research" in job_id
        
        # Monitor startup (should reach research_execution step)
        max_wait = 60  # 1 minute to start properly
        start_time = time.time()
        reached_execution = False
        
        while time.time() - start_time < max_wait:
            status = unified_research_service.get_status(job_id)
            
            if status.get("current_step") == "research_execution":
                reached_execution = True
                break
            elif status["status"] == "failed":
                pytest.fail(f"Deep research failed to start: {status.get('error', 'Unknown error')}")
            
            time.sleep(5)
        
        assert reached_execution, "Deep research did not reach execution phase within 1 minute"

    def test_pipeline_error_handling(self, azure_credentials, unified_research_service):
        """Test pipeline error handling with invalid inputs."""
        
        # Test with invalid story ID
        job_id = unified_research_service.start_research(
            story_id="99999",  # Non-existent story
            strategy=ResearchStrategy.SIMPLE,
            custom_prompt="Test prompt"
        )
        
        # Monitor for failure
        max_wait = 30
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            status = unified_research_service.get_status(job_id)
            
            if status["status"] == "failed":
                assert "error" in status
                break
            elif status["status"] == "completed":
                pytest.fail("Expected job to fail with invalid story ID")
            
            time.sleep(2)
        
        final_status = unified_research_service.get_status(job_id)
        assert final_status["status"] == "failed", "Job should have failed with invalid story ID"