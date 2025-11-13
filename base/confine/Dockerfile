FROM ghcr.io/gzctf/challenge-base/socat:alpine

RUN apk add --no-cache libcap

COPY --chmod=755 src/init.sh /init.sh
COPY --chmod=755 src/pwn /home/ctf/pwn

ENTRYPOINT ["/init.sh"]
