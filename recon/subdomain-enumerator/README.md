# Subdomain Collector

An engineering-grade, high-performance asynchronous subdomain discovery and DNS verification framework written in Python 3. Used during passive and active reconnaissance phases of security assessments (VAPT, bug bounties, and ASM).

## Key Features

- **Asynchronous DNS Validation**: Utilizes `dnspython` to query recursive resolvers concurrently with fine-grained throttling.
- **Passive Intelligence Modules**: Integrates multiple passive OSINT aggregators:
  - Certificate Transparency logs scraped via `crt.sh`.
  - DNS host search results fetched from the `HackerTarget` database.
- **Active Brute Forcing Candidate Generator**: Streams wordlist inputs and pipes them dynamically into the unified resolution engine.
- **Pre-Flight Wildcard DNS Protection**: Automatically detects wildcard records (e.g. `*.target.com`) by testing randomized inputs and compares results to prevent wildcard pollution.
- **Strict Scope Guardrails**: Restricts output strictly to target-specific subdomains to avoid out-of-scope leaks.
- **Structured JSON Reporting**: Automatically serializes final findings into standardized JSON files for pipeline integrations.

---

## Architecture Overview

```text
subdomain_collector/
├── config/
│   └── settings.yaml             # Settings for timeouts, resolvers, & concurrent throttles
├── subdomain_collector/
│   ├── main.py                   # Main CLI entrypoint and argument parser
│   ├── core/
│   │   ├── base_collector.py     # ABC Interface for discovery modules
│   │   ├── engine.py             # Orchestrates collection and validation loops
│   │   └── resolver.py           # Asynchronous DNS resolution engine
│   ├── modules/
│   │   ├── crtsh.py              # crt.sh passive scraper
│   │   ├── hackertarget.py       # HackerTarget passive lookup
│   │   └── brute_force.py        # Active wordlist candidate generator
│   └── utils/
│       ├── logger.py             # Custom colored console logging formatter
│       └── validator.py          # Input syntax and scope validation rules
```

---

## Installation

Ensure you have Python 3.8+ installed. Clone this repository, navigate to this directory, and install dependencies:

```bash
pip install -r requirements.txt
```

---

## Usage

Run standard operations (Passive + Active Brute-forcing) against a target domain:

```bash
python -m subdomain_collector.main -d example.com -o results.json
```

### Options

| Command Flag | Description |
|---|---|
| `-d`, `--domain` | **[Required]** The target root domain to query (e.g. `example.com`). |
| `-o`, `--output` | Save full discovery findings and resolved IPs to a structured JSON file. |
| `-c`, `--config` | Path to custom YAML settings configuration file. |
| `--mode` | Selection of `passive`, `active`, or `all` collection modes (default: `all`). |
| `--verbose` | Enable verbose debug output. |

### Running Mode Examples

**Passive Recon Only (No dictionary attacks):**
```bash
python -m subdomain_collector.main -d example.com --mode passive
```

**Active Brute Force Only:**
```bash
python -m subdomain_collector.main -d example.com --mode active -o brute_results.json
```

---

## Testing

Execute the test suites via Python's native `unittest` discovery module:

```bash
python -m unittest discover -s tests
```
