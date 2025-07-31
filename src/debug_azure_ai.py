#!/usr/bin/env python3
"""
Debug Azure AI Agents Issue
Test each component individually to find the hanging point
"""

import os
import sys
import time
from pathlib import Path

# Load environment
sys.path.append(str(Path(__file__).parent))

try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / '.env'
    load_dotenv(dotenv_path=env_path)
    print("✅ Environment loaded")
except ImportError:
    print("⚠️ dotenv not available")

def test_step(step_name, func):
    """Test a step and measure time."""
    print(f"\n🔍 Testing: {step_name}")
    start_time = time.time()
    try:
        result = func()
        elapsed = time.time() - start_time
        print(f"✅ {step_name} - Success ({elapsed:.2f}s)")
        return result
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ {step_name} - Failed ({elapsed:.2f}s): {e}")
        raise

def test_azure_identity():
    """Test Azure identity."""
    from azure.identity import DefaultAzureCredential
    credential = DefaultAzureCredential()
    return credential

def test_project_client():
    """Test Azure AI project client."""
    from azure.ai.projects import AIProjectClient
    from azure.identity import DefaultAzureCredential
    
    project_endpoint = os.environ["PROJECT_ENDPOINT"]
    print(f"Using endpoint: {project_endpoint}")
    
    client = AIProjectClient(
        endpoint=project_endpoint,
        credential=DefaultAzureCredential(),
    )
    return client

def test_connections():
    """Test getting connections."""
    from azure.ai.projects import AIProjectClient
    from azure.identity import DefaultAzureCredential
    
    project_endpoint = os.environ["PROJECT_ENDPOINT"]
    client = AIProjectClient(
        endpoint=project_endpoint,
        credential=DefaultAzureCredential(),
    )
    
    # This is likely where it hangs
    connections = client.connections.list()
    print(f"Found connections: {len(list(connections))}")
    return connections

def test_specific_connection():
    """Test getting specific Bing connection."""
    from azure.ai.projects import AIProjectClient
    from azure.identity import DefaultAzureCredential
    
    project_endpoint = os.environ["PROJECT_ENDPOINT"]
    client = AIProjectClient(
        endpoint=project_endpoint,
        credential=DefaultAzureCredential(),
    )
    
    bing_resource_name = os.environ["BING_RESOURCE_NAME"]
    print(f"Looking for Bing resource: {bing_resource_name}")
    
    connection = client.connections.get(name=bing_resource_name)
    print(f"Found connection: {connection.id}")
    return connection

def test_agents_client():
    """Test creating agents client."""
    from azure.ai.projects import AIProjectClient
    from azure.identity import DefaultAzureCredential
    
    project_endpoint = os.environ["PROJECT_ENDPOINT"]
    client = AIProjectClient(
        endpoint=project_endpoint,
        credential=DefaultAzureCredential(),
    )
    
    agents_client = client.agents
    print(f"Agents client created: {type(agents_client)}")
    return agents_client

def main():
    """Run diagnostic tests."""
    print("🚀 Starting Azure AI Agents Diagnostic")
    
    # Check environment variables
    required_vars = ["PROJECT_ENDPOINT", "MODEL_DEPLOYMENT_NAME", "BING_RESOURCE_NAME"]
    for var in required_vars:
        value = os.environ.get(var)
        if value:
            print(f"✅ {var}: {value[:50]}...")
        else:
            print(f"❌ {var}: Not set")
    
    try:
        # Test each component
        test_step("Azure Identity", test_azure_identity)
        test_step("Project Client Creation", test_project_client)
        test_step("Agents Client Creation", test_agents_client)
        test_step("Connections List", test_connections)
        test_step("Specific Connection", test_specific_connection)
        
        print("\n✅ All tests passed! Azure AI setup is working.")
        
    except Exception as e:
        print(f"\n❌ Test failed at: {e}")
        print("This is likely where the 30-minute hang occurs.")

if __name__ == "__main__":
    main()