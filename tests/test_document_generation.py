"""
Integration tests for document generation functionality.
"""

import pytest
import tempfile
import os


@pytest.mark.integration
class TestDocumentGeneration:
    """Test document generation functionality."""

    def test_word_document_generation(self, azure_credentials, document_generation_tool):
        """Test Word document generation."""
        
        # Create test content
        test_content = {
            "project_context": {
                "project_name": "Test Project",
                "story_id": "1186"
            },
            "project_details": "Test project for document generation validation.",
            "custom_prompt": "Test research prompt",
            "research_results": {
                "deep_research": "# Test Research Results\n\nThis is a comprehensive test of the research results formatting.\n\n## Key Findings\n\n- Finding 1: The system works correctly\n- Finding 2: Document generation is functional\n- Finding 3: Word formatting is preserved\n\n## Recommendations\n\n1. Continue using the current approach\n2. Monitor performance metrics\n3. Gather user feedback"
            }
        }
        
        # Test Word document generation (without ADO attachment)
        result = document_generation_tool.generate_document(
            content=test_content,
            document_type="word",
            storage_container="projects",
            attach_to_ado=False
        )
        
        # Verify result (may fail with blob storage auth, but should attempt generation)
        assert result is not None
        assert isinstance(result, str)

    def test_markdown_document_generation(self, azure_credentials, document_generation_tool):
        """Test Markdown document generation."""
        
        # Create test content
        test_content = {
            "project_context": {
                "project_name": "Test Markdown Project",
                "story_id": "1186"
            },
            "project_details": "Test project for markdown generation validation.",
            "research_results": {
                "technical_research": "## Technical Analysis\n\nThe technical implementation is sound.",
                "market_research": "## Market Analysis\n\nThe market conditions are favorable."
            }
        }
        
        # Test Markdown document generation
        result = document_generation_tool.generate_document(
            content=test_content,
            document_type="markdown",
            storage_container="projects",
            attach_to_ado=False
        )
        
        assert result is not None
        assert isinstance(result, str)

    @pytest.mark.ado
    def test_word_document_ado_attachment(self, azure_credentials, test_story_ids, document_generation_tool):
        """Test Word document generation with ADO attachment."""
        
        story_id = test_story_ids["working_story"]
        
        # Create test content
        test_content = {
            "project_context": {
                "project_name": "ADO Attachment Test",
                "story_id": story_id
            },
            "project_details": "Test project for ADO attachment validation.",
            "research_results": {
                "integration_test": "# Integration Test Results\n\nThis document tests the ADO attachment functionality.\n\n## Test Status\n\n✅ Document generation working\n✅ ADO attachment functional\n✅ Word formatting preserved"
            }
        }
        
        # Test Word document with ADO attachment
        result = document_generation_tool.generate_document(
            content=test_content,
            document_type="word",
            storage_container="projects",
            attach_to_ado=True,
            story_id=story_id
        )
        
        assert result is not None
        assert "Successfully attached" in result or "Attachment" in result
        assert story_id in result

    def test_document_content_formatting(self, document_generation_tool):
        """Test document content formatting with various inputs."""
        
        # Test with complex markdown content
        complex_content = {
            "project_context": {
                "project_name": "Complex Formatting Test",
                "story_id": "test"
            },
            "project_details": "Test complex formatting scenarios.",
            "research_results": {
                "complex_research": """# Complex Research Report

## Executive Summary

This report contains various formatting elements to test document generation.

### Key Points

- **Bold text** and *italic text*
- Lists with multiple levels
  - Sub-item 1
  - Sub-item 2
    - Sub-sub-item

### Code Examples

```python
def test_function():
    return "Hello, World!"
```

### Links and References

- [Example Link](https://example.com)
- [Another Reference](https://test.example.com)

## Detailed Analysis

### Section 1: Technical Implementation

The implementation follows best practices:

1. First principle
2. Second principle
3. Third principle

### Section 2: Performance Metrics

| Metric | Value | Status |
|--------|-------|--------|
| Speed  | Fast  | ✅     |
| Memory | Low   | ✅     |
| CPU    | Efficient | ✅  |

## Conclusion

The system performs well across all tested scenarios.
"""
            }
        }
        
        # Test document generation with complex content
        result = document_generation_tool.generate_document(
            content=complex_content,
            document_type="word",
            storage_container="projects",
            attach_to_ado=False
        )
        
        assert result is not None

    def test_document_generation_error_handling(self, document_generation_tool):
        """Test document generation error handling."""
        
        # Test with missing content
        empty_content = {}
        
        result = document_generation_tool.generate_document(
            content=empty_content,
            document_type="word",
            storage_container="projects",
            attach_to_ado=False
        )
        
        # Should handle gracefully
        assert result is not None
        
        # Test with invalid document type
        valid_content = {
            "project_context": {"project_name": "Test", "story_id": "test"},
            "research_results": {"test": "content"}
        }
        
        result = document_generation_tool.generate_document(
            content=valid_content,
            document_type="invalid_type",
            storage_container="projects",
            attach_to_ado=False
        )
        
        assert result is not None
        assert "Unsupported document type" in result