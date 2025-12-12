#!/usr/bin/env python3
"""Binary Ninja HTTP API helper script for firmware reversing."""

import argparse
import sys
import requests

API_URL = "http://127.0.0.1:31337/eval"

def run_code(code: str) -> dict:
    """Execute code via Binary Ninja HTTP API."""
    resp = requests.post(API_URL, json={"code": code}, timeout=30)
    return resp.json()

def unquote(s: str) -> str:
    """Remove surrounding quotes from repr'd string."""
    if s and (s.startswith("'") or s.startswith('"')):
        return eval(s)
    return s

def cmd_il(args, view_method):
    """Get IL view of a function."""
    code = f"""
from binaryninja import LinearViewObject, DisassemblySettings, DisassemblyOption
f = bv.get_function_at({args.address}) or next(iter(bv.get_functions_containing({args.address})), None)
if f:
    settings = DisassemblySettings.default_linear_settings()
    settings.set_option(DisassemblyOption.WaitForIL, True)
    lvo = LinearViewObject.{view_method}(f, settings)
    cursor = lvo.cursor
    cursor.seek_to_begin()
    lines = []
    while not cursor.after_end:
        lines.extend(str(line.contents) for line in cursor.lines)
        cursor.next()
    result = chr(10).join(lines[:{args.lines}])
else:
    result = "Function not found"
result
"""
    result = run_code(code)
    if result.get("success"):
        print(unquote(result["result"]))
    else:
        print(f"Error: {result}", file=sys.stderr)

def cmd_disasm(args):
    """Get disassembly of a function."""
    cmd_il(args, "single_function_disassembly")

def cmd_hlil(args):
    """Get HLIL of a function."""
    cmd_il(args, "single_function_hlil")

def cmd_funcs(args):
    """List functions in address range or by name pattern."""
    if args.pattern:
        code = f'[(hex(f.start), f.name) for f in bv.functions if "{args.pattern}" in f.name.lower()][:{args.limit}]'
    elif args.start and args.end:
        code = f'[(hex(f.start), f.name) for f in bv.functions if {args.start} <= f.start <= {args.end}][:{args.limit}]'
    elif args.named:
        code = f'[(hex(f.start), f.name) for f in bv.functions if not f.name.startswith("sub_")][:{args.limit}]'
    else:
        code = f'[(hex(f.start), f.name) for f in bv.functions][:{args.limit}]'

    result = run_code(code)
    if result.get("success"):
        funcs = eval(result["result"])
        for addr, name in funcs:
            print(f"{addr}  {name}")
    else:
        print(f"Error: {result}", file=sys.stderr)

def cmd_rename(args):
    """Rename a function."""
    code = f'bv.get_function_at({args.address}).name = "{args.name}"; "ok"'
    result = run_code(code)
    if result.get("success"):
        print(f"Renamed {hex(args.address)} to {args.name}")
    else:
        print(f"Error: {result}", file=sys.stderr)

def cmd_xrefs(args):
    """Get cross-references to an address."""
    if args.count:
        # Count refs grouped by function
        code = f'''
refs = list(bv.get_code_refs({args.address})) + list(bv.get_data_refs({args.address}))
func_counts = {{}}
for x in refs:
    if hasattr(x, "function"):
        name = x.function.name if x.function else "data"
    else:
        funcs = bv.get_functions_containing(x)
        name = funcs[0].name if funcs else "data"
    func_counts[name] = func_counts.get(name, 0) + 1
sorted(func_counts.items(), key=lambda x: -x[1])[:{args.limit}]
'''
        result = run_code(code)
        if result.get("success") and result["result"]:
            counts = eval(result["result"])
            if counts:
                total = sum(c for _, c in counts)
                print(f"Total: {total} refs")
                print("-" * 40)
                for name, count in counts:
                    print(f"{count:4d}  {name}")
            else:
                print("No references found")
        else:
            print(f"Error: {result}", file=sys.stderr)
    else:
        code = f'''
results = []
for x in bv.get_code_refs({args.address}):
    results.append((hex(x.address), x.function.name if x.function else "data"))
for x in bv.get_data_refs({args.address}):
    funcs = bv.get_functions_containing(x)
    name = funcs[0].name if funcs else "data"
    results.append((hex(x), name))
results[:{args.limit}]
'''
        result = run_code(code)
        if result.get("success") and result["result"]:
            refs = eval(result["result"])
            if refs:
                for addr, func in refs:
                    print(f"{addr}  {func}")
            else:
                print("No references found")
        else:
            print(f"Error: {result}", file=sys.stderr)

