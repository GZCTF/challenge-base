#!/bin/sh

set -euo pipefail

echo $GZCTF_FLAG > /flag
chmod 444 /flag
unset GZCTF_FLAG

mkdir /run/mysqld
chown www-data:www-data -R /var/lib/mysql /run/mysqld
mysql_install_db --user=www-data --ldata=/var/lib/mysql

/usr/bin/mysqld --user=www-data --console --skip-name-resolve --skip-networking=0 &
php-fpm -D
nginx -g 'daemon off;'
