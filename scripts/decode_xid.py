#!/usr/bin/env python3
"""
XID Decoder - Decode XID timestamps and components
Usage: python3 decode_xid.py <xid>
Example: python3 decode_xid.py d6k87bb24tekhfr24tg0
"""

import sys
from datetime import datetime

def decode_xid(xid: str) -> dict:
    """Decode an XID and return its components."""
    try:
        from xid import Xid
        
        xid_obj = Xid.from_string(xid)
        
        timestamp = xid_obj.time()
        counter = xid_obj.counter()
        machine = xid_obj.machine()
        pid = xid_obj.pid()
        dt = xid_obj.datetime()
        
        now = datetime.now()
        age_seconds = (now - dt).total_seconds()
        
        # Convert machine to hex for readability
        if isinstance(machine, bytes):
            machine_hex = machine.hex()
            machine_int = int.from_bytes(machine, 'big')
        elif isinstance(machine, str):
            # If it's a string, convert to bytes first
            machine_bytes = machine.encode('utf-8') if len(machine) <= 3 else bytes(machine[:3], 'utf-8')
            machine_hex = machine_bytes.hex()
            machine_int = int.from_bytes(machine_bytes, 'big')
        else:
            machine_hex = str(machine)
            machine_int = machine
        
        return {
            'valid': True,
            'xid': xid,
            'length': len(xid),
            'timestamp_unix': timestamp,
            'timestamp_utc': dt.strftime('%Y-%m-%d %H:%M:%S UTC'),
            'timestamp_est': dt.strftime('%Y-%m-%d %H:%M:%S EST'),
            'age_minutes': age_seconds / 60,
            'age_seconds': age_seconds,
            'components': {
                'time': timestamp,
                'machine_hex': machine_hex,
                'machine_int': machine_int,
                'pid': pid,
                'counter': counter
            }
        }
    except ImportError:
        return {'valid': False, 'error': 'XID library not installed'}
    except Exception as e:
        return {'valid': False, 'error': str(e)}

def format_output(result: dict) -> str:
    """Format decode result for display."""
    if not result['valid']:
        return f"❌ Decode failed: {result.get('error', 'Unknown error')}"
    
    lines = [
        "=" * 80,
        "🔍 XID DECODED",
        "=" * 80,
        "",
        f"📋 XID: {result['xid']}",
        f"   Length: {result['length']} characters",
        "",
        "📅 TIMESTAMP:",
        f"   Unix: {result['timestamp_unix']}",
        f"   UTC:  {result['timestamp_utc']}",
        f"   EST:  {result['timestamp_est']}",
        f"   Age:  {result['age_minutes']:.1f} minutes ago ({result['age_seconds']:.0f} seconds)",
        "",
        "🔢 COMPONENTS:",
        f"   Time:    {result['components']['time']} (4 bytes)",
        f"   Machine: 0x{result['components']['machine_hex']} ({result['components']['machine_int']:,} decimal)",
        f"   PID:     {result['components']['pid']} (2 bytes)",
        f"   Counter: {result['components']['counter']:,} (3 bytes)",
        "",
        "📊 STRUCTURE:",
        "   Total:   12 bytes (96 bits)",
        "   Format:  Base32 encoded → 20 characters",
        "   Sortable: Time-sorted for database performance",
        "",
        "✅ Valid XID",
        "=" * 80
    ]
    return "\n".join(lines)

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 decode_xid.py <xid>")
        print("Example: python3 decode_xid.py d6k87bb24tekhfr24tg0")
        sys.exit(1)
    
    xid = sys.argv[1]
    result = decode_xid(xid)
    print(format_output(result))

if __name__ == '__main__':
    main()
