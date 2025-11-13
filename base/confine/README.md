# Confine Base

This image provides a **chroot-based isolation environment** for CTF pwn challenges. It uses `setcap` to grant `cap_sys_chroot` capability to a custom chroot binary, allowing the challenge to run in an isolated filesystem environment as an unprivileged user.

## Features

- Built on top of `socat:alpine` base image
- Automatic chroot isolation using a custom `/chroot` binary with `cap_sys_chroot` capability
- Minimal attack surface through filesystem isolation
- Challenge runs at `/home/ctf/pwn` in chroot environment

## Quick Start

### Important Notes

**You must customize this image for your challenge:**

1. **Replace the default `/home/ctf/pwn`** with your challenge binary
2. **Add required dependencies** to `/home/ctf/lib` or `/home/ctf/lib64`
3. **Include shell and utilities** if your challenge needs them (e.g., for `system("/bin/sh")`)
4. **Copy all shared libraries** that your binaries depend on

After chroot, only files inside `/home/ctf` are accessible. The flag is at `/flag` (actually `/home/ctf/flag`).

## Complete Example

This Dockerfile creates a complete pwn challenge where players can exploit to execute `cat /flag`:

```dockerfile
FROM ubuntu:24.04 AS builder

# Build your challenge binary
COPY src/source.c source.c
RUN apt-get update && \
    apt-get --no-install-recommends install -y gcc-multilib && \
    gcc -m32 -z execstack -fno-stack-protector -o chall source.c && \
    strip -s chall

FROM ghcr.io/gzctf/challenge-base/confine:alpine

# Create directory structure for chroot environment
# Include /dev for device nodes that some programs may need
RUN mkdir -p /home/ctf/dev  && \
    mknod /home/ctf/dev/null c 1 3 && \
    mknod /home/ctf/dev/zero c 1 5 && \
    mknod /home/ctf/dev/random c 1 8 && \
    mknod /home/ctf/dev/urandom c 1 9 && \
    chmod 666 /home/ctf/dev/* && \
    mkdir -p /home/ctf/lib/x86_64-linux-gnu && \
    mkdir -p /home/ctf/lib64 && \
    mkdir -p /home/ctf/lib32 && \
    mkdir -p /home/ctf/bin

# Replace the default pwn binary with your challenge
COPY --from=builder --chmod=500 --chown=ctf:ctf /chall /home/ctf/pwn

# Copy essential binaries from builder
COPY --from=builder /bin/sh /home/ctf/bin/sh
COPY --from=builder /bin/ls /home/ctf/bin/ls
COPY --from=builder /bin/cat /home/ctf/bin/cat

# Copy required shared libraries for 32-bit challenge binary
COPY --from=builder /lib32/ld-linux.so.2 /home/ctf/lib/ld-linux.so.2
COPY --from=builder /lib32/libc.so.6 /home/ctf/lib32/libc.so.6

# Copy required shared libraries for 64-bit binaries (sh, ls, cat)
COPY --from=builder /lib/x86_64-linux-gnu/libc.so.6 /home/ctf/lib/x86_64-linux-gnu/libc.so.6
COPY --from=builder /lib64/ld-linux-x86-64.so.2 /home/ctf/lib64/ld-linux-x86-64.so.2

# Copy additional libraries needed by ls and cat
COPY --from=builder /lib/x86_64-linux-gnu/libpcre2-8.so.0 /home/ctf/lib/x86_64-linux-gnu/libpcre2-8.so.0
COPY --from=builder /lib/x86_64-linux-gnu/libselinux.so.1 /home/ctf/lib/x86_64-linux-gnu/libselinux.so.1
```

### Key Points Explained

**Multi-stage Build**: Use a builder stage to compile your challenge and identify dependencies from the same base image.

**Device Nodes**: Create essential device nodes in `/home/ctf/dev` for programs that may need them:

- `/dev/null`, `/dev/zero` - commonly used by many programs
- `/dev/random`, `/dev/urandom` - for random number generation

**32-bit vs 64-bit Libraries**:

- 32-bit challenge binary needs: `/lib32/ld-linux.so.2` and `/lib32/libc.so.6`
- 64-bit utilities (sh, cat, ls) need: `/lib64/ld-linux-x86-64.so.2` and `/lib/x86_64-linux-gnu/libc.so.6`

**Finding Dependencies**: Use `ldd` to check what libraries your binaries need:

