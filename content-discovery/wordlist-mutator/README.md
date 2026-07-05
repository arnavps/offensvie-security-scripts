# Wordlist Mutator

## Executive Summary
Wordlist Mutator is a focused command-line utility designed to generate extensive permutations of a given root string. By applying common capitalization rules, symbol substitutions, and numerical suffixes, it programmatic expands a single base word into a comprehensive dictionary of variations, suitable for testing authentication mechanisms and password policies.

## Features
*   **Capitalization Variations:** Generates permutations by capitalizing individual letters, making the entire string uppercase, or making it lowercase.
*   **Symbol Substitution:** Maps common characters to their symbol equivalents (e.g., 'a' to '@', 's' to '$') and generates combinations of these substitutions.
*   **Suffix Appending:** Appends common numeric and symbolic suffixes (e.g., '123', '!', '??').
*   **Date Appending:** Dynamically appends a range of years relative to the current year (±5 years).
*   **Deduplication:** Automatically removes duplicate entries from the generated list using set operations.

## Architecture Overview
The tool is a standalone Python script utilizing standard library functions. It employs a procedural approach, passing the input string through a sequence of transformation algorithms. The results of each transformation are aggregated into a single list, deduplicated, and written to a text file. The use of `itertools.combinations` allows for mathematical generation of complex substitution patterns.

## Installation
No external dependencies are required. Ensure Python 3.x is installed.
```bash
# Clone the repository and navigate to the directory
cd wordlist-mutator/
```

## Configuration
No configuration files are needed. The tool operates entirely via command-line arguments.

## Usage Examples

**Basic Usage:**
Generate variations of a base word and save them to a default file named after the word.
```bash
python mutate-pw.py CompanyName
```
*Output will be saved to `CompanyName.txt`.*

**Specify Output File:**
```bash
python mutate-pw.py SampleWord custom_list.txt
```

## Directory Structure
```text
wordlist-mutator/
├── mutate-pw.py    # The main executable script
├── LICENSE         # License definition
├── README.md       # Repository overview
└── .gitignore      # Git ignore rules
```

## Development Workflow
Development involves expanding the mutation logic—adding new substitution dictionaries, suffix lists, or transformation rules (like prepending or leetspeak). Changes can be tested immediately by running the script and inspecting the output text file.

## Testing
Testing is manual. Run the script with a sample word and verify the output file contains the expected mutations, the correct suffixes, and no duplicate lines.

## Logging and Error Handling
The script relies on `argparse` for input validation and error handling regarding missing arguments. It does not implement a formal logging framework, opting instead for standard `print()` statements to display the execution summary. File writing is handled inside a standard context manager, which will raise native OS exceptions if permission issues occur.

## Dependencies
*   Python Standard Library (`itertools`, `argparse`, `os`)

## Contributing Guidelines
Contributions are welcome, particularly additions to the `substitutions` dictionary, expanded suffix lists, or the introduction of prefix mutation rules. 

## License
Provided under the terms specified in the `LICENSE` file.

---