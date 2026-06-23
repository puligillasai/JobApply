# test_scraper.py - TDD tests for job scraper
import unittest
from datetime import datetime, timedelta
from scraper_module import fetch_raw_jobs, filter_and_rank_jobs, run_full_search

class TestJobScraper(unittest.TestCase):
    
    def test_fetch_raw_jobs_returns_list(self):
        """Test that fetch_raw_jobs returns a list"""
        jobs = fetch_raw_jobs()
        self.assertIsInstance(jobs, list)
    
    def test_fetch_raw_jobs_has_required_fields(self):
        """Test that jobs have required fields: title, company, url, posted_date"""
        jobs = fetch_raw_jobs()
        if jobs:
            job = jobs[0]
            self.assertIn('title', job)
            self.assertIn('company', job)
            self.assertIn('url', job)
            self.assertIn('posted_date', job)
    
    def test_filter_and_rank_jobs_returns_list(self):
        """Test that filter_and_rank_jobs returns a list"""
        raw_jobs = [
            {"title": "DevOps Engineer", "company": "Sponsor Corp", "url": "#", "posted_date": datetime.now()}
        ]
        filtered = filter_and_rank_jobs(raw_jobs)
        self.assertIsInstance(filtered, list)
    
    def test_filter_and_rank_jobs_has_required_fields(self):
        """Test that filtered jobs have required fields: title, company, link, confidence"""
        raw_jobs = [
            {"title": "DevOps Engineer", "company": "Sponsor Corp", "url": "#", "posted_date": datetime.now()}
        ]
        filtered = filter_and_rank_jobs(raw_jobs)
        if filtered:
            job = filtered[0]
            self.assertIn('title', job)
            self.assertIn('company', job)
            self.assertIn('link', job)
            self.assertIn('confidence', job)
    
    def test_jobs_are_recent(self):
        """Test that jobs are from the last 24 hours"""
        jobs = fetch_raw_jobs()
        now = datetime.now()
        for job in jobs:
            if 'posted_date' in job:
                job_age = now - job['posted_date']
                self.assertLess(job_age, timedelta(hours=24), 
                              f"Job {job.get('title')} is older than 24 hours")
    
    def test_jobs_are_usa_location(self):
        """Test that jobs are from USA locations"""
        jobs = fetch_raw_jobs()
        for job in jobs:
            if 'location' in job:
                self.assertIn('USA', job['location'], 
                            f"Job {job.get('title')} is not from USA")
    
    def test_visa_sponsorship_detection(self):
        """Test that visa sponsorship is properly detected"""
        jobs = filter_and_rank_jobs([
            {"title": "SRE", "company": "Visa Sponsor Inc", "url": "#", "posted_date": datetime.now()}
        ])
        self.assertGreater(len(jobs), 0, "Visa sponsorship jobs should be detected")

if __name__ == '__main__':
    unittest.main()
