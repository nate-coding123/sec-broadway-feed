import requests
import xml.etree.ElementTree as ET
import sys

# SEC REQUIRES a real-looking User-Agent with an email
HEADERS = {
    'User-Agent': 'Research Project (nate@coltonkids.com)',
    'Accept-Encoding': 'gzip, deflate'
}

def get_sec_data():
    # 1. Fetch the master list of all SEC entities
    index_url = "https://www.sec.gov/files/company_tickers.json"
    
    try:
        print("Fetching SEC master index...")
        res = requests.get(index_url, headers=HEADERS, timeout=15)
        res.raise_for_status()
        companies = res.json()
        
        # 2. MATCHING LOGIC: Search for the phrase anywhere in the name
        # This will catch: "Company Name Broadway Ltd Liability Co"
        search_phrase = "Broadway Ltd Liability Co".upper()
        matched_entities = []
        
        for key in companies:
            full_name = companies[key]['title'].upper()
            if search_phrase in full_name:
                matched_entities.append({
                    'cik': str(companies[key]['cik_str']).zfill(10),
                    'name': companies[key]['title']
                })
        
        if not matched_entities:
            print(f"Zero entities found containing '{search_phrase}'.")
            return '<?xml version="1.0" ?><rss version="2.0"><channel><title>No Results Found</title></channel></rss>'

        print(f"Found {len(matched_entities)} entities. Fetching filings...")

        # 3. Build RSS
        rss = ET.Element("rss", version="2.0")
        channel = ET.SubElement(rss, "channel")
        ET.SubElement(channel, "title").text = f"SEC Filings: *{search_phrase}*"
        ET.SubElement(channel, "link").text = "https://www.sec.gov/edgar/search/"
        
        # 4. Pull filings for each matched company
        for entity in matched_entities:
            try:
                # We hit the stable submissions API for each CIK found
                filing_url = f"https://data.sec.gov/submissions/CIK{entity['cik']}.json"
                f_res = requests.get(filing_url, headers=HEADERS, timeout=10)
                f_data = f_res.json()
                recent = f_data.get('filings', {}).get('recent', {})
                
                # Get last 5 filings for each matched company to prevent a massive file
                for i in range(min(5, len(recent.get('accessionNumber', [])))):
                    acc_no = recent['accessionNumber'][i]
                    form = recent['form'][i]
                    date = recent['filingDate'][i]
                    doc = recent['primaryDocument'][i]
                    
                    item = ET.SubElement(channel, "item")
                    # CUSTOM HEADLINE: [Company Name] Form Type - Date
                    item_title = f"[{entity['name']}] {form} - {date}"
                    ET.SubElement(item, "title").text = item_title
                    
                    clean_acc = acc_no.replace('-', '')
                    link = f"https://www.sec.gov/Archives/edgar/data/{entity['cik']}/{clean_acc}/{doc}"
                    ET.SubElement(item, "link").text = link
                    ET.SubElement(item, "guid", isPermaLink="false").text = acc_no
                    ET.SubElement(item, "pubDate").text = date
            except Exception as e:
                print(f"Skipping {entity['name']} due to error: {e}")
                continue

        return ET.tostring(rss, encoding='unicode')

    except Exception as e:
        print(f"Critical System Error: {e}")
        sys.exit(1)

# Write to file
xml_output = get_sec_data()
with open("feed.xml", "w") as f:
    f.write(xml_output)
print("Process Complete.")
