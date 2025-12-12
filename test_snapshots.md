# bn.py Snapshot Tests

Expected output from running bn.py against test_binary.

## funcs -n 20

```
0x401000  _init
0x401020  sub_401020
0x401030  free
0x401036  sub_401036
0x401040  strncpy
0x401046  sub_401046
0x401050  puts
0x401056  sub_401056
0x401060  printf
0x401066  sub_401066
0x401070  malloc
0x401076  sub_401076
0x401080  _start
0x4010b0  deregister_tm_clones
0x4010e0  sub_4010e0
0x401120  _FINI_0
0x401170  _INIT_0
0x401179  helper_add
0x40118d  helper_multiply
0x4011a0  helper_subtract
```

## funcs -p compute

```
0x40120a  compute_factorial
0x401235  compute_fibonacci
0x401295  compute_gcd
```

## funcs -p helper

```
0x401179  helper_add
0x40118d  helper_multiply
0x4011a0  helper_subtract
0x4011b2  helper_print_number
0x4011d9  helper_print_string
```

## funcs --named -n 30

```
0x401000  _init
0x401030  free
0x401040  strncpy
0x401050  puts
0x401060  printf
0x401070  malloc
0x401080  _start
0x4010b0  deregister_tm_clones
0x401120  _FINI_0
0x401170  _INIT_0
0x401179  helper_add
0x40118d  helper_multiply
0x4011a0  helper_subtract
0x4011b2  helper_print_number
0x4011d9  helper_print_string
0x40120a  compute_factorial
0x401235  compute_fibonacci
0x401295  compute_gcd
0x4012c2  process_command
0x4013ca  plugin_init
0x4013f9  plugin_process
0x40145f  plugin_cleanup
0x401489  create_entity
0x40151f  update_entity_position
0x40158e  destroy_entity
0x4015d2  validate_header
0x401668  process_file
0x4016d3  get_timestamp
0x4016f1  rotate_left
0x401709  rotate_right
```

## funcs -s 0x401700 -e 0x401900

```
0x401709  rotate_right
0x401721  bitfield_extract
0x40175e  bitfield_insert
0x4017aa  fill_buffer
0x4017e9  compare_buffers
0x401842  xor_buffers
0x40189c  initialize_globals
```

## disasm 0x401235 -n 30

```

00401235    int compute_fibonacci(int n) __pure

00401235  55                 push    rbp {__saved_rbp}
00401236  4889e5             mov     rbp, rsp {__saved_rbp}
00401239  897dec             mov     dword [rbp-0x14 {var_1c}], edi
0040123c  837dec00           cmp     dword [rbp-0x14 {var_1c}], 0x0
00401240  7f07               jg      0x401249

00401242  b800000000         mov     eax, 0x0
00401247  eb4a               jmp     0x401293

00401249  837dec01           cmp     dword [rbp-0x14 {var_1c}], 0x1
0040124d  7507               jne     0x401256

0040124f  b801000000         mov     eax, 0x1
00401254  eb3d               jmp     0x401293

00401256  c745f000000000     mov     dword [rbp-0x10 {a}], 0x0
0040125d  c745f401000000     mov     dword [rbp-0xc {b}], 0x1
00401264  c745f802000000     mov     dword [rbp-0x8 {i}], 0x2
0040126b  eb1b               jmp     0x401288

0040126d  8b55f0             mov     edx, dword [rbp-0x10 {a}]
00401270  8b45f4             mov     eax, dword [rbp-0xc {b}]
00401273  01d0               add     eax, edx
00401275  8945fc             mov     dword [rbp-0x4 {temp}], eax
00401278  8b45f4             mov     eax, dword [rbp-0xc {b}]
0040127b  8945f0             mov     dword [rbp-0x10 {a}], eax
0040127e  8b45fc             mov     eax, dword [rbp-0x4 {temp}]
```

## hlil 0x401235 -n 30

```

00401235    int compute_fibonacci(int n) __pure

00401240     if (n s<= 0)
00401242        return 0
00401242     
0040124d     if (n == 1)
0040124f        return 1
0040124f     
00401256     int a = 0
0040125d     int b = 1
0040125d     
0040128e     for (int i = 2; i s<= n; i += 1)
00401273        int32_t b_1 = b + a
0040127b        a = b
00401281        b = b_1
00401281     
00401290     return b
```

## mlil 0x401235 -n 20

