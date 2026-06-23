# scraper_module.py
import datetime
import requests
from bs4 import BeautifulSoup
from typing import List, Dict
import re
from difflib import SequenceMatcher
import asyncio
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
import time

# Target roles for filtering
TARGET_ROLES = ['devops', 'sre', 'site reliability', 'cloud engineer', 'cloud operations', 
                'observability', 'infrastructure', 'platform engineer', 'kubernetes', 'docker',
                'aws', 'azure', 'gcp', 'terraform', 'ansible', 'ci/cd', 'jenkins', 'gitops']

# Skills for matching
SKILLS_KEYWORDS = ['python', 'golang', 'java', 'kubernetes', 'docker', 'aws', 'azure', 'gcp',
                   'terraform', 'ansible', 'jenkins', 'gitlab', 'ci/cd', 'prometheus', 'grafana',
                   'elk', 'elasticsearch', 'linux', 'shell', 'bash', 'networking', 'security']

# Visa sponsorship keywords
VISA_KEYWORDS = ['visa sponsorship', 'h1b', 'h-1b', 'sponsorship available', 
                 'relocation available', 'relocation package', 'global talent']

# Location keywords for USA
USA_KEYWORDS = ['united states', 'usa', 'us', 'america', 'remote - us', 'remote usa']

# User profile for matching (customize these based on your actual skills)
USER_PROFILE = {
    'skills': ['python', 'kubernetes', 'docker', 'aws', 'terraform', 'ansible', 'ci/cd', 'linux'],
    'experience_years': 5,
    'preferred_locations': ['remote', 'usa', 'united states'],
    'target_roles': ['devops', 'sre', 'site reliability', 'cloud engineer', 'platform engineer']
}

def fetch_indeed_jobs(query: str = "DevOps Engineer", location: str = "USA") -> List[Dict]:
    """Scrape jobs from Indeed"""
    jobs = []
    try:
        url = f"https://www.indeed.com/jobs?q={query}&l={location}&fromage=1"
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            job_cards = soup.find_all('div', class_='job_seen_beacon')
            
            for card in job_cards[:20]:  # Limit to first 20 jobs
                try:
                    title_elem = card.find('h2', class_='jobTitle')
                    company_elem = card.find('span', {'data-testid': 'company-name'})
                    location_elem = card.find('div', {'data-testid': 'text-location'})
                    link_elem = card.find('a', class_='jcs-JobTitle')
                    
                    if title_elem and company_elem:
                        title = title_elem.get_text(strip=True)
                        company = company_elem.get_text(strip=True)
                        location = location_elem.get_text(strip=True) if location_elem else "Unknown"
                        link = "https://www.indeed.com" + link_elem['href'] if link_elem else "#"
                        
                        jobs.append({
                            'title': title,
                            'company': company,
                            'location': location,
                            'url': link,
                            'posted_date': datetime.datetime.now(),
                            'source': 'Indeed'
                        })
                except Exception as e:
                    print(f"Error parsing job card: {e}")
                    continue
    except Exception as e:
        print(f"Error scraping Indeed: {e}")
    
    return jobs

def fetch_linkedin_jobs(query: str = "DevOps Engineer") -> List[Dict]:
    """Scrape jobs from LinkedIn (limited due to anti-scraping)"""
    jobs = []
    try:
        url = f"https://www.linkedin.com/jobs/search/?keywords={query}&location=United%20States&f_TPR=r86400"
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            job_cards = soup.find_all('div', class_='base-card')
            
            for card in job_cards[:20]:
                try:
                    title_elem = card.find('h3', class_='base-search-card__title')
                    company_elem = card.find('h4', class_='base-search-card__subtitle')
                    location_elem = card.find('span', class_='job-search-card__location')
                    link_elem = card.find('a', class_='base-card__full-link')
                    
                    if title_elem and company_elem:
                        title = title_elem.get_text(strip=True)
                        company = company_elem.get_text(strip=True).replace('Hiring', '').strip()
                        location = location_elem.get_text(strip=True) if location_elem else "Unknown"
                        link = link_elem['href'] if link_elem else "#"
                        
                        jobs.append({
                            'title': title,
                            'company': company,
                            'location': location,
                            'url': link,
                            'posted_date': datetime.datetime.now(),
                            'source': 'LinkedIn'
                        })
                except Exception as e:
                    print(f"Error parsing LinkedIn job card: {e}")
                    continue
    except Exception as e:
        print(f"Error scraping LinkedIn: {e}")
    
    return jobs

