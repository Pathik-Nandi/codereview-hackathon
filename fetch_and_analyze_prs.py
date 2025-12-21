#!/usr/bin/env python3
"""
Script to fetch PRs from GitHub, analyze them using the multi-agent system,
and persist results to the database.

This script:
1. Fetches PR data from GitHub API (PRs #1-183)
2. Runs all agents (static analysis, security, code quality, context, coverage)
3. Persists analysis results to PostgreSQL database
4. Generates analytics and best practices
"""
import os
import sys
import json
import time
import requests
from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from models.pr_event import PREvent, PRFile, PRAuthor
from agents.dispatcher import AgentDispatcher
from agents.database_persistence_agent import DatabasePersistenceAgent
from services.database_service import DatabaseService
from services.github_service import GitHubService
from utils.logger import logger
from utils.constants import (
    GITHUB_TOKEN,
    GITHUB_BASE_URL,
    GITHUB_API_HEADERS,
    DEFAULT_REPOSITORY,
    GITHUB_API_DELAY,
    OUTPUT_DIR
)

# Load environment variables
load_dotenv()

# Configuration
REPOSITORY = os.getenv('GITHUB_REPOSITORY', DEFAULT_REPOSITORY)
START_PR = int(os.getenv('START_PR', '1'))
END_PR = int(os.getenv('END_PR', '183'))
DELAY_BETWEEN_PRS = float(os.getenv('DELAY_BETWEEN_PRS', str(GITHUB_API_DELAY)))

# API Configuration (use constants)
BASE_URL = GITHUB_BASE_URL
HEADERS = GITHUB_API_HEADERS

# Statistics
stats = {
    'total': 0,
    'fetched': 0,
    'analyzed': 0,
    'persisted': 0,
    'failed': 0,
    'skipped': 0
}


def check_rate_limit():
    """Check GitHub API rate limit status."""
    try:
        response = requests.get(f'{BASE_URL}/rate_limit', headers=HEADERS, timeout=10)
        if response.status_code == 200:
            data = response.json()
            core = data['resources']['core']
            remaining = core['remaining']
            limit = core['limit']
            print(f"Rate limit: {remaining}/{limit} requests remaining")
            
            if remaining < 50:
                reset_time = datetime.fromtimestamp(core['reset'])
                print(f"⚠️  Low rate limit! Resets at {reset_time}")
                return False
            return True
    except Exception as e:
        print(f"⚠️  Could not check rate limit: {e}")
    return True


def fetch_pr_from_github(pr_number):
    """Fetch a single PR from GitHub API."""
    url = f'{BASE_URL}/repos/{REPOSITORY}/pulls/{pr_number}'
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        
        if response.status_code == 404:
            print(f"  PR #{pr_number} not found (404)")
            return None
        
        if response.status_code != 200:
            print(f"  Failed to fetch PR #{pr_number}: {response.status_code}")
            return None
        
        pr_data = response.json()
        
        # Fetch files changed in the PR
        _fetch_pr_files(pr_number, pr_data)
        
        # Fetch user details (email and name)
        _fetch_user_details(pr_number, pr_data)
        
        return pr_data
        
    except requests.exceptions.Timeout:
        print(f"  Timeout fetching PR #{pr_number}")
        return None
    except Exception as e:
        print(f"  Error fetching PR #{pr_number}: {e}")
        return None


def _fetch_pr_files(pr_number, pr_data):
    """Fetch files changed in the PR."""
    files_url = f'{BASE_URL}/repos/{REPOSITORY}/pulls/{pr_number}/files'
    files_response = requests.get(files_url, headers=HEADERS, timeout=10)
    
    if files_response.status_code == 200:
        pr_data['files'] = files_response.json()
    else:
        pr_data['files'] = []


