# Confine 基础镜像

本镜像为 CTF pwn 题目提供**基于 chroot 的隔离环境**。它使用 `setcap` 为自定义的 chroot 二进制文件授予 `cap_sys_chroot` 能力，允许题目在非特权用户下运行于隔离的文件系统环境中。

## 特性

- 基于 `socat:alpine` 基础镜像构建
- 使用具有 `cap_sys_chroot` 能力的自定义 `/chroot` 二进制文件实现自动 chroot 隔离
- 通过文件系统隔离最小化攻击面
- 题目运行于 chroot 环境中的 `/home/ctf/pwn`

## 快速开始

### 重要提示

**您必须为您的题目自定义此镜像：**

1. **替换默认的 `/home/ctf/pwn`** 为您的题目二进制文件
2. **添加所需依赖** 到 `/home/ctf/lib` 或 `/home/ctf/lib64`
3. **包含 shell 和工具** 如果您的题目需要它们（例如 `system("/bin/sh")`）
4. **复制所有共享库** 您的二进制文件依赖的所有库文件

chroot 后，只有 `/home/ctf` 内的文件可访问。flag 位于 `/flag`（实际为 `/home/ctf/flag`）。

## 完整示例

此 Dockerfile 创建一个完整的 pwn 题目，玩家可以通过利用执行 `cat /flag`：

```dockerfile
FROM ubuntu:24.04 AS builder

# 构建您的题目二进制文件
COPY src/source.c source.c
RUN apt-get update && \
    apt-get --no-install-recommends install -y gcc-multilib && \
    gcc -m32 -z execstack -fno-stack-protector -o chall source.c && \
    strip -s chall

FROM ghcr.io/gzctf/challenge-base/confine:alpine

# 为 chroot 环境创建目录结构
# 包含 /dev 用于一些程序可能需要的设备节点
RUN mkdir -p /home/ctf/dev  && \
    mknod /home/ctf/dev/null c 1 3 && \
    mknod /home/ctf/dev/zero c 1 5 && \
    mknod /home/ctf/dev/random c 1 8 && \
    mknod /home/ctf/dev/urandom c 1 9 && \
    chmod 666 /home/ctf/dev/* && \
    mkdir -p /home/ctf/lib/x86_64-linux-gnu && \
    mkdir -p /home/ctf/lib64 && \
    mkdir -p /home/ctf/lib32 && \
    mkdir -p /home/ctf/bin

# 用您的题目替换默认的 pwn 二进制文件
COPY --from=builder --chmod=500 --chown=ctf:ctf /chall /home/ctf/pwn

# 从 builder 复制必要的二进制文件
COPY --from=builder /bin/sh /home/ctf/bin/sh
COPY --from=builder /bin/ls /home/ctf/bin/ls
COPY --from=builder /bin/cat /home/ctf/bin/cat

# 复制 32 位题目二进制文件所需的共享库
COPY --from=builder /lib32/ld-linux.so.2 /home/ctf/lib/ld-linux.so.2
COPY --from=builder /lib32/libc.so.6 /home/ctf/lib32/libc.so.6

# 复制 64 位二进制文件（sh, ls, cat）所需的共享库
COPY --from=builder /lib/x86_64-linux-gnu/libc.so.6 /home/ctf/lib/x86_64-linux-gnu/libc.so.6
COPY --from=builder /lib64/ld-linux-x86-64.so.2 /home/ctf/lib64/ld-linux-x86-64.so.2

# 复制 ls 和 cat 需要的额外库
COPY --from=builder /lib/x86_64-linux-gnu/libpcre2-8.so.0 /home/ctf/lib/x86_64-linux-gnu/libpcre2-8.so.0
COPY --from=builder /lib/x86_64-linux-gnu/libselinux.so.1 /home/ctf/lib/x86_64-linux-gnu/libselinux.so.1
```

### 关键点说明

**多阶段构建**：使用 builder 阶段编译您的题目，并从同一基础镜像中识别依赖项。

**设备节点**：在 `/home/ctf/dev` 中创建程序可能需要的基本设备节点：

- `/dev/null`、`/dev/zero` - 许多程序常用
- `/dev/random`、`/dev/urandom` - 用于随机数生成

**32 位与 64 位库的区别**：

- 32 位题目二进制文件需要：`/lib32/ld-linux.so.2` 和 `/lib32/libc.so.6`
- 64 位工具（sh、cat、ls）需要：`/lib64/ld-linux-x86-64.so.2` 和 `/lib/x86_64-linux-gnu/libc.so.6`

**查找依赖项**：使用 `ldd` 检查您的二进制文件需要哪些库：

