"""Load testing scenarios using Locust.

Run with:
    locust -f tests/load/locustfile.py --host=http://localhost:8000

For web UI:
    locust -f tests/load/locustfile.py --host=http://localhost:8000 --web-host=0.0.0.0

For headless mode (100 users, 10/sec spawn rate, 60 seconds):
    locust -f tests/load/locustfile.py --host=http://localhost:8000 --headless -u 100 -r 10 -t 60s
"""

from locust import HttpUser, task, between, events
import random
import json
from uuid import uuid4


class SupportFormUser(HttpUser):
    """
    Simulates users submitting support forms.

    This is the primary load test scenario for the web form submission flow.
    """

    # Wait 1-3 seconds between tasks (simulates user think time)
    wait_time = between(1, 3)

    def on_start(self):
        """Called when a user starts. Initialize user data."""
        self.ticket_ids = []
        self.customer_email = f"loadtest_{uuid4().hex[:8]}@example.com"

    @task(10)
    def submit_support_form(self):
        """Submit a support form (most common action - weight 10)."""
        categories = ["general", "technical", "billing", "feedback", "bug_report"]
        priorities = ["low", "medium", "high"]

        form_data = {
            "name": f"Load Test User {random.randint(1, 1000)}",
            "email": self.customer_email,
            "phone": f"+1{random.randint(2000000000, 9999999999)}",
            "subject": f"Load Test Support Request {random.randint(1, 10000)}",
            "category": random.choice(categories),
            "priority": random.choice(priorities),
            "message": "This is a load test message. " * random.randint(5, 20)
        }

        with self.client.post(
            "/support/submit",
            json=form_data,
            catch_response=True,
            name="/support/submit"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if "ticket_id" in data:
                    self.ticket_ids.append(data["ticket_id"])
                    response.success()
                else:
                    response.failure("No ticket_id in response")
            else:
                response.failure(f"Got status code {response.status_code}")

    @task(5)
    def check_ticket_status(self):
        """Check ticket status (weight 5)."""
        if not self.ticket_ids:
            # Skip if no tickets created yet
            return

        ticket_id = random.choice(self.ticket_ids)

        with self.client.get(
            f"/support/ticket/{ticket_id}",
            catch_response=True,
            name="/support/ticket/[id]"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if "status" in data:
                    response.success()
                else:
                    response.failure("No status in response")
            elif response.status_code == 404:
                # Ticket might not be found yet (async processing)
                response.success()
            else:
                response.failure(f"Got status code {response.status_code}")

    @task(1)
    def health_check(self):
        """Health check endpoint (weight 1)."""
        with self.client.get(
            "/health",
            catch_response=True,
            name="/health"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if data.get("status") in ["healthy", "degraded"]:
                    response.success()
                else:
                    response.failure(f"Unexpected health status: {data.get('status')}")
            else:
                response.failure(f"Got status code {response.status_code}")


class HighVolumeUser(HttpUser):
    """
    Simulates high-volume rapid submissions.

    Tests system behavior under stress with minimal wait time.
    """

    wait_time = between(0.1, 0.5)  # Very short wait time

    @task
    def rapid_submit(self):
        """Rapidly submit support forms."""
        form_data = {
            "name": "High Volume User",
            "email": f"highvolume_{uuid4().hex[:8]}@example.com",
            "subject": "Rapid Test",
            "category": "general",
            "priority": "low",
            "message": "Quick test message for high volume testing."
        }

        self.client.post("/support/submit", json=form_data, name="/support/submit [rapid]")


class MixedWorkloadUser(HttpUser):
    """
    Simulates realistic mixed workload.

    Combines form submissions, status checks, and API calls.
    """

    wait_time = between(2, 5)

    @task(5)
    def submit_form(self):
        """Submit support form."""
        form_data = {
            "name": "Mixed Workload User",
            "email": f"mixed_{uuid4().hex[:8]}@example.com",
            "subject": "Mixed Workload Test",
            "category": random.choice(["general", "technical", "billing"]),
            "priority": random.choice(["low", "medium", "high"]),
            "message": "Testing mixed workload scenario with various operations."
        }

        self.client.post("/support/submit", json=form_data)

    @task(3)
    def check_health(self):
        """Check system health."""
        self.client.get("/health")

    @task(1)
    def check_root(self):
        """Check root endpoint."""
        self.client.get("/")


# Event handlers for custom metrics
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when load test starts."""
    print("\n" + "="*60)
    print("🚀 Load Test Starting")
    print("="*60)
    print(f"Target: {environment.host}")
    print(f"Users: {environment.runner.target_user_count if hasattr(environment.runner, 'target_user_count') else 'N/A'}")
    print("="*60 + "\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when load test stops."""
    print("\n" + "="*60)
    print("🏁 Load Test Complete")
    print("="*60)

    stats = environment.stats
    print(f"Total Requests: {stats.total.num_requests}")
    print(f"Total Failures: {stats.total.num_failures}")
    print(f"Failure Rate: {stats.total.fail_ratio * 100:.2f}%")
    print(f"Average Response Time: {stats.total.avg_response_time:.2f}ms")
    print(f"95th Percentile: {stats.total.get_response_time_percentile(0.95):.2f}ms")
    print(f"99th Percentile: {stats.total.get_response_time_percentile(0.99):.2f}ms")
    print(f"Requests/sec: {stats.total.total_rps:.2f}")
    print("="*60 + "\n")
