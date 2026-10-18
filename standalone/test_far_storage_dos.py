#!/usr/bin/env python3
"""Actual DOS PROGRAM child validates retained far metadata/history allocation."""
import argparse,hashlib,json,re,struct,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('--binary',type=Path,default=ROOT/'build/terminal/TERMINAL.EXE');p.add_argument('--map',type=Path);a=p.parse_args();a.binary=a.binary.resolve();a.map=a.map or a.binary.parent/'terminal.map'
 listing=a.map.read_text();symbols={name:(int(seg,16),int(off,16)) for seg,off,name in re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$',listing,re.M|re.I)}
 group=re.search(r'^DGROUP\s+([0-9a-f]+):',listing,re.M|re.I);assert group;dg=int(group[1],16)
 def near(name):seg,off=symbols[name];return seg*16+off-dg*16
 far,shadow=symbols['erase_shadow_cells'];hseg,history=symbols['terminal_history_buffer'];endseg,endoff=symbols['terminal_far_storage_end'];assert far==hseg==endseg and endoff-shadow==12288
 defines={'DGROUP_SEG':dg,'FAR_SEG':far,'SHADOW_OFFSET':shadow,'HISTORY_OFFSET':history,'FAR_END_OFFSET':endoff,'PROCESS_PSP_OFFSET':near('process_psp'),'SHADOW_SEGMENT_OFFSET':near('erase_shadow_segment'),'HISTORY_POINTER_OFFSET':near('terminal_history_pointer')}
 out=ROOT/'build/far-storage-dos';out.mkdir(parents=True,exist_ok=True);child=out/'FARTEST.COM'
 subprocess.run(['nasm','-fbin',*[f'-D{k}={v}' for k,v in defines.items()],str(ROOT/'standalone/far_storage_child.asm'),'-o',str(child)],check=True)
 import test_connection_dos
 test_connection_dos.BINARY=a.binary
 from modem_fixtures import fixture
 keys=bytearray(540)
 for i in range(10):struct.pack_into('<H',keys,i*54,3)
 command=b'D:\\FARTEST.COM';struct.pack_into('<H',keys,0,1);keys[2:2+len(command)]=command
 folder=ROOT/'build/connection-dos/far-storage';folder.mkdir(parents=True,exist_ok=True);(folder/'FARTEST.BIN').unlink(missing_ok=True)
 proof=test_connection_dos.run('far-storage','success','p3000 a-1 p2000 space p1200 a-x',prm=fixture(timeout=5),arguments='@D:\\TEST.PRM /D:CaseTest:23 /T:D:\\TEST.KEY COM1 38400 HARD',files={'TEST.KEY':bytes(keys),'FARTEST.COM':child.read_bytes()})
 sample=(folder/'FARTEST.BIN').read_bytes() if (folder/'FARTEST.BIN').exists() else b''
 checks=proof['checks'];checks['owned_child_found_parent_and_retained_far_extent']=len(sample)==20 and struct.unpack_from('<H',sample)[0]==7
 if len(sample)==20:
  status,parent,retained,required,segment,allocated,*markers=struct.unpack('<10H',sample)
  checks['MCB_covers_far_end_after_STACK']=retained>=required==16+far+(endoff+15)//16
  checks['new_DOS_allocation_does_not_overlap_far_parent']=not(parent+16+far<=allocated<parent+required)
  checks['shadow_and_history_canaries_survive_child_allocation_fill']=markers==[0xcafe,0xbeef,0xdead,0xbabe]
 proof['passed']=all(checks.values());proof['binary_sha256']=hashlib.sha256(a.binary.read_bytes()).hexdigest();proof['sample_hex']=sample.hex();proof['linker_defines']=defines;proof['scope']='Actual DOS livePROGRAM/COMSPEC owned child locates parent PSP, checks retainedMCB throughfarend afterSTACK, allocates/fills16KB separateDOSmemory and verifies full-sizedshadow/history endpointcanaries. NormalUART/vector cleanup verified by existing sampler. No physical modem claim.'
 (out/'checks.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof,indent=2));return 0 if proof['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
