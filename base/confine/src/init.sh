#!/bin/sh

echo -n "$GZCTF_FLAG" > /home/ctf/flag
chmod 444 /home/ctf/flag
unset GZCTF_FLAG

cp /bin/busybox /chroot
setcap cap_sys_chroot=ep /chroot

su ctf -c 'socat TCP-LISTEN:7000,reuseaddr,fork EXEC:"/chroot /home/ctf /pwn",stderr'