async def fetch_glassdoor_jobs_playwright(query: str = "DevOps Engineer", location: str = "USA") -> List[Dict]:
    """Scrape jobs from Glassdoor using Playwright for JavaScript-rendered content"""
    jobs = []
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            url = f"https://www.glassdoor.com/Job/{query.replace(' ', '-')}-jobs-SRCH_KO0,14.htm?location={location}"
            
            try:
                await page.goto(url, timeout=30000, wait_until='networkidle')
                await page.wait_for_timeout(3000)  # Wait for dynamic content
                
                # Try multiple selectors for Glassdoor
                job_selectors = [
                    'li.react-job-listing',
                    'div.jobCard',
                    '[data-test="job-tile"]',
                    'div[data-testid="job-tile"]'
                ]
                
                job_cards = []
                for selector in job_selectors:
                    try:
                        cards = await page.query_selector_all(selector)
                        if cards:
                            job_cards = cards
                            break
                    except:
                        continue
                
                for card in job_cards[:15]:
                    try:
                        # Try to extract job details
                        title_elem = await card.query_selector('a.jobLink, h2, h3, [data-test="job-title"]')
                        company_elem = await card.query_selector('span.css-2x5zq0, [data-test="company-name"]')
                        location_elem = await card.query_selector('span.css-1buaf54, [data-test="location"]')
                        
                        if title_elem:
                            title = await title_elem.inner_text()
                            company = await company_elem.inner_text() if company_elem else "Unknown"
                            job_location = await location_elem.inner_text() if location_elem else "Unknown"
                            
                            link_elem = await card.query_selector('a')
                            link = await link_elem.get_attribute('href') if link_elem else "#"
                            if link and not link.startswith('http'):
                                link = "https://www.glassdoor.com" + link
                            
                            jobs.append({
                                'title': title.strip(),
                                'company': company.strip(),
                                'location': job_location.strip(),
                                'url': link,
                                'posted_date': datetime.datetime.now(),
                                'source': 'Glassdoor'
                            })
                    except Exception as e:
                        print(f"Error parsing Glassdoor job card: {e}")
                        continue
                        
            except PlaywrightTimeoutError:
                print(f"Timeout loading Glassdoor page")
            except Exception as e:
                print(f"Error navigating to Glassdoor: {e}")
            finally:
                await browser.close()
                
    except Exception as e:
        print(f"Error in Glassdoor Playwright scraper: {e}")
    
    return jobs

async def fetch_builtin_jobs_playwright(query: str = "DevOps Engineer") -> List[Dict]:
    """Scrape jobs from BuiltIn using Playwright"""
    jobs = []
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            url = f"https://www.builtin.com/jobs?query={query.replace(' ', '%20')}"
            
            try:
                await page.goto(url, timeout=30000, wait_until='networkidle')
                await page.wait_for_timeout(3000)
                
                job_selectors = [
                    'div.job-item',
                    'div.job-card',
                    '[data-testid="job-card"]',
                    'article'
                ]
                
                job_cards = []
                for selector in job_selectors:
                    try:
                        cards = await page.query_selector_all(selector)
                        if cards:
                            job_cards = cards
                            break
                    except:
                        continue
                
                for card in job_cards[:15]:
                    try:
                        title_elem = await card.query_selector('h3.job-title, h2, h3, a')
                        company_elem = await card.query_selector('div.company-name, [data-testid="company"]')
                        location_elem = await card.query_selector('div.location, [data-testid="location"]')
                        
                        if title_elem:
                            title = await title_elem.inner_text()
                            company = await company_elem.inner_text() if company_elem else "Unknown"
                            job_location = await location_elem.inner_text() if location_elem else "Unknown"
                            
                            link_elem = await card.query_selector('a')
                            link = await link_elem.get_attribute('href') if link_elem else "#"
                            
                            jobs.append({
                                'title': title.strip(),
                                'company': company.strip(),
                                'location': job_location.strip(),
                                'url': link,
                                'posted_date': datetime.datetime.now(),
                                'source': 'BuiltIn'
                            })
                    except Exception as e:
                        print(f"Error parsing BuiltIn job card: {e}")
                        continue
                        
            except PlaywrightTimeoutError:
                print(f"Timeout loading BuiltIn page")
            except Exception as e:
                print(f"Error navigating to BuiltIn: {e}")
            finally:
                await browser.close()
                
    except Exception as e:
        print(f"Error in BuiltIn Playwright scraper: {e}")
    
    return jobs

