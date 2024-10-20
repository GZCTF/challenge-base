# PHP Base

## Usage

Launch nginx and php, `init.sh` example:

```bash
#!/bin/sh
echo $GZCTF_FLAG > /flag
chmod 444 /flag
unset GZCTF_FLAG

php-fpm -D
nginx -g 'daemon off;'
```