```bash
# Check 32-bit binary dependencies
docker run --rm ubuntu:24.04 sh -c "apt-get update && apt-get install -y libc6-i386 && ldd /path/to/32bit/binary"

# Check 64-bit binary dependencies
docker run --rm ubuntu:24.04 ldd /bin/cat
# Output:
#   linux-vdso.so.1 (0x00007ffcc3f9a000)
#   libc.so.6 => /lib/x86_64-linux-gnu/libc.so.6 (0x00007f8e51400000)
#   /lib64/ld-linux-x86-64.so.2 (0x00007f8e51651000)

docker run --rm ubuntu:24.04 ldd /bin/ls
# Output will show additional dependencies like libpcre2-8.so.0, libselinux.so.1
```

## How It Works

The challenge execution flow:

1. `init.sh` writes flag to `/home/ctf/flag` and sets up the chroot environment
2. `socat` listens on port 7000 and executes: `/chroot /home/ctf /pwn`
3. The pwn binary runs with `/home/ctf` as its root directory
4. Players exploit the binary to execute commands like:
   ```c
   system("cat /flag");          // Reads /flag (actually /home/ctf/flag)
   execve("/bin/sh", ...);       // Spawns shell if /home/ctf/bin/sh exists
   ```

## Common Use Cases

### Case 1: 64-bit Challenge with Shell Access

Standard 64-bit binary with shell and common utilities:

```dockerfile
FROM ubuntu:24.04 AS builder
COPY challenge.c .
RUN apt-get update && apt-get install -y gcc && \
    gcc -o chall challenge.c

FROM ghcr.io/gzctf/challenge-base/confine:alpine
RUN mkdir -p /home/ctf/bin /home/ctf/lib/x86_64-linux-gnu /home/ctf/lib64

COPY --from=builder --chmod=500 /chall /home/ctf/pwn
COPY --from=builder /bin/sh /home/ctf/bin/sh
COPY --from=builder /bin/cat /home/ctf/bin/cat
COPY --from=builder /bin/ls /home/ctf/bin/ls

COPY --from=builder /lib/x86_64-linux-gnu/libc.so.6 /home/ctf/lib/x86_64-linux-gnu/
COPY --from=builder /lib64/ld-linux-x86-64.so.2 /home/ctf/lib64/
COPY --from=builder /lib/x86_64-linux-gnu/libpcre2-8.so.0 /home/ctf/lib/x86_64-linux-gnu/
COPY --from=builder /lib/x86_64-linux-gnu/libselinux.so.1 /home/ctf/lib/x86_64-linux-gnu/
```

### Case 2: 32-bit Challenge with Shell Access

32-bit binary with mixed architecture libraries:

```dockerfile
FROM ubuntu:24.04 AS builder
COPY challenge.c .
RUN apt-get update && apt-get install -y gcc-multilib && \
    gcc -m32 -o chall challenge.c

FROM ghcr.io/gzctf/challenge-base/confine:alpine
RUN mkdir -p /home/ctf/bin /home/ctf/lib /home/ctf/lib32 \
             /home/ctf/lib/x86_64-linux-gnu /home/ctf/lib64

COPY --from=builder --chmod=500 /chall /home/ctf/pwn

# 64-bit utilities (sh, cat, ls)
COPY --from=builder /bin/sh /home/ctf/bin/sh
COPY --from=builder /bin/cat /home/ctf/bin/cat
COPY --from=builder /bin/ls /home/ctf/bin/ls

# 32-bit libraries for challenge binary
COPY --from=builder /lib32/ld-linux.so.2 /home/ctf/lib/ld-linux.so.2
COPY --from=builder /lib32/libc.so.6 /home/ctf/lib32/libc.so.6

# 64-bit libraries for utilities
COPY --from=builder /lib/x86_64-linux-gnu/libc.so.6 /home/ctf/lib/x86_64-linux-gnu/
COPY --from=builder /lib64/ld-linux-x86-64.so.2 /home/ctf/lib64/
COPY --from=builder /lib/x86_64-linux-gnu/libpcre2-8.so.0 /home/ctf/lib/x86_64-linux-gnu/
COPY --from=builder /lib/x86_64-linux-gnu/libselinux.so.1 /home/ctf/lib/x86_64-linux-gnu/
```

### Case 3: Minimal Setup (cat only, no shell)

If you only need `cat /flag` without shell access:

