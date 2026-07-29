"""
Blockchain service for interacting with Ganache/Ethereum
"""

from web3 import Web3
from web3.middleware import geth_poa_middleware
from eth_account import Account
from typing import Dict, Optional, List
import json
from pathlib import Path

from app.core.config import settings


class BlockchainService:
    """Service for blockchain interactions"""

    def __init__(self):
        self.rpc_url = settings.BLOCKCHAIN_RPC_URL
        self.chain_id = settings.CHAIN_ID
        self.w3 = None
        self.contract_address = settings.CONTRACT_ADDRESS
        self.contract = None
        self.contract_abi = None

    def connect(self):
        """Connect to blockchain"""
        try:
            # Test if the RPC endpoint is reachable
            import requests
            try:
                response = requests.post(
                    self.rpc_url,
                    json={"jsonrpc": "2.0", "method": "eth_blockNumber", "params": [], "id": 1},
                    timeout=5
                )
                if response.status_code != 200:
                    print(f"Blockchain RPC endpoint returned status {response.status_code}")
                    print(f"Make sure your blockchain node (Ganache) is running at {self.rpc_url}")
                    return False
            except requests.exceptions.ConnectionError:
                print(f"Cannot reach blockchain at {self.rpc_url}")
                print(f"Make sure Ganache or your blockchain node is running")
                print(f"You can start Ganache with: ganache-cli -p 8545")
                return False
            except requests.exceptions.Timeout:
                print(f"Connection to {self.rpc_url} timed out")
                return False

            self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
            # Add POA middleware for Ganache
            self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)

            if not self.w3.is_connected():
                raise ConnectionError("Failed to connect to blockchain")

            print(f"Connected to blockchain at {self.rpc_url}")
            print(f"Chain ID: {self.chain_id}")
            return True
        except Exception as e:
            print(f"Blockchain connection error: {str(e)}")
            return False

    def is_connected(self) -> bool:
        """Check if connected to blockchain"""
        return self.w3 is not None and self.w3.is_connected()

    def get_account_balance(self, address: str) -> float:
        """Get ETH balance of an address"""
        if not self.is_connected():
            raise ConnectionError("Not connected to blockchain")

        balance_wei = self.w3.eth.get_balance(address)
        return self.w3.from_wei(balance_wei, "ether")

    def create_account(self) -> Dict[str, str]:
        """Create a new Ethereum account"""
        account = Account.create()
        return {
            "address": account.address,
            "private_key": account.key.hex(),
        }

    def load_contract(self, contract_address: str, abi_path: str):
        """Load smart contract"""
        if not self.is_connected():
            raise ConnectionError("Not connected to blockchain")

        with open(abi_path, "r") as f:
            abi = json.load(f)

        self.contract_address = contract_address
        self.contract_abi = abi
        self.contract = self.w3.eth.contract(address=contract_address, abi=abi)
        return self.contract

    def send_transaction(
        self,
        from_address: str,
        private_key: str,
        to_address: str,
        value: float = 0,
        data: str = None,
    ) -> str:
        """Send a transaction"""
        if not self.is_connected():
            raise ConnectionError("Not connected to blockchain")

        nonce = self.w3.eth.get_transaction_count(from_address)

        transaction = {
            "nonce": nonce,
            "to": to_address,
            "value": self.w3.to_wei(value, "ether"),
            "gas": 2000000,
            "gasPrice": self.w3.eth.gas_price,
            "chainId": self.chain_id,
        }

        if data:
            transaction["data"] = data

        signed_txn = self.w3.eth.account.sign_transaction(transaction, private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)

        return tx_hash.hex()

    def wait_for_transaction(self, tx_hash: str, timeout: int = 120) -> Dict:
        """Wait for transaction to be mined"""
        if not self.is_connected():
            raise ConnectionError("Not connected to blockchain")

        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=timeout)
        return {
            "transactionHash": receipt["transactionHash"].hex(),
            "blockNumber": receipt["blockNumber"],
            "gasUsed": receipt["gasUsed"],
            "status": receipt["status"],
        }

    def call_contract_function(
        self,
        function_name: str,
        *args,
        from_address: str = None,
        private_key: str = None,
    ):
        """Call a contract function (read or write)"""
        if not self.contract:
            raise ValueError("Contract not loaded")

        function = getattr(self.contract.functions, function_name)

        if private_key:
            # Write operation
            nonce = self.w3.eth.get_transaction_count(from_address)
            transaction = function(*args).build_transaction(
                {
                    "chainId": self.chain_id,
                    "gas": 2000000,
                    "gasPrice": self.w3.eth.gas_price,
                    "nonce": nonce,
                }
            )

            signed_txn = self.w3.eth.account.sign_transaction(transaction, private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            return tx_hash.hex()
        else:
            # Read operation
            return function(*args).call()

    def register_credential(
        self,
        issuer_address: str,
        issuer_private_key: str,
        credential_id: str,
        user_address: str,
        ipfs_cid: str,
        credential_hash: str,
        pqc_signature: str,
    ) -> str:
        """
        Register a credential on blockchain

        Args:
            issuer_address: Issuer's blockchain address
            issuer_private_key: Issuer's private key
            credential_id: Unique credential ID
            user_address: User's blockchain address
            ipfs_cid: IPFS CID of the document
            credential_hash: Hash of credential data
            pqc_signature: PQC signature

        Returns:
            Transaction hash
        """
        if not self.contract:
            raise ValueError("Contract not loaded. Call load_contract() first")

        try:
            tx_hash = self.call_contract_function(
                "registerCredential",
                credential_id,
                user_address,
                ipfs_cid,
                credential_hash,
                pqc_signature,
                from_address=issuer_address,
                private_key=issuer_private_key,
            )
            return tx_hash
        except Exception as e:
            raise Exception(f"Failed to register credential: {str(e)}")

    def verify_credential(self, credential_id: str) -> Optional[Dict]:
        """
        Verify a credential from blockchain

        Args:
            credential_id: Credential ID to verify

        Returns:
            Credential data if exists, None otherwise
        """
        if not self.contract:
            raise ValueError("Contract not loaded")

        try:
            result = self.call_contract_function("getCredential", credential_id)
            if result and result[0]:  # If credential exists
                return {
                    "exists": True,
                    "user_address": result[1],
                    "issuer_address": result[2],
                    "ipfs_cid": result[3],
                    "credential_hash": result[4],
                    "pqc_signature": result[5],
                    "timestamp": result[6],
                    "is_revoked": result[7],
                }
            return None
        except Exception as e:
            print(f"Failed to verify credential: {str(e)}")
            return None

    def revoke_credential(
        self, issuer_address: str, issuer_private_key: str, credential_id: str
    ) -> str:
        """Revoke a credential"""
        if not self.contract:
            raise ValueError("Contract not loaded")

        try:
            tx_hash = self.call_contract_function(
                "revokeCredential",
                credential_id,
                from_address=issuer_address,
                private_key=issuer_private_key,
            )
            return tx_hash
        except Exception as e:
            raise Exception(f"Failed to revoke credential: {str(e)}")

    def register_issuer(
        self,
        admin_address: str,
        admin_private_key: str,
        issuer_address: str,
        issuer_name: str,
        pqc_public_key: str,
    ) -> str:
        """Register an issuer on blockchain"""
        if not self.contract:
            raise ValueError("Contract not loaded")

        try:
            tx_hash = self.call_contract_function(
                "registerIssuer",
                issuer_address,
                issuer_name,
                pqc_public_key,
                from_address=admin_address,
                private_key=admin_private_key,
            )
            return tx_hash
        except Exception as e:
            raise Exception(f"Failed to register issuer: {str(e)}")

    def get_issuer(self, issuer_address: str) -> Optional[Dict]:
        """Get issuer information from blockchain"""
        if not self.contract:
            raise ValueError("Contract not loaded")

        try:
            result = self.call_contract_function("getIssuer", issuer_address)
            if result and result[0]:  # If issuer exists
                return {
                    "exists": True,
                    "name": result[1],
                    "pqc_public_key": result[2],
                    "is_active": result[3],
                    "registered_at": result[4],
                }
            return None
        except Exception as e:
            print(f"Failed to get issuer: {str(e)}")
            return None


# Singleton instance
blockchain_service = BlockchainService()
