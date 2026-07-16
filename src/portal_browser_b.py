# Company-board browser scrapers
import datetime
from typing import Dict, List

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

from src.job_config import TARGET_ROLES


async def fetch_greenhouse_jobs_playwright(custom_role: str = None) -> List[Dict]:
    """Scrape jobs from Greenhouse using Playwright
    
    Args:
        custom_role: Optional custom role to search for (e.g., "Software Engineer")
    """
    jobs = []
    companies = ['stripe', 'airbnb', 'doordash', 'instacart', 'shopify']
    
    # Use custom role if provided for filtering
    search_role = custom_role if custom_role else None
    
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
                            except Exception:
                                continue
                        
                        for card in job_cards[:10]:
                            try:
                                title_elem = await card.query_selector('a')
                                if title_elem:
                                    title = await title_elem.inner_text()
                                    link = await title_elem.get_attribute('href')
                                    
                                    if link and not link.startswith('http'):
                                        link = f"https://boards.greenhouse.io{link}"
                                    
                                    # Filter by custom role if provided, otherwise use TARGET_ROLES
                                    if search_role:
                                        if search_role.lower() in title.lower():
                                            jobs.append({
                                                'title': title.strip(),
                                                'company': comp.capitalize(),
                                                'location': 'USA',
                                                'url': link,
                                                'posted_date': datetime.datetime.now(),
                                                'source': 'Greenhouse'
                                            })
                                    else:
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

async def fetch_lever_jobs_playwright(custom_role: str = None) -> List[Dict]:
    """Scrape jobs from Lever using Playwright
    
    Args:
        custom_role: Optional custom role to search for (e.g., "Software Engineer")
    """
    jobs = []
    companies = ['netflix', 'uber', 'lyft', 'spotify', 'slack']
    
    # Use custom role if provided for filtering
    search_role = custom_role if custom_role else None
    
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
                            except Exception:
                                continue
                        
                        for card in job_cards[:10]:
                            try:
                                title_elem = await card.query_selector('h5, a, h3')
                                link_elem = await card.query_selector('a')
                                
                                if title_elem and link_elem:
                                    title = await title_elem.inner_text()
                                    link = await link_elem.get_attribute('href')
                                    
                                    # Filter by custom role if provided, otherwise use TARGET_ROLES
                                    if search_role:
                                        if search_role.lower() in title.lower():
                                            jobs.append({
                                                'title': title.strip(),
                                                'company': comp.capitalize(),
                                                'location': 'USA',
                                                'url': link,
                                                'posted_date': datetime.datetime.now(),
                                                'source': 'Lever'
                                            })
                                    else:
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

async def fetch_workday_jobs_playwright(custom_role: str = None) -> List[Dict]:
    """Scrape jobs from Workday companies using Playwright
    
    Args:
        custom_role: Optional custom role to search for (e.g., "Software Engineer")
    """
    jobs = []
    
    # Use custom role if provided, otherwise default to devops
    search_role = custom_role if custom_role else "devops"
    
    # Simplified Workday companies list to avoid timeouts
    companies = [
        {'name': 'Amazon', 'url': f'https://www.amazon.jobs/en/search?base_query={search_role}&location=usa'},
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
                            except Exception:
                                continue
                        
                        for card in job_cards[:10]:
                            try:
                                title_elem = await card.query_selector('h2, h3, h4, a')
                                if not title_elem:
                                    title_elem = await card.query_selector('a')
                                
                                if title_elem:
                                    title = await title_elem.inner_text()
                                    link = await title_elem.get_attribute('href')
                                    
                                    # Ensure link is absolute and valid
                                    if link:
                                        if not link.startswith('http'):
                                            if link.startswith('/'):
                                                link = f"https://{company['url'].split('/')[2]}{link}"
                                            else:
                                                link = f"{company['url']}/{link}"
                                    else:
                                        # If no link found, try to find it differently
                                        link_elem = await card.query_selector('a')
                                        if link_elem:
                                            link = await link_elem.get_attribute('href')
                                            if link and not link.startswith('http'):
                                                link = f"https://{company['url'].split('/')[2]}{link}"
                                        else:
                                            link = company['url']  # Fallback to company page
                                    
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

