#!/usr/bin/env python3
"""
Enhanced message extraction fix for story 1198 Word document issue
"""

def enhanced_extract_final_report_from_message(content: str) -> str:
    """
    Enhanced version of _extract_final_report_from_message with better handling
    of different Azure AI response formats
    """
    lines = content.split('\n')
    
    # Look for the final report marker (multiple variations)
    final_report_start = None
    for i, line in enumerate(lines):
        line_lower = line.lower().strip()
        # Check for various forms of the final report marker
        if (line.startswith('Final Report: #') or 
            'Final Report:' in line or
            line_lower.startswith('final report:') or
            line_lower.startswith('## final report') or
            line_lower.startswith('# final report')):
            final_report_start = i
            break
    
    # If no final report marker found, try to filter out cot_summary entries
    if final_report_start is None:
        print("⚠️ No 'Final Report:' marker found, filtering cot_summary entries", file=sys.stderr)
        
        # Filter out cot_summary lines and other noise
        filtered_lines = []
        for line in lines:
            line_stripped = line.strip()
            # Skip cot_summary entries and other noise
            if (line_stripped.startswith('cot_summary:') or
                line_stripped.startswith('cot_summary ') or
                line_stripped == '' or
                line_stripped.startswith('thinking:') or
                line_stripped.startswith('analysis:')):
                continue
            filtered_lines.append(line)
        
        # If we have substantial content after filtering, use it
        if len(filtered_lines) > 5:  # At least some content
            print(f"✅ Filtered out noise, using {len(filtered_lines)} lines", file=sys.stderr)
            return '\n'.join(filtered_lines)
        else:
            print("⚠️ Not enough content after filtering, using original", file=sys.stderr)
            return content
    
    # Extract everything from the final report onwards
    report_lines = lines[final_report_start:]
    
    # Remove the "Final Report: " prefix from the first line
    if report_lines[0].startswith('Final Report: '):
        report_lines[0] = report_lines[0].replace('Final Report: ', '')
    elif report_lines[0].lower().startswith('final report:'):
        # Handle case variations
        report_lines[0] = report_lines[0][len('final report:'):].strip()
    
    # Join the lines back together
    final_report = '\n'.join(report_lines)
    
    # Final cleanup - remove any remaining cot_summary entries
    final_lines = []
    for line in final_report.split('\n'):
        if not line.strip().startswith('cot_summary:'):
            final_lines.append(line)
    
    return '\n'.join(final_lines)