def _fetch_user_details(pr_number, pr_data):
    """Fetch user email and name from multiple sources."""
    user_login = pr_data['user']['login']
    user_email = None
    user_name = None
    
    # Try 1: Get from user API (public email)
    user_email, user_name = _fetch_from_user_api(user_login, user_email, user_name)
    
    # Try 2: Get from commits (more reliable for email)
    if not user_email:
        user_email, user_name = _fetch_from_commits(pr_number, user_email, user_name)
    
    # Store email and name in pr_data
    pr_data['user']['email'] = user_email
    pr_data['user']['name'] = user_name or user_login


def _fetch_from_user_api(user_login, user_email, user_name):
    """Fetch user details from GitHub user API."""
    user_url = f'{BASE_URL}/users/{user_login}'
    try:
        user_response = requests.get(user_url, headers=HEADERS, timeout=5)
        if user_response.status_code == 200:
            user_info = user_response.json()
            user_email = user_info.get('email') or user_email
            user_name = user_info.get('name') or user_name
    except Exception:
        pass
    return user_email, user_name


def _fetch_from_commits(pr_number, user_email, user_name):
    """Fetch user details from PR commits."""
    commits_url = f'{BASE_URL}/repos/{REPOSITORY}/pulls/{pr_number}/commits'
    try:
        commits_response = requests.get(commits_url, headers=HEADERS, timeout=5)
        if commits_response.status_code == 200:
            commits = commits_response.json()
            if commits and len(commits) > 0:
                # Get email from the first commit author
                commit_author = commits[0].get('commit', {}).get('author', {})
                if not user_email:
                    user_email = commit_author.get('email')
                if not user_name:
                    user_name = commit_author.get('name')
    except Exception:
        pass
    return user_email, user_name


def save_pr_locally(pr_number, pr_data):
    """Save PR data to local JSON file."""
    try:
        output_path = Path(OUTPUT_DIR)
        output_path.mkdir(exist_ok=True)
        
        file_path = output_path / f'pr_{pr_number}.json'
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(pr_data, f, indent=2, ensure_ascii=False)
        
        return True
    except Exception as e:
        print(f"  Error saving PR #{pr_number} locally: {e}")
        return False


def convert_to_pr_event(pr_data):
    """Convert GitHub PR data to PREvent model."""
    try:
        # Extract relevant fields and convert to PRFile objects
        files = []
        for file_data in pr_data.get('files', []):
            pr_file = PRFile(
                filename=file_data['filename'],
                status=file_data['status'],
                additions=file_data['additions'],
                deletions=file_data['deletions'],
                changes=file_data['changes'],
                patch=file_data.get('patch')
            )
            files.append(pr_file)
        
        # Convert author to PRAuthor
        author = PRAuthor(
            login=pr_data['user']['login'],
            id=pr_data['user']['id'],
            avatar_url=pr_data['user']['avatar_url']
        )
        
        # Create PREvent
        pr_event = PREvent(
            action='opened' if pr_data.get('state') == 'open' else 'closed',
            id=pr_data['id'],  # GitHub's unique PR ID
            pr_number=pr_data['number'],
            pr_title=pr_data['title'],
            pr_description=pr_data.get('body', ''),
            pr_url=pr_data['html_url'],
            repository=REPOSITORY,
            repository_url=f'https://github.com/{REPOSITORY}',
            author=author,
            base_branch=pr_data['base']['ref'],
            head_branch=pr_data['head']['ref'],
            files=files,
            created_at=pr_data.get('created_at', ''),
            updated_at=pr_data.get('updated_at', ''),
            is_draft=pr_data.get('draft', False)
        )
        return pr_event
    except Exception as e:
        print(f"  Error converting PR data to PREvent: {e}")
        return None


def analyze_pr(pr_event, dispatcher):
    """Run all agents on the PR and collect results."""
    try:
        print(f"  Analyzing PR #{pr_event.pr_number}...")
        
        # Run all agents through dispatcher - returns AgentResult object
        agent_result = dispatcher.dispatch(pr_event)
        
        if not agent_result or not agent_result.success:
            print(f"  No analysis results for PR #{pr_event.pr_number}")
            return None
        
        # Return the AgentResult directly - database persistence agent will handle it
        return agent_result
        
    except Exception as e:
        print(f"  Error analyzing PR #{pr_event.pr_number}: {e}")
        logger.error(f"Analysis failed for PR #{pr_event.pr_number}", error=str(e))
        return None


