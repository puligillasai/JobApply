# Browser-based portal scrapers
import datetime
from typing import Dict, List

import requests
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError


async def fetch_indeed_jobs_playwright(query: str = "DevOps Engineer", location: str = "USA") -> List[Dict]:
    """Scrape jobs from Indeed using Playwright for dynamic content"""
    jobs = []
    browser = None
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080}
            )
            page = await context.new_page()

            # Indeed search URL with location and time filters
            url = f"https://www.indeed.com/jobs?q={query}&l={location}&fromage=1"
            
            try:
                await page.goto(url, timeout=30000, wait_until='networkidle')
                await page.wait_for_timeout(3000)  # Wait for dynamic content

                # Scroll down to load more jobs
                for _ in range(5):
                    await page.evaluate('window.scrollBy(0, 1000)')
                    await page.wait_for_timeout(1000)

                # Try multiple selectors for Indeed job cards
                job_selectors = [
                    'div.job_seen_beacon',
                    'div.jobCard',
                    'div.slider_item',
                    'li.css-1x7z1ps'
                ]

                job_cards = []
                for selector in job_selectors:
                    try:
                        cards = await page.query_selector_all(selector)
                        if cards:
                            job_cards = cards
                            print(f"Indeed: Found {len(job_cards)} cards with selector: {selector}")
                            break
                    except Exception:
                        continue

                # Extract jobs
                for card in job_cards[:50]:
                    try:
                        # Try multiple selectors for job details
                        title_elem = await card.query_selector('h2.jobTitle, h2, span[title]')
                        company_elem = await card.query_selector('span[data-testid="company-name"], span.companyName')
                        location_elem = await card.query_selector('div[data-testid="text-location"], div.companyLocation')
                        link_elem = await card.query_selector('a.jcs-JobTitle, a[href]')

                        if title_elem:
                            title = await title_elem.evaluate('el => el.textContent || el.getAttribute("title") || ""')
                            company = await company_elem.evaluate('el => el.textContent') if company_elem else "Unknown"
                            location = await location_elem.evaluate('el => el.textContent') if location_elem else "Unknown"
                            link = await link_elem.evaluate('el => el.getAttribute("href")') if link_elem else "#"
                            
                            # Ensure link is absolute
                            if link and not link.startswith('http'):
                                if link.startswith('/'):
                                    link = "https://www.indeed.com" + link
                                else:
                                    link = "https://www.indeed.com/" + link
                            
                            jobs.append({
                                'title': title.strip(),
                                'company': company.strip(),
                                'location': location.strip(),
                                'url': link,
                                'posted_date': datetime.datetime.now(),
                                'source': 'Indeed'
                            })
                    except Exception as e:
                        print(f"Error parsing Indeed job card: {e}")
                        continue

                print(f"Indeed: {len(jobs)} jobs extracted")

            except PlaywrightTimeoutError:
                print(f"Timeout loading Indeed page")
            except Exception as e:
                print(f"Error navigating to Indeed: {e}")
            finally:
                if browser:
                    await browser.close()

    except Exception as e:
        print(f"Error in Indeed Playwright scraper: {e}")

    return jobs

def fetch_linkedin_jobs(query: str = "DevOps Engineer") -> List[Dict]:
    """Scrape jobs from LinkedIn using requests (Playwright gets blocked)"""
    jobs = []
    try:
        # Try multiple LinkedIn URLs to get more results
        urls = [
            f"https://www.linkedin.com/jobs/search/?keywords={query}&location=United%20States&f_TPR=r86400&f_JT=F",
            f"https://www.linkedin.com/jobs/search/?keywords={query}&location=United%20States&f_TPR=r604800",
            f"https://www.linkedin.com/jobs/search/?keywords={query}&location=Remote"
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
                        ('div', 'base-card'),
                        ('div', 'job-search-card'),
                        ('li', 'occludable-update')
                    ]
                    
                    job_cards = []
                    for tag, class_name in job_selectors:
                        cards = soup.find_all(tag, class_=class_name)
                        if cards:
                            job_cards = cards
                            print(f"LinkedIn: Found {len(job_cards)} cards with {tag}.{class_name}")
                            break
                    
                    for card in job_cards[:50]:  # Increased limit
                        try:
                            # Try multiple selectors for job details
                            title_elem = card.find('h3', class_='base-search-card__title') or card.find('h3')
                            company_elem = card.find('h4', class_='base-search-card__subtitle') or card.find('h4')
                            location_elem = card.find('span', class_='job-search-card__location') or card.find('span')
                            link_elem = card.find('a', class_='base-card__full-link') or card.find('a')
                            
                            if title_elem and company_elem:
                                title = title_elem.get_text(strip=True)
                                company = company_elem.get_text(strip=True).replace('Hiring', '').strip()
                                location = location_elem.get_text(strip=True) if location_elem else "Unknown"
                                link = link_elem['href'] if link_elem else "#"
                                
                                # Avoid duplicates
                                if not any(job['title'] == title and job['company'] == company for job in jobs):
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
                print(f"Error fetching LinkedIn from {url}: {e}")
                continue
                
    except Exception as e:
        print(f"Error scraping LinkedIn: {e}")
    
    print(f"LinkedIn: Total {len(jobs)} unique jobs")
    return jobs

