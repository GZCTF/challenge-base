FROM python:slim

RUN pip install --no-cache-dir numpy && \
    apt-get update && \
    apt-get install -y socat && \
    rm -rf /var/lib/apt/lists/* && \
    useradd -d /home/ctf ctf && \
    mkdir -p /home/ctf/app/ && \
    chown -R ctf:ctf /home/ctf

CMD ["sleep", "infinity"]