async def fetch_greenhouse_jobs_playwright() -> List[Dict]:
    """Scrape jobs from Greenhouse using Playwright"""
    jobs = []
    companies = ['stripe', 'airbnb', 'doordash', 'instacart', 'shopify']
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            
            for comp in companies:
                try:
                    page = await browser.new_page()
                    url = f"https://boards.greenhouse.io/{comp}/jobs"
                    
                    try:
                        await page.goto(url, timeout=30000, wait_until='networkidle')
                        await page.wait_for_timeout(2000)
                        
                        job_selectors = [
                            'div.opening',
                            'a.opening',
                            '[data-testid="job-opening"]',
                            'li.opening'
                        ]
                        
                        job_cards = []
                        for selector in job_selectors:
                            try:
                                cards = await page.query_selector_all(selector)
                                if cards:
                                    job_cards = cards
                                    break
                            except:
                                continue
                        
                        for card in job_cards[:10]:
                            try:
                                title_elem = await card.query_selector('a')
                                if title_elem:
                                    title = await title_elem.inner_text()
                                    link = await title_elem.get_attribute('href')
                                    
                                    if link and not link.startswith('http'):
                                        link = f"https://boards.greenhouse.io{link}"
                                    
                                    if any(role.lower() in title.lower() for role in TARGET_ROLES):
                                        jobs.append({
                                            'title': title.strip(),
                                            'company': comp.capitalize(),
                                            'location': 'USA',
                                            'url': link,
                                            'posted_date': datetime.datetime.now(),
                                            'source': 'Greenhouse'
                                        })
                            except Exception as e:
                                print(f"Error parsing Greenhouse job card: {e}")
                                continue
                                
                    except PlaywrightTimeoutError:
                        print(f"Timeout loading Greenhouse for {comp}")
                    except Exception as e:
                        print(f"Error navigating to Greenhouse for {comp}: {e}")
                    finally:
                        await page.close()
                        
                except Exception as e:
                    print(f"Error processing {comp}: {e}")
                    continue
                    
            await browser.close()
            
    except Exception as e:
        print(f"Error in Greenhouse Playwright scraper: {e}")
    
    return jobs

async def fetch_lever_jobs_playwright() -> List[Dict]:
    """Scrape jobs from Lever using Playwright"""
    jobs = []
    companies = ['netflix', 'uber', 'lyft', 'spotify', 'slack']
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            
            for comp in companies:
                try:
                    page = await browser.new_page()
                    url = f"https://jobs.lever.co/{comp}"
                    
                    try:
                        await page.goto(url, timeout=30000, wait_until='networkidle')
                        await page.wait_for_timeout(2000)
                        
                        job_selectors = [
                            'div.posting',
                            'a.posting-title',
                            '[data-testid="posting"]',
                            'article'
                        ]
                        
                        job_cards = []
                        for selector in job_selectors:
                            try:
                                cards = await page.query_selector_all(selector)
                                if cards:
                                    job_cards = cards
                                    break
                            except:
                                continue
                        
                        for card in job_cards[:10]:
                            try:
                                title_elem = await card.query_selector('h5, a, h3')
                                link_elem = await card.query_selector('a')
                                
                                if title_elem and link_elem:
                                    title = await title_elem.inner_text()
                                    link = await link_elem.get_attribute('href')
                                    
                                    if any(role.lower() in title.lower() for role in TARGET_ROLES):
                                        jobs.append({
                                            'title': title.strip(),
                                            'company': comp.capitalize(),
                                            'location': 'USA',
                                            'url': link,
                                            'posted_date': datetime.datetime.now(),
                                            'source': 'Lever'
                                        })
                            except Exception as e:
                                print(f"Error parsing Lever job card: {e}")
                                continue
                                
                    except PlaywrightTimeoutError:
                        print(f"Timeout loading Lever for {comp}")
                    except Exception as e:
                        print(f"Error navigating to Lever for {comp}: {e}")
                    finally:
                        await page.close()
                        
                except Exception as e:
                    print(f"Error processing {comp}: {e}")
                    continue
                    
            await browser.close()
            
    except Exception as e:
        print(f"Error in Lever Playwright scraper: {e}")
    
    return jobs

