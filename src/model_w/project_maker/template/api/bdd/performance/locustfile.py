"""
Locust performance tests for the SvelteKit frontend.
It's meant to be run with `make performance_test` which uses Docker as opposed to in
your local environment, as this gives a very realistic simulation of how the site will
perform in production.
"""

from locust import HttpUser, between, task  # type: ignore


class FrontendUser(HttpUser):
    """Simulate a user navigating through the SvelteKit frontend."""

    wait_time = between(1, 5)  # Simulates user think time

    @task()
    def home_page(self):
        """Load the homepage."""
        self.client.get("/")

    # :: IF api__testing
    @task()
    def demo_page(self):
        """Load the demo CMS page."""
        self.client.get("/demo/")

    # :: ENDIF

    @task()
    def non_cms_page(self):
        """Load the non-CMS page."""
        self.client.get("/non-cms")
