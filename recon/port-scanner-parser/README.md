# Port Scanner Parser & Recon Analysis Toolkit

A professional, engineering-grade utility for parsing, analyzing, and reporting on network reconnaissance data. 

This toolkit transforms massive, unstructured scanner outputs into strictly typed, actionable security intelligence. By utilizing streaming parsing techniques and modular data pipelines, it enables security analysts to quickly identify high-risk services, exposed cleartext protocols, and potential attack surfaces without memory exhaustion.

## Features
- **Streaming XML Parsing**: Safely processes multi-gigabyte Nmap XML files using `iterparse` with an O(1) memory footprint.
- **Data Normalization**: Enforces strict typing and data validation using Pydantic, ensuring clean downstream analysis.
- **Risk Enrichment**: Automatically flags and categorizes risky exposures (e.g., cleartext protocols like FTP and Telnet).
- **Modular Pipeline**: Built with a strategy pattern allowing easy integration of new parsers (Masscan, RustScan) and custom analysis plugins.
- **JSON & Markdown Export**: Generates machine-readable output for SIEM/toolchain integration and human-readable reports for client deliverables.
- **Defensive Engineering**: Prevents XML External Entity (XXE) vulnerabilities by strictly utilizing `defusedxml`.

## Use Cases
- **Vulnerability Assessments & Penetration Testing**: Rapidly extract and prioritize targets from massive initial port scans.
- **Red Teaming**: Filter through network noise to locate critical infrastructure and management interfaces.
- **Continuous Monitoring**: Ingest recurring network scans into automated pipelines to detect newly exposed services.

## Tech Stack
- **Language**: Python 3.10+
- **Libraries**: `typer` (CLI), `pydantic` (Data Modeling), `defusedxml` (Secure XML Parsing), `loguru` (Logging), `jinja2` (Reporting)
- **Protocols Involved**: Analyzes TCP/UDP port states, service banners, and protocol metadata.

## Project Architecture
The application follows a strictly decoupled pipeline architecture:
1. **Ingestion (`parsers/`)**: The parser safely streams the raw scan file (e.g., Nmap XML) element by element, preventing memory exhaustion.
2. **Normalization (`models/`)**: Raw XML data is immediately mapped into strongly-typed Pydantic classes (`Host`, `Port`, `Service`).
3. **Analysis (`analyzers/`)**: Normalized objects pass through enrichment layers to assign risk scores and categorize technologies.
4. **Output (`reporters/`)**: Processed data is sent to the requested reporter to generate stylized console output or structured files.

## Installation

Ensure you have Python 3.10+ and [Poetry](https://python-poetry.org/) installed.

```bash
# Clone the repository
git clone https://github.com/yourusername/port-scanner-parser.git
cd port-scanner-parser

# Install dependencies using Poetry
poetry install
```

## Usage

The tool is invoked via a Typer-powered CLI interface.

```bash
# Basic analysis with terminal output
poetry run recon scans/nmap_output.xml

# Analyze and export to JSON for further processing
poetry run recon scans/nmap_output.xml --output results.json
```

## Example Workflow
1. **Active Scanning (External)**: An analyst runs a comprehensive network scan against a client's subnet:
   `nmap -sV -p- -iL targets.txt -oX scans/initial_scan.xml`
2. **Data Ingestion**: The analyst runs the Port Scanner Parser to process the `initial_scan.xml` file.
3. **Intelligence Extraction**: The parser normalizes the data and immediately highlights that `10.0.0.50` has an unauthenticated `vsftpd` instance on port 21.
4. **Action**: The analyst pipes the JSON output into `jq` to extract all IPs with port 80/443 open and feeds them into a web vulnerability scanner.

## Example Output

```text
[*] Analyzing Nmap scan: test_data/sample.xml

[+] Host: 192.168.1.100
    [!] Port 21/tcp - ftp vsftpd
        Port 22/tcp - ssh OpenSSH
    [!] Port 80/tcp - http Apache httpd

[*] Results saved to results.json
```

## Detection / OPSEC Notes
- **Local Execution**: This tool performs **read-only** analysis of existing scan files. It does not generate network traffic, making it entirely invisible to IDS/IPS or network monitoring solutions.
- **Safe Parsing**: It actively defends against maliciously crafted XML files (XXE) that might be planted by defenders attempting to exploit analyst tools.

## Limitations
- **Passive Only**: This tool does not perform active network scanning or validation of the services.
- **Format Support**: Currently, the primary implemented parser supports Nmap XML. Support for Masscan and RustScan requires additional parser implementations.

## Future Improvements
- **Database Backend Integration**: Add support for streaming parsed data directly into an embedded SQLite or DuckDB database to enable complex SQL querying across enterprise-scale datasets.
- **Multi-Tool Correlation**: Implement modules to merge and correlate results from Masscan, RustScan, and Nmap into a unified host model.
- **Historical Diffing**: Add capability to compare `Day 1` vs `Day 2` scans to explicitly highlight state changes (e.g., "New ports opened").
- **Custom Plugin Engine**: Allow analysts to write hot-swappable Python plugins to apply custom organizational risk rules.

## Learning Objectives
By studying and building upon this project, you will learn:
- How to apply standard software engineering patterns (Strategy, MVC) to offensive security tooling.
- The mechanics of processing gigabyte-scale datasets without memory exhaustion (`xml.etree.ElementTree.iterparse`).
- How to safely handle untrusted serialized data to prevent vulnerabilities in your own tools.
- Data normalization techniques using modern Python (`Pydantic`).

## Disclaimer
This tool is designed explicitly for authorized penetration testing, security assessments, and educational purposes. The developers assume no liability and are not responsible for any misuse or damage caused by this tool. Always ensure you have explicit, written permission from the system owner before conducting any security testing.
