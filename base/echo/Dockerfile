FROM busybox:latest

COPY --chmod=755 echo.sh /echo.sh

EXPOSE 70

CMD ["nc", "-lk", "-p", "70", "-e", "/echo.sh"]
