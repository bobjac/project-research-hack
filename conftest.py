"""
Pytest configuration and fixtures for the project research hack tests.
"""

import os
import sys
import pytest
from pathlib import Path
from dotenv import load_dotenv

# Add src to Python path
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

# Load environment variables
env_path = project_root / '.env'
load_dotenv(dotenv_path=env_path)

@pytest.fixture(scope="session")
def azure_credentials():
    """Fixture to verify Azure credentials are available."""
    required_env_vars = [
        "PROJECT_ENDPOINT",
        "MODEL_DEPLOYMENT_NAME", 
        "DEEP_RESEARCH_MODEL_DEPLOYMENT_NAME",
        "BING_RESOURCE_NAME",
        "ADO_PAT"
    ]
    
    missing_vars = []
    for var in required_env_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        pytest.skip(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    return {var: os.getenv(var) for var in required_env_vars}

@pytest.fixture(scope="session")
def test_story_ids():
    """Fixture providing test story IDs for ADO tests."""
    return {
        "working_story": "1186",  # Known working story
        "complex_story": "1198",  # Story with complex formatting
    }

@pytest.fixture
def unified_research_service():
    """Fixture for unified research service."""
    from unified_research_service import unified_research_service
    return unified_research_service

@pytest.fixture
def ado_tool():
    """Fixture for ADO tool."""
    from AzureDevOpsTool import AzureDevOpsTool
    return AzureDevOpsTool(
        organization="gpsuscodewith",
        project="Code-With Engagement Portfolio"
    )

@pytest.fixture
def document_generation_tool():
    """Fixture for document generation tool."""
    from mcp_tools import DocumentGenerationTool
    return DocumentGenerationTool()

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "integration: Integration tests requiring external services"
    )
    config.addinivalue_line(
        "markers", "unit: Unit tests not requiring external services"
    )
    config.addinivalue_line(
        "markers", "slow: Tests that take a long time to run"
    )
    config.addinivalue_line(
        "markers", "ado: Tests requiring ADO connection"
    )
    config.addinivalue_line(
        "markers", "azure: Tests requiring Azure AI services"
    )
    config.addinivalue_line(
        "markers", "research: Tests involving research functionality"
    )
    config.addinivalue_line(
        "markers", "mcp: Tests for MCP server functionality"
    )

def pytest_collection_modifyitems(config, items):
    """Automatically mark tests based on their names."""
    for item in items:
        # Mark integration tests
        if "integration" in item.name.lower() or "full" in item.name.lower():
            item.add_marker(pytest.mark.integration)
        
        # Mark slow tests
        if any(keyword in item.name.lower() for keyword in ["deep_research", "research", "pipeline"]):
            item.add_marker(pytest.mark.slow)
        
        # Mark ADO tests
        if "ado" in item.name.lower():
            item.add_marker(pytest.mark.ado)
        
        # Mark Azure tests
        if any(keyword in item.name.lower() for keyword in ["azure", "research", "deep"]):
            item.add_marker(pytest.mark.azure)
        
        # Mark MCP tests
        if "mcp" in item.name.lower():
            item.add_marker(pytest.mark.mcp)