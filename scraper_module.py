# scraper_module.py
import asyncio
import datetime
import re
from typing import Dict, List

from src.job_config import (
    SECURITY_CLEARANCE_KEYWORDS,
    SUPPORTED_PORTALS,
    TARGET_ROLES,
    USER_PROFILE,
    USA_KEYWORDS,
    VISA_KEYWORDS,
)
from src.portal_browser_a import (
    fetch_builtin_jobs_playwright,
    fetch_glassdoor_jobs_playwright,
    fetch_indeed_jobs_playwright,
    fetch_linkedin_jobs,
    fetch_linkedin_jobs_playwright,
)
from src.portal_browser_b import (
    fetch_greenhouse_jobs_playwright,
    fetch_lever_jobs_playwright,
    fetch_workday_jobs_playwright,
)
from src.portal_requests import fetch_indeed_jobs


async def fetch_raw_jobs_async(custom_role: str = None, portals: List[str] = None) -> List[Dict]:
    """
    Fetch jobs from multiple job portals using Playwright for JavaScript-rendered sites
    Returns a list of raw job postings from the last 24 hours
    
    Args:
        custom_role: Optional custom role to search for (e.g., "Software Engineer")
        portals: Optional list of portals to scrape (e.g., ['linkedin', 'indeed', 'glassdoor'])
    """
    print("Scraping job sites for new jobs...")
    all_jobs = []
    
    # Use custom role if provided, otherwise default to DevOps Engineer
    search_role = custom_role if custom_role else "DevOps Engineer"
    print(f"Searching for role: {search_role}")
    
    # Default to implemented portals if none specified.
    if portals is None:
        portals = SUPPORTED_PORTALS.copy()
    
    print(f"Selected portals: {', '.join(portals)}")
    
    # Scrape from LinkedIn using requests (Playwright gets blocked)
    if 'linkedin' in portals:
        print("Fetching from LinkedIn...")
        try:
            linkedin_jobs = fetch_linkedin_jobs(search_role)
            all_jobs.extend(linkedin_jobs)
            print(f"LinkedIn: {len(linkedin_jobs)} jobs")
        except Exception as e:
            print(f"Error fetching LinkedIn: {e}")
    
    # Scrape from Indeed using requests (Playwright times out)
    if 'indeed' in portals:
        print("Fetching from Indeed (requests)...")
        try:
            indeed_jobs = fetch_indeed_jobs(search_role, "USA")
            all_jobs.extend(indeed_jobs)
            print(f"Indeed: {len(indeed_jobs)} jobs")
        except Exception as e:
            print(f"Error fetching Indeed: {e}")
    
    # Scrape from Glassdoor with timeout
    if 'glassdoor' in portals:
        print("Fetching from Glassdoor (Playwright)...")
        try:
            glassdoor_jobs = await asyncio.wait_for(fetch_glassdoor_jobs_playwright(search_role, "USA"), timeout=20)
            all_jobs.extend(glassdoor_jobs)
            print(f"Glassdoor: {len(glassdoor_jobs)} jobs")
        except asyncio.TimeoutError:
            print("Glassdoor: Timeout - skipping")
        except Exception as e:
            print(f"Error fetching Glassdoor: {e}")
    
    # Scrape from BuiltIn with timeout
    if 'builtin' in portals:
        print("Fetching from BuiltIn (Playwright)...")
        try:
            builtin_jobs = await asyncio.wait_for(fetch_builtin_jobs_playwright(search_role), timeout=20)
            all_jobs.extend(builtin_jobs)
            print(f"BuiltIn: {len(builtin_jobs)} jobs")
        except asyncio.TimeoutError:
            print("BuiltIn: Timeout - skipping")
        except Exception as e:
            print(f"Error fetching BuiltIn: {e}")
    
    # Scrape from Greenhouse with timeout
    if 'greenhouse' in portals:
        print("Fetching from Greenhouse (Playwright)...")
        try:
            greenhouse_jobs = await asyncio.wait_for(fetch_greenhouse_jobs_playwright(custom_role=search_role), timeout=20)
            all_jobs.extend(greenhouse_jobs)
            print(f"Greenhouse: {len(greenhouse_jobs)} jobs")
        except asyncio.TimeoutError:
            print("Greenhouse: Timeout - skipping")
        except Exception as e:
            print(f"Error fetching Greenhouse: {e}")
    
    # Scrape from Lever with timeout
    if 'lever' in portals:
        print("Fetching from Lever (Playwright)...")
        try:
            lever_jobs = await asyncio.wait_for(fetch_lever_jobs_playwright(custom_role=search_role), timeout=20)
            all_jobs.extend(lever_jobs)
            print(f"Lever: {len(lever_jobs)} jobs")
        except asyncio.TimeoutError:
            print("Lever: Timeout - skipping")
        except Exception as e:
            print(f"Error fetching Lever: {e}")
    
    # Scrape from Workday with timeout (increased)
    if 'workday' in portals:
        print("Fetching from Workday (Playwright)...")
        try:
            workday_jobs = await asyncio.wait_for(fetch_workday_jobs_playwright(custom_role=search_role), timeout=35)
            all_jobs.extend(workday_jobs)
            print(f"Workday: {len(workday_jobs)} jobs")
        except asyncio.TimeoutError:
            print("Workday: Timeout - skipping")
        except Exception as e:
            print(f"Error fetching Workday: {e}")
    
    print(f"Total jobs fetched: {len(all_jobs)}")
    return all_jobs

