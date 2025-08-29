#!/usr/bin/env python3
"""
CherryBott Web Dashboard Startup Script

Usage:
    python start_web_dashboard.py [--port 8080] [--host 0.0.0.0] [--dev]
"""

import sys
import argparse
import uvicorn
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(
        description="Start CherryBott Web Dashboard",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python start_web_dashboard.py                    # Start on default port 8080
    python start_web_dashboard.py --port 3000       # Start on custom port
    python start_web_dashboard.py --dev             # Start in development mode
    python start_web_dashboard.py --host 127.0.0.1  # Start on localhost only
        """
    )
    
    parser.add_argument(
        '--host', 
        default='0.0.0.0',
        help='Host to bind to (default: 0.0.0.0 - all interfaces)'
    )
    parser.add_argument(
        '--port', 
        type=int,
        default=8080,
        help='Port to bind to (default: 8080)'
    )
    parser.add_argument(
        '--dev', 
        action='store_true',
        help='Enable development mode with auto-reload'
    )
    parser.add_argument(
        '--log-level',
        choices=['debug', 'info', 'warning', 'error'],
        default='info',
        help='Log level (default: info)'
    )
    
    args = parser.parse_args()
    
    print(f"🚀 Starting CherryBott Web Dashboard...")
    print(f"   Host: {args.host}")
    print(f"   Port: {args.port}")
    print(f"   Mode: {'Development' if args.dev else 'Production'}")
    print(f"   Access URL: http://localhost:{args.port}")
    print(f"   Overlay URL: http://localhost:{args.port}/overlay/{{channel_name}}")
    print(f"   API URL: http://localhost:{args.port}/api/leaderboard/{{channel_name}}")
    print()
    
    try:
        uvicorn.run(
            "web.main:app",
            host=args.host,
            port=args.port,
            reload=args.dev,
            log_level=args.log_level,
            access_log=True
        )
    except KeyboardInterrupt:
        print("\n👋 CherryBott Web Dashboard stopped")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()