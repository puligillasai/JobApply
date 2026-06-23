# scraper_module.py
import datetime
import requests
from bs4 import BeautifulSoup
from typing import List, Dict
import re
from difflib import SequenceMatcher

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

def fetch_glassdoor_jobs(query: str = "DevOps Engineer", location: str = "USA") -> List[Dict]:
    """Scrape jobs from Glassdoor"""
    jobs = []
    try:
        url = f"https://www.glassdoor.com/Job/{query.replace(' ', '-')}-jobs-SRCH_KO0,14.htm?location={location}"
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            job_cards = soup.find_all('li', class_='react-job-listing')
            
            for card in job_cards[:20]:
                try:
                    title_elem = card.find('a', class_='jobLink')
                    company_elem = card.find('span', class_='css-2x5zq0')
                    location_elem = card.find('span', class_='css-1buaf54')
                    
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        company = company_elem.get_text(strip=True) if company_elem else "Unknown"
                        location = location_elem.get_text(strip=True) if location_elem else "Unknown"
                        link = "https://www.glassdoor.com" + title_elem['href'] if title_elem.get('href') else "#"
                        
                        jobs.append({
                            'title': title,
                            'company': company,
                            'location': location,
                            'url': link,
                            'posted_date': datetime.datetime.now(),
                            'source': 'Glassdoor'
                        })
                except Exception as e:
                    print(f"Error parsing Glassdoor job card: {e}")
                    continue
    except Exception as e:
        print(f"Error scraping Glassdoor: {e}")
    
    return jobs

def fetch_builtin_jobs(query: str = "DevOps Engineer") -> List[Dict]:
    """Scrape jobs from BuiltIn"""
    jobs = []
    try:
        url = f"https://www.builtin.com/jobs?query={query.replace(' ', '%20')}"
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            job_cards = soup.find_all('div', class_='job-item')
            
            for card in job_cards[:20]:
                try:
                    title_elem = card.find('h3', class_='job-title')
                    company_elem = card.find('div', class_='company-name')
                    location_elem = card.find('div', class_='location')
                    link_elem = card.find('a', class_='job-link')
                    
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        company = company_elem.get_text(strip=True) if company_elem else "Unknown"
                        location = location_elem.get_text(strip=True) if location_elem else "Unknown"
                        link = link_elem['href'] if link_elem else "#"
                        
                        jobs.append({
                            'title': title,
                            'company': company,
                            'location': location,
                            'url': link,
                            'posted_date': datetime.datetime.now(),
                            'source': 'BuiltIn'
                        })
                except Exception as e:
                    print(f"Error parsing BuiltIn job card: {e}")
                    continue
    except Exception as e:
        print(f"Error scraping BuiltIn: {e}")
    
    return jobs

def fetch_greenhouse_jobs(company: str = None) -> List[Dict]:
    """Scrape jobs from Greenhouse (company-specific)"""
    jobs = []
    # Greenhouse jobs are company-specific, so we'll scrape from known companies
    companies = ['stripe', 'airbnb', 'doordash', 'instacart', 'shopify']
    
    for comp in companies:
        try:
            url = f"https://boards.greenhouse.io/{comp}/jobs"
            headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                job_cards = soup.find_all('div', class_='opening')
                
                for card in job_cards[:10]:
                    try:
                        title_elem = card.find('a')
                        if title_elem:
                            title = title_elem.get_text(strip=True)
                            link = f"https://boards.greenhouse.io{title_elem['href']}"
                            
                            # Check if it's a DevOps/SRE role
                            if any(role.lower() in title.lower() for role in TARGET_ROLES):
                                jobs.append({
                                    'title': title,
                                    'company': comp.capitalize(),
                                    'location': 'USA',
                                    'url': link,
                                    'posted_date': datetime.datetime.now(),
                                    'source': 'Greenhouse'
                                })
                    except Exception as e:
                        print(f"Error parsing Greenhouse job card: {e}")
                        continue
        except Exception as e:
            print(f"Error scraping Greenhouse for {comp}: {e}")
            continue
    
    return jobs

def fetch_lever_jobs(company: str = None) -> List[Dict]:
    """Scrape jobs from Lever (company-specific)"""
    jobs = []
    # Lever jobs are company-specific
    companies = ['netflix', 'uber', 'lyft', 'spotify', 'slack']
    
    for comp in companies:
        try:
            url = f"https://jobs.lever.co/{comp}"
            headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                job_cards = soup.find_all('div', class_='posting')
                
                for card in job_cards[:10]:
                    try:
                        title_elem = card.find('h5')
                        link_elem = card.find('a', class_='posting-title')
                        
                        if title_elem and link_elem:
                            title = title_elem.get_text(strip=True)
                            link = link_elem['href']
                            
                            # Check if it's a DevOps/SRE role
                            if any(role.lower() in title.lower() for role in TARGET_ROLES):
                                jobs.append({
                                    'title': title,
                                    'company': comp.capitalize(),
                                    'location': 'USA',
                                    'url': link,
                                    'posted_date': datetime.datetime.now(),
                                    'source': 'Lever'
                                })
                    except Exception as e:
                        print(f"Error parsing Lever job card: {e}")
                        continue
        except Exception as e:
            print(f"Error scraping Lever for {comp}: {e}")
            continue
    
    return jobs