def persist_results(pr_event, analysis_results, db_agent, author_email=None, author_name=None):
    """Persist analysis results to database and trigger analytics processing."""
    try:
        print(f"  Persisting results for PR #{pr_event.pr_number}...")
        
        # Prepare PR data for database persistence
        pr_data = {
            'repository': pr_event.repository,
            'id': pr_event.id,  # GitHub's unique PR ID
            'pr_number': pr_event.pr_number,
            'number': pr_event.pr_number,  # Alternative field name
            'author': {
                'login': pr_event.author.login,
                'id': pr_event.author.id,
                'name': author_name or pr_event.author.login,
                'email': author_email
            },
            'title': pr_event.pr_title,
            'description': pr_event.pr_description,
            'body': pr_event.pr_description,  # Alternative field name
            'url': pr_event.pr_url,
            'html_url': pr_event.pr_url,  # Alternative field name
            'base_branch': pr_event.base_branch,
            'head_branch': pr_event.head_branch,
            'files_changed': len(pr_event.files),
            'lines_added': sum(getattr(f, 'additions', 0) or 0 for f in pr_event.files),
            'lines_deleted': sum(getattr(f, 'deletions', 0) or 0 for f in pr_event.files),
            'created_at': pr_event.created_at,
            'updated_at': pr_event.updated_at,
            'is_draft': pr_event.is_draft
        }
        
        # Persist using database persistence agent
        db_result = db_agent.persist_analysis(pr_data, analysis_results)
        
        if db_result.get('success'):
            print("  ✓ Persisted to database")
        else:
            print(f"  ✗ Failed to persist to database: {db_result.get('error')}")
            return False
        
        # Trigger async analytics processing for the user
        try:
            import threading
            
            def process_analytics_threaded():
                """Process analytics in a separate thread."""
                try:
                    from services.database_service import DatabaseService
                    from services.analytics_service import AnalyticsService
                    from agents.analytics_processing_agent import AnalyticsProcessingAgent
                    
                    # Initialize services in thread
                    db_svc = DatabaseService()
                    analytics_svc = AnalyticsService(db_svc)
                    analytics_agent = AnalyticsProcessingAgent(db_svc, analytics_svc)
                    
                    # Process analytics
                    result = analytics_agent.process_user_analytics(
                        author_login=pr_event.author.login,
                        author_email=author_email,
                        author_name=author_name
                    )
                    
                    if result.get('success'):
                        logger.info(
                            "Analytics processing completed",
                            author=pr_event.author.login,
                            analytics_id=result.get('analytics_id')
                        )
                    else:
                        logger.warning(
                            "Analytics processing had issues",
                            author=pr_event.author.login,
                            error=result.get('error')
                        )
                except Exception as e:
                    logger.error(
                        "Analytics thread failed",
                        author=pr_event.author.login,
                        error=str(e)
                    )
            
            # Start analytics in background thread
            analytics_thread = threading.Thread(
                target=process_analytics_threaded,
                daemon=True,
                name=f"Analytics-{pr_event.author.login}"
            )
            analytics_thread.start()
            print("  ✓ Analytics processing started in background")
            
        except Exception as e:
            # Analytics failure should not block PR processing
            print(f"  ⚠️  Analytics processing failed to start: {e}")
            logger.warning(f"Analytics failed for {pr_event.author.login}", error=str(e))
        
        return True
        
    except Exception as e:
        print(f"  Error persisting PR #{pr_event.pr_number}: {e}")
        logger.error(f"Persistence failed for PR #{pr_event.pr_number}", error=str(e))
        return False


