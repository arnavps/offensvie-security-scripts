# Technical Operational Notes - Subdomain Collector

This document outlines key technical decisions, design trade-offs, and future extensibility recommendations for the Subdomain Collector platform.

## Design Decisions and Trade-offs

### 1. Unified Asynchronous DNS Validation
Instead of running individual DNS queries inside passive and active modules, the collector decouples candidate extraction from DNS validation:
- **How it works**: The extraction modules (such as `brute_force.py`) purely stream hoststrings into a centralized event loop orchestrator (`engine.py`).
- **Trade-off/Benefit**: This minimizes duplicate code and optimizes overall memory usage. It also guarantees that all domains are queried using a uniform pool of resolvers, under a unified concurrency limit controlled by a single `asyncio.Semaphore`.

### 2. Wildcard DNS Mitigation Strategy
Many internal and external corporate networks use Wildcard DNS rules (`*.example.com` resolves to a catch-all IP). A naive brute-forcer will falsely record tens of thousands of active nodes.
- **Our Implementation**: The `AsyncDNSResolver` executes a pre-flight wildcard test against a randomized prefix (e.g. `d3k9a7v1z5x8y2.example.com`). If it successfully resolves:
  1. The resolution IP address list is stored in a `wildcard_ips` cache.
  2. The `wildcard_detected` flag is set to `True`.
  3. During active resolution checks, if a candidate's resolved IPs matches or is a subset of the catch-all wildcard IPs, its status is logged as `WildcardPolluted` instead of `Active`, filtering out false-positives.

### 3. Asynchronous HTTP Requests
We utilized `httpx` instead of standard `requests` because `httpx` natively supports async client pooling. This permits our passive engines to fire HTTPS requests concurrently to remote servers, preventing blocking latency issues during standard execution.

---

## Operational Security Considerations

### Rate-Limiting & SIEM Bypass
Standard, high-velocity DNS resolution checks can easily trip threshold-based alarms on client DNS servers or enterprise firewalls.
- **Mitigation**: Adjust `concurrency_limit` and `timeout` in `config/settings.yaml` depending on environment constraints. Lower concurrency levels to simulate slower, stealthier human-like inspection intervals if testing highly restrictive client scopes.

### Scope Control Guardrails
To prevent unintentional network interaction with out-of-scope targets (a common issue in bug bounties and corporate VAPTs):
- The `DomainValidator` verifies that every candidate strictly ends with `.{root_domain}` or matches `{root_domain}`. This filters out spoofed domains (e.g., `example.com.attacker.com` pointing back to external servers) parsed during passive scraping.

---

## Future Extensibility Roadmap

1. **Permutations Generator**: Integrate a permutation candidate builder module that parses initial passive results and generates variations based on standard patterns (e.g., if `staging1` is found, automatically generate and test `staging2`, `staging3`).
2. **Additional Passive Intelligence Integrations**:
   - **Shodan / Censys**: Queries certificate databases. Requires authentication headers.
   - **Virustotal**: Passive domain relationship mapping API.
   - **AlienVault OTX**: Open Threat Exchange active indices.
3. **Database Sink**: Implement a SQLite persistence sink to allow analysts to perform chronological "diffs" over consecutive days to detect newly exposed subdomains.