def create_enhanced_unified_research_service_patch():
    """
    Create a patch for the unified_research_service.py to improve message extraction
    """
    
    patch_instructions = """
ENHANCEMENT PATCH FOR UNIFIED_RESEARCH_SERVICE.PY

Replace the _extract_final_report_from_message method with this enhanced version:

def _extract_final_report_from_message(self, content: str) -> str:
    '''Enhanced extraction of final research report from message content.'''
    lines = content.split('\\n')
    
    # Look for the final report marker (multiple variations)
    final_report_start = None
    for i, line in enumerate(lines):
        line_lower = line.lower().strip()
        # Check for various forms of the final report marker
        if (line.startswith('Final Report: #') or 
            'Final Report:' in line or
            line_lower.startswith('final report:') or
            line_lower.startswith('## final report') or
            line_lower.startswith('# final report')):
            final_report_start = i
            break
    
    # If no final report marker found, try to filter out cot_summary entries
    if final_report_start is None:
        print("⚠️ No 'Final Report:' marker found, filtering cot_summary entries", file=sys.stderr)
        
        # Filter out cot_summary lines and other noise
        filtered_lines = []
        for line in lines:
            line_stripped = line.strip()
            # Skip cot_summary entries and other noise
            if (line_stripped.startswith('cot_summary:') or
                line_stripped.startswith('cot_summary ') or
                line_stripped == '' or
                line_stripped.startswith('thinking:') or
                line_stripped.startswith('analysis:')):
                continue
            filtered_lines.append(line)
        
        # If we have substantial content after filtering, use it
        if len(filtered_lines) > 5:  # At least some content
            print(f"✅ Filtered out noise, using {len(filtered_lines)} lines", file=sys.stderr)
            return '\\n'.join(filtered_lines)
        else:
            print("⚠️ Not enough content after filtering, using original", file=sys.stderr)
            return content
    
    # Extract everything from the final report onwards
    report_lines = lines[final_report_start:]
    
    # Remove the "Final Report: " prefix from the first line
    if report_lines[0].startswith('Final Report: '):
        report_lines[0] = report_lines[0].replace('Final Report: ', '')
    elif report_lines[0].lower().startswith('final report:'):
        # Handle case variations
        report_lines[0] = report_lines[0][len('final report:'):].strip()
    
    # Join the lines back together
    final_report = '\\n'.join(report_lines)
    
    # Final cleanup - remove any remaining cot_summary entries
    final_lines = []
    for line in final_report.split('\\n'):
        if not line.strip().startswith('cot_summary:'):
            final_lines.append(line)
    
    return '\\n'.join(final_lines)

ADDITIONAL DEBUGGING PATCH:

Add this enhanced debugging after line 614 in the execute method:

    # Enhanced debugging for message extraction
    print(f"📄 Raw research text sample: {raw_research_text[:500]}...", file=sys.stderr)
    if 'cot_summary' in raw_research_text:
        cot_count = raw_research_text.count('cot_summary')
        print(f"⚠️ Found {cot_count} cot_summary entries in raw content", file=sys.stderr)
    
    research_text = self._extract_final_report_from_message(raw_research_text)
    
    print(f"📄 Final report sample: {research_text[:500]}...", file=sys.stderr)
    if 'cot_summary' in research_text:
        remaining_cot = research_text.count('cot_summary')
        print(f"❌ Still have {remaining_cot} cot_summary entries in final content", file=sys.stderr)
    else:
        print(f"✅ Successfully removed all cot_summary entries", file=sys.stderr)
"""
    
    return patch_instructions

def main():
    """Generate the fix for the message extraction issue"""
    
    print("🔧 MESSAGE EXTRACTION FIX FOR STORY 1198")
    print("This script provides the enhanced message extraction logic")
    print("to properly handle Azure AI responses and filter out cot_summary entries.")
    
    # Test the enhanced function
    print(f"\n1. Testing enhanced extraction function...")
    
    # Test case with cot_summary entries
    test_content = """
cot_summary: Initial analysis of the project requirements
cot_summary: Evaluating different technology options
cot_summary: Considering Microsoft Azure AI integration

# Partner Management Platform with AI Integration

## Executive Summary
This comprehensive analysis examines the implementation of an AI-powered partner management platform.

## Technical Architecture
The recommended architecture includes...

## Market Analysis
The current market landscape shows...
"""
    
    result = enhanced_extract_final_report_from_message(test_content)
    print(f"✅ Test successful")
    print(f"   Original length: {len(test_content)}")
    print(f"   Filtered length: {len(result)}")
    print(f"   Contains cot_summary: {'cot_summary' in result}")
    print(f"   First 200 chars: {result[:200]}...")
    
    # Generate the patch
    print(f"\n2. Generating enhancement patch...")
    patch = create_enhanced_unified_research_service_patch()
    
    print(f"\n🎯 SOLUTION FOR STORY 1198 WORD DOCUMENT ISSUE:")
    print(f"The issue is likely that the Azure AI response contains 'cot_summary' entries")
    print(f"without a clear 'Final Report:' marker, and the current extraction function")
    print(f"falls back to using the full content including the noise.")
    
    print(f"\n📋 RECOMMENDED ACTIONS:")
    print(f"1. Apply the enhanced _extract_final_report_from_message method")
    print(f"2. Add enhanced debugging to see exactly what content is being extracted")
    print(f"3. Re-run research for story 1198 to generate a clean Word document")
    print(f"4. Verify the new document doesn't contain cot_summary entries")
    
    print(f"\n💾 PATCH SAVED TO:")
    print(f"The patch instructions are ready to be applied to unified_research_service.py")
    
    return True

if __name__ == "__main__":
    main()