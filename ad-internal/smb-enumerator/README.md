# SMB Share Enumerator

A professional, modular offensive security utility for enumerating Active Directory and Windows Server Message Block (SMB) network shares.

## Features
- **Concurrent Execution:** Fast enumeration across massive /24 or /16 subnets using `ThreadPoolExecutor` for optimized I/O bound network scanning.
- **Protocol Precision:** Bypasses standard Windows OS networking stacks entirely by using `impacket` for raw SMB/DCERPC communication.
- **Authentication Flexibility:** Supports cleartext passwords, NTLM Pass-the-Hash (PtH), and unauthenticated Null Sessions.
- **Active Access Verification:** Systematically verifies Read access and safely checks Write access by attempting to create and immediately delete a temporary file.
- **Actionable Reporting:** Provides clean, live terminal output via `rich` tables and supports JSON export for ingestion into platforms like BloodHound or ELK.
- **Strict Validation:** Uses `pydantic` to enforce data types and prevent mid-scan crashes due to malformed targets or credentials.

## Use Cases
During internal network VAPT (Vulnerability Assessment and Penetration Testing) or red team engagements, testers often encounter large networks suffering from permission drift. This tool is designed for the **Network Enumeration and Lateral Movement** phases:
- **Null Session Hunting:** Rapidly scanning a subnet to find misconfigured servers that allow unauthenticated guest accounts to view internal directories.
- **Sensitive Data Discovery:** Mapping out which shares a compromised low-privileged domain user can access to hunt for hardcoded credentials, configuration files, or backups (e.g., NTDS.dit).
- **Payload Hosting Identification:** Flagging shares where a user has Write access, identifying potential vectors for DLL hijacking, watering hole attacks, or hosting malicious payloads for lateral movement.

## Tech Stack
- **Language:** Python 3.8+
- **Core Protocol Library:** `impacket` (SMBv1/v2/v3, DCERPC `srvsvc` named pipes)
- **CLI Framework:** `typer`
- **Output & Logging:** `rich`, `logging`
- **Data Validation:** `pydantic`
- **Network Utilities:** `netaddr`

## Project Architecture
The tool strictly avoids the "god script" anti-pattern and is built as a maintainable software package:

- **UI Layer (`cli.py`):** Uses Typer to handle user arguments, flags, and help menus.
- **Configuration & Validation (`config.py`):** Uses Pydantic models to strictly validate IPs, CIDRs, and authentication parameters before touching the network.
- **Orchestration (`scanner.py`):** Manages a ThreadPool, safely dispatching IP addresses to worker threads and handling thread-safe data aggregation.
- **Protocol Interaction (`smb_client.py`):** Encapsulates all Impacket logic. It handles socket connections, timeouts, NTLM authentication, and executes the `NetShareEnum` RPC call via the `\pipe\srvsvc` interface.

```text
smb-enumerator/
├── smb_enum/
│   ├── cli.py              # UI Entry Point
│   ├── config.py           # Pydantic validation
│   ├── core/
│   │   ├── scanner.py      # Concurrency orchestrator
│   │   └── smb_client.py   # Impacket SMB/DCERPC wrapper
│   └── utils/
│       ├── file_io.py      # Target parsing & JSON export
│       ├── formatters.py   # Rich table generation
│       ├── logger.py       # Centralized logging
│       └── exceptions.py   # Custom error handling
├── smb_enum_run.py         # Executable wrapper
└── requirements.txt
```

## Installation
Requires Python 3.8 or higher. It is highly recommended to use a virtual environment.

