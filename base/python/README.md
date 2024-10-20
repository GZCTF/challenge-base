# Python Base

This image contains `socat` and `python3`.

## Usage

Add your challenge file, `init.sh` example:

```bash
#!/bin/sh
echo $GZCTF_FLAG > /home/ctf/flag
chmod 444 /home/ctf/flag
unset GZCTF_FLAG

socat TCP-LISTEN:1337,reuseaddr,fork EXEC:"python3 challenge.py",pty,stderr
```
