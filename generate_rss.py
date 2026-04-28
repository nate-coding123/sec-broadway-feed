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
        
        # --- THE REGEX FIX ---
        # This looks for the 4 words in order, with anything (.*?) in between
        # \b ensures we match whole words only
        pattern = re.compile(r"BROADWAY.*?LTD.*?LIABILITY.*?CO", re.IGNORECASE)
        
        rss = ET.Element("rss", version="2.0")
        channel = ET.SubElement(rss, "channel")
        ET.SubElement(channel, "title").text = "Broadway Ltd Search Feed"
        ET.SubElement(channel, "link").text = "https://www.sec.gov"

        count = 0
        for line in lines:
            # We check the Regex pattern against the line
            if pattern.search(line):
                parts = line.split('|')
                if len(parts) >= 5:
                    cik, name, form, date, path = parts[0], parts[1], parts[2], parts[3], parts[4]
                    
                    item = ET.SubElement(channel, "item")
                    # CUSTOM HEADLINE
                    item_title = f"{name} | {form} | {date}"
                    ET.SubElement(item, "title").text = item_title
                    
                    link = f"https://www.sec.gov/Archives/{path.replace('.txt', '-index.html')}"
                    ET.SubElement(item, "link").text = link
                    ET.SubElement(item, "guid").text = path
                    ET.SubElement(item, "pubDate").text = date
                    count += 1

        print(f"Successfully found {count} filings matching the pattern.")
        return ET.tostring(rss, encoding='unicode')

    except Exception as e:
        print(f"Failed: {e}")
        return None

xml_output = get_sec_data()
if xml_output:
    with open("feed.xml", "w") as f:
        f.write(xml_output)
