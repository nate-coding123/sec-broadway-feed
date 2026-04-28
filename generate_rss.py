import requests
import xml.etree.ElementTree as ET
import sys
import time

# SEC REQUIRES a descriptive User-Agent
# Replace with your actual email to avoid blocks
HEADERS = {
    'User-Agent': 'Research Project (nate@coltonkids.com)',
    'Accept': 'application/json',
    'Host': 'search.sec.gov'
}

def get_sec_data():
    # Searching for the exact phrase across all entities
    url = 'https://search.sec.gov/edgar/search/v1/search.json'
    params = {
        'q': '"Broadway Ltd Liability Co"',
        'from': 0,
        'size': 100  # Pulls up to 100 historical results
    }
    
    # Retry logic to bypass the flaky connection
    for attempt in range(3):
        try:
            print(f"Attempt {attempt+1}: Searching all entities for 'Broadway Ltd Liability Co'...")
            res = requests.get(url, params=params, headers=HEADERS, timeout=20)
            res.raise_for_status()
            data = res.json()
            break 
        except Exception as e:
            print(f"Connection failed: {e}")
            if attempt < 2:
                time.sleep(5) # Wait 5 seconds before trying again
            else:
                sys.exit(1)

    hits = data.get('hits', {}).get('hits', [])
    
    # Create RSS
    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = "Broadway Ltd Entity Filings"
    ET.SubElement(channel, "link").text = "https://www.sec.gov/edgar/search/"

    if not hits:
        # If no hits, create one "No Results" item so the feed is valid but empty
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = "No current filings found for Broadway Ltd Liability Co"
        return ET.tostring(rss, encoding='unicode')

    for hit in hits:
        s = hit['_source']
        item = ET.SubElement(channel, "item")
        
        # --- CUSTOM TITLE ---
        company_name = s.get('display_names', ['Unknown'])[0]
        form_type = s.get('file_type', 'Filing')
        file_date = s.get('file_date', 'Unknown')
        
        item_title = f"{company_name} | {form_type} | {file_date}"
        ET.SubElement(item, "title").text = item_title
        
        # Link construction
        cik = s['ciks'][0]
        acc_no = s['adsh'].replace('-', '')
        doc = s['primary_doc']
        link = f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc_no}/{doc}"
        
        ET.SubElement(item, "link").text = link
        ET.SubElement(item, "guid", isPermaLink="false").text = s['adsh']
        ET.SubElement(item, "pubDate").text = file_date

    return ET.tostring(rss, encoding='unicode')

# Save the file
xml_output = get_sec_data()
with open("feed.xml", "w") as f:
    f.write(xml_output)
print("Feed updated successfully.")