```dockerfile
FROM ubuntu:24.04 AS builder
COPY challenge.c .
RUN apt-get update && apt-get install -y gcc && \
    gcc -o chall challenge.c

FROM ghcr.io/gzctf/challenge-base/confine:alpine
RUN mkdir -p /home/ctf/bin /home/ctf/lib/x86_64-linux-gnu /home/ctf/lib64

COPY --from=builder --chmod=500 /chall /home/ctf/pwn
COPY --from=builder /bin/cat /home/ctf/bin/cat

# Minimal libraries for cat
COPY --from=builder /lib/x86_64-linux-gnu/libc.so.6 /home/ctf/lib/x86_64-linux-gnu/
COPY --from=builder /lib64/ld-linux-x86-64.so.2 /home/ctf/lib64/
```

### Case 4: With Device Nodes

For challenges that need access to `/dev/null`, `/dev/urandom`, etc:

```dockerfile
FROM ubuntu:24.04 AS builder
COPY challenge.c .
RUN apt-get update && apt-get install -y gcc && \
    gcc -o chall challenge.c

FROM ghcr.io/gzctf/challenge-base/confine:alpine

# Create device nodes
RUN mkdir -p /home/ctf/dev && \
    mknod /home/ctf/dev/null c 1 3 && \
    mknod /home/ctf/dev/zero c 1 5 && \
    mknod /home/ctf/dev/random c 1 8 && \
    mknod /home/ctf/dev/urandom c 1 9 && \
    chmod 666 /home/ctf/dev/*

RUN mkdir -p /home/ctf/bin /home/ctf/lib/x86_64-linux-gnu /home/ctf/lib64

COPY --from=builder --chmod=500 /chall /home/ctf/pwn
COPY --from=builder /bin/cat /home/ctf/bin/cat
COPY --from=builder /lib/x86_64-linux-gnu/libc.so.6 /home/ctf/lib/x86_64-linux-gnu/
COPY --from=builder /lib64/ld-linux-x86-64.so.2 /home/ctf/lib64/
```

## Testing Your Challenge

After building your Docker image, you can test it locally:

### Build and Run

```bash
# Build your challenge image
docker build -t my-pwn-challenge .

# Run the container with a test flag
docker run -d \
  --name pwn-test \
  -e GZCTF_FLAG="flag{test_flag_here}" \
  -p 7000:7000 \
  my-pwn-challenge

# Check if container is running
docker ps
```

### Connect and Test

Use `nc` (netcat) to connect to your challenge:

```bash
# Connect to the challenge
nc localhost 7000

# You should see your challenge prompt
# Try exploiting it to read the flag
```

### Example Interaction

```bash
$ nc localhost 7000
Welcome to my pwn challenge!
Enter your name: AAAA
Hello, AAAA!

# After successful exploitation:
$ nc localhost 7000
[exploit payload here]
$ cat /flag
flag{test_flag_here}
$ ls /
bin
flag
pwn
$ /bin/sh
$ whoami
ctf
$ exit
```

### Cleanup

```bash
# Stop and remove the test container
docker stop pwn-test
docker rm pwn-test
```

### Advanced Testing

Test with different flags to ensure the flag mechanism works:

```bash
# Test 1: Simple flag
docker run -d --name test1 -e GZCTF_FLAG="flag{simple}" -p 7001:7000 my-pwn-challenge

# Test 2: Flag with special characters
docker run -d --name test2 -e GZCTF_FLAG='flag{sp3c!@l_ch@rs}' -p 7002:7000 my-pwn-challenge

# Connect to each test
nc localhost 7001
nc localhost 7002

# Cleanup all
docker stop test1 test2 && docker rm test1 test2
```

## Troubleshooting

**Error: "not found" or "no such file"**

- Run `ldd` on your binary and copy all listed libraries
- Ensure `/lib64/ld-linux-x86-64.so.2` (dynamic linker) is present

**Shell doesn't work after exploitation**

- Verify `/home/ctf/bin/sh` exists and has correct permissions
- Check shell dependencies with `ldd /bin/sh`

**Port already in use**

```bash
# Check what's using port 7000
lsof -i :7000
# or
netstat -tuln | grep 7000

# Use a different port
docker run -d -e GZCTF_FLAG="flag{test}" -p 8000:7000 my-pwn-challenge
nc localhost 8000
```

**Container exits immediately**

```bash
# Check container logs
docker logs pwn-test

# Run interactively to debug
docker run --rm -it -e GZCTF_FLAG="flag{test}" my-pwn-challenge sh
```

**Verify chroot environment**

```bash
docker run --rm -it your-image sh
ls -laR /home/ctf/
```