```bash
git clone https://github.com/yourusername/smb-enumerator.git
cd smb-enumerator
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Usage
The tool accepts individual IPs, hostnames, CIDR notations, or text files containing targets.

```bash
# View the help menu and all available flags
python smb_enum_run.py --help
```

### Example Workflow

**1. Initial Discovery (Unauthenticated):**
You land on the network and want to identify open shares without credentials.
```bash
python smb_enum_run.py 10.10.10.0/24
```

**2. Standard Enumeration (Authenticated):**
You compromise the `svc_backup` account and want to see what it can access.
```bash
python smb_enum_run.py 10.10.10.0/24 -u "svc_backup" -p "Password123" -d "CORP.LOCAL"
```

**3. Advanced Enumeration (Pass-the-Hash & Write Checking):**
You dump hashes, extract the Administrator NT hash, and want to check specifically for Write access across a list of key servers. You also export the results to JSON for your report.
```bash
python smb_enum_run.py targets.txt -u "Administrator" -H "31d6cfe0d16ae931b73c59d7e0c089c0" -d "CORP.LOCAL" --check-write --json results.json
```

## Example Output
```text
[12:04:33] Starting scan against 256 targets with 20 threads...
           [10.10.10.5] Authentication Successful (Null Session: False)
           [10.10.10.5] Found 4 shares.
           [10.10.10.5] READ ACCESS confirmed on share: SYSVOL
           [10.10.10.5] READ ACCESS confirmed on share: NETLOGON
           [10.10.10.5] WRITE ACCESS confirmed on share: Public
           [10.10.10.12] Connection refused on port 445 (Firewall/Closed)
           Scan complete.

                             SMB Share Enumeration Results                              
┏━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Host        ┃ Share Name ┃ Read Access ┃ Write Access ┃ Remark                       ┃
┡━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ 10.10.10.5  │ ADMIN$     │      No     │      N/A     │ Remote Admin                 │
│ 10.10.10.5  │ C$         │      No     │      N/A     │ Default share                │
│ 10.10.10.5  │ SYSVOL     │     Yes     │      No      │ Logon server share           │
│ 10.10.10.5  │ Public     │     Yes     │      Yes     │                              │
└─────────────┴────────────┴─────────────┴──────────────┴──────────────────────────────┘
```

## Detection / OPSEC Notes
- **Account Lockouts:** The script does *not* password spray. It tests the single provided credential set against targets. Provided the credentials are correct, it will not cause lockouts.
- **Event Logs:** 
  - Successful authentications will generate **Event ID 4624** (Logon) on the target.
  - The `--check-write` flag actively creates and deletes a file. If detailed file auditing is enabled, this will trigger **Event ID 5145** (Network share object checked for access) and **Event ID 5140** (Network share object accessed).
- **Network Noise:** Concurrent threaded scanning (`-t 20`) across a `/16` subnet will generate a highly visible spike in traffic on port 445. Throttle the threads (`-t 3`) for stealthier operations.

## Limitations
- This tool does not recursively crawl directories or download files (spidering). It only verifies access at the root level of the share.
- It does not support Kerberos authentication (Pass-the-Ticket / `.ccache` files) natively in this version.

## Future Improvements
- **Kerberos Integration:** Add support for `KRB5CCNAME` environmental variables to authenticate via Ticket Granting Tickets (TGTs).
- **Regex File Spidering:** Add a flag to recursively search readable shares for specific file extensions (`.ps1`, `.config`, `.kdbx`) or regex patterns (e.g., `password=`).
- **BloodHound Ingestion Format:** Output results in a format directly ingestible by BloodHound custom queries (e.g., `HasWritePrivilege`).

## Learning Objectives
By studying this codebase, developers and junior security engineers can learn:
1. **Network Protocol Engineering:** How to bypass OS-level network abstraction and interact directly with Windows DCERPC named pipes (`\pipe\srvsvc`).
2. **Concurrency Patterns:** How to safely implement `ThreadPoolExecutor` and thread locks for fast, I/O-bound network scanning in Python.
3. **Offensive Architecture:** How to structure security tooling using modern engineering standards (`pydantic` validation, `typer` UI separation) rather than writing unmaintainable, single-file "hacker scripts."

## Disclaimer
This tool is provided for educational and authorized security testing purposes only. The author(s) and contributors are not responsible for any misuse or damage caused by this software. Always ensure you have explicit, written permission from the network owner before executing this tool against any systems.
