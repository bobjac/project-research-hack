"""
Integration tests for Azure DevOps functionality.
"""

import pytest
import time
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.agents.models import MessageRole


@pytest.mark.integration
@pytest.mark.ado
class TestADOIntegration:
    """Test Azure DevOps integration functionality."""

    def test_ado_story_retrieval(self, azure_credentials, test_story_ids, ado_tool):
        """Test basic ADO story retrieval."""
        story_id = test_story_ids["working_story"]
        
        # Test story retrieval
        story_details = ado_tool.get_azure_devops_story(story_id)
        
        assert story_details is not None
        assert "Failed to retrieve" not in story_details
        assert len(story_details) > 100
        assert story_id in story_details

    def test_ado_story_with_complex_formatting(self, azure_credentials, test_story_ids, ado_tool):
        """Test ADO story retrieval with complex formatting (story 1198)."""
        story_id = test_story_ids["complex_story"]
        
        # Test story retrieval for complex story
        story_details = ado_tool.get_azure_devops_story(story_id)
        
        assert story_details is not None
        assert "Failed to retrieve" not in story_details
        assert "Impartner" in story_details
        assert "Planning" in story_details

    def test_ado_attachment_upload(self, azure_credentials, test_story_ids, ado_tool):
        """Test uploading attachment to ADO story."""
        story_id = test_story_ids["working_story"]
        
        # Create test content
        test_content = b"# Test Document\n\nThis is a test document for ADO attachment."
        filename = "test_attachment.md"
        
        # Test attachment upload
        result = ado_tool.upload_attachment_to_story(
            story_id, test_content, filename, "Test attachment"
        )
        
        assert "Successfully attached" in result
        assert filename in result
        assert story_id in result

    @pytest.mark.azure
    def test_ado_agent_extraction(self, azure_credentials, test_story_ids):
        """Test ADO story extraction via Azure AI agent."""
        from main import capture_ado_story_details
        from AzureDevOpsTool import AzureDevOpsTool
        
        story_id = test_story_ids["working_story"]
        
        # Create Azure AI client and ADO tool
        project_client = AIProjectClient(
            endpoint=azure_credentials["PROJECT_ENDPOINT"],
            credential=DefaultAzureCredential(),
        )
        
        ado_tool = AzureDevOpsTool(
            organization="gpsuscodewith",
            project="Code-With Engagement Portfolio"
        )

        with project_client:
            # Create agent
            agent = project_client.agents.create_agent(
                model=azure_credentials["MODEL_DEPLOYMENT_NAME"],
                name="test-ado-agent",
                instructions="You are a helpful agent.",
                tools=ado_tool.definitions,
            )
            
            try:
                # Create thread and message
                thread = project_client.agents.threads.create()
                
                message = project_client.agents.messages.create(
                    thread_id=thread.id,
                    role="user",
                    content=f"Can you fetch the details of ADO story {story_id}",
                )
                
                project_client.agents.enable_auto_function_calls([
                    ado_tool.get_azure_devops_story
                ])
                
                # Run agent
                run = project_client.agents.runs.create_and_process(
                    thread_id=thread.id, 
                    agent_id=agent.id
                )
                
                assert run.status == "completed", f"Agent run failed: {run.status}"
                
                # Test extraction
                messages = list(project_client.agents.messages.list(thread_id=thread.id))
                story_details = capture_ado_story_details(messages)
                
                assert story_details is not None
                assert len(story_details) > 100
                assert any(keyword in story_details.lower() for keyword in ["state", "title", "story"])
                
            finally:
                # Cleanup
                project_client.agents.delete_agent(agent.id)