def cmd_callees(args):
    """Get functions called by a function."""
    code = f"""
import re
f = bv.get_function_at({args.address}) or next(iter(bv.get_functions_containing({args.address})), None)
if f:
    calls = set()
    for block in f.basic_blocks:
        for insn in block.get_disassembly_text():
            s = str(insn)
            if 'jsr' in s.lower() or 'bsr' in s.lower():
                m = re.search(r'@(0x[0-9a-fA-F]+)', s)
                if m:
                    target = int(m.group(1), 16)
                    tf = bv.get_function_at(target)
                    if tf:
                        calls.add((hex(target), tf.name))
    result = sorted(calls)
else:
    result = []
result
"""
    result = run_code(code)
    if result.get("success"):
        calls = eval(result["result"])
        for addr, name in calls:
            print(f"{addr}  {name}")
    else:
        print(f"Error: {result}", file=sys.stderr)

def cmd_strings(args):
    """Search for strings."""
    if args.pattern:
        code = f'[(hex(s.start), s.value) for s in bv.strings if "{args.pattern}" in s.value][:{args.limit}]'
    else:
        code = f'[(hex(s.start), s.value) for s in bv.strings if len(s.value) > 4][:{args.limit}]'

    result = run_code(code)
    if result.get("success"):
        strings = eval(result["result"])
        for addr, val in strings:
            print(f"{addr}  {repr(val)}")
    else:
        print(f"Error: {result}", file=sys.stderr)

def cmd_read(args):
    """Read bytes at address in hexdump -C format."""
    code = f'bv.read({args.address}, {args.length}).hex()'
    result = run_code(code)
    if result.get("success"):
        hex_str = result["result"].strip("'\"")
        data = bytes.fromhex(hex_str)
        addr = args.address
        for i in range(0, len(data), 16):
            chunk = data[i:i+16]
            # Hex part
            hex_part = ' '.join(f'{b:02x}' for b in chunk[:8])
            if len(chunk) > 8:
                hex_part += '  ' + ' '.join(f'{b:02x}' for b in chunk[8:])
            else:
                hex_part += '  '
            # Pad hex part to fixed width
            hex_part = hex_part.ljust(49)
            # ASCII part
            ascii_part = ''.join(chr(b) if 0x20 <= b < 0x7f else '.' for b in chunk)
            print(f'{addr + i:08x}  {hex_part} |{ascii_part}|')
        print(f'{addr + len(data):08x}')
    else:
        print(f"Error: {result}", file=sys.stderr)

def cmd_eval(args):
    """Run arbitrary Python code."""
    result = run_code(args.code)
    if result.get("success"):
        print(result["result"])
    else:
        print(f"Error: {result}", file=sys.stderr)

def show_struct(name):
    """Helper to display a struct by name."""
    code = f'''
t = bv.get_type_by_name("{name}")
if hasattr(t, 'target'):
    t = bv.get_type_by_name(str(t.target))
if not t:
    result = None
elif hasattr(t, 'members') and t.members:
    result = ("{name}", t.width, [(m.name, hex(m.offset), str(m.type)) for m in t.members])
else:
    result = ("{name}", t.width, [])
result
'''
    result = run_code(code)
    if result.get("success") and result["result"] and result["result"] != "None":
        sname, width, members = eval(result["result"])
        print(f"struct {sname} ({width} bytes):")
        for mname, offset, mtype in members:
            print(f"  {offset:6s}  {mtype:20s}  {mname}")
        return True
    elif result.get("success"):
        print(f"Type '{name}' not found")
    else:
        print(f"Error: {result}", file=sys.stderr)
    return False

