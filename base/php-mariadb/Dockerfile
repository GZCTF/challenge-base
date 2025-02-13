FROM ghcr.io/gzctf/challenge-base/php:alpine

RUN apk add --no-cache mariadb

COPY my.cnf /etc/mysql/my.cnf
COPY --chmod=500 init.sh /init.sh
