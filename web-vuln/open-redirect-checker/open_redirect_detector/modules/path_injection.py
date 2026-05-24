"""
Path Injection / Authority Bypass open redirect inspection module.
"""
from typing import List, Dict, Any
from urllib.parse import urlparse, urlunparse

from open_redirect_detector.core.base_checker import BaseRedirectChecker
from open_redirect_detector.core.http_client import AsyncHTTPClient

class PathInjectionChecker(BaseRedirectChecker):
    """
    Appends bypass path payloads (e.g. //evil.com, /\\evil.com) to check if 
    relative path filters are misconfigured on the target.
    """
    async def run_checks(self, client: AsyncHTTPClient) -> List[Dict[str, Any]]:
        findings: List[Dict[str, Any]] = []
        payload_targets = self.payload_config.get("targets", ["//evil.com"])
        
        parsed = urlparse(self.target_url)
        
        # We only apply path mutations on targets containing paths or base origins
        base_components = (parsed.scheme, parsed.netloc, "", "", "", "")
        base_origin = urlunparse(base_components)
        
        for payload in payload_targets:
            # We construct a fuzzed path directly
            # e.g., https://target.com//evil.com
            if not payload.startswith("/"):
                fuzzed_path = "/" + payload
            else:
                fuzzed_path = payload
                
            fuzzed_url = base_origin + fuzzed_path
            
            res = await client.inspect_url("GET", fuzzed_url)
            
            vulnerable = False
            final_destination = res.get("final_destination", "")
            final_parsed = urlparse(final_destination)
            
            if any(term in final_parsed.netloc for term in ("evil.com", "google.com")):
                if final_parsed.netloc != parsed.netloc:
                    vulnerable = True

            findings.append({
                "module": self.__class__.__name__,
                "vector": "PathInjectionBypass",
                "test_url": fuzzed_url,
                "payload": payload,
                "status_code": res.get("status"),
                "resolved_url": final_destination,
                "redirect_hops_count": len(res.get("redirect_chain", [])),
                "is_vulnerable": vulnerable,
                "error": res.get("error")
            })

        return findings
