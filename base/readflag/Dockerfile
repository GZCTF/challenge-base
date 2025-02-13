FROM alpine AS builder

RUN apk add --no-cache gcc

COPY readflag.S /readflag.S

RUN gcc -static -nostdlib -Os -masm=intel -z noseparate-code -o readflag readflag.S && \
    strip --strip-all readflag && \
    chmod u+s readflag

FROM scratch

ADD --chown=root:root --chmod=400 flag /flag
COPY --from=builder /readflag /readflag

CMD ["/readflag"]
