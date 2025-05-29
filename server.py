#!/usr/bin/env python3
"""
HTTPS Server for Minecraft Files
Serves static files over HTTPS with proper error handling and configuration.
"""
import http.server
import ssl
import os
import sys
import signal
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('minecraft-server')

class MinecraftHTTPSServer:
    """HTTPS Server for serving Minecraft files."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the server with configuration."""
        self.config = config
        self.httpd = None
        
    def setup_server(self) -> None:
        """Set up the HTTP server with SSL."""
        try:
            # Change to the directory where the script is located
            script_dir = Path(__file__).parent.absolute()
            os.chdir(script_dir)
            logger.info(f"Serving files from: {script_dir}")
            
            # Create HTTP server
            self.httpd = http.server.HTTPServer(
                (self.config['host'], self.config['port']), 
                http.server.SimpleHTTPRequestHandler
            )
            
            # Set up SSL context with modern security settings
            # Create a context with secure defaults
            context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            
            # Verify certificate files exist
            if not os.path.exists(self.config['cert_file']):
                raise FileNotFoundError(f"Certificate file not found: {self.config['cert_file']}")
            if not os.path.exists(self.config['key_file']):
                raise FileNotFoundError(f"Key file not found: {self.config['key_file']}")
                
            context.load_cert_chain(
                certfile=self.config['cert_file'], 
                keyfile=self.config['key_file']
            )
            
            # Modern security settings
            context.minimum_version = ssl.TLSVersion.TLSv1_2
            # No need to manually set ciphers or options as create_default_context
            # already uses secure defaults
            
            # Wrap the socket
            self.httpd.socket = context.wrap_socket(self.httpd.socket, server_side=True)
            
        except Exception as e:
            logger.error(f"Failed to set up server: {e}")
            sys.exit(1)
    
    def start(self) -> None:
        """Start the server."""
        try:
            logger.info(f"Starting HTTPS server on {self.config['host']}:{self.config['port']}...")
            self.httpd.serve_forever()
        except KeyboardInterrupt:
            logger.info("Server stopped by user interrupt")
        except Exception as e:
            logger.error(f"Server error: {e}")
            sys.exit(1)
        finally:
            if self.httpd:
                self.httpd.server_close()
                logger.info("Server closed")
    
    def stop(self) -> None:
        """Stop the server gracefully."""
        if self.httpd:
            logger.info("Shutting down server...")
            self.httpd.shutdown()


def parse_arguments() -> Dict[str, Any]:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='HTTPS Server for Minecraft Files')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=int(os.environ.get('PORT', 443)), help='Port to bind to')
    parser.add_argument('--cert', default=os.environ.get('CERT_FILE', './minecraft.pem'), help='Path to certificate file')
    parser.add_argument('--key', default=os.environ.get('KEY_FILE', './minecraft-key.pem'), help='Path to key file')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    
    args = parser.parse_args()
    
    # Set debug level if requested
    if args.debug:
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug mode enabled")
    
    return {
        'host': args.host,
        'port': args.port,
        'cert_file': args.cert,
        'key_file': args.key
    }


def signal_handler(sig, frame) -> None:
    """Handle termination signals."""
    logger.info(f"Received signal {sig}, shutting down...")
    sys.exit(0)


def main() -> None:
    """Main entry point."""
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Get configuration
    config = parse_arguments()
    
    # Create and start server
    server = MinecraftHTTPSServer(config)
    server.setup_server()
    server.start()


if __name__ == "__main__":
    main()
