# Engineering & Architectural Notes: Open Redirect Detector

This document outlines the architectural decisions, design patterns, and scaling methodologies implemented in the **Open Redirect Detector** framework.

---

## 1. Modular Separation of Concerns

To align with professional security frameworks (like the Subdomain Collector), the framework separates network I/O, validation, orchestration, and inspection modules:

```
                  ┌──────────────────────┐
                  │       settings       │
                  └──────────┬───────────┘
                             │
                             ▼
 ┌──────────┐     ┌──────────────────────┐     ┌──────────────────────┐
 │   CLI    │ ──> │      main.py         │ ──> │  DomainValidator     │
 └──────────┘     └──────────────────────┘     └──────────┬───────────┘
                             │                            │
                             ▼                            ▼
                  ┌──────────────────────┐     ┌──────────────────────┐
                  │   DetectionEngine    │ ──> │   AsyncHTTPClient    │
                  └──────────┬───────────┘     └──────────┬───────────┘
                             │                            │
                             ▼                            ▼
                  ┌──────────────────────┐     ┌──────────────────────┐
                  │ BaseRedirectChecker  │ ──> │   Vulnerability      │
                  │  (Polymorphic ABC)   │     │      Findings        │
                  └──────────────────────┘     └──────────────────────┘
```

- **Polymorphism**: Inspection rules inherit from `BaseRedirectChecker`. The orchestrator `DetectionEngine` does not have hardcoded rule logic; it registers modules dynamically and runs them polymorphically.
- **Isolated I/O**: Network requests are managed solely by `AsyncHTTPClient` inside `core/http_client.py`. Vulnerability checks only pass HTTP verbs and parameters; they never manage low-level network pools or direct socket streams.
- **Memory & Pool Safety**: Concurrency limit is locked globally through the async Semaphore. Manual redirection uses `allow_redirects=False` and cleanly calls `await response.release()` on intermediate hops to protect memory and avoid socket leaks.

---

## 2. Redirection Vulnerability Identification Strategy

An open redirect flaw occurs when a target parameter or path redirects an authenticated session to an untrusted third-party server.

Our framework uses two distinct detection vectors:
1. **QueryParameterMutation**: Targets parameter keys (e.g. `?url=`, `?next=`, `?redirect=`) and replaces them with an external destination like `evil.com`.
2. **PathInjectionBypass**: Appends bypass vectors to the base authority origin (e.g., `//evil.com`, `/\\evil.com`) to catch misconfigured routing filters that allow backslashes or double slashes to resolve as external hosts.

### Verification Flow
When the inspect client requests a fuzzed URL, the redirect chain is traced and returned as a list of dictionaries. The vulnerability engine parses this history and flags an active flaw if:
- The final resolved destination domain matches an untrusted target payload.
- The destination hostname differs from the target root domain hostname.

---

## 3. Scale-Out Capability

The tool is designed to support scanning across thousands of paths:
- **Thread Safety**: Built entirely on top of `asyncio` and `aiohttp` for non-blocking concurrent request execution.
- **Throttling**: The global HTTP client semaphore ensures the target server is never overloaded, respecting rates and limits.
- **Extensibility**: Adding new vulnerability vector checks is as simple as creating a new subclass file in `modules/` and registering it in `main.py`.
