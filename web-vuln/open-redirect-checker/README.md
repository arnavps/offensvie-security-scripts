# Asynchronous Open Redirect Detector

A production-grade, highly modular, and extensible asynchronous HTTP security analysis framework built in Python 3.11+ using `aiohttp` to inspect web redirection behaviors and validate unauthorized open redirect vulnerabilities.

---

## 1. What Is This Tool

This tool automates the detection and verification of open redirect vulnerabilities (`CWE-601`) across target web applications. By utilizing non-blocking asynchronous requests, it mutates query variables and injects bypass path structures, following redirection pathways manually to confirm if a session can be hijacked to an untrusted external domain.

- **Who it is useful for**: Security Engineers, Penetration Testers, and Bug Bounty Researchers.
- **Where it fits in offensive security**: Reconnaissance validation, active vulnerability scanning, and post-discovery verification pipelines.

---

## 2. Why I Built It

During active security engagements, validating open redirects is often a tedious process of manually identifying redirection parameters (e.g. `?url=`, `?next=`, `?redirect=`), crafting payloads, and checking them in a browser or sequential curl script. 

Existing web application scanners are either overly heavy (requiring full crawler setups) or blind (automatically following redirects inside standard libraries without capturing the intermediary redirect chain or detecting recursive loop traps). 

I built this framework to:
- Establish a high-throughput validation engine that inspects redirection intermediate hops safely under explicit concurrency throttling.
- Learn standard asynchronous connection pool patterns using `aiohttp.TCPConnector`.
- Design an extensible polymorphic engine where security engineers can register custom inspection rules as separate plugins without touching the core orchestration logic.

---

## 3. Problem Statement

Modern web applications frequently implement redirect pathways for user navigation, Single Sign-On (SSO) handshakes, and OAuth callback routines. If input validation is poorly implemented on these parameters, attackers can inject arbitrary destinations. 

