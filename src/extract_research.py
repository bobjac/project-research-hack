#!/usr/bin/env python3
"""
Extract and format the research results from messages.md
"""

def extract_final_report(content: str) -> str:
    """Extract the final research report from the message content."""
    lines = content.split('\n')
    
    # Look for the final report marker
    final_report_start = None
    for i, line in enumerate(lines):
        if line.startswith('Final Report: #'):
            final_report_start = i
            break
    
    if final_report_start is None:
        print("❌ Could not find 'Final Report:' marker")
        return ""
    
    # Extract everything from the final report onwards
    report_lines = lines[final_report_start:]
    
    # Remove the "Final Report: " prefix from the first line
    if report_lines[0].startswith('Final Report: '):
        report_lines[0] = report_lines[0].replace('Final Report: ', '')
    
    # Join the lines back together
    final_report = '\n'.join(report_lines)
    
    return final_report

def main():
    print("=== EXTRACTING RESEARCH RESULTS FROM MESSAGES.MD ===")
    
    # Read the messages.md file
    try:
        with open('messages.md', 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"✅ Loaded messages.md: {len(content)} characters")
        
        # Extract the final report
        final_report = extract_final_report(content)
        
        if final_report:
            print(f"✅ Extracted final report: {len(final_report)} characters")
            
            # Save to a clean research file
            output_filename = "research_partner_management_platforms_2024.md"
            with open(output_filename, 'w', encoding='utf-8') as f:
                f.write(final_report)
            
            print(f"✅ Saved clean research report to: {output_filename}")
            
            # Show preview
            print(f"\n=== RESEARCH REPORT PREVIEW ===")
            print(final_report[:500] + "...")
            print(f"=== END PREVIEW ===")
            
            return output_filename
        else:
            print("❌ Could not extract final report")
            
    except FileNotFoundError:
        print("❌ messages.md file not found")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()