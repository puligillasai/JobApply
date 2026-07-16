# test_scraper.py - deterministic tests for job scraper and API behavior
import unittest
from datetime import datetime, timedelta
from unittest.mock import patch

from app import app
from scraper_module import (
    SUPPORTED_PORTALS,
    fetch_raw_jobs,
    filter_and_rank_jobs,
    has_visa_sponsorship,
    is_usa_location,
    requires_security_clearance,
    run_full_search,
)


def sample_job(**overrides):
    job = {
        "title": "DevOps Engineer",
        "company": "Sponsor Corp",
        "location": "Remote USA",
        "url": "https://example.com/job",
        "posted_date": datetime.now(),
        "description": "Visa sponsorship available for Kubernetes and AWS engineers.",
        "source": "TestSource",
    }
    job.update(overrides)
    return job


class TestJobScraper(unittest.TestCase):
    def test_fetch_raw_jobs_returns_list_without_live_network(self):
        """fetch_raw_jobs should return the async scraper result."""
        with patch("scraper_module.fetch_raw_jobs_async", return_value=[sample_job()]):
            jobs = fetch_raw_jobs(portals=["linkedin"])

        self.assertIsInstance(jobs, list)
        self.assertEqual(jobs[0]["title"], "DevOps Engineer")

    def test_run_full_search_uses_supported_portals_and_ranks_results(self):
        """run_full_search should fetch then return ranked job dictionaries."""
        with patch("scraper_module.fetch_raw_jobs", return_value=[sample_job()]):
            jobs = run_full_search(portals=["linkedin"])

        self.assertEqual(len(jobs), 1)
        self.assertIn("confidence", jobs[0])
        self.assertIn("match_percentage", jobs[0])
        self.assertEqual(jobs[0]["link"], "https://example.com/job")

    def test_filter_and_rank_jobs_requires_recent_usa_target_roles(self):
        raw_jobs = [
            sample_job(title="DevOps Engineer", location="Remote USA"),
            sample_job(title="Sales Manager", location="Remote USA"),
            sample_job(title="SRE", location="London"),
            sample_job(title="Cloud Engineer", posted_date=datetime.now() - timedelta(days=2)),
        ]

        filtered = filter_and_rank_jobs(raw_jobs)

        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["title"], "DevOps Engineer")

    def test_filter_and_rank_jobs_has_required_fields(self):
        filtered = filter_and_rank_jobs([sample_job()])

        self.assertEqual(len(filtered), 1)
        self.assertIn("title", filtered[0])
        self.assertIn("company", filtered[0])
        self.assertIn("link", filtered[0])
        self.assertIn("confidence", filtered[0])

    def test_visa_sponsorship_detection_uses_description(self):
        self.assertTrue(has_visa_sponsorship(sample_job(description="H-1B sponsorship available.")))

    def test_security_clearance_jobs_are_excluded(self):
        jobs = filter_and_rank_jobs([
            sample_job(title="SRE", description="Active security clearance required."),
            sample_job(title="SRE", description="No clearance requirement mentioned."),
        ])

        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0]["company"], "Sponsor Corp")

    def test_security_clearance_detection(self):
        self.assertTrue(requires_security_clearance(sample_job(description="TS/SCI clearance required.")))
        self.assertFalse(requires_security_clearance(sample_job(description="No clearance requirement.")))

    def test_usa_location_does_not_match_inside_other_words(self):
        self.assertTrue(is_usa_location("Remote USA"))
        self.assertFalse(is_usa_location("Sydney, Australia"))

    def test_supported_portals_are_currently_implemented(self):
        self.assertEqual(
            SUPPORTED_PORTALS,
            ["linkedin", "indeed", "glassdoor", "builtin", "greenhouse", "lever", "workday"],
        )


class TestSearchApi(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_search_api_validates_custom_role_type(self):
        response = self.client.post("/api/search", json={"custom_role": 123, "portals": ["linkedin"]})

        self.assertEqual(response.status_code, 400)
        self.assertIn("custom_role", response.get_json()["error"])

    def test_search_api_validates_custom_role_length(self):
        response = self.client.post("/api/search", json={"custom_role": "x" * 81, "portals": ["linkedin"]})

        self.assertEqual(response.status_code, 400)

    def test_search_api_rejects_unsupported_portals(self):
        response = self.client.post("/api/search", json={"portals": ["linkedin", "monster"]})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["unsupported_portals"], ["monster"])

    def test_search_api_rejects_empty_portal_selection(self):
        response = self.client.post("/api/search", json={"portals": []})

        self.assertEqual(response.status_code, 400)
        self.assertIn("At least one", response.get_json()["error"])

    def test_search_api_calls_scraper_for_valid_request(self):
        with patch("app.run_full_search", return_value=[{"title": "DevOps Engineer"}]) as search:
            response = self.client.post("/api/search", json={"custom_role": " DevOps Engineer ", "portals": ["linkedin"]})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), [{"title": "DevOps Engineer"}])
        search.assert_called_once_with(custom_role="DevOps Engineer", portals=["linkedin"])


if __name__ == "__main__":
    unittest.main()
