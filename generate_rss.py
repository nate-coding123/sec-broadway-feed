import requests
import xml.etree.ElementTree as ET
import sys

# THE SECRET SAUCE: These headers make the SEC think we are their own search page
HEADERS = {
    'User-Agent': 'Research Project (nate@coltonkids.com)',
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Host': 'search.sec.gov',
    'Referer': 'https://www.sec.gov/edgar/search/',
    'Origin': 'https://www.sec.gov'
}

def get_sec_data():
    # Correct Endpoint: search.sec.gov (NOT www.sec.gov)
    url = 'https://search.sec.gov/edgar/search/v1/search.json'
    
    # Building the query exactly how the website does it
    payload = {
        "q": "\"Broadway Ltd Liability Co\"",
        "from": 0,
        "size": 100
    }
    
    try:
        print("Pinging the SEC Search API...")
        # We use 'json=payload' because this API expects a POST request, not a GET
        res = requests.post(url, json=payload, headers=HEADERS, timeout=20)
        
        if res.status_code == 404:
            print("Error: SEC returned 404. Checking alternative endpoint...")
            # Fallback to GET if POST fails
            res = requests.get(url, params=payload, headers=HEADERS, timeout=20)
            
        res.raise_for_status()
        data = res.json()
        
        hits = data.get('hits', {}).get('hits', [])
        
        rss = ET.Element("rss", version="2.0")
        channel = ET.SubElement(rss, "channel")
        ET.SubElement(channel, "title").text = "Broadway Ltd Filings"
        ET.SubElement(channel, "link").text = "https://www.sec.gov/edgar/search/"

        if not hits:
            print("No hits found.")
            item = ET.SubElement(channel, "item")
            ET.SubElement(item, "title").text = "No filings found"
            return ET.tostring(rss, encoding='unicode')

        for hit in hits:
            s = hit['_source']
            item = ET.SubElement(channel, "item")
            
            # Custom Headline
            company = s.get('display_names', ['Unknown'])[0]
            form = s.get('file_type', 'Filing')
            date = s.get('file_date', 'Unknown')
            ET.SubElement(item, "title").text = f"{company} | {form} | {date}"
            
            # Link Construction
            cik = s['ciks'][0]
            acc_no = s['adsh'].replace('-', '')
            doc = s['primary_doc']
            link = f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc_no}/{doc}"
            
            ET.SubElement(item, "link").text = link
            ET.SubElement(item, "guid").text = s['adsh']
            ET.SubElement(item, "pubDate").text = date

        return ET.tostring(rss, encoding='unicode')

    except Exception as e:
        print(f"Failed to fetch data: {e}")
        # Create a basic file so the build doesn't crash
        return '<?xml version="1.0" ?><rss version="2.0"><channel><title>Error</title></channel></rss>'

# Execution
xml_output = get_sec_data()
with open("feed.xml", "w") as f:
    f.write(xml_output)
