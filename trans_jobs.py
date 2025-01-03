import requests
import re
import csv
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from googlesearch import search


def calculate_external_link_percentage(url, page_content):
    """
    Calculates the percentage of external links on a webpage.

    Args:
        url (str): The URL of the webpage.
        page_content (str): The HTML content of the webpage.

    Returns:
        float: The percentage of external links on the page.
    """
    from bs4 import BeautifulSoup

    # Parse the webpage content with BeautifulSoup
    soup = BeautifulSoup(page_content, 'html.parser')

    # Get the domain of the current page
    domain = urlparse(url).netloc

    # Find all anchor tags with href attributes
    links = soup.find_all('a', href=True)

    # Count the total and external links
    total_links = len(links)
    external_links = 0

    for link in links:
        href = link['href']
        # Parse the href to check its domain
        parsed_href = urlparse(href)
        # If the link has a different domain, consider it external
        if parsed_href.netloc and parsed_href.netloc != domain:
            external_links += 1

    # Calculate the percentage of external links
    external_percentage = (external_links / total_links) * 100 if total_links > 0 else 0

    return external_percentage

def get_job_links(query):
    # Perform a Google search
    links = []
    for url in search(query, num_results=500):  # Change num_results as needed
        if "flexjobs.com" in url: continue
        if "totaljobs.com" in url: continue
        links.append(url)
    return links

def is_job_listing(page_content, soup, url):
    """
    Checks if the page is likely a job listing or a list of companies.
    This is a heuristic approach based on the number of external links.
    """
    # Get the domain of the current page
    domain = urlparse(url).netloc

    # Check if the URL indicates a forum post (e.g., quora.com, reddit.com)
    if "quora.com" in domain or "reddit.com" in domain:
        print(f"Skipping {url}: It's a forum post.")
        return False

    # Find all the links on the page
    links = soup.find_all('a', href=True)

    # Count the number of outgoing (external) links
    external_links = 0
    for link in links:
        href = link['href']
        # Check if the link is an external link
        if urlparse(href).netloc and urlparse(href).netloc != domain:
            external_links += 1

    # Calculate the percentage of external links
    external_link_percentage = (external_links / len(links)) * 100 if len(links) > 0 else 0

    # If 50% or more of the links are external, consider it a list of transcription companies
    if external_link_percentage >= 50:
        print(f"Skipping {url}: It's a list of transcription companies (more than 50% external links).")
        return False

    # Otherwise, consider it a job listing
    return True

def extract_pay_rate(page_content):
    """
    Extracts the pay rate from the page content using regex for 'per audio hour' and 'per audio minute'.
    """
    # Define regex patterns for both "per audio hour" and "per audio minute"
    patterns = [
        r'(\$\d+(\.\d{1,2})?)\s*(per\s*audio\s*hour)',  # Example: $15 per audio hour
        r'(\$\d+(\.\d{1,2})?)\s*(per\s*audio\s*minute)',  # Example: $0.25 per audio minute
        r'(\£\d+(\.\d{1,2})?)\s*(per\s*audio\s*minute)',  # Example: £15 per audio hour
        r'(\£\d+(\.\d{1,2})?)\s*(per\s*audio\s*minute)',  # Example: £0.25 per audio minute
    ]

    for pattern in patterns:
        match = re.search(pattern, page_content, re.IGNORECASE)
        if match:
            return match.group(1)  # Return the pay rate (the amount matched)

    return "Not mentioned"  # Return this if no pay rate is found

def save_to_csv(jobs):
    """
    Saves the job details to a CSV file.
    """
    # Define the CSV file fieldnames
    fieldnames = ['Job Title', 'URL', 'Pay Rate', 'Description']
    filename = 'transcription_jobs.csv'

    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()  # Write the header row

            # Write each job to the CSV file
            for job in jobs:
                # Use `.get()` to handle missing keys and avoid KeyError
                writer.writerow({
                    'Job Title': job.get('Job Title', 'No Title Found'),
                    'URL': job.get('URL', ''),
                    'Pay Rate': job.get('Pay Rate', 'Not mentioned'),
                    'Description': job.get('Description', 'Not available'),
                })

        print(f"Jobs successfully saved to {filename}")
    except Exception as e:
        print(f"Error while saving to CSV: {e}")

def get_job_info(url):
    try:
        # Set a timeout of 5 seconds for the request (you can adjust this as needed)
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            page_content = soup.get_text()

            # Extract the title of the page
            title = soup.find('title').text if soup.find('title') else 'No Title Found'
            external_link_percent = calculate_external_link_percentage(url, response.text)
            print(url, ":", external_link_percent)
            if external_link_percent > 40:
                print(f"Skipping {url}: High number of external links.")
                return None  # Skip this page if it matches the pattern
            # Regex check for titles like "28 Transcription jobs"
            if re.search(r'\d+\s+transcription\s+jobs', title, re.IGNORECASE):
                print(f"Skipping {url}: Title matches '[number] transcription jobs'.")
                return None  # Skip this page if it matches the pattern
            # Regex check for titles like "28 Transcription jobs"
            if re.search(r'\d+\sonline\s+transcription\s+jobs', title, re.IGNORECASE):
                print(f"Skipping {url}: Title matches '[number] online transcription jobs'.")
                return None  # Skip this page if it matches the pattern

            # Check if the page is a job listing or a list of companies
            if is_job_listing(page_content, soup, url):
                pay_rate = extract_pay_rate(page_content)  # Use the regex function for pay rate extraction
                description = 'Not available'  # Default description

                # Look for description in the page
                if soup.find('meta', {'name': 'description'}):
                    description = soup.find('meta', {'name': 'description'})['content']

                return {
                    'Job Title': title,  # Change key to match fieldname
                    'URL': url,  # Change key to match fieldname
                    'Pay Rate': pay_rate,  # Change key to match fieldname
                    'Description': description  # Change key to match fieldname
                }
            else:
                return None
        else:
            return None
    except requests.exceptions.Timeout:
        print(f"Timeout occurred while trying to access {url}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Error occurred: {e}")
        return None

def main():
    query = "audio transcription jobs"
    job_links = get_job_links(query)
    print("got links")

    all_jobs = []
    for link in job_links:
        job_info = get_job_info(link)
        print("getting info", link)
        if job_info:
            all_jobs.append(job_info)

    # Save the jobs to a CSV file
    if all_jobs:
        save_to_csv(all_jobs)
        print(f"Saved {len(all_jobs)} jobs to transcription_jobs.csv")
    else:
        print("No jobs found.")

if __name__ == "__main__":
    main()