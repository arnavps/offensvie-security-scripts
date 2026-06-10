# Employee Email Harvester

A professional, asynchronous Open-Source Intelligence (OSINT) utility designed to passively identify and collect employee email addresses associated with a target domain. 

This tool is built for penetration testers, red team operators, and security researchers to map an organization's footprint during the reconnaissance phase of authorized security engagements. It uses a scalable, plugin-based architecture to aggregate data from public sources concurrently.

## Features
- **Asynchronous Execution:** Leverages `asyncio` to query multiple OSINT sources concurrently, drastically reducing reconnaissance time.
- **Robust Network Handling:** Implements exponential backoff, automated retries, and User-Agent rotation using `tenacity` to handle transient network failures and rate limiting.
- **Plugin Architecture:** Designed for extensibility. New search engines, APIs, or data sources can be integrated simply by subclassing a `BaseSource`.
- **Strict Data Validation:** Utilizes `Pydantic` models to enforce rigid data schemas, ensuring parsed emails are strictly typed, normalized, and deduplicated.
- **Heuristic Extraction:** Employs precise regular expressions combined with heuristic filtering to reject common false positives (e.g., image filenames mistaken for email addresses).
- **Structured Export:** Natively supports exporting normalized intelligence to JSON and CSV formats for integration into broader security pipelines.

## Use Cases
- **Attack Surface Mapping:** Discovering the organizational hierarchy, naming conventions, and public exposure of corporate email addresses.
- **Phishing Simulation Targeting:** Building authorized target lists for internal security awareness assessments.
- **Identity Correlation:** Correlating discovered personnel with other OSINT findings (e.g., public code repositories, breached credential databases).
- **Breach Discovery:** Validating exposed contact information appearing in public data leaks.

## Tech Stack
- **Language:** Python 3.10+
- **Concurrency:** `asyncio`
- **Network / HTTP:** `httpx` (async HTTP client)
- **Resilience:** `tenacity` (retry/backoff logic)
- **Data Validation:** `pydantic` (strict modeling)
- **Parsing:** `beautifulsoup4`, `re` (Regex)
- **CLI / UX:** `typer`, `rich` (terminal formatting)

## Project Architecture
The project follows clean architecture principles, separating the orchestration engine, data sources, utilities, and presentation layer:

- **Orchestrator (`engine.py`):** Dynamically discovers and loads plugins from the `sources/` directory. It spins up an `httpx.AsyncClient` session and executes all loaded sources concurrently using `asyncio.gather`.
- **Sources (`sources/`):** Pluggable modules (e.g., DuckDuckGo, Bing, public APIs) that inherit from `BaseSource`. Each source is responsible only for fetching and returning a set of strictly typed `EmailResult` models.
- **Utilities (`utils/`):** Centralized logic. `http.py` manages all outbound requests and retry logic globally. `extractors.py` houses the regex and heuristic logic for pulling valid emails from raw HTML or JSON.
- **State Management:** Extracted data is automatically deduplicated and normalized by the Pydantic models inside a thread-safe global set before export.

```text
email-harvester/
├── harvester/
│   ├── cli.py                  # CLI interface using Typer
│   ├── core/
│   │   ├── engine.py           # Async orchestrator
│   │   └── models.py           # Pydantic data schemas
│   ├── sources/
│   │   ├── base.py             # Abstract Base Class for plugins
│   │   └── search_engines.py   # Implementations (DDG, Bing, etc.)
│   └── utils/
│       ├── extractors.py       # Regex & heuristic validation
│       ├── exporters.py        # CSV/JSON output handling
│       ├── http.py             # Resilient async HTTP client
│       └── logger.py           # Rich structured logging
├── payloads/                   # Advanced search dorks and payload lists
├── tests/                      # Unit tests for core logic
├── requirements.txt            
└── run.py                      # Main entry point
```

## Installation
It is highly recommended to use a virtual environment.

