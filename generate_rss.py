import requests
import xml.etree.ElementTree as ET
import sys
from datetime import datetime

# SEC REQUIRES a specific User-Agent format
# REPLACE 'yourname@email.com' with your actual email
HEADERS = {
    'User-Agent': 'Research Project (nate@coltonkids.com)',
    'Accept-Encoding': 'gzip, deflate',
    'Host': 'search.sec.gov'
}

def get_sec_data():
    # This query searches for the phrase in the entity name field
    # We set 'size' to 100 to get a large historical chunk
    url = 'https://search.sec.gov/edgar/search/v1/search.json'
    params = {
        'q': '"Broadway Ltd Liability Co"',
        'from': 0,
        'size': 100
    }
    
    try:
        print("Searching all entities for 'Broadway Ltd Liability Co'...")
        res = requests.get(url, params=params, headers=HEADERS, timeout=20)
        res.raise_for_status()
        data = res.json()
        
        hits = data.get('hits', {}).get('hits', [])
        if not hits:
            print("No filings found across any entities.")
            return None

        # Create RSS Structure
        rss = ET.Element("rss", version="2.0")
        channel = ET.SubElement(rss, "channel")
        ET.SubElement(channel, "title").text = "Broadway Ltd Entity Filings"
        ET.SubElement(channel, "link").text = "https://www.sec.gov/edgar/search/"
        ET.SubElement(channel, "description").text = "Aggregate feed for all companies matching 'Broadway Ltd Liability Co'"

        for hit in hits:
            s = hit['_source']
            item = ET.SubElement(channel, "item")
            
            # --- CUSTOM HEADLINE ---
            # Includes Company Name + Form Type + Date
            company_name = s.get('display_names', ['Unknown'])[0]
            form_type = s.get('file_type', 'Filing')
            file_date = s.get('file_date', 'Unknown Date')
            
            item_title = f"{company_name} | {form_type} | {file_date}"
            ET.SubElement(item, "title").text = item_title
            
            # URL Construction
            # Search API uses 'adsh' (Accession Number) and CIKs
            cik = s['ciks'][0]
            acc_no = s['adsh'].replace('-', '')
            doc = s['primary_doc']
            link = f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc_no}/{doc}"
            
            ET.SubElement(item, "link").text = link
            ET.SubElement(item, "guid", isPermaLink="false").text = s['adsh']
            ET.SubElement(item, "pubDate").text = file_date

        return ET.tostring(rss, encoding='unicode')

    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

xml_output = get_sec_data()
if xml_output:
    with open("feed.xml", "w") as f:
        f.write(xml_output)
    print(f"Success! Generated feed with {xml_output.count('<item>')} entries.")
