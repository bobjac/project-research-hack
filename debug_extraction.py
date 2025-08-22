#!/usr/bin/env python3
"""
Debug script to test the _extract_final_report_from_message function
and investigate the Word document issue for story 1198
"""

import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from unified_research_service import DeepResearchExecutor

def test_extraction_scenarios():
    """Test different message extraction scenarios that might cause the issue"""
    
    print("=== DEBUGGING MESSAGE EXTRACTION FOR STORY 1198 ===")
    
    executor = DeepResearchExecutor()
    
    # Scenario 1: Message with cot_summary entries (likely the issue)
    print("\n1. Testing scenario with cot_summary entries:")
    raw_message_with_cot = """
cot_summary: This is a chain of thought summary entry that should not be in the final document.
cot_summary: Another intermediate thinking step that pollutes the output.
cot_summary: Multiple intermediate steps that make the document look messy.

Final Report: # Partner Management Platform with Microsoft AI Integration

## Executive Summary
This report analyzes the implementation of an AI-powered partner management platform...

## Technical Architecture
Based on the project requirements, we recommend...

## Market Analysis
The partner management software market is experiencing...
"""
    
    extracted = executor._extract_final_report_from_message(raw_message_with_cot)
    print(f"Raw content length: {len(raw_message_with_cot)}")
    print(f"Extracted content length: {len(extracted)}")
    print(f"First 200 chars of extracted: {extracted[:200]}...")
    
    if "cot_summary" in extracted:
        print("❌ ISSUE FOUND: cot_summary entries still present in extracted content")
    else:
        print("✅ cot_summary entries properly removed")
    
    # Scenario 2: Message without Final Report marker
    print("\n2. Testing scenario without 'Final Report:' marker:")
    raw_message_no_marker = """
# Partner Management Platform Analysis

## Overview
This is research content without the Final Report marker...

## Technical Recommendations
Based on the analysis...
"""
    
    extracted_no_marker = executor._extract_final_report_from_message(raw_message_no_marker)
    print(f"Raw content length: {len(raw_message_no_marker)}")
    print(f"Extracted content length: {len(extracted_no_marker)}")
    
    if len(extracted_no_marker) == len(raw_message_no_marker):
        print("✅ Full content returned when no Final Report marker found")
    else:
        print("❌ Content was truncated incorrectly")
    
    # Scenario 3: Message with Final Report in middle
    print("\n3. Testing scenario with Final Report marker in middle:")
    raw_message_middle = """
cot_summary: Initial analysis phase
cot_summary: Gathering information about the project
cot_summary: Evaluating technology options

Final Report: # Comprehensive Research Analysis

## Project Overview
This section contains the actual research results...

## Detailed Analysis
More research content here...

Additional content after final report...
"""
    
    extracted_middle = executor._extract_final_report_from_message(raw_message_middle)
    print(f"Raw content length: {len(raw_message_middle)}")
    print(f"Extracted content length: {len(extracted_middle)}")
    
    if "cot_summary" not in extracted_middle and "# Comprehensive Research Analysis" in extracted_middle:
        print("✅ Final Report properly extracted from middle of message")
    else:
        print("❌ Final Report extraction from middle failed")
    
    return extracted, extracted_no_marker, extracted_middle

def investigate_word_document_issue():
    """Investigate what might be causing the Word document to be wrong"""
    
    print("\n=== WORD DOCUMENT INVESTIGATION ===")
    
    # The likely issues based on the description:
    issues = [
        "Deep research completed but message extraction failing to get 'Final Report:' section",
        "Research content showing 'cot_summary' entries instead of actual research", 
        "Word document formatting not handling research content properly"
    ]
    
    print("\nPossible issues with story 1198 Word document:")
    for i, issue in enumerate(issues, 1):
        print(f"{i}. {issue}")
    
    print(f"\n📋 DEBUGGING STEPS:")
    print(f"1. Check if research job completed for story 1198")
    print(f"2. Look at raw research output vs extracted content")
    print(f"3. Verify _extract_final_report_from_message is working")
    print(f"4. Check Word document generation receives clean content")
    
    print(f"\n🔍 KEY INVESTIGATION POINTS:")
    print(f"• Does the raw Azure AI message contain 'cot_summary' entries?")
    print(f"• Is the 'Final Report:' marker present in the message?")
    print(f"• Is the extraction function being called at all?")
    print(f"• Is the Word document getting the extracted content or raw content?")

def main():
    """Main debug function"""
    
    print("🔧 STORY 1198 WORD DOCUMENT DEBUG TOOL")
    print("Investigating why the Word document generated for story 1198 is wrong")
    
    # Test extraction scenarios
    extracted_samples = test_extraction_scenarios()
    
    # Investigate the specific issue
    investigate_word_document_issue()
    
    print(f"\n🎯 LIKELY ROOT CAUSE:")
    print(f"The Word document for story 1198 probably contains:")
    print(f"• Raw Azure AI Foundry message format")
    print(f"• 'cot_summary' entries showing intermediate thinking steps")
    print(f"• Missing 'Final Report:' extraction or extraction failure")
    
    print(f"\n🔧 RECOMMENDED FIXES:")
    print(f"1. Verify _extract_final_report_from_message is called in DeepResearchExecutor")
    print(f"2. Check if the message actually contains 'Final Report:' marker")
    print(f"3. Add better fallback when Final Report marker is missing")
    print(f"4. Add logging to see what content is passed to Word document generation")
    
    return True

if __name__ == "__main__":
    main()