```bash
# Clone the repository
git clone https://github.com/yourusername/employee-email-harvester.git
cd employee-email-harvester

# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

The tool uses a standard Typer CLI interface. You must provide a target domain.

### Basic Usage
```bash
python run.py --domain example.com
```

### Export Results to JSON and CSV
```bash
python run.py --domain example.com --json results.json --csv results.csv
```

### Enable Verbose Logging
Useful for debugging rate limits or viewing the exact URLs being requested.
```bash
python run.py -d example.com --verbose
```

### View Help
```bash
python run.py --help
```

## Example Workflow
1. **Scope Verification:** A penetration tester validates that passive reconnaissance against `example.com` is within the Rules of Engagement.
2. **Execution:** The tester runs `python run.py -d example.com --csv targets.csv`.
3. **Data Gathering:** The orchestrator loads the DuckDuckGo source, spins up an async task, and queries the search engine using targeted OSINT dorks (e.g., `intext:"@example.com"`).
4. **Extraction:** The raw HTML is parsed, common obfuscations are reversed, and false positives are stripped.
5. **Deduplication:** The resulting emails are normalized and deduplicated.
6. **Export:** The final unique list is exported to `targets.csv` for use in a secondary tool, such as cross-referencing against the HaveIBeenPwned API.

## Example Output

```text
WARNING: This tool is for authorized security testing and OSINT research only.
Do not use against targets without explicit permission.

[06/10/26 14:14:39] INFO     Targeting Domain: example.com                     
[06/10/26 14:14:40] INFO     Loaded 1 modules. Starting asynchronous           
                             harvesting...                                     
                    INFO     Starting module: DuckDuckGo                       
                    INFO     [DuckDuckGo] Searching for: "example.com"         
[06/10/26 14:14:41] INFO     [+] DuckDuckGo found 3 emails                     
                    INFO     Harvesting complete.                              
                    INFO     Total Unique Emails Found: 3                      

Results for example.com
 - email@example.com (Source: DuckDuckGo)
 - mail@example.com (Source: DuckDuckGo)
 - someone@example.com (Source: DuckDuckGo)
```

## Detection / OPSEC Notes
- **Completely Passive:** This tool does *not* send any traffic to the target domain's infrastructure or mail servers. It relies entirely on third-party aggregators and search engines.
- **Search Engine Rate Limiting:** Search engines (Google, Bing, DDG) monitor for automated scraping. If run too aggressively, the IP executing the script will face CAPTCHAs or temporary blocks (HTTP 429). The tool implements random jitter and backoffs to mitigate this, but excessive concurrent searches will still be flagged by the search provider.

## Limitations
- This tool does not perform active SMTP validation (`VRFY` or `RCPT TO`).
- It cannot bypass CAPTCHAs.
- It only finds data that has been indexed by search engines or is available in public APIs; it will not find internal, unexposed email addresses.

## Future Improvements
- **Proxy/Tor Support:** Integration of proxy pools or Tor routing within the `AsyncHttpClient` to seamlessly bypass search engine rate limiting.
- **API Integrations:** Built-in support for authenticated API endpoints like Hunter.io, DeHashed, or Apollo.
- **Active Validation Plugin:** An optional module to perform active SMTP validation checks on discovered emails, provided the engagement allows active probing.
- **Database Backend:** Support for SQLite/Redis to track findings over long-running, multi-domain campaigns.

## Learning Objectives
By analyzing and modifying this project, researchers can learn:
- How to structure modern Python applications using Clean Architecture.
- Techniques for managing highly concurrent I/O operations with `asyncio`.
- Advanced error handling, exponential backoff, and network resilience strategies.
- How to enforce data integrity using `Pydantic` in offensive tooling.
- Practical OSINT scraping techniques and regex parsing methodologies.

## Disclaimer
> **Warning**
> This tool is strictly intended for **authorized security testing**, educational purposes, and OSINT research. You may only use this tool against infrastructure, networks, or domains for which you have explicit, written authorization. The authors and contributors are not responsible for any misuse, unauthorized access, or illegal activities performed using this software. Always adhere to local laws, search engine Terms of Service, and professional ethics.
