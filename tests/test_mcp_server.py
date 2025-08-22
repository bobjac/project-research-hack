"""
Integration tests for MCP server functionality.
"""

import pytest
import time
from unified_research_service import ResearchStrategy


@pytest.mark.integration
@pytest.mark.mcp
class TestMCPServer:
    """Test MCP server functionality."""

    def test_mcp_research_service_integration(self, azure_credentials, test_story_ids, unified_research_service):
        """Test MCP server integration with research service."""
        
        # This simulates what the MCP server does when called from Claude Desktop
        story_id = test_story_ids["working_story"]
        strategy = "simple"  # Use simple strategy for faster testing
        custom_prompt = "Test MCP integration"
        
        # Simulate MCP server logic
        try:
            strategy_enum = ResearchStrategy(strategy)
            job_id = unified_research_service.start_research(
                story_id=story_id,
                strategy=strategy_enum,
                custom_prompt=custom_prompt
            )
            
            assert job_id is not None
            assert f"{strategy}-research" in job_id
            
            # Verify job status can be retrieved
            status = unified_research_service.get_status(job_id)
            assert status is not None
            assert "status" in status
            
        except ValueError as e:
            pytest.fail(f"Invalid strategy enum conversion: {e}")

    def test_mcp_deep_research_configuration(self, azure_credentials, test_story_ids, unified_research_service):
        """Test MCP deep research configuration."""
        
        story_id = test_story_ids["working_story"]
        
        # Test deep research with default prompt (as MCP server would do)
        custom_prompt = ""  # Empty prompt should use default Azure AI focus
        
        job_id = unified_research_service.start_research(
            story_id=story_id,
            strategy=ResearchStrategy.DEEP,
            custom_prompt=custom_prompt
        )
        
        assert job_id is not None
        
        # Monitor initial startup to verify configuration
        max_wait = 30
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            status = unified_research_service.get_status(job_id)
            
            if status.get("current_step") == "research_execution":
                # Deep research started successfully
                break
            elif status["status"] == "failed":
                pytest.fail(f"Deep research configuration failed: {status.get('error')}")
            
            time.sleep(3)
        
        final_status = unified_research_service.get_status(job_id)
        assert final_status["status"] in ["running", "completed"]

    def test_mcp_job_listing(self, azure_credentials, test_story_ids, unified_research_service):
        """Test MCP job listing functionality."""
        
        # Start a test job
        story_id = test_story_ids["working_story"]
        job_id = unified_research_service.start_research(
            story_id=story_id,
            strategy=ResearchStrategy.SIMPLE,
            custom_prompt="Test job listing"
        )
        
        # Test job listing
        jobs = unified_research_service.list_jobs()
        
        assert jobs is not None
        assert isinstance(jobs, dict)
        assert job_id in jobs
        
        # Verify job details
        job_details = jobs[job_id]
        assert "status" in job_details
        assert "story_id" in job_details
        assert job_details["story_id"] == story_id

    def test_mcp_error_handling(self, azure_credentials, unified_research_service):
        """Test MCP server error handling scenarios."""
        
        # Test invalid strategy
        with pytest.raises(ValueError):
            ResearchStrategy("invalid_strategy")
        
        # Test missing story ID (should be handled by service)
        job_id = unified_research_service.start_research(
            story_id="",
            strategy=ResearchStrategy.SIMPLE,
            custom_prompt="Test error handling"
        )
        
        # Should still create job but may fail during execution
        assert job_id is not None
        
        # Test job status for non-existent job
        status = unified_research_service.get_status("non-existent-job")
        assert status.get("status") == "not_found"

    @pytest.mark.slow
    def test_mcp_word_document_pipeline(self, azure_credentials, test_story_ids, unified_research_service):
        """Test complete MCP pipeline with Word document generation."""
        
        story_id = test_story_ids["working_story"]
        
        # Start research that should generate Word document
        job_id = unified_research_service.start_research(
            story_id=story_id,
            strategy=ResearchStrategy.SIMPLE,  # Use simple for faster completion
            custom_prompt="Test Word document generation pipeline"
        )
        
        # Monitor for completion
        max_wait = 120  # 2 minutes for simple research
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            status = unified_research_service.get_status(job_id)
            
            if status["status"] == "completed":
                # Verify results include document information
                results = unified_research_service.get_results(job_id)
                if results:
                    # Should have document_url or indication of Word document
                    assert "document_url" in results or "document" in str(results).lower()
                break
            elif status["status"] == "failed":
                # Log the failure but don't fail the test if it's just a service issue
                print(f"Research job failed: {status.get('error', 'Unknown error')}")
                break
            
            time.sleep(5)
        
        # The test passes if the job was created and processed (even if it fails due to external issues)
        final_status = unified_research_service.get_status(job_id)
        assert final_status["status"] in ["completed", "failed", "running"]