def fetch_raw_jobs(custom_role: str = None, portals: List[str] = None) -> List[Dict]:
    """
    Synchronous wrapper for async fetch_raw_jobs_async
    Fetch jobs from multiple job portals
    Returns a list of raw job postings from the last 24 hours
    
    Args:
        custom_role: Optional custom role to search for (e.g., "Software Engineer")
        portals: Optional list of portals to scrape (e.g., ['linkedin', 'indeed', 'glassdoor'])
    """
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    try:
        jobs = loop.run_until_complete(fetch_raw_jobs_async(custom_role=custom_role, portals=portals))
        return jobs
    except Exception as e:
        print(f"Error in async job fetching: {e}")
        # Fallback to LinkedIn only if async fails
        print("Falling back to LinkedIn only...")
        search_role = custom_role if custom_role else "DevOps Engineer"
        return fetch_linkedin_jobs(search_role)

def is_target_role(title: str) -> bool:
    """Check if job title matches target roles"""
    title_lower = title.lower()
    return any(role in title_lower for role in TARGET_ROLES)

def is_usa_location(location: str) -> bool:
    """Check if location is in USA"""
    location_lower = location.lower()
    if 'remote' in location_lower:
        return True
    return any(re.search(rf'\b{re.escape(keyword)}\b', location_lower) for keyword in USA_KEYWORDS)

def calculate_match_percentage(job: Dict) -> float:
    """
    Calculate match percentage based on:
    - Skills match (40%)
    - Role match (30%)
    - Location match (20%)
    - Visa sponsorship (10%)
    """
    match_score = 0.0
    
    # Skills match (40%)
    job_text = f"{job.get('title', '')} {job.get('company', '')}".lower()
    matched_skills = 0
    for skill in USER_PROFILE['skills']:
        if skill in job_text:
            matched_skills += 1
    skills_percentage = (matched_skills / len(USER_PROFILE['skills'])) * 40
    match_score += skills_percentage
    
    # Role match (30%)
    title_lower = job.get('title', '').lower()
    role_match = any(role in title_lower for role in USER_PROFILE['target_roles'])
    if role_match:
        match_score += 30
    
    # Location match (20%)
    location_lower = job.get('location', '').lower()
    location_match = any(loc in location_lower for loc in USER_PROFILE['preferred_locations'])
    if location_match:
        match_score += 20
    
    # Visa sponsorship (10%)
    if has_visa_sponsorship(job):
        match_score += 10
    
    return round(match_score, 1)

def has_visa_sponsorship(job: Dict) -> bool:
    """Detect visa sponsorship signals in job description or company"""
    company_lower = job.get('company', '').lower()
    title_lower = job.get('title', '').lower()
    description_lower = job.get('description', '').lower()
    
    combined_text = f"{company_lower} {title_lower} {description_lower}"
    return any(keyword in combined_text for keyword in VISA_KEYWORDS)

def requires_security_clearance(job: Dict) -> bool:
    """Detect roles that likely require a security clearance."""
    combined_text = " ".join([
        job.get('title', ''),
        job.get('company', ''),
        job.get('description', '')
    ]).lower()
    return any(keyword in combined_text for keyword in SECURITY_CLEARANCE_KEYWORDS)

def filter_and_rank_jobs(raw_jobs: List[Dict], custom_role: str = None) -> List[Dict]:
    """
    Filter jobs based on criteria:
    - Target roles: DevOps, SRE, Cloud, Observability (or custom role if provided)
    - Location: USA
    - Timeframe: Last 24 hours
    - Visa sponsorship signal boosts ranking
    - No security clearance required
    - Calculate match percentage
    
    Args:
        custom_role: Optional custom role to search for (e.g., "Software Engineer")
    """
    filtered_results = []
    now = datetime.datetime.now()
    
    for job in raw_jobs:
        # Check if job is from last 24 hours
        if 'posted_date' in job:
            job_age = now - job['posted_date']
            if job_age > datetime.timedelta(hours=24):
                continue
        
        # Check if it's a target role (or custom role if provided)
        if custom_role:
            # For custom role, check if the custom role is in the title
            if custom_role.lower() not in job.get('title', '').lower():
                continue
        else:
            # Use default target roles
            if not is_target_role(job.get('title', '')):
                continue
        
        # Check if it's USA location
        if not is_usa_location(job.get('location', '')):
            continue

        if requires_security_clearance(job):
            continue
        
        # Calculate match percentage
        match_percentage = calculate_match_percentage(job)
        
        # Calculate confidence based on match percentage
        if match_percentage >= 70:
            confidence = "High Confidence"
        elif match_percentage >= 50:
            confidence = "Medium Confidence"
        else:
            confidence = "Low Confidence"
        
        filtered_results.append({
            "title": job.get('title', ''),
            "company": job.get('company', ''),
            "location": job.get('location', ''),
            "link": job.get('url', '#'),
            "confidence": confidence,
            "match_percentage": match_percentage,
            "source": job.get('source', 'Unknown'),
            "posted_date": job.get('posted_date', datetime.datetime.now()).strftime('%Y-%m-%d %H:%M')
        })
    
    # Sort by match percentage (highest first)
    filtered_results.sort(key=lambda x: x['match_percentage'], reverse=True)
    
    print(f"Filtered jobs matching criteria: {len(filtered_results)}")
    return filtered_results

def run_full_search(custom_role: str = None, portals: List[str] = None) -> List[Dict]:
    """Combines fetching and filtering into one function
    
    Args:
        custom_role: Optional custom role to search for (e.g., "Software Engineer")
        portals: Optional list of portals to scrape (e.g., ['linkedin', 'indeed', 'glassdoor'])
    """
    raw = fetch_raw_jobs(custom_role=custom_role, portals=portals)
    return filter_and_rank_jobs(raw, custom_role=custom_role)

# End of scraper_module.py
