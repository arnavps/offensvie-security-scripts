# Detection Engineering & Security Telemetry Guide

To detect SSRF attempts, defenders must instrument application-level logging, DNS query logs, and egress proxy telemetry. Relying solely on web server access logs (which record incoming requests) is insufficient because they lack context on what the backend server subsequently fetched.

---

## 1. Outgoing Egress Log Schema
The validation library and HTTP client middleware should emit structured JSON logs whenever an outbound request is evaluated.

### Log Event Example (Blocked Attack)
```json
{
  "timestamp": "2026-06-18T13:00:00Z",
  "log_level": "WARNING",
  "event_type": "SSRF_PREVENTED",
  "actor": {
    "user_id": "usr_99812",
    "ip_address": "203.0.113.50",
    "user_agent": "Mozilla/5.0..."
  },
  "request": {
    "method": "GET",
    "url": "http://169.254.169.254/latest/meta-data/iam/security-credentials/",
    "host": "169.254.169.254",
    "port": 80
  },
  "action": {
    "decision": "BLOCKED",
    "reason": "Target IP falls within the restricted Link-Local cloud metadata blocklist (169.254.0.0/16)."
  }
}
```

---

## 2. SIEM Detection Rules

### A. Splunk SPL: Blocked Outbound Attempts
Finds events where the security middleware blocked an outbound connection:
```splunk
index=application_logs event_type="SSRF_PREVENTED"
| stats count by request.host, request.port, action.reason, actor.ip_address
```

### B. Elastic KQL: Cloud Metadata Exfiltration Attempts
Identifies direct requests containing metadata address indicators:
```kql
event_type: "SSRF_PREVENTED" AND (request.host: "169.254.169.254" OR request.url: *metadata* OR request.url: *instance-identity*)
```

### C. Sigma Rule: Outbound Requests to Private Address Ranges
This generic Sigma rule detects applications resolving hostnames to local/private network ranges:

```yaml
title: Outbound Connection Attempt to Private IP from Application
id: a7e3b5e4-23b9-4e45-8f64-d390a3a2d21a
status: experimental
description: Detects when the application-level validator resolves a host to RFC1918 or loopback IP ranges.
logsource:
    category: application
    product: webserver
detection:
    selection:
        event_type: "SSRF_PREVENTED"
    filter_reason:
        action.reason: 
            - "*private subnet*"
            - "*loopback*"
            - "*restricted range*"
    condition: selection and filter_reason
falsepositives:
    - Internal webhook systems explicitly configured to call inside a private network partition (these should be allowlisted by domain).
level: high
```

---

## 3. Monitoring Dashboard Layout Design

A dedicated security monitoring dashboard for SSRF telemetry should display:

### 1. Alert Counters (Real-time)
*   **Total Prevented SSRF Attempts:** Total count of blocked requests.
*   **Unique Blocked Hosts:** Count of unique destination domains/IPs requested.
*   **Unique Attacker IPs:** Source IPs triggering the most block events.

### 2. Time-Series Metrics
*   **SSRF Blocks vs. Time:** Spikes indicate active vulnerability scanning or automated scraping against candidate parameters.
*   **Outbound Call Latency Log:** Spikes in latency might represent blind SSRF scanners testing time-based responses against closed internal ports.

### 3. Geographic & Network Visuals
*   **Top Requested Prohibited Ports:** Visualizes if scans are looking for SSH (`22`), Redis (`6379`), or Memcached (`11211`).
*   **Destination Network Breakdown:** Ratio of blocked requests targeting `127.0.0.1` vs. `169.254.169.254` vs. private Class A/B/C subnets.
