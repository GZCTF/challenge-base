# Crypto Base

This image contains `pycryptodome` and `gmpy2` for Python and `socat`.

## Usage

Add your challenge file, `init.sh` example:

```bash
#!/bin/sh
echo $GZCTF_FLAG > /home/ctf/flag
chmod 444 /home/ctf/flag
unset GZCTF_FLAG

socat TCP-LISTEN:1337,reuseaddr,fork EXEC:"python3 challenge.py",pty,stderr
```
