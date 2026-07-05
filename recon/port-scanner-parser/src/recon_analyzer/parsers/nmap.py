import defusedxml.ElementTree as ET
from typing import Iterator
from ..models.host import Host, Service

class NmapParser:
    """Streams large Nmap XML files safely and yields normalized Host objects."""
    
    def __init__(self, file_path: str):
        self.file_path = file_path

    def parse(self) -> Iterator[Host]:
        # iterparse prevents loading massive XML files entirely into RAM
        context = ET.iterparse(self.file_path, events=("end",))
        
        for event, elem in context:
            if elem.tag == "host":
                host = self._parse_host(elem)
                if host:
                    yield host
                # Free memory immediately after processing the element
                elem.clear()

    def _parse_host(self, host_elem) -> Host | None:
        status_elem = host_elem.find("status")
        if status_elem is None or status_elem.get("state") != "up":
            return None
            
        address_elem = host_elem.find("address")
        if address_elem is None:
            return None
            
        ip_addr = address_elem.get("addr")
        services = []
        
        ports_elem = host_elem.find("ports")
        if ports_elem:
            for port in ports_elem.findall("port"):
                state_elem = port.find("state")
                state = state_elem.get("state") if state_elem is not None else "unknown"
                
                if state != "open":
                    continue  # Filter out closed/filtered ports by default
                    
                service_elem = port.find("service")
                services.append(Service(
                    port_id=int(port.get("portid", 0)),
                    protocol=port.get("protocol", "tcp"),
                    state=state,
                    name=service_elem.get("name") if service_elem is not None else None,
                    product=service_elem.get("product") if service_elem is not None else None,
                    version=service_elem.get("version") if service_elem is not None else None
                ))
                
        # Only return hosts that actually have open services
        return Host(ip_address=ip_addr, status="up", services=services) if services else None