def cmd_struct(args):
    """Show or define a structure."""
    if args.define:
        # Define a new struct from C-like syntax
        # Format: "struct Foo { int32_t x; uint8_t y; }"
        c_def = args.define.strip()
        code = f'''
try:
    t, name = bv.parse_type_string("""{c_def}""")
    if name:
        bv.define_user_type(name, t)
    result = ("ok", name)
except Exception as e:
    result = ("error", str(e))
result
'''
        result = run_code(code)
        if result.get("success"):
            out = eval(result["result"])
            if out[0] == "ok":
                show_struct(out[1])
            else:
                print(f"Parse error: {out[1]}", file=sys.stderr)
        else:
            print(f"Error: {result}", file=sys.stderr)
    elif args.name:
        show_struct(args.name)
    elif args.list:
        # List all user types
        code = '[(str(k), bv.get_type_by_name(str(k)).width if bv.get_type_by_name(str(k)) else 0) for k in bv.types.keys()]'
        result = run_code(code)
        if result.get("success"):
            types = eval(result["result"])
            for name, width in sorted(types):
                print(f"{width:4d}  {name}")
        else:
            print(f"Error: {result}", file=sys.stderr)

def cmd_vars(args):
    """List or define data variables."""
    if args.address:
        # Show var at address
        code = f'''
var = bv.get_data_var_at({args.address})
(hex(var.address), str(var.type), var.name if hasattr(var, "name") else "") if var else None
'''
        result = run_code(code)
        if result.get("success") and result["result"] and result["result"] != "None":
            addr, vtype, name = eval(result["result"])
            print(f"{addr}  {vtype}  {name}")
        else:
            print("No variable at address")
    else:
        # List all named data vars in range
        start = args.start or 0x400000
        end = args.end or 0x500000
        code = f'''
vars = []
for addr in range({start}, {end}, 8):
    var = bv.get_data_var_at(addr)
    if var and hasattr(var, "name") and var.name:
        vars.append((hex(var.address), str(var.type)[:30], var.name))
vars[:{args.limit}]
'''
        result = run_code(code)
        if result.get("success") and result["result"]:
            variables = eval(result["result"])
            if variables:
                for addr, vtype, name in variables:
                    print(f"{addr}  {vtype:30s}  {name}")
            else:
                print("No named variables in range")
        else:
            print(f"Error: {result}", file=sys.stderr)

def cmd_callers(args):
    """Get functions that call a function."""
    code = f'''
f = bv.get_function_at({args.address})
sorted({{(hex(ref.function.start), ref.function.name) for ref in bv.get_code_refs(f.start) if ref.function}}) if f else []
'''
    result = run_code(code)
    if result.get("success"):
        callers = eval(result["result"])
        for addr, name in callers:
            print(f"{addr}  {name}")
    else:
        print(f"Error: {result}", file=sys.stderr)

def cmd_sig(args):
    """Show or set function signature."""
    if args.signature:
        # Set signature using bv.parse_type_string
        # Escape the signature for embedding in Python code
        sig_escaped = args.signature.replace('\\', '\\\\').replace('"', '\\"')
        code = f'''
f = bv.get_function_at({args.address})
if f:
    try:
        t, name = bv.parse_type_string("{sig_escaped}")
        f.set_user_type(t)
        result = "ok"
    except Exception as e:
        result = f"Parse error: {{e}}"
else:
    result = "Function not found"
result
'''
        result = run_code(code)
        if result.get("success"):
            out = unquote(result["result"])
            if out == "ok":
                print(f"Set signature at {hex(args.address)}")
            else:
                print(out, file=sys.stderr)
        else:
            print(f"Error: {result}", file=sys.stderr)
    else:
        # Show current signature
        code = f'''
f = bv.get_function_at({args.address})
f"{{f.return_type}} {{f.name}}({{', '.join(f'{{str(p.type)}} {{p.name}}' for p in f.parameter_vars)}})" if f else "Function not found"
'''
        result = run_code(code)
        if result.get("success"):
            print(unquote(result["result"]))
        else:
            print(f"Error: {result}", file=sys.stderr)

