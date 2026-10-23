#!/usr/bin/env python3
"""Explicit optional comparison of the new codec with original HOOK instructions.
Build the codec from source first, then replay the hash-checked original at its
existing simulated resolver/EXEC/UI boundaries. No DOS helper process is run.
"""
import argparse,ctypes,hashlib,json,shutil,struct,subprocess
from pathlib import Path
from unicorn.x86_const import *
from check_meta_keys import Meta,ROOT,PROOF

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--original',action='store_true',required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
    names=['src/process/hook_exchange.c','src/process/hook_exchange.h','standalone/compare_hook_exchange_native.py','standalone/check_meta_keys.py','standalone/dos_image.py','reconstruction/meta_keys/provenance.json']
    sources={n:sha(ROOT/n) for n in names}
    for n in names:
        target=out/'source'/n;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/n,target)
    subprocess.run(['cc','-std=c89','-Wall','-Wextra','-Werror','-shared','-fPIC','-o',str(out/'exchange.so'),str(out/'source/src/process/hook_exchange.c')],check=True)
    library=ctypes.CDLL(str(out/'exchange.so'))
    class Command(ctypes.Structure):_fields_=[('integers',ctypes.c_ulong),('strings',ctypes.c_ulong),('prm',ctypes.c_ulong),('context',ctypes.c_long)]
    library.hook_key_format.argtypes=[ctypes.POINTER(Command),ctypes.c_void_p,ctypes.c_uint];library.hook_key_format.restype=ctypes.c_uint
    library.hook_key_parse.argtypes=[ctypes.c_void_p,ctypes.c_uint,ctypes.POINTER(Command)];library.hook_key_parse.restype=ctypes.c_uint
    cases=[]
    for context in [3,0,-1,32767,-32768]:
        m=Meta(original=True);pointer=m.input(b'HOOK.EXE');u=m.uc
        for reg,value in [(UC_X86_REG_CS,0x1000),(UC_X86_REG_DS,m.ds),(UC_X86_REG_SS,m.ds),(UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678)]:u.reg_write(reg,value)
        sp=0xe000;u.mem_write(m.data_base+sp,struct.pack('<5H',0xf000,1,0,context&65535,pointer));u.reg_write(UC_X86_REG_SP,sp);m.returned=False
        u.emu_start(m.symbols['meta_keys_hook'],0,count=100000)
        assert m.returned and u.reg_read(UC_X86_REG_SP)==sp+10
        assert len(m.events)==2 and m.events[0]==('resolve',b'HOOK.EXE')
        event=m.events[1];assert event[:2]==('program',b'HOOK.EXE') and event[3:]==(0,0,0)
        tail=event[2];packed=lambda name:(m.ds<<16)|m.offset(name)
        command=Command(packed('meta_hook_exchange_a'),packed('meta_hook_exchange_b'),packed('meta_prm_image'),context)
        output=ctypes.create_string_buffer(48);assert library.hook_key_format(ctypes.byref(command),output,48)==0 and output.value==tail
        parsed=Command();assert library.hook_key_parse(tail,len(tail),ctypes.byref(parsed))==0
        assert (parsed.integers,parsed.strings,parsed.prm,parsed.context)==(command.integers,command.strings,command.prm,context)
        cases.append(dict(context=context,tail_hex=tail.hex(),integers=command.integers,strings=command.strings,prm=command.prm,passed=True))
    result=dict(passed=True,cases=cases,sources=sources,original_sha256=PROOF['source_sha256'],host_library_sha256=sha(out/'exchange.so'),
        scope='Five direct new-codec comparisons with genuine original414C KEY-mode command construction. Original target is read only after the source-only host codec is compiled. Resolver/EXEC/UI are explicit recording boundaries; no actual helper, terminal application, PRM mutation or hardware acceptance.')
    for n,h in sources.items():assert sha(ROOT/n)==h,n
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS five original HOOK/new codec comparisons')
if __name__=='__main__':main()