async def fetch_linkedin_jobs_playwright(query: str = "DevOps Engineer") -> List[Dict]:
    """Scrape jobs from LinkedIn using Playwright for dynamic content"""
    jobs = []
    browser = None
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080}
            )
            page = await context.new_page()

            # LinkedIn search URL with location filter
            url = f"https://www.linkedin.com/jobs/search/?keywords={query}&location=United%20States&f_TPR=r86400&f_JT=F"
            
            try:
                await page.goto(url, timeout=30000, wait_until='networkidle')
                await page.wait_for_timeout(3000)  # Wait for dynamic content

                # Scroll down to load more jobs
                for _ in range(5):
                    await page.evaluate('window.scrollBy(0, 1000)')
                    await page.wait_for_timeout(1000)

                # Try multiple selectors for LinkedIn job cards
                job_selectors = [
                    'div.job-search-card',
                    'li.occludable-update',
                    'div[data-urn]',
                    '.jobs-search-results__list-item'
                ]

                job_cards = []
                for selector in job_selectors:
                    try:
                        cards = await page.query_selector_all(selector)
                        if cards:
                            job_cards = cards
                            print(f"Found {len(job_cards)} job cards with selector: {selector}")
                            break
                    except Exception:
                        continue

                # Extract more jobs (up to 100)
                for card in job_cards[:100]:
                    try:
                        # Try multiple selectors for job details
                        title_elem = await card.query_selector('h3, .job-card-list__title, [data-automation-id="job-title"]')
                        company_elem = await card.query_selector('h4, .job-card-container__company-name, [data-automation-id="company-name"]')
                        location_elem = await card.query_selector('span, .job-card-container__metadata-item, [data-automation-id="location"]')
                        link_elem = await card.query_selector('a, .job-card-list__title, [data-automation-id="job-title"]')

                        if title_elem:
                            title = await title_elem.inner_text()
                            company = await company_elem.inner_text() if company_elem else "Unknown"
                            job_location = await location_elem.inner_text() if location_elem else "Unknown"
                            
                            link = "#"
                            if link_elem:
                                link = await link_elem.get_attribute('href')
                                if link and not link.startswith('http'):
                                    link = "https://www.linkedin.com" + link

                            jobs.append({
                                'title': title.strip(),
                                'company': company.strip(),
                                'location': job_location.strip(),
                                'url': link,
                                'posted_date': datetime.datetime.now(),
                                'source': 'LinkedIn'
                            })
                    except Exception as e:
                        print(f"Error parsing LinkedIn job card: {e}")
                        continue

                print(f"LinkedIn: {len(jobs)} jobs extracted")

            except PlaywrightTimeoutError:
                print(f"Timeout loading LinkedIn page")
            except Exception as e:
                print(f"Error navigating to LinkedIn: {e}")
            finally:
                if browser:
                    await browser.close()

    except Exception as e:
        print(f"Error in LinkedIn Playwright scraper: {e}")

    return jobs

async def fetch_glassdoor_jobs_playwright(query: str = "DevOps Engineer", location: str = "USA") -> List[Dict]:
    """Scrape jobs from Glassdoor using Playwright for JavaScript-rendered content

    Args:
        query: Job title to search for
        location: Location filter
    """
    jobs = []
    browser = None
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            )
            page = await context.new_page()

            url = f"https://www.glassdoor.com/Job/{query.replace(' ', '-')}-jobs-SRCH_KO0,14.htm?location={location}"

            try:
                await page.goto(url, timeout=30000, wait_until='domcontentloaded')
                await page.wait_for_timeout(5000)  # Wait for dynamic content

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
                    except Exception:
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
                if browser:
                    await browser.close()

    except Exception as e:
        print(f"Error in Glassdoor Playwright scraper: {e}")

    return jobs

async def fetch_builtin_jobs_playwright(query: str = "DevOps Engineer") -> List[Dict]:
    """Scrape jobs from BuiltIn using Playwright

    Args:
        query: Job title to search for
    """
    jobs = []
    browser = None
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            )
            page = await context.new_page()

            url = f"https://www.builtin.com/jobs?query={query.replace(' ', '%20')}"

            try:
                await page.goto(url, timeout=30000, wait_until='domcontentloaded')
                await page.wait_for_timeout(5000)

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
                    except Exception:
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
                            if link and not link.startswith('http'):
                                link = "https://www.builtin.com" + link

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
                if browser:
                    await browser.close()

    except Exception as e:
        print(f"Error in BuiltIn Playwright scraper: {e}")

    return jobs