```bash
# 检查 32 位二进制文件依赖
docker run --rm ubuntu:24.04 sh -c "apt-get update && apt-get install -y libc6-i386 && ldd /path/to/32bit/binary"

# 检查 64 位二进制文件依赖
docker run --rm ubuntu:24.04 ldd /bin/cat
# 输出：
#   linux-vdso.so.1 (0x00007ffcc3f9a000)
#   libc.so.6 => /lib/x86_64-linux-gnu/libc.so.6 (0x00007f8e51400000)
#   /lib64/ld-linux-x86-64.so.2 (0x00007f8e51651000)

docker run --rm ubuntu:24.04 ldd /bin/ls
# 输出会显示额外的依赖，如 libpcre2-8.so.0、libselinux.so.1
```

## 工作原理

题目执行流程：

1. `init.sh` 将 flag 写入 `/home/ctf/flag` 并设置 chroot 环境
2. `socat` 监听 7000 端口并执行：`/chroot /home/ctf /pwn`
3. pwn 二进制文件以 `/home/ctf` 作为根目录运行
4. 玩家利用二进制文件执行命令，例如：
   ```c
   system("cat /flag");          // 读取 /flag（实际为 /home/ctf/flag）
   execve("/bin/sh", ...);       // 如果 /home/ctf/bin/sh 存在则生成 shell
   ```

## 常见使用场景

### 场景 1：64 位题目 + Shell 访问

标准的 64 位二进制文件，带 shell 和常用工具：

```dockerfile
FROM ubuntu:24.04 AS builder
COPY challenge.c .
RUN apt-get update && apt-get install -y gcc && \
    gcc -o chall challenge.c

FROM ghcr.io/gzctf/challenge-base/confine:alpine
RUN mkdir -p /home/ctf/bin /home/ctf/lib/x86_64-linux-gnu /home/ctf/lib64

COPY --from=builder --chmod=500 /chall /home/ctf/pwn
COPY --from=builder /bin/sh /home/ctf/bin/sh
COPY --from=builder /bin/cat /home/ctf/bin/cat
COPY --from=builder /bin/ls /home/ctf/bin/ls

COPY --from=builder /lib/x86_64-linux-gnu/libc.so.6 /home/ctf/lib/x86_64-linux-gnu/
COPY --from=builder /lib64/ld-linux-x86-64.so.2 /home/ctf/lib64/
COPY --from=builder /lib/x86_64-linux-gnu/libpcre2-8.so.0 /home/ctf/lib/x86_64-linux-gnu/
COPY --from=builder /lib/x86_64-linux-gnu/libselinux.so.1 /home/ctf/lib/x86_64-linux-gnu/
```

### 场景 2：32 位题目 + Shell 访问

32 位二进制文件，混合架构库：

```dockerfile
FROM ubuntu:24.04 AS builder
COPY challenge.c .
RUN apt-get update && apt-get install -y gcc-multilib && \
    gcc -m32 -o chall challenge.c

FROM ghcr.io/gzctf/challenge-base/confine:alpine
RUN mkdir -p /home/ctf/bin /home/ctf/lib /home/ctf/lib32 \
             /home/ctf/lib/x86_64-linux-gnu /home/ctf/lib64

COPY --from=builder --chmod=500 /chall /home/ctf/pwn

# 64 位工具（sh、cat、ls）
COPY --from=builder /bin/sh /home/ctf/bin/sh
COPY --from=builder /bin/cat /home/ctf/bin/cat
COPY --from=builder /bin/ls /home/ctf/bin/ls

# 题目二进制文件的 32 位库
COPY --from=builder /lib32/ld-linux.so.2 /home/ctf/lib/ld-linux.so.2
COPY --from=builder /lib32/libc.so.6 /home/ctf/lib32/libc.so.6

# 工具的 64 位库
COPY --from=builder /lib/x86_64-linux-gnu/libc.so.6 /home/ctf/lib/x86_64-linux-gnu/
COPY --from=builder /lib64/ld-linux-x86-64.so.2 /home/ctf/lib64/
COPY --from=builder /lib/x86_64-linux-gnu/libpcre2-8.so.0 /home/ctf/lib/x86_64-linux-gnu/
COPY --from=builder /lib/x86_64-linux-gnu/libselinux.so.1 /home/ctf/lib/x86_64-linux-gnu/
```

### 场景 3：最小化配置（仅 cat，无 shell）

如果您只需要 `cat /flag` 而不需要 shell 访问：

