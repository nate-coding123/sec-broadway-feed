import requests
import xml.etree.ElementTree as ET
from datetime import datetime

# SEC REQUIRES THIS
HEADERS = {'User-Agent': 'Nate Colton (nate@coltonkids.com)'}

def get_sec_data():
    url = 'https://search.sec.gov/edgar/search/v1/search.json?q="Broadway Ltd Liability Co"'
    res = requests.get(url, headers=HEADERS)
    data = res.json()
    
    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = "Broadway Ltd Filings"
    ET.SubElement(channel, "link").text = "https://www.sec.gov"
    
    for hit in data['hits']['hits'][:20]: # Last 20 filings
        s = hit['_source']
        item = ET.SubElement(channel, "item")
        
        # CUSTOM TITLE HERE
        item_title = f"{s['file_type']} - {s['file_date']} - {s['display_names'][0]}"
        ET.SubElement(item, "title").text = item_title
        
        # Link construction
        acc_no = s['adsh'].replace('-', '')
        link = f"https://www.sec.gov/Archives/edgar/data/{s['ciks'][0]}/{acc_no}/{s['primary_doc']}"
        ET.SubElement(item, "link").text = link
        ET.SubElement(item, "guid").text = link

    return ET.tostring(rss, encoding='unicode')

with open("feed.xml", "w") as f:
    f.write(get_sec_data())
