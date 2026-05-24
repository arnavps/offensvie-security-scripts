"""
Parameter Mutation open redirect inspection module.
"""
from typing import List, Dict, Any
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

from open_redirect_detector.core.base_checker import BaseRedirectChecker
from open_redirect_detector.core.http_client import AsyncHTTPClient

class ParamMutationChecker(BaseRedirectChecker):
    """
    Mutates query parameters (e.g. ?url=) with external targets to detect flaws.
    """
    async def run_checks(self, client: AsyncHTTPClient) -> List[Dict[str, Any]]:
        findings: List[Dict[str, Any]] = []
        
        # Load targets and key to fuzz
        fuzz_key = self.payload_config.get("fuzz_param", "url")
        payload_targets = self.payload_config.get("targets", ["evil.com"])
        
        # Parse query components
        parsed = urlparse(self.target_url)
        query_params = parse_qsl(parsed.query, keep_blank_values=True)
        
        # Reconstruct base component
        components = (parsed.scheme, parsed.netloc, parsed.path, parsed.params, "", parsed.fragment)
        
        for payload in payload_targets:
            # Re-generate query string replacing or adding fuzz_key
            replaced = False
            new_params = []
            for k, v in query_params:
                if k == fuzz_key:
                    new_params.append((k, payload))
                    replaced = True
                else:
                    new_params.append((k, v))
            if not replaced:
                new_params.append((fuzz_key, payload))
                
            encoded_query = urlencode(new_params)
            fuzzed_url = urlunparse((
                components[0],
                components[1],
                components[2],
                components[3],
                encoded_query,
                components[5]
            ))
            
            # Request and trace behavior
            res = await client.inspect_url("GET", fuzzed_url)
            
            # Determine if open redirect was triggered
            vulnerable = False
            final_destination = res.get("final_destination", "")
            final_parsed = urlparse(final_destination)
            
            # If the final domain matches the payload domain
            if any(term in final_parsed.netloc for term in ("evil.com", "google.com")):
                if final_parsed.netloc != parsed.netloc:
                    vulnerable = True

            findings.append({
                "module": self.__class__.__name__,
                "vector": "QueryParameterMutation",
                "test_url": fuzzed_url,
                "payload": payload,
                "status_code": res.get("status"),
                "resolved_url": final_destination,
                "redirect_hops_count": len(res.get("redirect_chain", [])),
                "is_vulnerable": vulnerable,
                "error": res.get("error")
            })

        return findings