```

00401235    int compute_fibonacci(int n) __pure

   0 @ 00401239  var_1c = n
   1 @ 00401240  if (var_1c s> 0) then 2 @ 0x40124d else 3 @ 0x401242

   2 @ 0040124d  if (var_1c != 1) then 5 @ 0x401256 else 9 @ 0x40124f

   3 @ 00401242  rax_1 = 0
   4 @ 00401247  goto 11 @ 0x401294

   5 @ 00401256  a = 0
   6 @ 0040125d  b = 1
   7 @ 00401264  i = 2
   8 @ 0040126b  goto 12 @ 0x401288

   9 @ 0040124f  rax_1 = 1
  10 @ 00401254  goto 11 @ 0x401294

  11 @ 00401294  return rax_1
```

## disasm 0x999999

```
Function not found
```

## strings -n 15

```
0x4003b4  '/lib64/ld-linux-x86-64.so.2'
0x4004fe  'strncpy'
0x40050b  'malloc'
0x400512  '__libc_start_main'
0x400524  '__cxa_finalize'
0x400533  'printf'
0x40053a  'libc.so.6'
0x400544  'GLIBC_2.34'
0x40054f  'GLIBC_2.2.5'
0x40055b  '_ITM_deregisterTMCloneTable'
0x400577  '__gmon_start__'
0x400586  '_ITM_registerTMCloneTable'
0x401426  'gfffH'
0x4015f3  '<Tu$H'
0x402008  'BNTestBinary'
```

## strings -p Error

```
0x402036  'Error: invalid input'
0x40222f  'Error: invalid magic'
```

## xrefs 0x401235

```
0x401378  process_command
0x40144a  plugin_process
0x4019da  main
```

## xrefs 0x401179 -c

```
Total: 1 refs
----------------------------------------
   1  process_command
```

## xrefs 0x999999

```
No references found
```

## callers 0x401235

```
0x4012c2  process_command
0x4013f9  plugin_process
0x401936  main
```

## callees 0x4012c2

```

```

## read 0x402008 -n 64

```
00402008  42 4e 54 65 73 74 42 69  6e 61 72 79 00 31 2e 30  |BNTestBinary.1.0|
00402018  2e 30 2d 74 65 73 74 00  43 6c 61 75 64 65 20 54  |.0-test.Claude T|
00402028  65 73 74 20 47 65 6e 65  72 61 74 6f 72 00 45 72  |est Generator.Er|
00402038  72 6f 72 3a 20 69 6e 76  61 6c 69 64 20 69 6e 70  |ror: invalid inp|
00402048
```

## read 0x404080 -n 64

```
00404080  4d 61 69 6e 45 6e 74 69  74 79 00 00 00 00 00 00  |MainEntity......|
00404090  00 00 00 00 00 00 00 00  00 00 00 00 00 00 00 00  |................|
004040a0  2a 00 00 00 34 12 00 00  0a 00 00 00 14 00 00 00  |*...4...........|
004040b0  1e 00 00 00 00 00 00 00  00 00 00 00 00 00 00 00  |................|
004040c0
```

## sig 0x401235

```
int compute_fibonacci(int n)
```

## sig 0x401489

```
char* create_entity(char const* name, uint32_t id)
```

## struct --list

```
  16  Elf64_Dyn
  64  Elf64_Header
  16  Elf64_Ident
  56  Elf64_ProgramHeader
  24  Elf64_Rela
  64  Elf64_SectionHeader
  24  Elf64_Sym
  52  Entity
  32  FileHeader
  32  PluginInterface
  12  Point3D
   4  __int32_t
   4  __uint32_t
   8  __uint64_t
   1  __uint8_t
   8  e_dyn_tag
   2  e_machine
   2  e_type
   4  int32_t
   4  p_flags
   4  p_type
   8  sh_flags
   4  sh_type
   8  size_t
   4  uint32_t
   8  uint64_t
   1  uint8_t
   8  va_list
```

## struct Entity

```
struct Entity (52 bytes):
  0x0     char[0x20]            name
  0x20    uint32_t              id
  0x24    uint32_t              flags
  0x28    struct Point3D        position
```

## struct PluginInterface

```
struct PluginInterface (32 bytes):
  0x0     void (*)()            init
  0x8     void (*)(int)         process
  0x10    void (*)()            cleanup
  0x18    char const*           name
```

## struct Point3D

```
struct Point3D (12 bytes):
  0x0     int32_t               x
  0x4     int32_t               y
  0x8     int32_t               z
```

## struct NonExistent

```
Type 'NonExistent' not found
```

## vars 0x404160

```
0x404160  void*  g_plugin
```

## deref 0x404160 -d 4

```
0x404160: 0x4013ca  plugin_init
0x404168: 0x4013f9  plugin_process
0x404170: 0x40145f  plugin_cleanup
0x404178: 0x402168  'TestPlugin'
```

## eval "[(hex(f.start), f.name) for f in bv.functions if 'main' in f.name]"

```
[('0x401936', 'main')]
```
