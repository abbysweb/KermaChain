#!/usr/bin/env python3
"""
WebSocket Test Client for KermaChain API

Connects to ws://localhost:3001/ws/live and prints all events.

Run: python scripts/ws_test.py
"""

import asyncio
import json
import sys
import websockets

WS_URL = "ws://localhost:3001/ws/live"

EVENT_COLORS = {
    "new_block": "\033[92m",      # Green
    "new_tx": "\033[94m",         # Blue
    "reorg": "\033[93m",          # Yellow
    "peer_update": "\033[96m",    # Cyan
    "error": "\033[91m",          # Red
}
RESET = "\033[0m"
BOLD = "\033[1m"

async def listen():
    print(f"🔌 Connecting to {WS_URL}...")
    try:
        async with websockets.connect(WS_URL) as ws:
            print(f"✅ Connected! Listening for events...\n")
            
            async for message in ws:
                try:
                    data = json.loads(message)
                    event_type = data.get("type", "unknown")
                    payload = data.get("data", {})
                    
                    color = EVENT_COLORS.get(event_type, "")
                    timestamp = payload.get("timestamp", "")
                    
                    if event_type == "new_block":
                        print(f"{color}{BOLD}📦 NEW BLOCK{RESET}")
                        print(f"   Height:    {payload.get('height')}")
                        print(f"   Block ID:  {payload.get('blockid', '')[:16]}...")
                        print(f"   TXs:       {payload.get('txCount')}")
                        print(f"   Miner:     {payload.get('miner')}")
                        if timestamp:
                            print(f"   Time:      {timestamp}")
                    
                    elif event_type == "new_tx":
                        print(f"{color}{BOLD}💸 NEW TX{RESET}")
                        print(f"   TX ID:     {payload.get('txid', '')[:16]}...")
                        print(f"   Inputs:    {payload.get('inputs')}")
                        print(f"   Outputs:   {payload.get('outputs')}")
                        print(f"   Value:     {payload.get('totalValue', 0):,} sat")
                    
                    elif event_type == "reorg":
                        print(f"{color}{BOLD}🔄 CHAIN REORG{RESET}")
                        print(f"   Old tip:   {payload.get('old_tip', '')[:16]}...")
                        print(f"   New tip:   {payload.get('new_tip', '')[:16]}...")
                        print(f"   Disconnected: {payload.get('disconnected', [])}")
                        print(f"   Connected:    {payload.get('connected', [])}")
                    
                    elif event_type == "peer_update":
                        print(f"{color}{BOLD}👥 PEER UPDATE{RESET}")
                        print(f"   Host:      {payload.get('host')}:{payload.get('port')}")
                        print(f"   Connected: {payload.get('connected')}")
                        if payload.get('connectedSince'):
                            print(f"   Since:     {payload.get('connectedSince')}")
                    
                    else:
                        print(f"{color}{BOLD}📡 {event_type.upper()}{RESET}")
                        print(f"   {json.dumps(payload, indent=4)}")
                    
                    print()
                    
                except json.JSONDecodeError:
                    print(f"⚠️  Invalid JSON: {message}")
                    
    except websockets.exceptions.ConnectionRefused:
        print(f"❌ Connection refused. Is the API server running on :3001?")
        print(f"   Start it with: cd backend && python -m kerma.main")
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    print("="*60)
    print(" KermaChain WebSocket Test Client")
    print("="*60)
    print(f" Connecting to: {WS_URL}")
    print(" Events: new_block, new_tx, reorg, peer_update")
    print(" Press Ctrl+C to exit")
    print("="*60 + "\n")
    
    try:
        asyncio.run(listen())
    except KeyboardInterrupt:
        print("\n👋 Disconnected")

if __name__ == "__main__":
    main()