def cmd_type(args):
    """Set type on a symbol (function or data variable)."""
    type_escaped = args.type_str.replace('\\', '\\\\').replace('"', '\\"')
    code = f'''
try:
    t, _ = bv.parse_type_string("{type_escaped}")
    f = bv.get_function_at({args.address})
    if f:
        f.set_user_type(t)
        result = ("ok", "function")
    else:
        bv.define_user_data_var({args.address}, t)
        result = ("ok", "data")
except Exception as e:
    result = ("error", str(e))
result
'''
    result = run_code(code)
    if result.get("success"):
        out = eval(result["result"])
        if out[0] == "ok":
            print(f"Set {out[1]} type at {hex(args.address)}")
        else:
            print(f"Parse error: {out[1]}", file=sys.stderr)
    else:
        print(f"Error: {result}", file=sys.stderr)

def cmd_mlil(args):
    """Get MLIL of a function."""
    cmd_il(args, "single_function_mlil")

def cmd_deref(args):
    """Dereference pointer chain at address."""
    code = f'''
results = []
for i in range({args.depth}):
    addr = {args.address} + i*8
    val = bv.read(addr, 8)
    if len(val) == 8:
        ptr = int.from_bytes(val, "little")
        s = bv.get_ascii_string_at(ptr)
        f = bv.get_function_at(ptr)
        results.append((hex(addr), hex(ptr), f.name if f else "", s.value[:50] if s else ""))
results
'''
    result = run_code(code)
    if result.get("success"):
        ptrs = eval(result["result"])
        for addr, val, fname, sval in ptrs:
            extra = fname if fname else (repr(sval) if sval else "")
            print(f"{addr}: {val}  {extra}")
    else:
        print(f"Error: {result}", file=sys.stderr)

def cmd_comment(args):
    """Set comment at address."""
    code = f'f = bv.get_functions_containing({args.address}); f[0].set_comment_at({args.address}, """{args.text}""") if f else None; "ok"'
    result = run_code(code)
    if result.get("success"):
        print(f"Comment set at {hex(args.address)}")
    else:
        print(f"Error: {result}", file=sys.stderr)

def cmd_patch(args):
    """Patch bytes at address."""
    # Parse hex bytes
    hex_bytes = args.bytes.replace(" ", "")
    try:
        patch_data = bytes.fromhex(hex_bytes)
    except ValueError as e:
        print(f"Invalid hex bytes: {e}", file=sys.stderr)
        return

    # Convert to list for embedding in code
    byte_list = list(patch_data)

    code = f'''
original = bv.read({args.address}, {len(byte_list)})
bv.write({args.address}, bytes({byte_list}))
original.hex()
'''
    result = run_code(code)
    if result.get("success"):
        original = unquote(result["result"])
        print(f"Patched {hex(args.address)}: {original} -> {hex_bytes}")
    else:
        print(f"Error: {result}", file=sys.stderr)

def parse_addr(s):
    """Parse address from hex or decimal string."""
    return int(s, 16) if s.startswith("0x") else int(s)