While open redirects are often categorized as "low severity," they represent a critical bridge in the exploit chain. Attackers rely on open redirects to make phishing emails look completely legitimate (by using the trusted company's root domain in the visible link) before silently redirecting victims to credential-harvesting portals. Additionally, they are key vectors in OAuth token disclosure attacks.

---

## 4. Features

### Core Features
- **Asynchronous HTTP Client Engine**: High-throughput inspect cycles utilizing pooled keep-alive TCP connections.
- **Unified Parameter Normalization**: Pre-flight validation layer standardizing domain inputs and recovering missing schemes.
- **JSON Intelligence Reports**: Serializes finding parameters, hops, and severities to standard structured JSON files.

### Advanced Features
- **Polymorphic Checker Architecture**: ABC-based checkers structure allowing new test vectors to be registered dynamically.
- **Manual Redirect Chain Tracking**: Completely bypasses automatic redirect loops to inspect intermediate response headers, status codes, and locations individually.
- **Zero-Waste Loop Detection**: Tracks a visited URL memory cache per request to catch recursive redirects instantly on the first repeat, terminating safely.

---

## 5. Architecture / Workflow

The framework follows a decoupled, sequential flow where target ingestion, validation, parameter mutation, request dispatching, and report exporting are strictly isolated:

```text
       [ Target Input ]
              │
              ▼
    [ DomainValidator ] ────────> Normalize URL & Scheme
              │
              ▼
     [ DetectionEngine ] ───────> Resolves YAML settings.yaml
              │
      ┌───────┴───────┐
      ▼               ▼
[ ParamMutation ] [ PathInjection ] ──> Generates test vectors
      └───────┬───────┘
              │
              ▼
     [ AsyncHTTPClient ] ───────> Acquirer Semaphore slot
              │
              ▼
     [ Request Dispatch ] ──────> allow_redirects=False
              │
      ┌───────┴───────┐
      ▼               ▼
(Final Target)  (Redirect Hop) ──> Record RedirectHop
      │               │
      │               ▼
      │         [ Loop Check ] ──> Visited? Yes ──> LoopError
      │               │
      │               ▼ No ──> Keep-alive close ──> Next Hop
      ▼               │
    [ Findings Mapping ] <────┘
              │
              ▼
     [ Exporter Utility ] ──────> JSON / Standard Stderr report
```

---

## 6. Technical Concepts Used

- **Asynchronous IO & Semaphores**: Leverages `asyncio` for non-blocking concurrent requests execution, governed by `asyncio.Semaphore` to prevent socket exhaustion or target DDoS.
- **Redirection Isolation**: Manually handles HTTP 3xx responses via `allow_redirects=False` rather than native standard library loops to inspect and release intermediary socket layers.
- **URL Parameter preservation**: Implements query parsing using ordered tuples (`parse_qsl`) to maintain duplicate query keys and exact sequencing structures.
- **Polymorphism Design Pattern**: Utilizes an Abstract Base Class (`BaseRedirectChecker`) defining runtime checking contracts for plugins.

---

## 7. Libraries Used

- `aiohttp`: High-performance asynchronous HTTP networking engine.
- `multidict` & `yarl`: Parsing and standardizing complex, special-character-heavy URL structures safely.
- `pyyaml`: Loading structured scanning settings, thread counts, and target payloads externally.

---

## 8. Challenges Faced

- **Preventing Socket Leakage during Redirection**: Standard async libraries buffer response bodies or leave connection handles open when redirects are handled manually. To solve this, we explicitly call `await response.release()` immediately after capturing the header values of an intermediate hop, before moving to the next.
- **Redirection Loop Safety**: Circular redirects (e.g. A -> B -> A) can lead to infinite loops. We solved this by implementing a fast per-path memory set that halts immediately on the first repeated URL, recording a `RedirectLoopDetected` error.
- **URL Encoding Preservation**: Injecting injection bypass strings (e.g. `//evil.com` or `/\\evil.com`) requires careful reconstruction to prevent the standard URL parser from dropping backslashes. We utilized clean `urllib.parse` reconstructions to ensure exact payloads are sent over the wire.

---

## 9. Security Relevance

- **For Attackers**: Open redirects are utilized in highly targeted phishing campaigns, OAuth callback flow hijackings, and proxying SSRF vulnerabilities.
- **For Pentesters**: Demonstrates to clients the risk of using unvalidated user inputs in redirection controllers, showing full exploitation paths using clean JSON reports.
- **Bug Bounty Relevance**: Confirms low-effort, high-impact bugs with high-fidelity proofs of concept.

---

## 10. Limitations

- **No JavaScript Execution**: The engine does not execute client-side scripts. Open redirects triggered through `window.location` changes inside JS files cannot be detected.
- **No Headless Browser Emulation**: Inspects server-side HTTP behavior only; does not validate DOM-based validation bypasses.

---

## 11. Future Improvements

- **DOM redirection parsing**: Integrating a lightweight headless browser crawler module to inspect DOM-based `window.location` mutations.
- **OAuth flow fuzzer**: Implementing dynamic checks validating OAuth callback parameters (`redirect_uri`).
- **Dynamic Port scanning**: Supporting port mutations alongside domain mutations.

---

## 12. Example Usage

Ensure you are inside the `web-vuln/open-redirect-checker/` directory:

```bash
# 1. Set the python path to the current directory
export PYTHONPATH="."   # On Linux/macOS
$env:PYTHONPATH="."     # On Windows PowerShell

# 2. Run open redirect check against a target and save report
python -m open_redirect_detector.main -t "https://httpbin.org/redirect-to?url=https://safe.com" -o report.json
```

### Sample CLI Report Output

```text
============================================================
 SECURITY DETECTION REPORT FOR: https://httpbin.org/redirect-to?url=https://safe.com
============================================================
[!] WARNING: TARGET IS VULNERABLE TO OPEN REDIRECTS!
------------------------------------------------------------
  [1] Vector  : QueryParameterMutation
      Module  : ParamMutationChecker
      Payload : evil.com
      Fuzzed  : https://httpbin.org/redirect-to?url=evil.com
      Resolved: http://evil.com/
      Status  : 302
------------------------------------------------------------
Total vector paths tested: 14
Total vulnerabilities confirmed: 7
============================================================
```

---

## 13. Ethical Disclaimer

This project is intended strictly for authorized security testing, educational purposes, and defensive validations on systems you own or have explicit permission to test. Unauthorized scanning against third-party systems is illegal and violates standard terms of service. The developers assume no liability for misuse or damage caused by this software.
