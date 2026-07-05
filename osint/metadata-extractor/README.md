# MetaDetective

## Executive Summary
MetaDetective is an advanced, multithreaded Open Source Intelligence (OSINT) utility engineered to scrape, download, and analyze files from target domains for exposed metadata. By automating document discovery, executing local forensic analysis via `exiftool`, and geolocating embedded GPS coordinates, it provides comprehensive reports on software usage, document authorship, and geolocation intelligence.

## Features
*   **Web Scraping & Link Extraction:** Crawls target URLs and parses HTML to identify downloadable files based on configurable extension lists.
*   **Multithreaded Processing:** Utilizes thread pools for concurrent downloading and metadata analysis, maximizing network and CPU throughput.
*   **Deep Metadata Extraction:** Leverages `exiftool` to extract standard attributes (Author, Software, Create Date) and hidden unique fields.
*   **GPS Geolocation & Mapping:** Parses embedded EXIF GPS data (DMS), translates it to Decimal Degrees, resolves it to human-readable addresses using the Nominatim (OpenStreetMap) API, and generates map links.
*   **Deduplication Architecture:** Implements CRC32 hashing to prevent duplicate file analysis and normalizes URLs to avoid redundant crawling.
*   **Dynamic User-Agent Spoofing:** Includes preset User-Agent strings (Chrome, Firefox, Safari, Mobile, Stealth) to bypass basic anti-scraping filters.

## Architecture Overview
MetaDetective is built on a modular, Object-Oriented architecture. It orchestrates a suite of specialized worker classes: `WebScraper` (HTML parsing), `FileDownloader` (network IO and hashing), `MetadataExtractor` (subprocess management), and `AddressResolver` (API integration with caching). The system employs thread-safe data structures (`FileStats`, `URLSet`) and the `queue` module to manage task distribution across worker threads safely.

## Installation
Ensure Python 3.8+ is installed.
**System Dependency:** The system requires `exiftool` to be installed and accessible in the system PATH.

```bash
# Ubuntu/Debian
sudo apt-get install libimage-exiftool-perl

# Mac (Homebrew)
brew install exiftool
```

## Configuration
Configuration is managed via command-line arguments. Default behaviors (timeouts, rate limits, thread counts) are defined as constants at the top of the script.

## Usage Examples

**Basic Analysis:**
Scrape a specific URL and extract metadata from default file types.
```bash
python MetaDetective.py -u https://example.com/documents
```

**Targeted Extension Scraping:**
Focus only on PDF and DOCX files.
```bash
python MetaDetective.py -u https://example.com/reports -e pdf,docx
```

**Stealth Extraction:**
Use a specific User-Agent and increase thread count.
```bash
python MetaDetective.py -u https://example.com/assets --user-agent stealth --threads 8
```

## Directory Structure
```text
metadata-extractor/
├── src/
│   └── MetaDetective/
│       └── MetaDetective.py  # Main application script
├── docs/                     # Documentation files
├── docker/                   # Containerization files
├── pyproject.toml            # Python project metadata
└── README.md                 # Project root README
```

## Development Workflow
Development requires testing against controlled environments or public domains explicitly authorizing scraping. Enhancements typically focus on extending the `MetadataExtractor` parsing logic or adding new API integrations to the `AddressResolver`.

## Testing
Unit testing can be implemented by mocking the `urllib.request` network calls and `subprocess.run` executions. 

## Logging and Error Handling
The application uses a custom `Logger` class for structured, leveled console output. Network operations wrap `urllib` calls in extensive `try-except` blocks, specifically catching timeout, decoding, and HTTP errors. The API integration uses threading locks and caching to prevent rate-limit bans and handles JSON decode errors gracefully.

## Dependencies
*   Python Standard Library (`threading`, `urllib`, `html.parser`, `subprocess`, `zlib`)
*   External: `exiftool` executable

## Contributing Guidelines
Contributions are welcome for adding output serialization formats (e.g., exporting the generated metadata dictionaries directly to JSON/CSV) and expanding the HTML parsing logic to handle single-page applications (SPAs).

## License
Provided under the terms specified in the `LICENSE` file.

---