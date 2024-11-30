from loguru import logger
from solana.rpc.async_api import AsyncClient
from solana.transaction import Transaction, TransactionInstruction
from solana.system_program import TransferParams, transfer
from solders.pubkey import Pubkey
import base58
from typing import Optional, Dict, Any
import json
import asyncio

class PhantomWallet:
    def __init__(self, rpc_url: str = "https://api.mainnet-beta.solana.com"):
        """
        Initialize Phantom wallet interface
        
        Args:
            rpc_url: Solana RPC endpoint URL
        """
        self.connection = AsyncClient(rpc_url)
        self.public_key: Optional[Pubkey] = None
        self.is_connected: bool = False
        self._provider = None
        logger.info(f"Initialized Phantom wallet interface with RPC: {rpc_url}")

    async def connect(self, only_if_trusted: bool = False) -> bool:
        """
        Connect to Phantom wallet
        
        Args:
            only_if_trusted: Only connect if the app is already trusted
            
        Returns:
            bool: True if connected successfully
        """
        try:
            # In a real browser environment, this would use window.phantom.solana
            # For CLI, we'll need to implement a different connection method
            # This is a placeholder for the actual connection logic
            if not self._check_phantom_installed():
                raise Exception("Phantom wallet is not installed")

            connect_params = {"onlyIfTrusted": only_if_trusted} if only_if_trusted else {}
            response = await self._request("connect", connect_params)
            
            if response and "publicKey" in response:
                self.public_key = Pubkey.from_string(response["publicKey"])
                self.is_connected = True
                logger.info(f"Connected to Phantom wallet: {self.public_key}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to connect to Phantom wallet: {str(e)}")
            self.is_connected = False
            return False

    async def disconnect(self) -> bool:
        """
        Disconnect from Phantom wallet
        
        Returns:
            bool: True if disconnected successfully
        """
        try:
            await self._request("disconnect")
            self.public_key = None
            self.is_connected = False
            logger.info("Disconnected from Phantom wallet")
            return True
        except Exception as e:
            logger.error(f"Failed to disconnect from Phantom wallet: {str(e)}")
            return False

    async def sign_and_send_transaction(self, transaction: Transaction) -> Optional[str]:
        """
        Sign and send a transaction using Phantom wallet
        
        Args:
            transaction: Solana transaction to sign and send
            
        Returns:
            Optional[str]: Transaction signature if successful
        """
        if not self.is_connected:
            raise Exception("Wallet not connected")

        try:
            # Serialize the transaction message
            serialized_message = base58.b58encode(transaction.serialize()).decode("utf-8")
            
            # Request signature from Phantom
            response = await self._request("signAndSendTransaction", {
                "message": serialized_message
            })
            
            if response and "signature" in response:
                signature = response["signature"]
                # Wait for confirmation
                await self.connection.confirm_transaction(signature)
                logger.info(f"Transaction confirmed: {signature}")
                return signature
                
        except Exception as e:
            logger.error(f"Failed to sign and send transaction: {str(e)}")
            return None

    async def get_balance(self) -> Optional[float]:
        """
        Get wallet SOL balance
        
        Returns:
            Optional[float]: Balance in SOL
        """
        if not self.public_key:
            return None
            
        try:
            balance = await self.connection.get_balance(self.public_key)
            return balance / 1e9  # Convert lamports to SOL
        except Exception as e:
            logger.error(f"Failed to get wallet balance: {str(e)}")
            return None

    async def _request(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Make a request to the Phantom wallet
        
        Args:
            method: Request method name
            params: Request parameters
            
        Returns:
            Dict[str, Any]: Response from Phantom
        """
        # This is a placeholder for the actual request implementation
        # In a browser environment, this would use window.phantom.solana.request
        raise NotImplementedError("Request method needs to be implemented based on the environment")

    def _check_phantom_installed(self) -> bool:
        """
        Check if Phantom wallet is installed
        
        Returns:
            bool: True if Phantom is installed
        """
        # This is a placeholder for the actual check
        # In a browser environment, this would check window.phantom
        raise NotImplementedError("Phantom installation check needs to be implemented based on the environment")