async def fetch_workday_jobs_playwright() -> List[Dict]:
    """Scrape jobs from Workday companies using Playwright"""
    jobs = []
    
    # Major Workday companies
    companies = [
        {'name': 'Amazon', 'url': 'https://www.amazon.jobs/en/search?base_query=devops&location=usa'},
        {'name': 'Microsoft', 'url': 'https://careers.microsoft.com/professionals/us/en/search-results?keywords=devops'},
        {'name': 'Google', 'url': 'https://careers.google.com/jobs/results/?keyword=devops'},
    ]
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            
            for company in companies:
                try:
                    page = await browser.new_page()
                    
                    try:
                        await page.goto(company['url'], timeout=30000, wait_until='networkidle')
                        await page.wait_for_timeout(3000)
                        
                        job_selectors = [
                            'div.job-item',
                            'li.job-tile',
                            'div.job-tile',
                            '[data-automation="job-tile"]',
                            'a.job-title-link',
                            'h3.job-title'
                        ]
                        
                        job_cards = []
                        for selector in job_selectors:
                            try:
                                cards = await page.query_selector_all(selector)
                                if cards:
                                    job_cards = cards
                                    break
                            except:
                                continue
                        
                        for card in job_cards[:10]:
                            try:
                                title_elem = await card.query_selector('h2, h3, h4, a')
                                if not title_elem:
                                    title_elem = await card.query_selector('a')
                                
                                if title_elem:
                                    title = await title_elem.inner_text()
                                    link = await title_elem.get_attribute('href')
                                    
                                    if link and not link.startswith('http'):
                                        if link.startswith('/'):
                                            link = f"https://{company['url'].split('/')[2]}{link}"
                                        else:
                                            link = f"{company['url']}/{link}"
                                    
                                    if any(role.lower() in title.lower() for role in TARGET_ROLES):
                                        location_elem = await card.query_selector('span, div, p')
                                        location = await location_elem.inner_text() if location_elem else "USA"
                                        
                                        jobs.append({
                                            'title': title.strip(),
                                            'company': company['name'],
                                            'location': location.strip(),
                                            'url': link,
                                            'posted_date': datetime.datetime.now(),
                                            'source': 'Workday'
                                        })
                            except Exception as e:
                                print(f"Error parsing Workday job card: {e}")
                                continue
                                
                    except PlaywrightTimeoutError:
                        print(f"Timeout loading {company['name']}")
                    except Exception as e:
                        print(f"Error navigating to {company['name']}: {e}")
                    finally:
                        await page.close()
                        
                except Exception as e:
                    print(f"Error processing {company['name']}: {e}")
                    continue
                    
            await browser.close()
            
    except Exception as e:
        print(f"Error in Workday Playwright scraper: {e}")
    
    return jobs

