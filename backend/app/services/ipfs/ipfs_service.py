"""
IPFS service for decentralized document storage
"""

import base64
import io
from typing import Optional, Dict
from pathlib import Path
import warnings

from app.core.config import settings

# Patch version checking BEFORE importing ipfshttpclient
# This allows compatibility with IPFS versions beyond the hardcoded 0.8.0 limit
import sys
from unittest.mock import Mock

# Create a mock for the version checking
def _mock_assert_version(*args, **kwargs):
    """Mock function that accepts any IPFS version"""
    pass

# Patch the client module's assert_version before it's used
try:
    import ipfshttpclient.client as _client_module
    _client_module.assert_version = _mock_assert_version
except ImportError:
    pass

# Now import ipfshttpclient
import ipfshttpclient

# Double-check the patch is applied
if hasattr(ipfshttpclient.client, 'assert_version'):
    ipfshttpclient.client.assert_version = _mock_assert_version


class IPFSService:
    """Service for IPFS operations"""

    def __init__(self):
        self.host = settings.IPFS_HOST
        self.port = settings.IPFS_PORT
        self.gateway = settings.IPFS_GATEWAY
        self.client = None

    def connect(self):
        """Connect to IPFS daemon (version checking disabled via monkey patch)"""
        try:
            # Connect to IPFS (version checking is patched to support IPFS 0.24.0+)
            self.client = ipfshttpclient.connect(f"/ip4/{self.host}/tcp/{self.port}")
            print(f"Connected to IPFS at {self.host}:{self.port}")
            # Try to get and display version info
            try:
                version_info = self.client.version()
                print(f"IPFS daemon version: {version_info.get('Version', 'unknown')}")
            except Exception as ve:
                warnings.warn(f"Could not get IPFS version: {ve}")
            return True
        except Exception as e:
            error_msg = str(e)
            print(f"Failed to connect to IPFS: {error_msg}")
            if "Unsupported daemon version" in error_msg or "not in range" in error_msg:
                print("ERROR: Version check patch failed!")
                print("Note: Your IPFS version may be newer than supported by ipfshttpclient")
                print("Consider downgrading IPFS or using a different IPFS client library")
            elif "Connection refused" in error_msg or "Failed to connect" in error_msg:
                print(f"Make sure IPFS daemon is running with: ipfs daemon")
            return False

    def is_connected(self) -> bool:
        """Check if connected to IPFS"""
        if not self.client:
            return False
        try:
            self.client.version()
            return True
        except:
            return False

    def upload_file(self, file_data: bytes, filename: str = None) -> Dict[str, str]:
        """
        Upload a file to IPFS

        Args:
            file_data: File content as bytes
            filename: Optional filename

        Returns:
            Dictionary with CID and gateway URL
        """
        if not self.is_connected():
            raise ConnectionError("Not connected to IPFS")

        try:
            result = self.client.add_bytes(file_data)
            cid = result

            return {
                "cid": cid,
                "gateway_url": f"{self.gateway}/ipfs/{cid}",
                "size": len(file_data),
            }
        except Exception as e:
            raise Exception(f"Failed to upload file to IPFS: {str(e)}")

    def upload_base64_file(self, base64_data: str, filename: str = None) -> Dict[str, str]:
        """
        Upload a base64 encoded file to IPFS

        Args:
            base64_data: Base64 encoded file content
            filename: Optional filename

        Returns:
            Dictionary with CID and gateway URL
        """
        try:
            # Decode base64
            file_data = base64.b64decode(base64_data)
            return self.upload_file(file_data, filename)
        except Exception as e:
            raise Exception(f"Failed to decode and upload base64 file: {str(e)}")

    def download_file(self, cid: str) -> bytes:
        """
        Download a file from IPFS

        Args:
            cid: IPFS CID of the file

        Returns:
            File content as bytes
        """
        if not self.is_connected():
            raise ConnectionError("Not connected to IPFS")

        try:
            file_data = self.client.cat(cid)
            return file_data
        except Exception as e:
            raise Exception(f"Failed to download file from IPFS: {str(e)}")

    def download_file_as_base64(self, cid: str) -> str:
        """
        Download a file from IPFS and return as base64

        Args:
            cid: IPFS CID of the file

        Returns:
            Base64 encoded file content
        """
        file_data = self.download_file(cid)
        return base64.b64encode(file_data).decode("utf-8")

    def pin_file(self, cid: str) -> bool:
        """
        Pin a file to keep it in IPFS

        Args:
            cid: IPFS CID to pin

        Returns:
            True if successful
        """
        if not self.is_connected():
            raise ConnectionError("Not connected to IPFS")

        try:
            self.client.pin.add(cid)
            return True
        except Exception as e:
            print(f"Failed to pin file: {str(e)}")
            return False

    def unpin_file(self, cid: str) -> bool:
        """
        Unpin a file from IPFS

        Args:
            cid: IPFS CID to unpin

        Returns:
            True if successful
        """
        if not self.is_connected():
            raise ConnectionError("Not connected to IPFS")

        try:
            self.client.pin.rm(cid)
            return True
        except Exception as e:
            print(f"Failed to unpin file: {str(e)}")
            return False

    def get_file_stats(self, cid: str) -> Optional[Dict]:
        """
        Get stats for a file

        Args:
            cid: IPFS CID

        Returns:
            Dictionary with file stats
        """
        if not self.is_connected():
            raise ConnectionError("Not connected to IPFS")

        try:
            stats = self.client.files.stat(f"/ipfs/{cid}")
            return {
                "hash": stats.get("Hash"),
                "size": stats.get("Size"),
                "cumulative_size": stats.get("CumulativeSize"),
                "type": stats.get("Type"),
            }
        except Exception as e:
            print(f"Failed to get file stats: {str(e)}")
            return None

    def file_exists(self, cid: str) -> bool:
        """
        Check if a file exists in IPFS

        Args:
            cid: IPFS CID

        Returns:
            True if file exists
        """
        try:
            self.client.cat(cid, length=1)
            return True
        except:
            return False

    def upload_json(self, data: dict) -> Dict[str, str]:
        """
        Upload JSON data to IPFS

        Args:
            data: Dictionary to upload

        Returns:
            Dictionary with CID and gateway URL
        """
        import json

        json_bytes = json.dumps(data).encode("utf-8")
        return self.upload_file(json_bytes)

    def download_json(self, cid: str) -> dict:
        """
        Download and parse JSON from IPFS

        Args:
            cid: IPFS CID

        Returns:
            Parsed JSON data
        """
        import json

        file_data = self.download_file(cid)
        return json.loads(file_data.decode("utf-8"))

    def get_gateway_url(self, cid: str) -> str:
        """Get gateway URL for a CID"""
        return f"{self.gateway}/ipfs/{cid}"

    def disconnect(self):
        """Disconnect from IPFS"""
        if self.client:
            self.client.close()
            self.client = None


# Singleton instance
ipfs_service = IPFSService()
