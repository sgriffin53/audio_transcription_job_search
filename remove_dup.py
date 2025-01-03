import csv
from urllib.parse import urlparse

# Remove duplicate urls from CSV file

def remove_duplicate_domains(input_csv, output_csv):
    """
    Scans a CSV file for duplicate domains and removes duplicate entries.

    Args:
        input_csv (str): Path to the input CSV file.
        output_csv (str): Path to the output CSV file.
    """
    seen_domains = set()
    unique_rows = []

    # Read the input CSV
    with open(input_csv, 'r', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames

        for row in reader:
            # Parse the domain from the URL
            url = row.get('URL', '')  # Assuming 'url' is the column name for URLs
            domain = urlparse(url).netloc

            # Skip duplicates
            if domain not in seen_domains:
                seen_domains.add(domain)
                unique_rows.append(row)

    # Write the unique rows to the output CSV
    with open(output_csv, 'w', newline='', encoding='utf-8') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(unique_rows)

    print(f"Processed {len(unique_rows)} unique entries. Saved to {output_csv}.")

# Example usage
input_csv = 'transcription_jobs1.csv'
output_csv = 'transcription_jobs_deduplicated.csv'
remove_duplicate_domains(input_csv, output_csv)