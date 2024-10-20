FROM python:alpine

RUN pip install --no-cache-dir flask && \
    adduser -D -h /home/ctf ctf && \
    mkdir -p /home/ctf/app/ && \
    chown -R ctf:ctf /home/ctf

CMD ["sleep", "infinity"]
