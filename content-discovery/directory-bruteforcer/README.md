# DirBruter

DirBruter is a professional, highly concurrent, and memory-efficient directory and file brute-forcing utility. Designed for authorized Vulnerability Assessments, Penetration Testing (VAPT), and Bug Bounty engagements, it systematically discovers hidden endpoints, administrative panels, and unlinked resources on web servers.

## Features
- **High Concurrency:** Utilizes `asyncio` and `httpx` with connection pooling to maximize network I/O.
- **Memory Efficient:** Wordlists are streamed line-by-line into an asynchronous bounded queue, preventing memory exhaustion when processing massive payload files (e.g., multi-gigabyte SecLists).
- **Network Resilience:** Employs exponential backoff retry logic (via `tenacity`) to gracefully handle dropped connections, timeouts, and WAF rate limiting (429s).
- **Smart Soft-404 Detection:** Automatically establishes a baseline response signature from a randomized missing path to dynamically filter out false positives when servers return `200 OK` for non-existent pages.
- **Strict Validation:** Configuration and inputs are validated using `pydantic` to ensure safe execution states.
- **Modular Output:** Provides thread-safe, colorful terminal reporting via `rich` and standard JSON export.

## Use Cases
During reconnaissance and content discovery phases of a penetration test or bug bounty hunt, DirBruter maps the application's attack surface. It is designed to uncover:
- Forgotten development and staging environments.
- Exposed administrative interfaces or configuration files.
- Unlinked API endpoints.
- Backup files (`.bak`, `.old`, `.tar.gz`).

## Tech Stack
- **Language:** Python 3
- **Core Libraries:** `asyncio` (Native async event loop)
- **Dependencies:** 
  - `httpx` (HTTP/2 capable asynchronous client)
  - `pydantic` (Data validation and configuration management)
  - `tenacity` (Retry and backoff logic)
  - `rich` & `colorama` (Terminal formatting and UX)
- **Protocols:** HTTP/1.1, HTTP/2, HTTPS

## Project Architecture
DirBruter abandons the monolithic script approach in favor of clean architecture principles:
- **`dirbrute.py`**: The main entry point that bootstraps the environment.
- **`cli.py` & `config.py`**: Handles user input mapping it to strictly typed `Pydantic` configurations.
- **`engine.py`**: The core async orchestrator. It uses a Producer-Consumer pattern where a single producer streams file contents into an `asyncio.Queue` (with a `maxsize`), and N worker tasks consume payloads, keeping memory usage flat.
- **`requester.py`**: An `httpx.AsyncClient` wrapper managing the connection pool, timeout contexts, and `tenacity` retry decorators.
- **`filters.py`**: Implements the response evaluation logic, including baseline comparison for Soft-404 rejection.

## Installation

```bash
# Clone the repository (or copy the project folder)
git clone https://github.com/yourusername/directory-bruteforcer.git
cd directory-bruteforcer

# (Optional but recommended) Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

```bash
usage: dirbrute.py [-h] -u URL -w WORDLIST [-e EXTENSIONS] [-t THREADS]
                   [--timeout TIMEOUT] [--retries RETRIES] [-a USER_AGENT]
                   [-o OUTPUT] [--follow-redirects]
```

### Basic Example
```bash
python dirbrute.py -u https://target.com/ -w payloads/common.txt
```

### Advanced Example (Extensions, Tuning, Output)
```bash
python dirbrute.py -u https://target.com/ -w payloads/common.txt -e php,bak,txt -t 100 --retries 5 -o results.json
```

## Example Workflow
1. **Target Identification:** Identify an active web application in-scope for testing.
2. **Wordlist Selection:** Select an appropriate wordlist (e.g., raft-small-words) based on the target stack.
3. **Execution:** Launch DirBruter with targeted extensions. The tool first queries a junk path to determine the server's default "Not Found" behavior (baseline signature).
4. **Analysis:** The workers stream requests asynchronously. If a WAF blocks a request, the worker backs off and retries automatically. Valid hits are printed to the terminal instantly and flushed to `results.json`.
5. **Pivoting:** Discovered paths (e.g., `/admin/backup.zip`) are investigated manually or fed into subsequent testing tools.

## Example Output

```text
[17:13:51] INFO     Starting directory brute force against:       engine.py:104
                    https://example.com/                                       
           INFO     Threads: 50 | Wordlist: payloads/common.txt   engine.py:105
           INFO     Establishing baseline for Soft 404s using:     engine.py:81
                    https://example.com/this-path-definitely-does-             
                    not-exist-12345                                            
           INFO     Baseline established. Soft 404 size: 1450 bytes 

[200] https://example.com/admin (Size: 4502)
[301] https://example.com/api (Size: 0)
[403] https://example.com/server-status (Size: 1024)
[200] https://example.com/backup.zip (Size: 1540392)

[17:14:19] INFO     Scan complete.                                engine.py:127
```

## Detection / OPSEC Notes
- **Noise:** Directory brute-forcing is inherently noisy. High thread counts without delays will generate thousands of requests per second and will be heavily logged by SIEM solutions.
- **WAF/IPS:** Modern WAFs will detect rapid `404 Not Found` responses from a single IP and may issue a temporary block (`403` or `429`). DirBruter's exponential backoff helps keep the tool running, but manual tuning (lowering `-t`) is required for stealth.
- **User-Agent:** By default, the tool announces itself (`DirBruter/1.0`). Use the `-a` flag to spoof a standard browser User-Agent if required.

## Limitations
- Does not currently support proxies (e.g., SOCKS5 or HTTP proxies like Burp Suite) natively out-of-the-box (planned feature).
- Cannot parse or execute JavaScript; purely analyzes raw HTTP responses.
- Soft-404 detection relies on response size matching. Highly dynamic error pages (e.g., containing generated timestamps that alter the byte count) may still slip through as false positives.

## Future Improvements
- **Recursive Scanning:** Automatically re-queue discovered directories (e.g., finding `/admin/` queues `/admin/WORDLIST`).
- **Proxy Support:** Integration for forwarding traffic through Burp Suite or rotating proxies.
- **Advanced Heuristics:** Implementing DOM hashing or NLP clustering to better detect dynamic Soft-404 pages beyond simple byte length.

## Learning Objectives
By studying and modifying this codebase, developers and security engineers can learn:
- How to implement the `asyncio` Producer-Consumer pattern for high-performance I/O tasks.
- How to handle massive datasets securely without triggering Out-Of-Memory (OOM) exceptions.
- Defensive engineering principles, such as exponential backoff algorithms and dynamic anomaly detection (baseline signatures).

## Disclaimer
**This tool is designed for educational and authorized security testing purposes only.** 
Usage of this tool for attacking targets without prior mutual consent is illegal. It is the end user's responsibility to obey all applicable local, state, and federal laws. Developers assume no liability and are not responsible for any misuse or damage caused by this program.
