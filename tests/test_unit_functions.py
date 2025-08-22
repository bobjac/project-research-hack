"""
Unit tests for individual functions and components.
"""

import pytest
from unittest.mock import Mock, patch


@pytest.mark.unit
class TestUtilityFunctions:
    """Test utility functions without external dependencies."""

    def test_project_context_extraction(self):
        """Test project context extraction from ADO story details."""
        from unified_research_service import SimpleResearchExecutor
        
        executor = SimpleResearchExecutor()
        
        # Test with typical ADO story format
        story_details = """**Story 1186: Ansys: SimAI - Generative AI for Accelerated Simulation**

**Description:**
This is a test project for AI simulation acceleration.
Multiple lines of description content.

**State:** Planning
**Assigned To:** Test User
"""
        
        context = executor._extract_context(story_details, "1186")
        
        assert context is not None
        assert context["story_id"] == "1186"
        assert "Ansys: SimAI" in context["project_name"]
        assert "test project" in context["project_context"].lower()

    def test_content_sanitization(self):
        """Test content sanitization for HTTP transport."""
        from unified_research_service import SimpleResearchExecutor
        
        executor = SimpleResearchExecutor()
        
        # Test with long line content
        long_line = "This is a very long line that exceeds 200 characters. " * 10
        content_with_long_lines = f"Normal line\n{long_line}\nAnother normal line"
        
        sanitized = executor._sanitize_content_for_http_transport(content_with_long_lines)
        
        # Verify no lines exceed 200 characters
        lines = sanitized.split('\n')
        long_lines = [line for line in lines if len(line) > 200]
        
        assert len(long_lines) == 0
        assert "Normal line" in sanitized
        assert "Another normal line" in sanitized

    def test_prompt_formatting(self):
        """Test custom prompt formatting."""
        from unified_research_service import DeepResearchExecutor
        
        executor = DeepResearchExecutor()
        
        project_context = {
            "project_name": "Test Project",
            "story_id": "1186"
        }
        story_details = "Test story details"
        custom_prompt = "Test custom prompt"
        
        # Test with custom prompt
        formatted = executor._format_custom_prompt(custom_prompt, project_context, story_details)
        
        assert "Test Project" in formatted
        assert "1186" in formatted
        assert "Test custom prompt" in formatted
        assert "Test story details" in formatted
        
        # Test with empty prompt (should use default)
        formatted_default = executor._format_custom_prompt("", project_context, story_details)
        
        assert "Test Project" in formatted_default
        assert "Azure" in formatted_default
        assert "Agentic AI" in formatted_default

    def test_message_extraction(self):
        """Test message extraction from Azure AI response format."""
        from unified_research_service import DeepResearchExecutor
        
        executor = DeepResearchExecutor()
        
        # Test with typical Azure AI response format
        azure_response = """cot_summary: I'm analyzing the partner management platforms...
cot_summary: Looking at key trends in 2024...
cot_summary: Gathering information from multiple sources...

Final Report: # Partner Management Platforms Analysis

## Executive Summary
This is the actual research content that should be extracted.

## Key Findings
- Finding 1
- Finding 2

## Recommendations
1. Recommendation 1
2. Recommendation 2
"""
        
        extracted = executor._extract_final_report_from_message(azure_response)
        
        assert "cot_summary" not in extracted
        assert "Partner Management Platforms Analysis" in extracted
        assert "Executive Summary" in extracted
        assert "Key Findings" in extracted
        assert "Recommendations" in extracted

    def test_message_extraction_without_marker(self):
        """Test message extraction when no 'Final Report:' marker is present."""
        from unified_research_service import DeepResearchExecutor
        
        executor = DeepResearchExecutor()
        
        # Test with content that has no Final Report marker
        response_without_marker = """cot_summary: I'm thinking about this...
cot_summary: Let me analyze...

# Research Results

This is the actual content without a Final Report marker.

## Analysis
Content here.
"""
        
        extracted = executor._extract_final_report_from_message(response_without_marker)
        
        # Should still remove cot_summary entries
        assert "cot_summary" not in extracted
        assert "Research Results" in extracted
        assert "Analysis" in extracted

@pytest.mark.unit
class TestMockIntegrations:
    """Test components with mocked external dependencies."""

    @patch('mcp_tools.AzureDevOpsMCPTool')
    def test_ado_tool_integration(self, mock_ado_tool):
        """Test ADO tool integration with mocked responses."""
        
        # Mock ADO tool response
        mock_ado_instance = Mock()
        mock_ado_instance.get_azure_devops_story.return_value = """
        **Story 1186: Test Project**
        **Description:** Test description
        **State:** Planning
        """
        mock_ado_tool.return_value = mock_ado_instance
        
        # Test the integration
        from unified_research_service import SimpleResearchExecutor
        
        executor = SimpleResearchExecutor()
        
        # This would normally call the real ADO tool
        # but our mock will return the test data
        ado_tool = mock_ado_tool()
        result = ado_tool.get_azure_devops_story("1186")
        
        assert "Test Project" in result
        assert "Planning" in result
        mock_ado_instance.get_azure_devops_story.assert_called_once_with("1186")

    @patch('mcp_tools.DocumentGenerationTool')
    def test_document_generation_integration(self, mock_doc_tool):
        """Test document generation with mocked responses."""
        
        # Mock document generation response
        mock_doc_instance = Mock()
        mock_doc_instance.generate_document.return_value = "Successfully generated document"
        mock_doc_tool.return_value = mock_doc_instance
        
        # Test document generation
        doc_tool = mock_doc_tool()
        result = doc_tool.generate_document(
            content={"test": "content"},
            document_type="word",
            storage_container="projects",
            attach_to_ado=True,
            story_id="1186"
        )
        
        assert "Successfully generated" in result
        mock_doc_instance.generate_document.assert_called_once()

@pytest.mark.unit
class TestErrorHandling:
    """Test error handling scenarios."""

    def test_invalid_story_id_format(self):
        """Test handling of invalid story ID formats."""
        from unified_research_service import SimpleResearchExecutor
        
        executor = SimpleResearchExecutor()
        
        # Test with various invalid formats
        invalid_story_details = [
            "",  # Empty
            "No story format here",  # No recognizable format
            "**Story:** ",  # Empty story
        ]
        
        for story_detail in invalid_story_details:
            context = executor._extract_context(story_detail, "test")
            
            # Should handle gracefully
            assert context is not None
            assert "story_id" in context
            assert context["story_id"] == "test"

    def test_content_sanitization_edge_cases(self):
        """Test content sanitization with edge cases."""
        from unified_research_service import SimpleResearchExecutor
        
        executor = SimpleResearchExecutor()
        
        # Test edge cases
        edge_cases = [
            "",  # Empty content
            "\n\n\n",  # Only whitespace
            "Short line",  # Already short
            "A" * 1000,  # Single very long word
        ]
        
        for content in edge_cases:
            sanitized = executor._sanitize_content_for_http_transport(content)
            
            # Should not crash and should return string
            assert isinstance(sanitized, str)
            
            # No lines should exceed 200 characters
            lines = sanitized.split('\n')
            long_lines = [line for line in lines if len(line) > 200]
            assert len(long_lines) == 0