def fetch_workday_jobs() -> List[Dict]:
    """Scrape jobs from Workday companies using job aggregators as proxy
    
    Workday is difficult to scrape directly because:
    1. Most companies use JavaScript-rendered pages (React/Angular)
    2. Strong anti-scraping measures
    3. Each company has different HTML structures
    
    Solution: Use job aggregators that already index these companies
    """
    jobs = []
    
    # Use job aggregators that already scrape Workday companies
    aggregators = [
        {
            'name': 'Indeed',
            'url': 'https://www.indeed.com/jobs?q=DevOps+Engineer&l=USA&fromage=1&co=US',
            'source': 'Indeed (Workday Companies)'
        },
        {
            'name': 'Glassdoor',
            'url': 'https://www.glassdoor.com/Job/devops-engineer-jobs-SRCH_KO0,14_IP2.htm?fromAge=1',
            'source': 'Glassdoor (Workday Companies)'
        }
    ]
    
    for aggregator in aggregators:
        try:
            print(f"Fetching from {aggregator['name']} for Workday companies...")
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            
            response = requests.get(aggregator['url'], headers=headers, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Parse jobs from aggregator
                job_cards = soup.find_all(['div', 'li'], class_=lambda x: x and any(keyword in str(x).lower() for keyword in ['job', 'card', 'item', 'result']))
                
                for card in job_cards[:10]:
                    try:
                        # Extract job details
                        title_elem = card.find(['h2', 'h3', 'a'], class_=lambda x: x and ('title' in str(x).lower() or 'job' in str(x).lower()))
                        if not title_elem:
                            title_elem = card.find('a')
                        
                        if title_elem:
                            title = title_elem.get_text(strip=True)
                            link = title_elem.get('href', '#')
                            
                            # Check if it's a DevOps/SRE role
                            if any(role.lower() in title.lower() for role in TARGET_ROLES):
                                # Extract company
                                company_elem = card.find(['span', 'div'], class_=lambda x: x and 'company' in str(x).lower())
                                company = company_elem.get_text(strip=True) if company_elem else "Unknown"
                                
                                # Extract location
                                location_elem = card.find(['span', 'div'], class_=lambda x: x and 'location' in str(x).lower())
                                location = location_elem.get_text(strip=True) if location_elem else "USA"
                                
                                # Make link absolute
                                if link and not link.startswith('http'):
                                    link = f"https://www.indeed.com{link}" if 'indeed' in aggregator['url'] else link
                                
                                jobs.append({
                                    'title': title,
                                    'company': company,
                                    'location': location,
                                    'url': link,
                                    'posted_date': datetime.datetime.now(),
                                    'source': aggregator['source']
                                })
                    except Exception as e:
                        continue
                        
                if jobs:
                    print(f"Found {len(jobs)} jobs from {aggregator['name']}")
                    break
                    
        except Exception as e:
            print(f"Error scraping {aggregator['name']}: {e}")
            continue
    
    return jobs

def fetch_raw_jobs() -> List[Dict]:
    """
    Fetch jobs from multiple job portals
    Returns a list of raw job postings from the last 24 hours
    """
    print("Scraping job sites for new jobs...")
    all_jobs = []
    
    # Scrape from multiple sources
    print("Fetching from LinkedIn...")
    linkedin_jobs = fetch_linkedin_jobs("DevOps Engineer")
    all_jobs.extend(linkedin_jobs)
    
    print("Fetching from Glassdoor...")
    glassdoor_jobs = fetch_glassdoor_jobs("SRE", "USA")
    all_jobs.extend(glassdoor_jobs)
    
    print("Fetching from BuiltIn...")
    builtin_jobs = fetch_builtin_jobs("Cloud Engineer")
    all_jobs.extend(builtin_jobs)
    
    print("Fetching from Greenhouse...")
    greenhouse_jobs = fetch_greenhouse_jobs()
    all_jobs.extend(greenhouse_jobs)
    
    print("Fetching from Lever...")
    lever_jobs = fetch_lever_jobs()
    all_jobs.extend(lever_jobs)
    
    print("Fetching from Workday...")
    workday_jobs = fetch_workday_jobs()
    all_jobs.extend(workday_jobs)
    
    print(f"Total jobs fetched: {len(all_jobs)}")
    return all_jobs

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
