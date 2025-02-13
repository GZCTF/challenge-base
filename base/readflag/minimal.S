[bits 64]
file_load_va: equ 0x500000000

db 0x7f
entry_point:
db 'E', 'L', 'F'
  mov al, 2
  lea rdi, [rel flag_path]
  xor esi, esi
  db 0xeb
dw 3
dw 0x3e
code_chunk_2:
  syscall
  jmp code_chunk_3

program_headers_start:
dq entry_point + file_load_va
dq program_headers_start
dq file_load_va + program_headers_start
flag_path: db `/flag\0`
dw 0x38
dq 1
dq 1

code_chunk_3:
  mov edi, eax
  mov al, 0
  mov dl, 0xff
  push rsp
  pop rsi
  syscall

  mov edx, eax
  mov al, 1
  mov edi, eax
  syscall

  mov al, 60
  xor edi, edi
  syscall
