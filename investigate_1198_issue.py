#!/usr/bin/env python3
"""
Investigate the story 1198 Word document issue by running a fresh research job
and monitoring the message extraction and document generation process
"""

import sys
import time
import json
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from unified_research_service import unified_research_service, ResearchStrategy

def investigate_story_1198():
    """Start a new research job for story 1198 and monitor the process"""
    
    print("=== INVESTIGATING STORY 1198 WORD DOCUMENT ISSUE ===")
    print("Starting fresh deep research to monitor message extraction and document generation")
    
    try:
        # Start deep research for story 1198
        print(f"\n1. Starting new deep research for story 1198...")
        job_id = unified_research_service.start_research(
            story_id="1198",
            strategy=ResearchStrategy.DEEP,
            custom_prompt=""  # Use default prompt
        )
        print(f"✅ Research job started: {job_id}")
        
        # Monitor the job progress with detailed status checks
        print(f"\n2. Monitoring job progress...")
        previous_step = None
        
        for i in range(120):  # Monitor for 10 minutes max
            status = unified_research_service.get_status(job_id)
            current_step = status.get('current_step', 'unknown')
            
            # Only print when step changes or every 30 seconds
            if current_step != previous_step or i % 6 == 0:
                elapsed_minutes = (i + 1) * 5 / 60
                print(f"   [{elapsed_minutes:.1f}m] Status: {status['status']}")
                print(f"        Step: {current_step}")
                print(f"        Progress: {status.get('progress', 'N/A')}")
                
                if status.get('error'):
                    print(f"        Error: {status['error']}")
                
                previous_step = current_step
            
            # Check for completion or failure
            if status['status'] == 'failed':
                print(f"\n❌ Job failed: {status.get('error', 'Unknown error')}")
                return False
            elif status['status'] == 'completed':
                print(f"\n✅ Job completed successfully!")
                break
            
            time.sleep(5)  # Check every 5 seconds
        
        # Get final status and analyze results
        final_status = unified_research_service.get_status(job_id)
        print(f"\n3. Analyzing final results...")
        print(f"   Status: {final_status['status']}")
        print(f"   Document URL: {final_status.get('document_url', 'N/A')}")
        
        if final_status['status'] == 'completed':
            # Get the actual research results
            results = unified_research_service.get_results(job_id)
            if results:
                print(f"\n4. Examining research content...")
                research_results = results.get('research_results', {})
                deep_research = research_results.get('deep_research', '')
                
                print(f"   Research content length: {len(deep_research)}")
                print(f"   First 200 chars: {deep_research[:200]}...")
                
                # Check for indicators of the issue
                if 'cot_summary' in deep_research:
                    print(f"   ❌ ISSUE FOUND: 'cot_summary' entries in final research")
                    print(f"   → Message extraction may have failed")
                else:
                    print(f"   ✅ No 'cot_summary' entries found in final research")
                
                if 'Final Report:' in deep_research:
                    print(f"   ❌ ISSUE FOUND: 'Final Report:' marker in final content")
                    print(f"   → Content may not have been properly extracted")
                else:
                    print(f"   ✅ No 'Final Report:' marker in final content")
                
                # Check if content looks like a proper research report
                if deep_research.strip().startswith('#') and len(deep_research) > 500:
                    print(f"   ✅ Content appears to be a proper research report")
                else:
                    print(f"   ❌ Content may not be properly formatted")
                    
                return True
        
        elif final_status['status'] == 'running':
            print(f"\n⏳ Job still running after 10 minutes")
            print(f"   This is normal for deep research (20-30 minutes total)")
            print(f"   Job ID for continued monitoring: {job_id}")
            return True
        
        return False
        
    except Exception as e:
        print(f"❌ Investigation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_existing_research_output():
    """Check if there are any existing research output files from previous runs"""
    
    print("\n=== CHECKING FOR EXISTING RESEARCH OUTPUT FILES ===")
    
    # Look for the research_output directory
    research_output_dir = Path("research_output")
    if research_output_dir.exists():
        print(f"✅ Found research_output directory")
        
        # Look for files related to story 1198
        files_1198 = list(research_output_dir.glob("*1198*"))
        if files_1198:
            print(f"✅ Found {len(files_1198)} files related to story 1198:")
            for file in files_1198:
                print(f"   - {file.name}")
                
            # Try to read the most recent file
            latest_file = max(files_1198, key=lambda f: f.stat().st_mtime)
            print(f"\n📄 Reading latest file: {latest_file.name}")
            
            try:
                content = latest_file.read_text(encoding='utf-8')
                print(f"   File size: {len(content)} characters")
                print(f"   First 300 chars: {content[:300]}...")
                
                # Check for the issues
                if 'cot_summary' in content:
                    print(f"   ❌ File contains 'cot_summary' entries")
                if 'Final Report:' in content:
                    print(f"   ⚠️ File contains 'Final Report:' marker")
                
                return True
            except Exception as e:
                print(f"   ❌ Could not read file: {e}")
        else:
            print(f"⚠️ No files found for story 1198 in research_output")
    else:
        print(f"⚠️ No research_output directory found")
    
    return False

def main():
    """Main investigation function"""
    
    print("🔍 STORY 1198 WORD DOCUMENT ISSUE INVESTIGATION")
    print("This script will:")
    print("1. Check for existing research output files")
    print("2. Start a fresh deep research job for story 1198")
    print("3. Monitor the message extraction process")
    print("4. Analyze the final document content")
    
    # Check for existing output files first
    check_existing_research_output()
    
    # Run the investigation
    print(f"\n" + "="*60)
    success = investigate_story_1198()
    
    if success:
        print(f"\n🎯 INVESTIGATION SUMMARY:")
        print(f"✅ Successfully monitored story 1198 research process")
        print(f"✅ Can now analyze what content is generated")
        print(f"✅ Can verify if message extraction is working correctly")
        
        print(f"\n📋 NEXT STEPS:")
        print(f"1. Compare the new research output with the problematic Word document")
        print(f"2. Check if the issue is in message extraction or document generation")
        print(f"3. Look for 'cot_summary' entries in the raw vs processed content")
        
    else:
        print(f"\n❌ INVESTIGATION INCOMPLETE")
        print(f"Unable to complete the research process for analysis")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)