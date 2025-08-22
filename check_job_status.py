#!/usr/bin/env python3
"""
Check the status of the running research job for story 1198
"""

import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from unified_research_service import unified_research_service

def check_current_jobs():
    """Check all current jobs in the unified research service"""
    
    print("=== CHECKING CURRENT RESEARCH JOBS ===")
    
    jobs = unified_research_service.list_jobs()
    
    if not jobs:
        print("No jobs found in the unified research service")
        return
    
    print(f"Found {len(jobs)} total jobs:")
    
    for job_id, status in jobs.items():
        print(f"\n📋 Job ID: {job_id}")
        print(f"   Story ID: {status.get('story_id', 'N/A')}")
        print(f"   Status: {status.get('status', 'N/A')}")
        print(f"   Strategy: {status.get('strategy', 'N/A')}")
        print(f"   Current Step: {status.get('current_step', 'N/A')}")
        print(f"   Progress: {status.get('progress', 'N/A')}")
        print(f"   Started: {status.get('started_at', 'N/A')}")
        print(f"   Completed: {status.get('completed_at', 'N/A')}")
        print(f"   Document URL: {status.get('document_url', 'N/A')}")
        
        if status.get('error'):
            print(f"   ❌ Error: {status['error']}")
        
        # If this is a story 1198 job, get more details
        if status.get('story_id') == '1198':
            print(f"\n🔍 STORY 1198 JOB DETAILS:")
            
            if status.get('status') == 'completed':
                print(f"   ✅ Job completed successfully")
                
                # Try to get the results
                results = unified_research_service.get_results(job_id)
                if results:
                    research_results = results.get('research_results', {})
                    deep_research = research_results.get('deep_research', '')
                    
                    print(f"   📄 Research content length: {len(deep_research)}")
                    
                    if deep_research:
                        print(f"   📄 First 300 chars: {deep_research[:300]}...")
                        
                        # Check for the specific issues
                        if 'cot_summary' in deep_research:
                            print(f"   ❌ ISSUE: 'cot_summary' entries found in final content")
                        else:
                            print(f"   ✅ No 'cot_summary' entries in final content")
                        
                        if 'Final Report:' in deep_research:
                            print(f"   ❌ ISSUE: 'Final Report:' marker found in final content")
                        else:
                            print(f"   ✅ No 'Final Report:' marker in final content")
                        
                        # Check content quality
                        if deep_research.strip().startswith('#') and len(deep_research) > 1000:
                            print(f"   ✅ Content appears to be well-formatted research")
                        else:
                            print(f"   ⚠️ Content may have formatting issues")
                    else:
                        print(f"   ❌ No research content found")
                else:
                    print(f"   ❌ Could not retrieve results")
            
            elif status.get('status') == 'running':
                print(f"   ⏳ Job still running")
                print(f"   Current progress: {status.get('progress', 'N/A')}")
            
            elif status.get('status') == 'failed':
                print(f"   ❌ Job failed: {status.get('error', 'Unknown error')}")

def main():
    """Main function to check job status"""
    
    print("🔍 CHECKING STORY 1198 RESEARCH JOB STATUS")
    
    check_current_jobs()
    
    print(f"\n📋 STATUS CHECK COMPLETE")

if __name__ == "__main__":
    main()