async def fetch_raw_jobs_async() -> List[Dict]:
    """
    Fetch jobs from multiple job portals using Playwright for JavaScript-rendered sites
    Returns a list of raw job postings from the last 24 hours
    """
    print("Scraping job sites for new jobs...")
    all_jobs = []
    
    # Scrape from LinkedIn (still using requests - works well)
    print("Fetching from LinkedIn...")
    try:
        linkedin_jobs = fetch_linkedin_jobs("DevOps Engineer")
        all_jobs.extend(linkedin_jobs)
        print(f"LinkedIn: {len(linkedin_jobs)} jobs")
    except Exception as e:
        print(f"Error fetching LinkedIn: {e}")
    
    # Scrape from Playwright-based scrapers
    print("Fetching from Glassdoor (Playwright)...")
    try:
        glassdoor_jobs = await fetch_glassdoor_jobs_playwright("SRE", "USA")
        all_jobs.extend(glassdoor_jobs)
        print(f"Glassdoor: {len(glassdoor_jobs)} jobs")
    except Exception as e:
        print(f"Error fetching Glassdoor: {e}")
    
    print("Fetching from BuiltIn (Playwright)...")
    try:
        builtin_jobs = await fetch_builtin_jobs_playwright("Cloud Engineer")
        all_jobs.extend(builtin_jobs)
        print(f"BuiltIn: {len(builtin_jobs)} jobs")
    except Exception as e:
        print(f"Error fetching BuiltIn: {e}")
    
    print("Fetching from Greenhouse (Playwright)...")
    try:
        greenhouse_jobs = await fetch_greenhouse_jobs_playwright()
        all_jobs.extend(greenhouse_jobs)
        print(f"Greenhouse: {len(greenhouse_jobs)} jobs")
    except Exception as e:
        print(f"Error fetching Greenhouse: {e}")
    
    print("Fetching from Lever (Playwright)...")
    try:
        lever_jobs = await fetch_lever_jobs_playwright()
        all_jobs.extend(lever_jobs)
        print(f"Lever: {len(lever_jobs)} jobs")
    except Exception as e:
        print(f"Error fetching Lever: {e}")
    
    print("Fetching from Workday (Playwright)...")
    try:
        workday_jobs = await fetch_workday_jobs_playwright()
        all_jobs.extend(workday_jobs)
        print(f"Workday: {len(workday_jobs)} jobs")
    except Exception as e:
        print(f"Error fetching Workday: {e}")
    
    print(f"Total jobs fetched: {len(all_jobs)}")
    return all_jobs

def fetch_raw_jobs() -> List[Dict]:
    """
    Synchronous wrapper for async fetch_raw_jobs_async
    Fetch jobs from multiple job portals
    Returns a list of raw job postings from the last 24 hours
    """
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    try:
        jobs = loop.run_until_complete(fetch_raw_jobs_async())
        return jobs
    except Exception as e:
        print(f"Error in async job fetching: {e}")
        # Fallback to LinkedIn only if async fails
        print("Falling back to LinkedIn only...")
        return fetch_linkedin_jobs("DevOps Engineer")

def is_target_role(title: str) -> bool:
    """Check if job title matches target roles"""
    title_lower = title.lower()
    return any(role in title_lower for role in TARGET_ROLES)

def is_usa_location(location: str) -> bool:
    """Check if location is in USA"""
    location_lower = location.lower()
    return any(keyword in location_lower for keyword in USA_KEYWORDS) or 'remote' in location_lower

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
    # Check company name
    company_lower = job.get('company', '').lower()
    title_lower = job.get('title', '').lower()
    
    # Check if any visa keywords are present
    combined_text = company_lower + " " + title_lower
    return any(keyword in combined_text for keyword in VISA_KEYWORDS)

def filter_and_rank_jobs(raw_jobs: List[Dict]) -> List[Dict]:
    """
    Filter jobs based on criteria:
    - Target roles: DevOps, SRE, Cloud, Observability
    - Location: USA
    - Timeframe: Last 24 hours
    - Visa sponsorship signal
    - No security clearance required
    - Calculate match percentage
    """
    filtered_results = []
    now = datetime.datetime.now()
    
    for job in raw_jobs:
        # Check if job is from last 24 hours
        if 'posted_date' in job:
            job_age = now - job['posted_date']
            if job_age > datetime.timedelta(hours=24):
                continue
        
        # Check if it's a target role
        if not is_target_role(job.get('title', '')):
            continue
        
        # Check if it's USA location
        if not is_usa_location(job.get('location', '')):
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

def run_full_search() -> List[Dict]:
    """Combines fetching and filtering into one function"""
    raw = fetch_raw_jobs()
    return filter_and_rank_jobs(raw)

# End of scraper_module.py
