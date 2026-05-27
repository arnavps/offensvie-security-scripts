# Penetration Testing Notes: JWT Analysis

## Methodology

When testing JWTs in the wild, follow this workflow:

1. **Information Gathering**:
   - Extract JWTs from `Authorization: Bearer` headers, cookies, or local storage.
   - Run `jwt-analyzer` to get a quick visual breakdown of the header and payload.
   
2. **Algorithm Tampering (The "None" Exploit)**:
   - If the analyzer flags that `alg=none` is accepted (or if you just want to test it), change the header to `{"alg": "none"}` and strip the signature.
   - Forward the request. If accepted, you have authentication bypass.
   
3. **Key Confusion Attacks (RS256 to HS256)**:
   - If the token uses `RS256` (Asymmetric), the server expects an RSA public key.
   - If you have the server's public key, change the algorithm to `HS256` (Symmetric) and sign the token using the *public key* as the HMAC secret.
   - If the backend uses the same `verify()` function blindly, it will validate your signature.
   
4. **Information Disclosure**:
   - Review the analyzer's "Potential Sensitive Data Exposed" section. 
   - Look for internal IP addresses, database IDs (`uid`), roles (`is_admin: false`), or cleartext secrets.
   
5. **Signature Cracking**:
   - If the algorithm is symmetric (e.g., `HS256`), try to crack the signature offline.
   - Save the token to a file and run Hashcat:
     `hashcat -m 16500 token.txt wordlist.txt`

## Future Development Ideas

- Integrate directly into Burp Suite as a Jython extension.
- Add an automated signature cracking module that runs in a background thread.
