#!/usr/bin/env python3.10
"""Performance test script for PR analysis."""
import requests
import time
import sys

def test_pr_performance():
    """Test analysis performance for PRs 1-10."""
    total_start = time.time()
    execution_times = []
    
    print("Starting performance test...")
    print("=" * 80)
    
    for pr_num in range(1, 11):
        print(f'\n{"=" * 80}')
        print(f'Analyzing PR #{pr_num}...')
        print("=" * 80)
        
        pr_start = time.time()
        
        try:
            response = requests.post(
                'http://localhost:5000/api/analyze',
                headers={'Content-Type': 'application/json'},
                json={
                    'repository': 'tarentomaheshvakkund/testdata-hackathon',
                    'pr_number': pr_num,
                    'post_comments': True,
                    'skip_if_has_comments': False
                },
                timeout=120
            )
            
            pr_end = time.time()
            pr_time = pr_end - pr_start
            execution_times.append(pr_time)
            
            if response.status_code == 200:
                data = response.json()
                print(f'✅ Status: {data.get("status")}')
                print(f'📊 Issues Found: {data.get("issues_found", 0)}')
                print(f'⏱️  Backend Time: {data.get("execution_time", 0):.2f}s')
                print(f'⏱️  Total Time (with network): {pr_time:.2f}s')
                comments = data.get('comments_posted', {})
                print(f'💬 Summary Posted: {comments.get("summary_posted", False)}')
                print(f'💬 Inline Comments: {comments.get("inline_comments_posted", 0)}')
            else:
                print(f'❌ Error: {response.status_code}')
                print(response.text[:200])
                
        except Exception as e:
            print(f'❌ Exception: {e}')
            pr_end = time.time()
            pr_time = pr_end - pr_start
            execution_times.append(pr_time)
        
        # Small delay between PRs
        if pr_num < 10:
            time.sleep(1)
    
    total_end = time.time()
    total_time = total_end - total_start
    
    # Print summary
    print('\n' + '=' * 80)
    print('PERFORMANCE SUMMARY')
    print('=' * 80)
    print(f'Total PRs analyzed: {len(execution_times)}')
    print(f'Total time: {total_time:.2f}s')
    if execution_times:
        avg_time = sum(execution_times) / len(execution_times)
        print(f'Average time per PR: {avg_time:.2f}s')
        print(f'Min time: {min(execution_times):.2f}s')
        print(f'Max time: {max(execution_times):.2f}s')
        print(f'\nPrevious baseline: ~10s per PR')
        improvement = ((10 - avg_time) / 10 * 100)
        print(f'Improvement: {improvement:.1f}%')
        if improvement > 0:
            print(f'✅ Performance improved by {improvement:.1f}%!')
        else:
            print(f'⚠️  Performance degraded by {abs(improvement):.1f}%')
    print('=' * 80)

if __name__ == '__main__':
    test_pr_performance()
