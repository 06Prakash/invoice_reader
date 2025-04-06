import requests
import json
import os
import time

# Constants
SEC_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
HEADERS = {"User-Agent": "MyApp/1.0 (naranecv2004@gmail.com)"}
BASE_DIR = "C:\\FinancialData\\companies"

# Ensure base directory exists
os.makedirs(BASE_DIR, exist_ok=True)

def get_sec_tickers():
    """Fetch SEC tickers data."""
    try:
        response = requests.get(SEC_TICKERS_URL, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"Error": f"Failed to fetch SEC tickers: {str(e)}"}

def search_company(company_name, tickers_data):
    """Search for companies matching the given name."""
    company_name = company_name.lower().strip()
    results = []

    for value in tickers_data.values():
        if company_name in value['title'].lower():
            results.append({
                "CIK": str(value["cik_str"]).zfill(10),
                "Ticker": value["ticker"],
                "Company Name": value["title"]
            })
    return results

def get_latest_filing_urls(cik, year):
    """Fetch URLs of the latest 10-K and 10-Q filings for a given year."""
    cik = str(cik).zfill(10)
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"

    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()

        filings = data.get("filings", {}).get("recent", {})
        filing_urls = []

        for i, form in enumerate(filings.get("form", [])):
            filing_date = filings["filingDate"][i]
            filing_year = int(filing_date[:4])

            if form in ["10-K", "10-Q","20-F"] and filing_year == year:
                accession_no = filings["accessionNumber"][i]
                index_url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession_no.replace('-', '')}/index.json"
                filing_urls.append((index_url, form))
                
        return filing_urls if filing_urls else None

    except requests.exceptions.RequestException as e:
        return {"Error": f"Failed to fetch filing data: {str(e)}"}

def get_financial_reports(index_url, ticker, year, form_type, quarter=1):
    """Download Financial Reports (Excel files) from SEC filing index."""
    try:
        response = requests.get(index_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        sec_data = response.json()

        # Ensure ticker folder and year subfolder exist
        ticker_dir = os.path.join(BASE_DIR, ticker)
        year_dir = os.path.join(ticker_dir, str(year))
        os.makedirs(year_dir, exist_ok=True)

        for file in sec_data.get('directory', {}).get('item', []):
            filename = file.get('name', '')
            if filename.endswith('.xlsx'):
                file_url = f"{index_url.rsplit('/', 1)[0]}/{filename}"
                if form_type == "10-Q":
                    file_name = f"{form_type}-Q{quarter}.xlsx"
                elif form_type == "20-F":
                    file_name = f"{form_type}.xlsx"
                else:
                    file_name = f"{form_type}.xlsx"
                save_path = os.path.join(year_dir, file_name)

                # Check if file already exists
                if os.path.exists(save_path):
                    print(f"Already Exists: {save_path}")
                else:
                    download_file(file_url, save_path)

        return None
    
    except requests.exceptions.RequestException as e:
        return {"Error": f"Failed to fetch filing details: {str(e)}"}

def download_file(url, save_path):
    """Download and save a file."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=20)
        response.raise_for_status()
        
        with open(save_path, "wb") as file:
            file.write(response.content)
        print(f"Downloaded: {save_path}")

    except requests.exceptions.RequestException as e:
        print(f"Failed to download {url}: {str(e)}")

if __name__ == "__main__":
    tickers_data = get_sec_tickers()

    if "Error" in tickers_data:
        print(json.dumps(tickers_data, indent=4))
    else:
        company_name = input("Enter the company name to search: ")
        search_results = search_company(company_name, tickers_data)

        if search_results:
            print("\nMatching Companies:")
            for idx, company in enumerate(search_results, start=1):
                print(f"{idx}. {company['Company Name']} (Ticker: {company['Ticker']}, CIK: {company['CIK']})")

            while True:
                try:
                    choice = int(input("\nEnter the number of the company you want details for (or 0 to exit): "))
                    if choice == 0:
                        print(json.dumps({"Message": "Exiting."}, indent=4))
                        break
                    elif 1 <= choice <= len(search_results):
                        selected_company = search_results[choice - 1]
                        cik = selected_company["CIK"]
                        ticker = selected_company["Ticker"]
                        
                        # Accept multiple years from user
                        year_input = input("Enter the years to fetch filings (comma-separated, e.g., 2022, 2023): ")
                        years = [int(y.strip()) for y in year_input.split(",") if y.strip().isdigit()]
                        
                        for year in years:
                            print(f"\nFetching filings for {ticker} - {year}...")
                            filing_urls = get_latest_filing_urls(cik, year)

                            if not filing_urls:
                                print(json.dumps({"Error": f"No filings found for {year}."}, indent=4))
                            else:
                                quarter = 1  # Initialize quarter count for 10-Q filings
                                for url, form in filing_urls:
                                    time.sleep(2)  # To comply with SEC request rate limits
                                    get_financial_reports(url, ticker, year, form, quarter)

                                    if form == "10-Q":
                                        quarter += 1  # Increment quarter for next 10-Q filing
                        break
                    else:
                        print(json.dumps({"Error": "Invalid selection. Please enter a number from the list."}, indent=4))
                except ValueError:
                    print(json.dumps({"Error": "Invalid input. Please enter a valid number."}, indent=4))
        else:
            print(json.dumps({"Error": "No matching companies found."}, indent=4))