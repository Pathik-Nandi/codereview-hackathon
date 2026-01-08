"""
Load Testing Script for PR Review System using Locust.

Usage:
    # Install locust first
    pip install locust

    # Run with web UI
    locust -f tests/load_test.py --host=http://localhost:5000

    # Run headless (no UI)
    locust -f tests/load_test.py --host=http://localhost:5000 --headless -u 10 -r 2 -t 60s

Options:
    -u: Number of users to simulate
    -r: Spawn rate (users per second)
    -t: Test duration
"""
import json
import random
from locust import HttpUser, task, between, events
from locust.runners import MasterRunner


# Sample test data
REPOSITORIES = [
    "test-org/test-repo",
    "sample-org/sample-repo",
    "demo-org/demo-repo"
]

PR_NUMBERS = list(range(1, 20))

TEST_USERS = [
    "developer@example.com",
    "reviewer@example.com",
    "admin@example.com"
]


class PRReviewUser(HttpUser):
    """
    Simulates a user interacting with the PR Review System.
    
    Behaviors:
    - Checks health endpoint frequently
    - Lists PRs periodically
    - Analyzes PRs occasionally (heavy operation)
    """
    
    # Wait between 1 to 5 seconds between tasks
    wait_time = between(1, 5)
    
    def on_start(self):
        """Called when user starts - can be used for login."""
        self.user_email = random.choice(TEST_USERS)
    
    @task(10)
    def health_check(self):
        """
        Frequently check health endpoint.
        Weight: 10 (most common operation)
        """
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    response.success()
                else:
                    response.failure(f"Unhealthy status: {data}")
            else:
                response.failure(f"Status code: {response.status_code}")
    
    @task(5)
    def list_prs(self):
        """
        List PRs for a user.
        Weight: 5 (common operation)
        """
        payload = {
            "email": self.user_email,
            "limit": 50
        }
        with self.client.post(
            "/api/prs/list",
            json=payload,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 503:
                # Service unavailable is acceptable during load testing
                response.success()
            else:
                response.failure(f"Status code: {response.status_code}")
    
    @task(2)
    def get_pr_details(self):
        """
        Get details for a specific PR.
        Weight: 2 (less common)
        """
        repo = random.choice(REPOSITORIES)
        pr_number = random.choice(PR_NUMBERS)
        
        with self.client.get(
            f"/api/prs/{repo.replace('/', '%2F')}/{pr_number}",
            catch_response=True
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Status code: {response.status_code}")
    
    @task(1)
    def analyze_pr(self):
        """
        Trigger PR analysis (heavy operation).
        Weight: 1 (least common due to being CPU intensive)
        """
        payload = {
            "repository": random.choice(REPOSITORIES),
            "pr_number": random.choice(PR_NUMBERS)
        }
        with self.client.post(
            "/api/analyze",
            json=payload,
            catch_response=True,
            timeout=60  # Analysis can take longer
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 400:
                # Bad request (missing params) is acceptable
                response.success()
            elif response.status_code == 404:
                # PR not found is acceptable
                response.success()
            else:
                response.failure(f"Status code: {response.status_code}")


class DashboardUser(HttpUser):
    """
    Simulates a user viewing the dashboard.
    Lighter load, primarily read operations.
    """
    
    wait_time = between(2, 8)
    weight = 2  # Less common than PR users
    
    @task(5)
    def get_analytics(self):
        """Fetch analytics data."""
        with self.client.get(
            "/api/analytics/overview",
            catch_response=True
        ) as response:
            if response.status_code in [200, 404, 503]:
                response.success()
            else:
                response.failure(f"Status code: {response.status_code}")
    
    @task(3)
    def get_user_stats(self):
        """Fetch user statistics."""
        payload = {"email": random.choice(TEST_USERS)}
        with self.client.post(
            "/api/analytics/user",
            json=payload,
            catch_response=True
        ) as response:
            if response.status_code in [200, 404, 503]:
                response.success()
            else:
                response.failure(f"Status code: {response.status_code}")
    
    @task(2)
    def health_check(self):
        """Quick health check."""
        self.client.get("/health")


# ============================================================================
# Event Handlers for Custom Reporting
# ============================================================================

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when load test starts."""
    print("\n" + "="*60)
    print("🚀 Starting Load Test for PR Review System")
    print("="*60 + "\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when load test stops."""
    print("\n" + "="*60)
    print("✅ Load Test Completed")
    print("="*60 + "\n")


# ============================================================================
# Quick Run Script
# ============================================================================

if __name__ == "__main__":
    import os
    import sys
    
    print("""
    Load Testing Script for PR Review System
    =========================================
    
    To run this script:
    
    1. Install locust:
       pip install locust
    
    2. Run with web UI (recommended):
       locust -f tests/load_test.py --host=http://localhost:5000
       Then open http://localhost:8089 in your browser
    
    3. Run headless:
       locust -f tests/load_test.py --host=http://localhost:5000 --headless -u 10 -r 2 -t 60s
       
       Options:
         -u 10    : 10 concurrent users
         -r 2     : Spawn 2 users per second
         -t 60s   : Run for 60 seconds
    """)
