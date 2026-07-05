# SSRF Incident Response Playbook

This document defines the step-by-step incident response playbook for security operations teams when active Server-Side Request Forgery (SSRF) exploitation is suspected or detected.

---

## Phase 1: Detection & Analysis

The goal of this phase is to confirm whether an alert represents a true positive SSRF exploitation attempt.

### 1. Alert Triage
Review incoming telemetry alerts (`SSRF_PREVENTED` or out-of-norm egress logs):
*   **Analyze the payload:** What target hostname or IP was the application requested to fetch?
    *   *Indicator of Compromise (IoC):* Hostnames containing `169.254.169.254`, `localhost`, `127.0.0.1`, or local private addresses (`10.x.x.x`, `192.168.x.x`).
    *   *External DNS callbacks:* Outbound calls resolving to unfamiliar external DNS servers or request bin domains.
*   **Identify the entry point:** Which endpoint and HTTP parameter was exploited (e.g. `/fetch-image?url=...`)?

### 2. Scoping and Impact Assessment
Check if the request was blocked by security middleware:
*   **Case A: Connection Blocked (True Positive - Prevented)**
    *   The request was caught by the validator or egress firewall.
    *   *Action:* No immediate data leak, but update firewall logs and monitor the source IP for further scanning.
*   **Case B: Connection Executed (True Positive - Compromised)**
    *   The request succeeded and returned internal data to the caller.
    *   *Immediate Risk:* If the target was the cloud metadata endpoint, assume the instance's IAM role keys have been compromised.

---

## Phase 2: Containment

The priority is to stop active data exfiltration and prevent the attacker from scanning further internal assets.

### 1. Block the Attacking IP
*   Apply temporary block rules at the Web Application Firewall (WAF) or CDN level for the attacker's source IP address.

### 2. Disable Vulnerable Endpoint
*   If possible, temporarily disable the specific vulnerable route or feature (e.g., disable webhook deliveries or remote image fetches) via feature flags or virtual patching.

### 3. Immediate Egress Isolation
*   If the application container does not require access to the general internet, restrict all outbound egress traffic at the VPC Security Group level.
*   If internet access is required, enforce a proxy whitelist that denies all traffic targeting RFC 1918 subnets and the link-local metadata address (`169.254.169.254`).

---

## Phase 3: Eradication

Eliminate the root cause of the vulnerability.

### 1. Credential Revocation (Critical if Cloud Metadata was Exposed)
*   **Rotate IAM Credentials:** If the metadata service was queried, immediately revoke the temporary security credentials associated with the host's IAM role.
*   **Re-issue API Keys:** Rotate any database credentials, internal service API keys, or API tokens stored on the compromised host, as they may have been harvested via internal reads.

### 2. Code Remediation
*   Deploy the `SSRFValidator` library to sanitize all user-supplied URL inputs.
*   Configure the application HTTP clients to use `DNSRebindingSafeAsyncTransport` to enforce single IP resolution pinning.
*   Ensure redirect handling is disabled or validated.

---

## Phase 4: Recovery & Lessons Learned

### 1. Restore Services
*   Enable the remediated route in staging first; run verification tests.
*   Deploy the patch to production and monitor outbound log metrics for exceptions or drop-offs.
*   Remove temporary WAF blocks on source IPs once the software fix is live.

### 2. Post-Incident Review
*   Perform a root-cause analysis: Why was the validation missing or bypassed?
*   Update the CI/CD pipeline tests to include unit tests checking for private IP subnets and DNS rebinding protections.
