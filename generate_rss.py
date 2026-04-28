import requests
import xml.etree.ElementTree as ET
import sys
import gzip
import io
import re

# SEC MANDATORY HEADERS
HEADERS = {
    'User-Agent': 'Research Project (nate@coltonkids.com)', 
    'Accept-Encoding': 'gzip, deflate',
    'Host': 'www.sec.gov'
}

def get_sec_data():
    url = "https://www.sec.gov/Archives/edgar/full-index/2026/QTR2/master.gz"
    
    try:
        print(f"Fetching SEC index from {url}...")
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        
        with gzip.GzipFile(fileobj=io.BytesIO(response.content)) as f:
            content = f.read().decode('latin-1')
        
        lines = content.split('\n')
        pattern = re.compile(r"BROADWAY.*?LTD.*?LIABILITY.*?CO", re.IGNORECASE)
        
        all_matches = []

        for line in lines:
            if pattern.search(line):
                parts = line.split('|')
                if len(parts) >= 5:
                    all_matches.append({
                        'cik': parts[0],
                        'name': parts[1],
                        'form': parts[2],
                        'date': parts[3],
                        'path': parts[4]
                    })

        # --- SORTING LOGIC ---
        # Sorts by 'date' string (YYYY-MM-DD) in reverse (most recent first)
        all_matches.sort(key=lambda x: x['date'], reverse=True)

        # Build RSS
        rss = ET.Element("rss", version="2.0")
        channel = ET.SubElement(rss, "channel")
        ET.SubElement(channel, "title").text = "Broadway Ltd Search Feed"
        ET.SubElement(channel, "link").text = "https://www.sec.gov"

        for entry in all_matches:
            item = ET.SubElement(channel, "item")
            # CUSTOM HEADLINE
            item_title = f"{entry['name']} | {entry['form']} | {entry['date']}"
            ET.SubElement(item, "title").text = item_title
            
            link = f"https://www.sec.gov/Archives/{entry['path'].replace('.txt', '-index.html')}"
            ET.SubElement(item, "link").text = link
            ET.SubElement(item, "guid").text = entry['path']
            ET.SubElement(item, "pubDate").text = entry['date']

        print(f"Successfully found and sorted {len(all_matches)} filings.")
        return ET.tostring(rss, encoding='unicode')

    except Exception as e:
        print(f"Failed: {e}")
        return None

xml_output = get_sec_data()
if xml_output:
    with open("feed.xml", "w") as f:
        f.write(xml_output)