```dockerfile
FROM ubuntu:24.04 AS builder
COPY challenge.c .
RUN apt-get update && apt-get install -y gcc && \
    gcc -o chall challenge.c

FROM ghcr.io/gzctf/challenge-base/confine:alpine
RUN mkdir -p /home/ctf/bin /home/ctf/lib/x86_64-linux-gnu /home/ctf/lib64

COPY --from=builder --chmod=500 /chall /home/ctf/pwn
COPY --from=builder /bin/cat /home/ctf/bin/cat

# cat 的最小化库
COPY --from=builder /lib/x86_64-linux-gnu/libc.so.6 /home/ctf/lib/x86_64-linux-gnu/
COPY --from=builder /lib64/ld-linux-x86-64.so.2 /home/ctf/lib64/
```

### 场景 4：带设备节点

对于需要访问 `/dev/null`、`/dev/urandom` 等的题目：

```dockerfile
FROM ubuntu:24.04 AS builder
COPY challenge.c .
RUN apt-get update && apt-get install -y gcc && \
    gcc -o chall challenge.c

FROM ghcr.io/gzctf/challenge-base/confine:alpine

# 创建设备节点
RUN mkdir -p /home/ctf/dev && \
    mknod /home/ctf/dev/null c 1 3 && \
    mknod /home/ctf/dev/zero c 1 5 && \
    mknod /home/ctf/dev/random c 1 8 && \
    mknod /home/ctf/dev/urandom c 1 9 && \
    chmod 666 /home/ctf/dev/*

RUN mkdir -p /home/ctf/bin /home/ctf/lib/x86_64-linux-gnu /home/ctf/lib64

COPY --from=builder --chmod=500 /chall /home/ctf/pwn
COPY --from=builder /bin/cat /home/ctf/bin/cat
COPY --from=builder /lib/x86_64-linux-gnu/libc.so.6 /home/ctf/lib/x86_64-linux-gnu/
COPY --from=builder /lib64/ld-linux-x86-64.so.2 /home/ctf/lib64/
```

## 测试您的题目

构建 Docker 镜像后，您可以在本地测试：

### 构建和运行

```bash
# 构建您的题目镜像
docker build -t my-pwn-challenge .

# 使用测试 flag 运行容器
docker run -d \
  --name pwn-test \
  -e GZCTF_FLAG="flag{test_flag_here}" \
  -p 7000:7000 \
  my-pwn-challenge

# 检查容器是否正在运行
docker ps
```

### 连接和测试

使用 `nc`（netcat）连接到您的题目：

```bash
# 连接到题目
nc localhost 7000

# 您应该会看到题目提示
# 尝试利用它来读取 flag
```

### 交互示例

```bash
$ nc localhost 7000
Welcome to my pwn challenge!
Enter your name: AAAA
Hello, AAAA!

# 成功利用后：
$ nc localhost 7000
[exploit payload here]
$ cat /flag
flag{test_flag_here}
$ ls /
bin
flag
pwn
$ /bin/sh
$ whoami
ctf
$ exit
```

### 清理

```bash
# 停止并删除测试容器
docker stop pwn-test
docker rm pwn-test
```

### 高级测试

使用不同的 flag 进行测试以确保 flag 机制正常工作：

```bash
# 测试 1：简单 flag
docker run -d --name test1 -e GZCTF_FLAG="flag{simple}" -p 7001:7000 my-pwn-challenge

# 测试 2：带特殊字符的 flag
docker run -d --name test2 -e GZCTF_FLAG='flag{sp3c!@l_ch@rs}' -p 7002:7000 my-pwn-challenge

# 连接到每个测试
nc localhost 7001
nc localhost 7002

# 全部清理
docker stop test1 test2 && docker rm test1 test2
```

## 故障排查

**错误："not found" 或 "no such file"**

- 在您的二进制文件上运行 `ldd` 并复制所有列出的库
- 确保 `/lib64/ld-linux-x86-64.so.2`（动态链接器）存在

**利用后 shell 无法工作**

- 验证 `/home/ctf/bin/sh` 存在且权限正确
- 使用 `ldd /bin/sh` 检查 shell 依赖

**端口已被占用**

```bash
# 检查什么正在使用 7000 端口
lsof -i :7000
# 或
netstat -tuln | grep 7000

# 使用不同的端口
docker run -d -e GZCTF_FLAG="flag{test}" -p 8000:7000 my-pwn-challenge
nc localhost 8000
```

**容器立即退出**

```bash
# 检查容器日志
docker logs pwn-test

# 以交互模式运行以调试
docker run --rm -it -e GZCTF_FLAG="flag{test}" my-pwn-challenge sh
```

**验证 chroot 环境**

```bash
docker run --rm -it your-image sh
ls -laR /home/ctf/
```
