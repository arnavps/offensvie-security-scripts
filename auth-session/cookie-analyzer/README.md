# Cookie Analyzer

## Executive Summary
Cookie Analyzer is a dual-approach utility designed to automate the extraction, tabulation, and storage of HTTP cookies from target web applications. It provides capabilities to handle modern dynamic applications via a headless browser approach (Selenium) and static endpoints via a standard HTTP client (Requests), exporting the results into standardized text and Excel formats for further review.

## Features
*   **Headless Browser Scraping:** Utilizes Selenium with ChromeDriver to evaluate JavaScript and capture cookies generated post-load.
*   **Static Request Scraping:** Uses the `requests` library for fast, lightweight cookie extraction from static responses.
*   **Structured Export:** Outputs parsed cookie attributes (Name, Value, Domain, Path, Expires, HttpOnly, Secure, SameSite) into tabular console output, text files, and Excel spreadsheets.
*   **Batch Processing:** Supports reading a list of target URLs from an input file for bulk analysis.

## Architecture Overview
The project consists of standalone Python scripts that operate independently. They rely on web-automation and HTTP request libraries to act as clients. The data flow starts from an input source (CLI or file), initiates a network request, parses the returned cookie jar, structures the attributes into a dictionary, and pipes the structured data into file-writing functions (using `pandas` and `prettytable`).

## Installation
Ensure Python 3.8+ is installed.
```bash
pip install -r requirements.txt
```
*Note: The Selenium script requires a valid `chromedriver` executable corresponding to your browser version in the `chromedriver_win32/` directory, or properly configured in your system PATH.*

## Configuration
*   **Input File:** `cookie-scraper.py` reads targets from `URLS.txt` by default.
*   **Browser Binary:** The Selenium script specifies a hardcoded binary location for the Brave browser. You may need to modify the `options.binary_location` variable to point to your local Chrome/Brave installation.
*   **Headless Mode:** Selenium runs in headless mode by default.

## Usage Examples

**Bulk Extraction (Selenium):**
Populate `URLS.txt` with targets (e.g., `https://example.com`, `https://test.local`).
```bash
python cookie-scraper.py
```
*Output will be saved to `output.txt` and `cookie-db.xlsx`.*

**Single Target Extraction (Requests):**
```bash
python cookie-using-requests.py
# Prompt: Enter URL: https://example.com
```

## Directory Structure
```text
cookie-analyzer/
├── cookie-scraper.py          # Selenium-based bulk scraper
├── cookie-using-requests.py   # Requests-based single-target scraper
├── requirements.txt           # Python dependencies
├── URLS.txt                   # Input file for bulk processing
└── chromedriver_win32/        # WebDriver directory
```

## Development Workflow
Development involves modifying the extraction logic to capture additional headers or local storage if needed. Testing is done by running the scripts against known, controlled web servers to verify the presence of generated cookies in the output files.

## Testing
Currently, the tool relies on manual execution against sample endpoints. 

## Logging and Error Handling
`cookie-scraper.py` includes a basic `try-except` block during the Selenium `.get()` method to catch connection errors and timeouts, printing the exception to `stdout` and continuing to the next URL. 

## Dependencies
*   `selenium`
*   `requests`
*   `pandas`
*   `prettytable`
*   `openpyxl` (implied for pandas Excel export)

## Contributing Guidelines
Contributions to improve error handling, parameterize configurations (like the browser binary path), and add parallel processing are welcome via Pull Requests.

## License
MIT License

---