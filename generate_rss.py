import requests
import xml.etree.ElementTree as ET
import sys

# SEC REQUIREMENTS: Use a realistic User-Agent with your email
HEADERS = {
    'User-Agent': 'Individual Research (nate@coltonkids.com)',
    'Accept-Encoding': 'gzip, deflate',
    'Host': 'search.sec.gov'
}

def get_sec_data():
    # We use the official JSON search endpoint
    url = 'https://search.sec.gov/edgar/search/v1/search.json?q="Broadway Ltd Liability Co"'
    
    try:
        print("Requesting data from SEC...")
        res = requests.get(url, headers=HEADERS, timeout=15)
        res.raise_for_status() # This will tell us if it's a 403 Forbidden
        data = res.json()
        
        # Check if we actually got results
        hits = data.get('hits', {}).get('hits', [])
        if not hits:
            print("No filings found for this company name.")
            return None

        # Build the RSS XML structure
        rss = ET.Element("rss", version="2.0")
        channel = ET.SubElement(rss, "channel")
        ET.SubElement(channel, "title").text = "Broadway Ltd Filings Custom Feed"
        ET.SubElement(channel, "link").text = "https://www.sec.gov/edgar/search/"
        ET.SubElement(channel, "description").text = "SEC Filings for Broadway Ltd Liability Co"

        for hit in hits:
            s = hit['_source']
            item = ET.SubElement(channel, "item")
            
            # --- CUSTOMIZE YOUR HEADLINE HERE ---
            # Using 'file_type' (e.g. 4) and 'file_date' (e.g. 2024-04-28)
            custom_title = f"{s.get('file_type', 'Filing')} - {s.get('file_date', '')} - {s.get('display_names', ['Unknown'])[0]}"
            ET.SubElement(item, "title").text = custom_title
            
            # Build the direct URL to the filing
            acc_no = s['adsh'].replace('-', '')
            link = f"https://www.sec.gov/Archives/edgar/data/{s['ciks'][0]}/{acc_no}/{s['primary_doc']}"
            
            ET.SubElement(item, "link").text = link
            ET.SubElement(item, "guid", isPermaLink="false").text = s['adsh']
            ET.SubElement(item, "pubDate").text = s['file_date']

        return ET.tostring(rss, encoding='unicode')

    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

xml_output = get_sec_data()
if xml_output:
    with open("feed.xml", "w") as f:
        f.write(xml_output)
    print("Success! feed.xml has been updated.")
