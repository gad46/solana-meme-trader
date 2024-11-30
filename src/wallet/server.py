from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import uvicorn
import json
import asyncio
from loguru import logger
import webbrowser
from typing import Optional, Dict

class WalletServer:
    def __init__(self, port: int = 8000):
        self.app = FastAPI()
        self.port = port
        self.connected_wallet: Optional[str] = None
        self._setup_routes()
        self._setup_cors()
        self.connection_event = asyncio.Event()
        
    def _setup_cors(self):
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def _setup_routes(self):
        @self.app.get("/", response_class=HTMLResponse)
        async def wallet_page():
            return """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Phantom Wallet Connection</title>
                <script>
                    let provider;
                    
                    async function connectWallet() {
                        try {
                            if ("solana" in window) {
                                provider = window.phantom?.solana;
                                
                                if (provider?.isPhantom) {
                                    const resp = await provider.connect();
                                    const publicKey = resp.publicKey.toString();
                                    
                                    // Send public key to backend
                                    await fetch('/connect', {
                                        method: 'POST',
                                        headers: {
                                            'Content-Type': 'application/json',
                                        },
                                        body: JSON.stringify({
                                            public_key: publicKey
                                        })
                                    });
                                    
                                    document.getElementById('status').innerText = 
                                        `Connected: ${publicKey}`;
                                    
                                    // Setup disconnect listener
                                    provider.on("disconnect", () => {
                                        document.getElementById('status').innerText = 
                                            "Disconnected";
                                        fetch('/disconnect', { method: 'POST' });
                                    });
                                } else {
                                    throw new Error("Phantom wallet not found!");
                                }
                            }
                        } catch (err) {
                            console.error(err);
                            document.getElementById('status').innerText = 
                                `Error: ${err.message}`;
                        }
                    }
                </script>
            </head>
            <body>
                <h1>Phantom Wallet Connection</h1>
                <button onclick="connectWallet()">Connect Phantom Wallet</button>
                <p id="status">Not connected</p>
            </body>
            </html>
            """

        @self.app.post("/connect")
        async def connect(data: Dict[str, str]):
            self.connected_wallet = data["public_key"]
            logger.info(f"Wallet connected: {self.connected_wallet}")
            self.connection_event.set()
            return {"status": "connected", "public_key": self.connected_wallet}

        @self.app.post("/disconnect")
        async def disconnect():
            self.connected_wallet = None
            logger.info("Wallet disconnected")
            self.connection_event.clear()
            return {"status": "disconnected"}

    async def start(self):
        """Start the wallet server and open the browser"""
        server = uvicorn.Server(
            config=uvicorn.Config(
                app=self.app,
                host="127.0.0.1",
                port=self.port,
                log_level="info"
            )
        )
        
        # Open browser
        webbrowser.open(f"http://localhost:{self.port}")
        
        # Start server
        await server.serve()

    async def wait_for_connection(self, timeout: float = 60.0) -> Optional[str]:
        """Wait for wallet connection with timeout"""
        try:
            await asyncio.wait_for(self.connection_event.wait(), timeout)
            return self.connected_wallet
        except asyncio.TimeoutError:
            logger.error("Timeout waiting for wallet connection")
            return None

    @property
    def is_connected(self) -> bool:
        """Check if wallet is connected"""
        return self.connected_wallet is not None