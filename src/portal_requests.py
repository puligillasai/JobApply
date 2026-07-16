# Request-based portal scrapers
import datetime
from typing import Dict, List

import requests
from bs4 import BeautifulSoup


def fetch_indeed_jobs(query: str = "DevOps Engineer", location: str = "USA") -> List[Dict]:
    """Scrape jobs from Indeed using multiple selectors and URLs"""
    jobs = []
    try:
        # Try multiple Indeed URLs for better coverage
        urls = [
            f"https://www.indeed.com/jobs?q={query}&l={location}&fromage=1",
            f"https://www.indeed.com/jobs?q={query}&l={location}&fromage=7",
            f"https://www.indeed.com/jobs?q={query}&l={location}"
        ]
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive'
        }
        
        for url in urls:
            try:
                response = requests.get(url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Try multiple selectors for job cards
                    job_selectors = [
                        ('div', 'job_seen_beacon'),
                        ('div', 'jobCard'),
                        ('div', 'slider_item'),
                        ('li', 'css-1x7z1ps')
                    ]
                    
                    job_cards = []
                    for tag, class_name in job_selectors:
                        cards = soup.find_all(tag, class_=class_name)
                        if cards:
                            job_cards = cards
                            print(f"Indeed: Found {len(job_cards)} cards with {tag}.{class_name}")
                            break
                    
                    for card in job_cards[:50]:  # Increased limit
                        try:
                            # Try multiple selectors for job details
                            title_elem = card.find('h2', class_='jobTitle') or card.find('h2') or card.find('span', {'title': True})
                            company_elem = card.find('span', {'data-testid': 'company-name'}) or card.find('span', class_='companyName')
                            location_elem = card.find('div', {'data-testid': 'text-location'}) or card.find('div', class_='companyLocation')
                            link_elem = card.find('a', class_='jcs-JobTitle') or card.find('a', href=True)
                            
                            if title_elem:
                                title = title_elem.get_text(strip=True) if hasattr(title_elem, 'get_text') else title_elem.get('title', '')
                                company = company_elem.get_text(strip=True) if company_elem else "Unknown"
                                location = location_elem.get_text(strip=True) if location_elem else "Unknown"
                                link = link_elem['href'] if link_elem else "#"
                                
                                # Ensure link is absolute
                                if link and not link.startswith('http'):
                                    if link.startswith('/'):
                                        link = "https://www.indeed.com" + link
                                    else:
                                        link = "https://www.indeed.com/" + link
                                
                                # Avoid duplicates
                                if not any(job['title'] == title and job['company'] == company for job in jobs):
                                    jobs.append({
                                        'title': title,
                                        'company': company,
                                        'location': location,
                                        'url': link,
                                        'posted_date': datetime.datetime.now(),
                                        'source': 'Indeed'
                                    })
                        except Exception as e:
                            print(f"Error parsing Indeed job card: {e}")
                            continue
            except Exception as e:
                print(f"Error fetching Indeed from {url}: {e}")
                continue
                
    except Exception as e:
        print(f"Error scraping Indeed: {e}")
    
    print(f"Indeed: Total {len(jobs)} unique jobs")
    return jobs

