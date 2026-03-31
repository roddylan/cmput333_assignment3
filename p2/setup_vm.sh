#!/bin/bash
# VM/WSL2 setup script for buffer overflow assignment (CMPUT 333)
#
# Run as root inside the bof-vuln Multipass VM, OR inside WSL2:
#
#   Multipass:  multipass exec bof-vuln -- sudo bash setup_vm.sh
#   WSL2:       wsl -d Ubuntu -u root -- bash /path/to/setup_vm.sh
#
set -e

echo "=== Step 1: Disable ASLR (address space randomization) ==="
echo 0 > /proc/sys/kernel/randomize_va_space
# Make persistent across reboots (VM only; WSL2 does not persist /proc writes)
grep -q "randomize_va_space" /etc/sysctl.conf 2>/dev/null \
    || echo "kernel.randomize_va_space = 0" >> /etc/sysctl.conf
echo "ASLR status (should be 0): $(cat /proc/sys/kernel/randomize_va_space)"

echo ""
echo "=== Step 2: Install required packages ==="
apt-get update -q
apt-get install -y gdb python3 gcc binutils file

echo ""
echo "=== Setup complete ==="
echo "Installed: gdb, python3, gcc, binutils (objdump/readelf/nm), file"
echo ""
echo "Next steps:"
echo "  1. Transfer vulnprog and exploit.py to the VM"
echo "  2. chmod +x vulnprog"
echo "  3. Verify PIE base: gdb -batch -ex 'starti' -ex 'info proc mappings' ./vulnprog"
echo "  4. Run exploit:  python3 exploit.py | ./vulnprog"
