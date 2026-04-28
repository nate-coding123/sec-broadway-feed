import requests
import xml.etree.ElementTree as ET
import sys

# SEC REQUIRES a real-looking User-Agent with an email
HEADERS = {
    'User-Agent': 'Research Project (nate@coltonkids.com)',
    'Accept-Encoding': 'gzip, deflate'
}

def get_sec_data():
    # 1. Get the master list of all CIKs (Company IDs) from the stable data site
    # This URL is much more reliable than the search URL
    index_url = "https://www.sec.gov/files/company_tickers.json"
    
    try:
        print("Fetching SEC company index...")
        res = requests.get(index_url, headers=HEADERS, timeout=15)
        res.raise_for_status()
        companies = res.json()
        
        # 2. Find all companies matching your string
        # We search the 'title' field for your specific string
        target_string = "Broadway Ltd Liability Co".upper()
        matched_ciks = []
        for key in companies:
            if target_string in companies[key]['title'].upper():
                matched_ciks.append({
                    'cik': str(companies[key]['cik_str']).zfill(10),
                    'name': companies[key]['title']
                })
        
        if not matched_ciks:
            print("No companies found with that name.")
            return None

        # 3. Build the RSS
        rss = ET.Element("rss", version="2.0")
        channel = ET.SubElement(rss, "channel")
        ET.SubElement(channel, "title").text = "Broadway Ltd Combined Feed"
        ET.SubElement(channel, "link").text = "https://www.sec.gov"

        # 4. For each matched company, get their recent filings
        for company in matched_ciks:
            print(f"Fetching filings for: {company['name']} (CIK {company['cik']})")
            filing_url = f"https://data.sec.gov/submissions/CIK{company['cik']}.json"
            f_res = requests.get(filing_url, headers=HEADERS, timeout=15)
            f_data = f_res.json()
            
            recent = f_data.get('filings', {}).get('recent', {})
            
            # Loop through the last 10 filings per company to keep the feed clean
            for i in range(min(10, len(recent.get('accessionNumber', [])))):
                acc_no = recent['accessionNumber'][i]
                form = recent['form'][i]
                date = recent['filingDate'][i]
                doc = recent['primaryDocument'][i]
                
                item = ET.SubElement(channel, "item")
                # --- YOUR CUSTOM TITLE ---
                item_title = f"{company['name']} | {form} | {date}"
                ET.SubElement(item, "title").text = item_title
                
                clean_acc = acc_no.replace('-', '')
                link = f"https://www.sec.gov/Archives/edgar/data/{company['cik']}/{clean_acc}/{doc}"
                ET.SubElement(item, "link").text = link
                ET.SubElement(item, "guid").text = acc_no
                ET.SubElement(item, "pubDate").text = date

        return ET.tostring(rss, encoding='unicode')

    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

xml_output = get_sec_data()
if xml_output:
    with open("feed.xml", "w") as f:
        f.write(xml_output)
    print("Success!")
