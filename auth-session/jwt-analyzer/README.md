# JWT Analyzer

A professional offensive security utility for the rapid triage and analysis of JSON Web Tokens (JWTs).

## Features
- Safely decodes Base64url JWTs without requiring cryptographic verification, allowing analysis of malformed or invalid tokens.
- Automatically detects high-risk misconfigurations such as the `alg=none` authentication bypass vulnerability.
- Flags missing cryptographic signatures.
- Identifies potential Information Disclosure by cross-referencing payload claims against a configurable watch-list (e.g., detecting `is_admin`, `password`, `ssn`, `role`).
- Validates token lifecycle timestamps (`exp`, `nbf`) to highlight session expiration anomalies.
- Provides a clean, colorized terminal interface tailored for rapid visual analysis during security assessments.
- Supports JSON export for seamless integration into broader automation pipelines.

## Use Cases
During a Vulnerability Assessment and Penetration Testing (VAPT) engagement or Bug Bounty hunt, security engineers frequently intercept HTTP requests containing session tokens. `jwt-analyzer` automates the initial triage of these tokens. Instead of manually copying tokens into web-based decoders (which poses an OpSec risk for sensitive client data) or manually parsing Base64 strings, testers can pipe tokens directly into this utility to instantly surface structural weaknesses, configuration errors, and sensitive data exposures.

## Tech Stack
- **Language**: Python 3.9+
- **Libraries**: `typer` (CLI architecture), `rich` (terminal formatting), `pydantic` (data validation), `pyyaml` (configuration management).
- **Protocols/Standards**: JSON Web Token (JWT), Base64url encoding.

## Project Architecture
The architecture follows professional software engineering principles, separating the command-line presentation layer from the core analytical engine.

- **Workflow**: The tool ingests a raw token via standard input, file, or CLI argument. It passes the string to the decoder, which normalizes Base64 padding and extracts the header, payload, and signature components as JSON objects. The analyzer engine then evaluates these components against loaded security heuristics before passing the results to the presentation layer.
- **Modules**:
  - `cli.py`: Orchestrates the execution flow and handles argument parsing.
  - `core/decoder.py`: Responsible for safe token parsing and Base64 padding normalization.
  - `core/analyzer.py`: The vulnerability detection engine containing the core heuristic logic.
  - `utils/`: Contains shared utilities for configuration loading (`config.py`) and stylized logging (`logger.py`).

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/jwt-analyzer.git
cd jwt-analyzer

# Create and activate a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate

# Install the package and dependencies
pip install -e .
```

## Usage

The tool can be executed using the `jwt-analyzer` command.

```bash
# Analyze a token provided directly via argument
jwt-analyzer --token "eyJhbGciOiJIUzI1NiIsInR5..."

# Analyze a token stored in a file
jwt-analyzer --file token.txt

# Pipe a token from another command (useful for chaining tools)
echo "eyJhbGciOiJub25lI..." | jwt-analyzer

# Export the analysis results to a JSON file for further automation
jwt-analyzer --file token.txt --export-json results.json

# Enable verbose logging for debugging
jwt-analyzer --token "eyJhbGciOi..." --verbose
```

## Example Workflow

1. **Interception**: A penetration tester intercepts an API request in Burp Suite and identifies an `Authorization: Bearer <token>` header.
2. **Execution**: The tester copies the token and passes it to `jwt-analyzer --token "<token>"`.
3. **Analysis**: The tool instantly decodes the token and displays the payload. It highlights in red that the token is utilizing the `none` algorithm and lacks a signature.
4. **Exploitation**: The tester modifies the payload (e.g., changing `"role": "user"` to `"role": "admin"`), re-encodes the token with the `none` algorithm, and forwards the modified request to achieve an authentication bypass.

## Example Output

```text
JWT Analyzer v0.1.0
Offensive Security Utility

[+] Decoding JWT...
[+] Analyzing JWT...

╭─────────────────────── Header ───────────────────────╮
│ {                                                    │
│   "alg": "none",                                     │
│   "typ": "JWT"                                       │
│ }                                                    │
╰──────────────────────────────────────────────────────╯
╭─────────────────────── Payload ──────────────────────╮
│ {                                                    │
│   "sub": "1234567890",                               │
│   "role": "admin",                                   │
│   "password": "secretpassword"                       │
│ }                                                    │
╰──────────────────────────────────────────────────────╯

                            Vulnerabilities Found
┏━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Severity ┃ Title                       ┃ Description                        ┃
┡━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ CRITICAL │ Weak or None Algorithm: none│ The token uses a weak algorithm or │
│          │                             │ 'none', allowing signature bypass. │
│ HIGH     │ Missing Signature           │ The token has no signature and may │
│          │                             │ be accepted without verification.  │
│ MEDIUM   │ Sensitive Data Exposure     │ The payload contains claims that   │
│          │                             │ might leak sensitive information...│
└──────────┴─────────────────────────────┴────────────────────────────────────┘

Potential Sensitive Data Exposed:
  - role: admin
  - password: secretpassword
```

## Detection / OPSEC Notes
- **Local Execution**: This tool runs entirely locally and does not make any outbound network requests. It is safe to use on sensitive client tokens without risking data leakage to third-party decoding websites.
- **Stealth**: As it performs passive analysis on intercepted tokens, its usage is completely invisible to the target infrastructure (no IDS/WAF triggers).

## Limitations
- This tool is designed for passive analysis and anomaly detection; it does not actively forge or sign new tokens.
- It does not currently perform offline dictionary attacks or brute-forcing of weak HMAC secrets.
- It does not automatically fetch or verify signatures against remote JSON Web Key Sets (JWKS).

## Future Improvements
- **Signature Cracking Integration**: Integrate an offline dictionary attack module to attempt cracking weak `HS256` secrets directly within the tool.
- **JWKS Verification**: Add a feature to supply a JWKS URL and automatically verify the token's cryptographic signature.
- **Automated Forgery**: Implement a module to generate common tampered variants (e.g., algorithm confusion payloads) for active testing.

## Learning Objectives
By studying and building this project, you will learn:
- The internal structure of JSON Web Tokens and the mechanics of Base64url encoding.
- How to identify critical misconfigurations in authentication mechanisms, such as the `alg=none` exploit.
- Professional Python engineering practices, including modular design, data validation with Pydantic, and building robust CLI applications.
- How to parse and handle malformed data defensively in security tooling.

## Disclaimer
This tool is intended for educational purposes and authorized security testing only. The authors assume no liability and are not responsible for any misuse or damage caused by this program. Ensure you have explicit, written permission from the system owner before targeting any infrastructure.
