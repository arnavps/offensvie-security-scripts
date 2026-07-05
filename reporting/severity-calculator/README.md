# Severity Calculator

A professional CLI utility that standardizes the calculation of vulnerability impact by mapping CVSS vectors alongside business context.

## Features
- Parses standard CVSS v3.1 and v4.0 vectors programmatically.
- Applies asset criticality multipliers to adjust raw technical scores to realistic business risk.
- Outputs human-readable terminal tables or structured JSON for automated reporting workflows.
- Implements strict score capping to ensure valid CVSS maximums (10.0).

## Use Cases
This tool is utilized during the reporting and documentation phase of a Vulnerability Assessment and Penetration Testing (VAPT) engagement. It allows security engineers to quickly translate technical findings into standardized, business-contextualized risk ratings for executive summaries and technical reports.

## Tech Stack
- **Language**: Python 3
- **Libraries**: `cvss` (parsing), `argparse` (CLI routing), `rich` (terminal formatting)
- **Protocols/Standards**: CVSS v3.1, CVSS v4.0

## Project Architecture
The project follows a modular design to ensure maintainability and future extensibility:
- **`severity_calculator.py`**: The main entry point handling CLI arguments and orchestrating the workflow.
- **`core/cvss_parser.py`**: Encapsulates the logic for parsing vectors, isolating version-specific CVSS logic.
- **`core/business_logic.py`**: Houses the risk multipliers and qualitative mapping logic, allowing easy updates to organizational risk models.
- **`utils/formatter.py`**: Separates the presentation layer (Rich tables, JSON serialization) from the core logic.

## Installation
Ensure you have Python 3 installed. Set up a virtual environment and install the required dependencies:

```bash
# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows use: .\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Usage
Run the script by providing a CVSS vector and optional criticality flags.

**Arguments & Flags:**
- `vector` (Positional): The CVSS string.
- `-c, --criticality`: Asset criticality (low, medium, high, critical). Defaults to medium.
- `-j, --json`: Output raw JSON instead of a terminal table.
- `-v, --verbose`: Enable verbose logging.

**Example Commands:**
```bash
python severity_calculator.py "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"
python severity_calculator.py "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H" --criticality high
```

## Example Workflow
1. A penetration tester identifies an unauthenticated Remote Code Execution (RCE) vulnerability.
2. The tester determines the raw CVSS vector is `CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H` (Base 9.8).
3. The tester notes the affected asset is a mission-critical payment gateway.
4. The tester runs the tool with the `--criticality high` flag.
5. The tool outputs the adjusted risk score and qualitative rating to include in the final report.

## Example Output
```text
                        Severity Calculation Results                        
+--------------------------------------------------------------------------+
| Metric                    | Value                                        |
|---------------------------+----------------------------------------------|
| CVSS Version              | 3.x                                          |
| Vector                    | CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H |
| Base Score                | 9.8                                          |
| Original Severity         | Critical                                     |
|---------------------------+----------------------------------------------|
| Asset Criticality         | High                                         |
| Adjusted Risk Score       | 10.0                                         |
| Adjusted Risk Rating      | Critical                                     |
+--------------------------------------------------------------------------+
```

## Detection / OPSEC Notes
As an offline reporting utility, this tool does not interact with target systems and generates no network traffic. There are no OPSEC considerations regarding IDS/WAF visibility.

## Limitations
- Only supports CVSS v3.1 and v4.0. Legacy CVSS v2 is not supported.
- Cannot calculate environmental metrics from raw data points; requires a pre-calculated or standard vector string.

## Future Improvements
- **Batch Processing**: Ingest a CSV of findings and output a processed CSV with adjusted severities.
- **Jira/DefectDojo Integration**: Add export options that format output for automated ticketing systems.
- **Custom Configs**: Allow users to define custom criticality multipliers in a YAML file.

## Learning Objectives
By studying this project, developers and security engineers can learn:
- How to structure a professional, modular Python CLI application.
- How CVSS vectors are programmatically parsed and manipulated.
- The importance of business context in translating technical vulnerabilities into actual risk.

## Disclaimer
This tool is designed for educational purposes and authorized security reporting. It is intended to assist security professionals in documenting and standardizing their findings. Ensure you are following your organization's risk assessment guidelines when applying criticality multipliers.
