#!/usr/bin/env python3
"""
Fallback approach using the standalone DeepResearchMCPTool from mcp_tools.py
"""

import sys
from pathlib import Path
from dotenv import load_dotenv

# Add src to path and load environment
sys.path.append('src')
env_path = Path('.env')
load_dotenv(dotenv_path=env_path)

from AzureDevOpsTool import AzureDevOpsTool
from mcp_tools import DeepResearchMCPTool

def extract_project_context(story_details: str, story_id: str) -> dict:
    """Extract project context from ADO story details."""
    lines = story_details.split('\n')
    
    # Extract title (assuming format: **Story ID: Title**)
    title = "Unknown Project"
    for line in lines:
        if line.startswith("**Story") and ":" in line:
            title = line.split(":", 1)[1].strip().rstrip("*")
            break
    
    return {
        "project_name": title,
        "story_id": story_id
    }

def format_custom_prompt(project_context: dict, story_details: str) -> str:
    """Format custom prompt with project context."""
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
    return formatted

def extract_final_report_from_content(content: str) -> str:
    """Extract the final research report from the content."""
    lines = content.split('\n')
    
    # Look for the final report marker
    final_report_start = None
    for i, line in enumerate(lines):
        if line.startswith('Final Report: #') or 'Final Report:' in line:
            final_report_start = i
            break
    
    if final_report_start is None:
        print("⚠️ Could not find 'Final Report:' marker, using full content")
        return content
    
    # Extract everything from the final report onwards
    report_lines = lines[final_report_start:]
    
    # Remove the "Final Report: " prefix from the first line
    if report_lines[0].startswith('Final Report: '):
        report_lines[0] = report_lines[0].replace('Final Report: ', '')
    
    # Join the lines back together
    final_report = '\n'.join(report_lines)
    
    return final_report

def save_research_results(content: str, project_name: str, story_id: str) -> str:
    """Save research results to a file."""
    # Extract just the final report section
    final_report = extract_final_report_from_content(content)
    
    # Create a clean filename
    clean_name = project_name.replace(" ", "_").replace(":", "").replace("/", "_")
    filename = f"research_summary_{story_id}_{clean_name}.md"
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(final_report)
    
    return filename

def main():
    print("=== ADO to Deep Research Integration Test (Fallback Method) ===")
    
    # Step 1: Get ADO story details
    print("1. Fetching ADO story details...")
    ado_tool = AzureDevOpsTool(
        organization="gpsuscodewith",  
        project="Code-With Engagement Portfolio"  
    )
    
    story_id = "1186"  # Using the story ID from your updated file
    story_details = ado_tool.get_azure_devops_story(story_id)
    
    if "Failed to retrieve" in story_details:
        print(f"❌ Error retrieving story: {story_details}")
        return
    
    print("✅ Successfully retrieved ADO story details")
    print(f"   Story length: {len(story_details)} characters")
    
    # Step 2: Extract project context
    print("2. Extracting project context...")
    project_context = extract_project_context(story_details, story_id)
    print(f"✅ Project: {project_context['project_name']}")
    print(f"   Story ID: {project_context['story_id']}")
    
    # Step 3: Format research prompt
    print("3. Generating custom research prompt...")
    research_prompt = format_custom_prompt(project_context, story_details)
    print(f"✅ Generated prompt: {len(research_prompt)} characters")
    
    # Step 4: Run deep research using standalone tool
    print("4. Running deep research (this may take several minutes)...")
    print("   Using DeepResearchMCPTool from mcp_tools.py")
    
    try:
        research_tool = DeepResearchMCPTool()
        print("✅ DeepResearchMCPTool initialized")
        
        # Run the research
        print("   Starting research request...")
        research_results = research_tool.deep_research(research_prompt)
        
        if research_results and len(research_results) > 100:
            print(f"✅ Research completed successfully!")
            print(f"   Results length: {len(research_results)} characters")
            
            # Step 5: Save results
            print("5. Saving research results...")
            filename = save_research_results(research_results, project_context['project_name'], story_id)
            print(f"✅ Research saved to: {filename}")
            
            # Show preview
            print("\n=== RESEARCH PREVIEW ===")
            print(research_results[:500] + "...\n")
            print("=== END PREVIEW ===")
            
            return filename
        else:
            print(f"❌ Research failed or returned minimal content")
            print(f"   Result: {research_results}")
            
    except Exception as e:
        print(f"❌ Deep research failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()