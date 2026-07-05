# LDAP Query Helper

## Executive Summary
LDAP Query Helper is a Python-based utility designed to facilitate authenticated queries against Lightweight Directory Access Protocol (LDAP) servers. It provides a clean, object-oriented wrapper around the `python-ldap` library, simplifying the process of establishing connections, binding with credentials, and executing subtree searches.

## Features
*   **Simple Authentication:** Handles simple binding using DN (Distinguished Name) and password credentials.
*   **Subtree Searching:** Executes LDAP search operations specifically targeting the `SCOPE_SUBTREE`, allowing for deep directory queries.
*   **Callback Support:** Supports passing custom callback functions to process search results incrementally as they are returned.
*   **Connection Management:** Automatically handles binding and unbinding from the LDAP server to ensure clean connection lifecycles.

## Architecture Overview
The project is structured as an installable Python package (`ldap_simple_search`). At its core is the `LDAPSearch` class, which manages the state of the LDAP connection and exposes a simplified API for querying. It abstracts away the verbosity of the underlying `python-ldap` C-bindings, wrapping connection initialization, error handling, and result iteration into clean, maintainable methods.

## Installation
Ensure you have the necessary system dependencies for `python-ldap` (e.g., `libldap2-dev` and `libsasl2-dev` on Debian/Ubuntu).

```bash
# Install the package locally
pip install .
```

## Configuration
Configuration is handled programmatically during the instantiation of the `LDAPSearch` class. You must provide the URI, Bind DN, and Password.

## Usage Examples

**Basic Search Script:**
```python
from ldap_simple_search.search import LDAPSearch

# Initialize the connection
ldap_client = LDAPSearch(
    uri="ldap://sample-dc.local",
    bind_dn="CN=ReadOnlyUser,CN=Users,DC=sample-dc,DC=local",
    password="SuperSecretPassword123"
)

# Execute a search
results = ldap_client.search(
    base_dn="DC=sample-dc,DC=local",
    searchFilter="(objectClass=user)",
    searchAttribute=["cn", "mail"]
)

# Process results
for dn, attributes in results:
    print(f"User: {dn}")
```

## Directory Structure
```text
ldap-query-helper/
├── setup.py                        # Package installation script
├── LICENSE                         # License definition
├── README.md                       # Repository overview
└── ldap_simple_search/             # Main package module
    ├── __init__.py                 # Package initializer
    └── search.py                   # Core LDAPSearch class implementation
```

## Development Workflow
Development involves expanding the `LDAPSearch` class to support more advanced LDAP features, such as paging controls, different binding mechanisms (like SASL/GSSAPI), and varying search scopes (e.g., `SCOPE_BASE`, `SCOPE_ONELEVEL`).

## Testing
No formal testing suite is currently included. Testing requires setting up an active LDAP directory server (like OpenLDAP or Active Directory) to execute integration tests.

## Logging and Error Handling
The library uses the standard Python `logging` module (`logger = logging.getLogger(__name__)`). It specifically catches `ldap.INVALID_CREDENTIALS` and generic `ldap.LDAPError` exceptions, routing the error descriptions to the logger as errors and raising the exceptions for the caller to handle.

## Dependencies
*   `python-ldap`

## Contributing Guidelines
Contributions aimed at adding support for LDAPS (LDAP over SSL) configuration, pagination, and a command-line interface (CLI) wrapper are encouraged.

## License
Provided under the terms specified in the `LICENSE` file.