from scraper_module import run_full_search

print('=== RED TEAM TESTING: END-TO-END TEST ===\n')

jobs = run_full_search()
print(f'Total jobs found: {len(jobs)}')

if jobs:
    print(f'\nData Completeness Check:')
    has_title = sum(1 for j in jobs if j.get('title'))
    has_company = sum(1 for j in jobs if j.get('company'))
    has_location = sum(1 for j in jobs if j.get('location'))
    has_link = sum(1 for j in jobs if j.get('link') and j['link'] != '#')
    has_match = sum(1 for j in jobs if j.get('match_percentage') is not None)
    
    print(f'  Titles: {has_title}/{len(jobs)} ({has_title/len(jobs)*100:.0f}%)')
    print(f'  Companies: {has_company}/{len(jobs)} ({has_company/len(jobs)*100:.0f}%)')
    print(f'  Locations: {has_location}/{len(jobs)} ({has_location/len(jobs)*100:.0f}%)')
    print(f'  Valid Links: {has_link}/{len(jobs)} ({has_link/len(jobs)*100:.0f}%)')
    print(f'  Match %: {has_match}/{len(jobs)} ({has_match/len(jobs)*100:.0f}%)')
    
    print(f'\nMatch Percentage Distribution:')
    high = sum(1 for j in jobs if j.get('match_percentage', 0) >= 70)
    medium = sum(1 for j in jobs if 50 <= j.get('match_percentage', 0) < 70)
    low = sum(1 for j in jobs if j.get('match_percentage', 0) < 50)
    print(f'  High (70%+): {high}')
    print(f'  Medium (50-69%): {medium}')
    print(f'  Low (<50%): {low}')
    
    print(f'\nSource Distribution:')
    sources = {}
    for j in jobs:
        source = j.get('source', 'Unknown')
        sources[source] = sources.get(source, 0) + 1
    for source, count in sources.items():
        print(f'  {source}: {count}')
else:
    print('No jobs found - check scraper configuration')
