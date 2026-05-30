import socket
import ntpath
import random
import string
import logging
from typing import List, Dict, Any, Tuple

from impacket.smbconnection import SMBConnection, SessionError
from impacket.dcerpc.v5 import transport, srvs
from impacket.nmb import NetBIOSTimeout, NetBIOSError

from smb_enum.utils.exceptions import (
    AuthenticationError,
    HostUnreachableError,
    ConnectionRefusedError
)

logger = logging.getLogger("smb_enum")

class SMBEnumClient:
    """
    Wrapper around Impacket's SMBConnection to handle connections,
    authentication, and enumeration in a clean, error-handled way.
    """
    
    def __init__(self, target: str, port: int = 445, timeout: float = 3.0):
        self.target = target
        self.port = port
        self.timeout = timeout
        self.smb_conn = None
        
    def connect_and_login(self, username: str = "", password: str = "", domain: str = "", hashes: str = "") -> bool:
        """
        Attempts to connect and authenticate to the target.
        If username is empty, attempts a Null Session.
        
        Raises domain-specific exceptions on failure.
        """
        try:
            # Set socket timeout
            socket.setdefaulttimeout(self.timeout)
            
            # Initialize SMB Connection
            self.smb_conn = SMBConnection(
                self.target, 
                self.target, 
                sess_port=self.port,
                timeout=self.timeout
            )
            
            # Parse hashes if provided (format LM:NT)
            lmhash = ""
            nthash = ""
            if hashes:
                if ':' in hashes:
                    lmhash, nthash = hashes.split(':')
                else:
                    # If only NT hash is provided
                    nthash = hashes
                    lmhash = "00000000000000000000000000000000"
                    
            # Authenticate
            self.smb_conn.login(username, password, domain, lmhash, nthash)
            return True
            
        except (socket.timeout, NetBIOSTimeout):
            raise HostUnreachableError(f"[{self.target}] Timeout connecting to port {self.port}")
        except ConnectionRefusedError:
            raise ConnectionRefusedError(f"[{self.target}] Connection refused on port {self.port} (Firewall/Closed)")
        except SessionError as e:
            if 'STATUS_LOGON_FAILURE' in str(e) or 'STATUS_ACCESS_DENIED' in str(e):
                raise AuthenticationError(f"[{self.target}] Login failed for user '{username}'")
            # If we hit an unexpected session error during login, we re-raise it
            raise e
        except Exception as e:
             # Catch-all for weird impacket issues or network drops
             if "Connection reset by peer" in str(e):
                 raise HostUnreachableError(f"[{self.target}] Connection reset")
             if "timed out" in str(e).lower():
                  raise HostUnreachableError(f"[{self.target}] Socket timeout")
             raise e

    def list_shares(self) -> List[Dict[str, str]]:
        """
        Uses DCERPC (srvs) to enumerate shares on the target.
        Returns a list of dicts: [{'name': 'C$', 'remark': 'Default share'}]
        """
        if not self.smb_conn:
            return []
            
        shares = []
        try:
            # We use the RPC interface to list shares. It's more reliable than standard SMB enum.
            rpctransport = transport.DCERPCTransportFactory(r'ncacn_np:%s[\pipe\srvsvc]' % self.target)
            rpctransport.set_smb_connection(self.smb_conn)
            
            dce = rpctransport.get_dce_rpc()
            dce.connect()
            dce.bind(srvs.MSRPC_UUID_SRVS)
            
            # Level 1 gets us the share name and remark
            resp = srvs.hNetrShareEnum(dce, 1)
            
            for share in resp['InfoStruct']['ShareInfo']['Level1']['Buffer']:
                shares.append({
                    'name': share['shi1_netname'][:-1], # Remove null byte
                    'remark': share['shi1_remark'][:-1]
                })
                
            dce.disconnect()
            
        except SessionError as e:
            if 'STATUS_ACCESS_DENIED' in str(e):
                logger.debug(f"[{self.target}] Access Denied listing shares via RPC (Expected for Null sessions on hardened hosts)")
            else:
                logger.debug(f"[{self.target}] Session error listing shares: {e}")
        except Exception as e:
            logger.debug(f"[{self.target}] Error listing shares via RPC: {e}")
            
        return shares

    def check_access(self, share_name: str, check_write: bool = False) -> Tuple[bool, bool]:
        """
        Checks if the current session has Read and/or Write access to a specific share.
        Returns a tuple: (read_access, write_access)
        """
        if not self.smb_conn:
            return False, False
            
        read_access = False
        write_access = False
        
        # 1. Check Read Access (Try to list the root directory)
        try:
            self.smb_conn.listPath(share_name, '*')
            read_access = True
        except SessionError as e:
            if 'STATUS_ACCESS_DENIED' in str(e):
                pass # Expected if no read access
            elif 'STATUS_BAD_NETWORK_NAME' in str(e):
                 # Share might exist in RPC enum but is offline/invalid
                 pass
            elif 'STATUS_OBJECT_PATH_NOT_FOUND' in str(e) or 'STATUS_OBJECT_NAME_NOT_FOUND' in str(e):
                # We can connect, but root is empty/weird. Let's still count it as readable contextually.
                read_access = True
        except Exception as e:
             pass

        # 2. Check Write Access
        if check_write and read_access: # Only check write if we can read and user requested it
            # Generate random file name
            test_file = ''.join(random.choices(string.ascii_letters + string.digits, k=8)) + ".txt"
            try:
                # Try to create a dummy file
                # Use standard file creation flags
                tid = self.smb_conn.connectTree(share_name)
                # Just open/create and immediately close.
                fid = self.smb_conn.createFile(tid, test_file)
                self.smb_conn.closeFile(tid, fid)
                
                # If we got here, we have write access! Now clean up.
                write_access = True
                self.smb_conn.deleteFile(share_name, test_file)
                
            except SessionError as e:
                pass # Usually STATUS_ACCESS_DENIED
            except Exception as e:
                pass
                
        return read_access, write_access

    def disconnect(self):
        """Closes the SMB connection."""
        if self.smb_conn:
            try:
                self.smb_conn.logoff()
            except Exception:
                pass
            self.smb_conn = None