def process_pr(pr_number, dispatcher, db_agent):
    """Fetch, analyze, and persist a single PR."""
    try:
        print(f"\n📋 Processing PR #{pr_number}...")
        
        # Step 1: Fetch from GitHub
        pr_data = fetch_pr_from_github(pr_number)
        if not pr_data:
            stats['skipped'] += 1
            return False
        
        stats['fetched'] += 1
        print(f"  ✓ Fetched: {pr_data['title'][:60]}...")
        
        # Step 2: Save locally for backup
        save_pr_locally(pr_number, pr_data)
        
        # Step 3: Convert to PREvent
        pr_event = convert_to_pr_event(pr_data)
        if not pr_event:
            stats['failed'] += 1
            return False
        
        # Step 4: Analyze using agents
        analysis_results = analyze_pr(pr_event, dispatcher)
        if not analysis_results:
            stats['failed'] += 1
            return False
        
        stats['analyzed'] += 1
        
        # Step 5: Persist to database with email and name
        author_email = pr_data.get('user', {}).get('email')
        author_name = pr_data.get('user', {}).get('name') or pr_event.author.login
        
        if persist_results(pr_event, analysis_results, db_agent, author_email, author_name):
            stats['persisted'] += 1
            print(f"  ✓ PR #{pr_number} completed successfully")
            return True
        else:
            stats['failed'] += 1
            return False
        
    except Exception as e:
        print(f"  ✗ Error processing PR #{pr_number}: {e}")
        logger.error(f"Processing failed for PR #{pr_number}", error=str(e))
        stats['failed'] += 1
        return False


def main():
    """Main execution function."""
    print("=" * 80)
    print("PR Fetch, Analysis, and Persistence Script")
    print("=" * 80)
    print(f"Repository: {REPOSITORY}")
    print(f"PR Range: #{START_PR} to #{END_PR}")
    print(f"Output Directory: {OUTPUT_DIR}")
    print("=" * 80)
    
    # Validate GitHub token
    if not GITHUB_TOKEN:
        print("❌ Error: GITHUB_TOKEN not found in environment variables")
        sys.exit(1)
    
    # Check rate limit
    if not check_rate_limit():
        print("❌ Error: Insufficient GitHub API rate limit")
        sys.exit(1)
    
    # Initialize services
    print("\n🔧 Initializing services...")
    try:
        db_service = DatabaseService()
        dispatcher = AgentDispatcher()
        db_agent = DatabasePersistenceAgent(db_service)
        # Note: Analytics processing is now handled via Celery async tasks
        print("✓ Services initialized")
    except Exception as e:
        print(f"❌ Error initializing services: {e}")
        sys.exit(1)
    
    # Process PRs
    print(f"\n🚀 Starting to process {END_PR - START_PR + 1} PRs...\n")
    
    start_time = time.time()
    stats['total'] = END_PR - START_PR + 1
    
    for pr_number in range(START_PR, END_PR + 1):
        process_pr(pr_number, dispatcher, db_agent)
        
        # Delay between requests to respect rate limits
        if pr_number < END_PR:
            time.sleep(DELAY_BETWEEN_PRS)
        
        # Check rate limit every 20 PRs
        if pr_number % 20 == 0:
            check_rate_limit()
    
    # Summary
    elapsed_time = time.time() - start_time
    print("\n" + "=" * 80)
    print("📊 SUMMARY")
    print("=" * 80)
    print(f"Total PRs to process: {stats['total']}")
    print(f"Successfully fetched:  {stats['fetched']}")
    print(f"Successfully analyzed: {stats['analyzed']}")
    print(f"Successfully persisted: {stats['persisted']}")
    print(f"Skipped (not found):   {stats['skipped']}")
    print(f"Failed:                {stats['failed']}")
    print(f"Elapsed time:          {elapsed_time:.1f} seconds ({elapsed_time/60:.1f} minutes)")
    print("=" * 80)
    
    if stats['persisted'] > 0:
        print(f"\n✓ Successfully processed {stats['persisted']} PRs!")
        print("  Data persisted to database: pr_analysis")
        print(f"  Local backups saved to: {OUTPUT_DIR}/")
    else:
        print("\n⚠️  No PRs were successfully processed")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Process interrupted by user")
        print(f"Processed {stats['persisted']}/{stats['total']} PRs before interruption")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        logger.error("Fatal error in main", error=str(e))
        sys.exit(1)
