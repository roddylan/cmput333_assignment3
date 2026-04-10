# Running the Buffer Overflow Exploit
**CMPUT 333 Assignment 3 — Group 9**

> [!NOTE]
> THIS EXPLOIT SCRIPT USES THE X86 VERSION OF THE PROGRAM
---

## Prerequisites

- Multipass installed on your host machine
- `vulnprog`, `exploit.py`, `setup_vm.sh`, `run_exploit.sh` available

---

## Step 1 — Create the VM
(in p2 folder)
```bash
multipass launch --name bof-vuln --cpus 2 --mem 4G --disk 12G --cloud-init cloud-config.yaml
```

## Step 2 — Transfer files into the VM

```bash
multipass transfer vulnprog bof-vuln:/home/ubuntu/
multipass transfer exploit.py bof-vuln:/home/ubuntu/
multipass transfer setup_vm.sh bof-vuln:/home/ubuntu/
multipass transfer run_exploit.sh bof-vuln:/home/ubuntu/
```

## Step 3 — Shell into the VM

```bash
multipass shell bof-vuln
```

## Step 4 — Run setup (once, as root)

```bash
chmod +x vulnprog
sudo bash setup_vm.sh
```

This disables ASLR and installs `gdb`, `python3`, `gcc`, and `binutils`.

## Step 5 — Run the exploit

```bash
python3 exploit.py | ./vulnprog
```

Or using the convenience wrapper:

```bash
bash run_exploit.sh 9
```

## Expected Output

```
SECRET CMPUT 333 Group 09 reached
```

Exit status will be 16 — this is a clean exit (no crash, no signal).

---

## Verify Addresses (optional)

Confirm PIE base:
```bash
gdb -batch -ex 'starti' -ex 'info proc mappings' ./vulnprog
# Look for: 0x555555554000  vulnprog
```

Confirm exit@plt address (used by the exploit):
```bash
objdump -d ./vulnprog | grep '<exit@plt>:'
# Look for a line like:  1030 <exit@plt>:
# exit@plt VA = 0x555555554000 + 0x1030
```
