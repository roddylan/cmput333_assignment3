#!/usr/bin/env python3
"""
Helper script to find the PIE base address of vulnprog in the VM.
Run this INSIDE the VM after ASLR has been disabled.

Usage:
    python3 find_base.py

This script runs the program under GDB to find the load base address,
then computes and prints all secret function addresses.
"""

import subprocess
import re

GDB_SCRIPT = """
set pagination off
file ./vulnprog
start
info proc mappings
quit
"""

def main():
    # Write GDB script
    with open('/tmp/gdb_find_base.gdb', 'w') as f:
        f.write(GDB_SCRIPT)

    print("[*] Running gdb to find PIE base address...")
    result = subprocess.run(
        ['gdb', '-batch', '-x', '/tmp/gdb_find_base.gdb'],
        capture_output=True, text=True, timeout=30
    )

    output = result.stdout + result.stderr
    # Look for the mapping of vulnprog executable
    base_addr = None
    for line in output.split('\n'):
        # Match lines like: 0x555555554000 0x555555556000 0x2000 0x0 /path/vulnprog
        m = re.search(r'(0x[0-9a-f]+)\s+0x[0-9a-f]+\s+\S+\s+0x0\s+.*vulnprog', line)
        if m:
            base_addr = int(m.group(1), 16)
            print(f"[+] Found PIE base address: 0x{base_addr:016x}")
            break

    if base_addr is None:
        # Try alternative: parse from 'start' output
        for line in output.split('\n'):
            m = re.search(r'Temporary breakpoint.*at\s+(0x[0-9a-f]+)', line)
            if m:
                print(f"[*] Entry point hint: {m.group(1)}")

        # Common default on Ubuntu with ASLR disabled
        base_addr = 0x555555554000
        print(f"[!] Could not auto-detect base. Using default: 0x{base_addr:016x}")
        print("    Verify with: gdb -batch -ex 'start' -ex 'info proc mappings' ./vulnprog")

    print(f"\n[+] PIE base: 0x{base_addr:016x}")
    print("\n[+] Secret function addresses:")

    # All 23 secret functions (PIE-relative offsets)
    for group in range(1, 24):
        offset = 0x1249 + (group - 1) * 0x1a
        abs_addr = base_addr + offset
        print(f"    Group {group:02d}: offset=0x{offset:04x}  abs=0x{abs_addr:016x}")

    return base_addr

if __name__ == '__main__':
    main()
