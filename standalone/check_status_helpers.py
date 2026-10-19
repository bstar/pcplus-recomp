#!/usr/bin/env python3
"""Source-only CPU and actual8086DOS status helper/formatter composition proof."""
import argparse,hashlib,json,os,struct,subprocess
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_16,UC_HOOK_CODE,UC_HOOK_INTR,UC_HOOK_INSN
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/status-helpers'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def cpu_case(units,count,cga,direct=False):
 u=Uc(UC_ARCH_X86,UC_MODE_16);u.mem_map(0,0x100000)
 for p in units:u.mem_write(0x10000+p['entry'],(OUT/f"unit{p['unit']}.bin").read_bytes())
 for r,v in [(UC_X86_REG_CS,0x1000),(UC_X86_REG_DS,0x3000),(UC_X86_REG_SS,0x3000),(UC_X86_REG_ES,0xb800),(UC_X86_REG_SP,0x8800),(UC_X86_REG_DI,0x4321),(UC_X86_REG_EFLAGS,0x202)]:u.reg_write(r,v)
 put=lambda o,v:u.mem_write(0x30000+o,struct.pack('<H',v));put(0x8800,0xf000);put(0x7a78,0xb800);put(0x7a8e,0x3da if cga else 0)
 u.mem_write(0xb8000,b'\xcc'*4004);visited=set();reads=[]
 def code(m,a,n,d):
  if a==0x1f000:m.emu_stop()
  else:visited.add(a-0x10000)
 def port(m,p,n,d):
  assert p==0x3da and n==1
  value=[1,0,0,1][len(reads)%4];reads.append(value);return value
 u.hook_add(UC_HOOK_CODE,code);u.hook_add(UC_HOOK_INTR,lambda *a:(_ for _ in ()).throw(AssertionError('Unexpected OS interrupt')));u.hook_add(UC_HOOK_INSN,port,None,1,0,UC_X86_INS_IN)
 if direct:
  entry=0x7e0e;u.reg_write(UC_X86_REG_DX,0x3da);u.reg_write(UC_X86_REG_DI,3840);u.reg_write(UC_X86_REG_AX,90)
 else:entry=0x7630;put(0x8802,count);put(0x8804,3840);put(0x8806,90)
 u.emu_start(0x10000+entry,0x20000,count=10000);assert u.reg_read(UC_X86_REG_IP)==0xf000
 size=1 if direct else count;expected=bytearray(b'\xcc'*4004)
 for i in range(size):expected[3840+i*2]=90
 assert bytes(u.mem_read(0xb8000,4004))==bytes(expected)
 assert u.reg_read(UC_X86_REG_SP)==0x8802+(0 if direct else 6)
 assert u.reg_read(UC_X86_REG_DI)==(3841 if direct else 0x4321)
 assert len(reads)==4*size if cga else len(reads)==0
 return dict(count=count,cga=cga,direct=direct,passed=True,port_reads=reads,instruction_addresses=[hex(a)for a in sorted(visited)])
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--original',nargs='?',const='analysis/pcplus-originals/PCPLUS-main-2.01.EXE');args=parser.parse_args()
 m=json.loads((OUT/'manifest.json').read_text());assert m['original_inputs']==[]
 for p,h in m['source_dependencies'].items():assert sha(ROOT/p)==h,p
 assert sha(ROOT/'standalone/build_status_helpers.py')==m['builder_sha256'];assert sha(OUT/'STATUS.EXE')==m['diagnostic_sha256'];assert sha(OUT/'diagnostic.c')==m['generated_c_sha256']
 for p,h in m['objects'].items():assert sha(OUT/p)==h,p
 originals=[]
 if args.original:
  p=(ROOT/args.original).resolve();b=p.read_bytes();base=json.loads((ROOT/'standalone/fixtures/status_helper_units.json').read_text());assert hashlib.sha256(b).hexdigest()==base['original_sha256']
  for unit in m['units']:assert(OUT/f"unit{unit['unit']}.bin").read_bytes()==b[0x1200+unit['entry']:0x1200+unit['end']]
  originals=[dict(path=str(p),sha256=hashlib.sha256(b).hexdigest())]
 cpu=[cpu_case(m['units'],n,cga,direct)for n,cga,direct in [(1,False,False),(3,False,False),(1,True,False),(3,True,False),(0,True,False),(1,True,True)]]
 v=json.loads((ROOT/'standalone/fixtures/status_formatter_vectors.json').read_text())['cases'];conf=OUT/'dosbox.conf';conf.write_text(f'[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\ncycles=fixed 6000\n[mixer]\nnosound=true\n[autoexec]\n@echo off\nmount c "{OUT}"\nc:\nSTATUS\nexit\n')
 for pattern in ['T*.BIN','U*.BIN','MESSAGE.BIN','FILL.BIN']:
  for p in OUT.glob(pattern):p.unlink()
 with(OUT/'dosbox.log').open('w')as log:subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(conf)],cwd=OUT,stdout=log,stderr=log,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),timeout=30,check=True)
 dos=[];composed=[]
 for i,c in enumerate(v):
  p=OUT/f'T{i:02d}.BIN';expected=struct.pack('<h',c['expected_result'])+bytes.fromhex(c['expected_hex'])+b'\0';assert p.read_bytes()==expected,(c['name'],p.read_bytes(),expected);dos.append(dict(name=c['name'],passed=True,sha256=sha(p)))
  if i in m['composed_vector_indices']:
   expected=bytearray(b'\xcc'*4004)
   for j,ch in enumerate(bytes.fromhex(c['expected_hex'])):expected[3840+2*j:3842+2*j]=bytes([ch,0x1f])
   p=OUT/f'U{i:02d}.BIN';assert p.read_bytes()==expected,c['name'];composed.append(dict(name=c['name'],passed=True,screen_sha256=sha(p)))
 expected=bytearray(b'\xcc'*4004);expected[3840:4000]=b'\x20\x1f'*80
 for i,ch in enumerate(b'TEST'):expected[3840+2*(38+i)]=ch
 assert(OUT/'MESSAGE.BIN').read_bytes()==expected
 expected=bytearray(b'\xcc'*4004)
 for i in range(3):expected[3842+2*i]=90
 assert(OUT/'FILL.BIN').read_bytes()==expected
 record=dict(passed=True,original_inputs=originals,checker_sha256=sha(Path(__file__)),manifest_sha256=sha(OUT/'manifest.json'),diagnostic_sha256=m['diagnostic_sha256'],cpu=cpu,dos_formatter=dos,dos_composed=composed,dos_message_fill_cases=2,scope='Source-only exact175B helpers+maintained boundedformatter.6CPUcases include modeledCGAportsequence;25actual8086DOSformatter+7printf/screen+message+fill compositions. No physicalCGA, full2FB8, parentRPC orcompleteCRT claim. NonCGAcount0native65536-iterationquirk deliberately not exercised.')
 target=OUT/('checks-native.json'if args.original else'checks.json');target.write_text(json.dumps(record,indent=2)+'\n');print('STATUS:6CPUcases,25DOSformats,9DOScompositions PASS'+(' +175originalbytes'if args.original else''))
if __name__=='__main__':main()
