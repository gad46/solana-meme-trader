from solana.rpc.async_api import AsyncClient
from solana.transaction import Transaction
from solders.pubkey import Pubkey
from solana.rpc.commitment import Confirmed
from loguru import logger
from typing import Optional, Dict, Any
import asyncio
import base58
from .server import WalletServer

class PhantomWallet:
    def __init__(
        self,
        rpc_url: str = "https://api.mainnet-beta.solana.com",
        server_port: int = 8000
    ):
        """
        Initialize Phantom wallet interface
        
        Args:
            rpc_url: Solana RPC endpoint URL
            server_port: Port for local wallet server
        """
        self.connection = AsyncClient(rpc_url, commitment=Confirmed)
        self.server = WalletServer(port=server_port)
        self.public_key: Optional[Pubkey] = None
        logger.info(f"Initialized Phantom wallet interface with RPC: {rpc_url}")

    async def connect(self, timeout: float = 60.0) -> bool:
        """
        Connect to Phantom wallet through local server
        
        Args:
            timeout: Maximum time to wait for connection in seconds
            
        Returns:
            bool: True if connected successfully
        """
        try:
            # Start server in background
            server_task = asyncio.create_task(self.server.start())
            
            # Wait for wallet connection
            public_key_str = await self.server.wait_for_connection(timeout)
            if not public_key_str:
                return False
                
            # Convert to Pubkey
            self.public_key = Pubkey.from_string(public_key_str)
            logger.info(f"Connected to Phantom wallet: {self.public_key}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Phantom wallet: {str(e)}")
            return False

    async def sign_and_send_transaction(
        self,
        transaction: Transaction,
        recent_blockhash: Optional[str] = None
    ) -> Optional[str]:
        """
        Sign and send a transaction
        
        Args:
            transaction: Transaction to sign and send
            recent_blockhash: Recent blockhash (fetched if not provided)
            
        Returns:
            Optional[str]: Transaction signature if successful
        """
        if not self.is_connected:
            raise Exception("Wallet not connected")

        try:
            if not recent_blockhash:
                recent_blockhash = (
                    await self.connection.get_latest_blockhash()
                ).value.blockhash
            
            transaction.recent_blockhash = recent_blockhash
            
            # In browser this would use window.phantom.solana.signAndSendTransaction
            # For CLI we need to implement signing logic
            # This is a placeholder for the actual implementation
            raise NotImplementedError(
                "Transaction signing needs to be implemented through web interface"
            )
            
        except Exception as e:
            logger.error(f"Failed to sign and send transaction: {str(e)}")
            return None

    async def get_balance(self) -> Optional[float]:
        """
        Get wallet SOL balance
        
        Returns:
            Optional[float]: Balance in SOL
        """
        if not self.is_connected:
            return None
            
        try:
            balance = await self.connection.get_balance(self.public_key)
            return balance.value / 1e9  # Convert lamports to SOL
        except Exception as e:
            logger.error(f"Failed to get wallet balance: {str(e)}")
            return None

    @property
    def is_connected(self) -> bool:
        """Check if wallet is connected"""
        return self.public_key is not None and self.server.is_connected