def main():
    parser = argparse.ArgumentParser(description="Binary Ninja HTTP API helper")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # disasm
    p = subparsers.add_parser("disasm", aliases=["d"], help="Disassemble function")
    p.add_argument("address", type=parse_addr, help="Function address")
    p.add_argument("-n", "--lines", type=int, default=100, help="Max lines")
    p.set_defaults(func=cmd_disasm)

    # hlil
    p = subparsers.add_parser("hlil", aliases=["h"], help="Get HLIL of function")
    p.add_argument("address", type=parse_addr, help="Function address")
    p.add_argument("-n", "--lines", type=int, default=100, help="Max lines")
    p.set_defaults(func=cmd_hlil)

    # funcs
    p = subparsers.add_parser("funcs", aliases=["f"], help="List functions")
    p.add_argument("-p", "--pattern", help="Name pattern to search")
    p.add_argument("-s", "--start", type=parse_addr, help="Start address")
    p.add_argument("-e", "--end", type=parse_addr, help="End address")
    p.add_argument("--named", action="store_true", help="Only named functions")
    p.add_argument("-n", "--limit", type=int, default=50, help="Max results")
    p.set_defaults(func=cmd_funcs)

    # rename
    p = subparsers.add_parser("rename", aliases=["r"], help="Rename function")
    p.add_argument("address", type=parse_addr, help="Function address")
    p.add_argument("name", help="New name")
    p.set_defaults(func=cmd_rename)

    # xrefs
    p = subparsers.add_parser("xrefs", aliases=["x"], help="Get xrefs to address")
    p.add_argument("address", type=parse_addr, help="Target address")
    p.add_argument("-c", "--count", action="store_true", help="Group by function and count")
    p.add_argument("-n", "--limit", type=int, default=50, help="Max results")
    p.set_defaults(func=cmd_xrefs)

    # callees
    p = subparsers.add_parser("callees", aliases=["c"], help="Get callees of function")
    p.add_argument("address", type=parse_addr, help="Function address")
    p.set_defaults(func=cmd_callees)

    # strings
    p = subparsers.add_parser("strings", aliases=["s"], help="Search strings")
    p.add_argument("-p", "--pattern", help="Pattern to search")
    p.add_argument("-n", "--limit", type=int, default=30, help="Max results")
    p.set_defaults(func=cmd_strings)

    # read
    p = subparsers.add_parser("read", help="Read bytes at address")
    p.add_argument("address", type=parse_addr, help="Address")
    p.add_argument("-n", "--length", type=int, default=32, help="Bytes to read")
    p.set_defaults(func=cmd_read)

    # eval
    p = subparsers.add_parser("eval", aliases=["e"], help="Run arbitrary code")
    p.add_argument("code", help="Python code to execute")
    p.set_defaults(func=cmd_eval)

    # struct
    p = subparsers.add_parser("struct", aliases=["st"], help="Show/list structures")
    p.add_argument("name", nargs="?", help="Structure name to show")
    p.add_argument("-l", "--list", action="store_true", help="List all types")
    p.add_argument("-d", "--define", help="Define struct (JSON format)")
    p.set_defaults(func=cmd_struct)

    # vars
    p = subparsers.add_parser("vars", aliases=["v"], help="List/show data variables")
    p.add_argument("address", type=parse_addr, nargs="?", help="Variable address")
    p.add_argument("-s", "--start", type=parse_addr, help="Start address for listing")
    p.add_argument("-e", "--end", type=parse_addr, help="End address for listing")
    p.add_argument("-n", "--limit", type=int, default=50, help="Max results")
    p.set_defaults(func=cmd_vars)

    # callers
    p = subparsers.add_parser("callers", aliases=["cr"], help="Get callers of function")
    p.add_argument("address", type=parse_addr, help="Function address")
    p.set_defaults(func=cmd_callers)

    # sig
    p = subparsers.add_parser("sig", help="Show/set function signature")
    p.add_argument("address", type=parse_addr, help="Function address")
    p.add_argument("signature", nargs="?", help="New signature (e.g., 'int32_t foo(char* a, int b)')")
    p.set_defaults(func=cmd_sig)

    # type
    p = subparsers.add_parser("type", aliases=["t"], help="Set type on symbol (function or data)")
    p.add_argument("address", type=parse_addr, help="Symbol address")
    p.add_argument("type_str", help="Type string (e.g., 'int32_t foo(char* a)' or 'uint8_t[16]')")
    p.set_defaults(func=cmd_type)

    # mlil
    p = subparsers.add_parser("mlil", aliases=["m"], help="Get MLIL of function")
    p.add_argument("address", type=parse_addr, help="Function address")
    p.add_argument("-n", "--lines", type=int, default=100, help="Max lines")
    p.set_defaults(func=cmd_mlil)

    # deref
    p = subparsers.add_parser("deref", aliases=["dr"], help="Dereference pointer(s)")
    p.add_argument("address", type=parse_addr, help="Start address")
    p.add_argument("-d", "--depth", type=int, default=8, help="Number of pointers")
    p.set_defaults(func=cmd_deref)

    # comment
    p = subparsers.add_parser("comment", aliases=["cmt"], help="Set comment at address")
    p.add_argument("address", type=parse_addr, help="Address")
    p.add_argument("text", help="Comment text")
    p.set_defaults(func=cmd_comment)

    # patch
    p = subparsers.add_parser("patch", aliases=["p"], help="Patch bytes at address")
    p.add_argument("address", type=parse_addr, help="Address to patch")
    p.add_argument("bytes", help="Hex bytes to write (e.g., 'EB30' or '90 90 90')")
    p.set_defaults(func=cmd_patch)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    args.func(args)

if __name__ == "__main__":
    main()
