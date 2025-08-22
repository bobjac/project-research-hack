# Integration Test Suite

This directory contains pytest-based integration tests for the project research hack system.

## Test Structure

### Test Files

- **`test_ado_integration.py`** - Azure DevOps integration tests
- **`test_research_pipeline.py`** - Research pipeline functionality tests  
- **`test_document_generation.py`** - Document generation and formatting tests
- **`test_mcp_server.py`** - MCP server functionality tests
- **`test_unit_functions.py`** - Unit tests for individual functions

### Test Categories (Markers)

- `@pytest.mark.unit` - Unit tests (no external dependencies)
- `@pytest.mark.integration` - Integration tests (require external services)
- `@pytest.mark.ado` - Tests requiring ADO connection
- `@pytest.mark.azure` - Tests requiring Azure AI services  
- `@pytest.mark.mcp` - Tests for MCP server functionality
- `@pytest.mark.research` - Tests involving research functionality
- `@pytest.mark.slow` - Tests that take significant time (>1 minute)

## Running Tests

### Prerequisites

1. **Install test dependencies:**
   ```bash
   pip install -r test_requirements.txt
   ```

2. **Set up environment variables:**
   Ensure your `.env` file contains:
   ```
   PROJECT_ENDPOINT=your_azure_ai_endpoint
   MODEL_DEPLOYMENT_NAME=your_model_name
   DEEP_RESEARCH_MODEL_DEPLOYMENT_NAME=your_deep_research_model
   BING_RESOURCE_NAME=your_bing_resource
   ADO_PAT=your_ado_personal_access_token
   ```

### Running Tests

#### Quick Start
```bash
# Run the test runner script
python run_tests.py --type fast -v
```

#### Direct pytest Commands
```bash
# Run all tests
pytest tests/ -v

# Run only unit tests (fast, no external dependencies)
pytest tests/ -m unit -v

# Run only integration tests
pytest tests/ -m integration -v

# Run fast tests only (exclude slow tests)
pytest tests/ -m "not slow" -v

# Run specific test categories
pytest tests/ -m ado -v          # ADO tests only
pytest tests/ -m azure -v        # Azure AI tests only
pytest tests/ -m mcp -v          # MCP server tests only
pytest tests/ -m research -v     # Research pipeline tests only

# Run a specific test file
pytest tests/test_unit_functions.py -v

# Run a specific test function
pytest tests/test_ado_integration.py::TestADOIntegration::test_ado_story_retrieval -v
```

#### Test Runner Options
```bash
# List available test types
python run_tests.py --list-tests

# Run different test categories
python run_tests.py --type unit          # Unit tests only  
python run_tests.py --type integration   # Integration tests only
python run_tests.py --type ado           # ADO-related tests
python run_tests.py --type azure         # Azure AI tests
python run_tests.py --type mcp           # MCP server tests
python run_tests.py --type research      # Research pipeline tests
python run_tests.py --type fast          # Fast tests (exclude slow)
python run_tests.py --type slow          # Slow tests only
python run_tests.py --type all           # All tests
```

### Test Reports

Generate test reports:
```bash
# HTML report
pytest tests/ --html=test_report.html --self-contained-html

# Coverage report
pytest tests/ --cov=src --cov-report=html --cov-report=term

# JSON report
pytest tests/ --json-report --json-report-file=test_report.json
```

## Test Design

### Integration Test Philosophy

These tests are designed as **integration tests** that verify the complete functionality of the system components working together. They:

- Test real interactions with Azure AI services
- Validate ADO API integration
- Verify document generation and attachment
- Test the complete research pipeline
- Validate MCP server functionality

### Fixtures

The test suite uses pytest fixtures for:
- **`azure_credentials`** - Validates required environment variables
- **`test_story_ids`** - Provides known test story IDs
- **`unified_research_service`** - Research service instance
- **`ado_tool`** - ADO tool instance
- **`document_generation_tool`** - Document generation tool instance

### Test Data

Tests use:
- **Real ADO stories** (1186, 1198) for integration testing
- **Mock responses** for unit tests
- **Generated test content** for document generation

## Troubleshooting

### Common Issues

1. **Missing Environment Variables**
   ```
   SKIPPED: Missing required environment variables
   ```
   Solution: Ensure all required variables are set in `.env`

2. **Azure Authentication Failures**
   ```
   Azure authentication failed
   ```
   Solution: Verify Azure CLI login and credentials

3. **ADO Connection Issues**
   ```
   ADO_PAT authentication failed
   ```
   Solution: Check ADO Personal Access Token permissions

4. **Slow Test Timeouts**
   ```
   Test timed out
   ```
   Solution: Use `--type fast` to exclude slow tests

### Test Isolation

- Tests are designed to be independent
- External service failures don't cascade
- Mock tests provide fallback verification
- Tests clean up resources after completion

### Performance

- **Unit tests**: < 1 second each
- **Fast integration tests**: < 30 seconds each  
- **Slow integration tests**: 1-5 minutes each
- **Deep research tests**: 20-30 minutes each

## Contributing

When adding new tests:

1. Use appropriate markers (`@pytest.mark.integration`, etc.)
2. Include docstrings explaining test purpose
3. Clean up resources in test teardown
4. Use fixtures for common setup
5. Test both success and failure scenarios
6. Add unit tests for new utility functions