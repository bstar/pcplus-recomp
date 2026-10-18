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
 snapseg,snapoff=symbols['terminal_snapshot_image'];snapendseg,snapendoff=symbols['terminal_snapshot_image_end'];assert snapseg==snapendseg and snapendoff-snapoff==2000
 required=16+(max(endseg*16+endoff,snapendseg*16+snapendoff,symbols['terminal_stack_top'][0]*16+symbols['terminal_stack_top'][1])+15)//16
 defines={'DGROUP_SEG':dg,'FAR_SEG':far,'SHADOW_OFFSET':shadow,'HISTORY_OFFSET':history,'FAR_END_OFFSET':endoff,'PROCESS_PSP_OFFSET':near('process_psp'),'SHADOW_SEGMENT_OFFSET':near('erase_shadow_segment'),'HISTORY_POINTER_OFFSET':near('terminal_history_pointer')}
 code_seg,code_off=symbols['terminal_controller_code_start'];code_endseg,code_endoff=symbols['terminal_controller_code_end'];assert code_seg==code_endseg
 image=a.binary.read_bytes();header=struct.unpack_from('<14H',image);first=struct.unpack_from('<H',image,header[4]*16+code_seg*16+code_off)[0]
 required=max(required,16+(code_seg*16+code_endoff+15)//16)
 defines.update(SNAPSHOT_SEG=snapseg,SNAPSHOT_OFFSET=snapoff,REQUIRED_PARAS=required,CODE_SEG=code_seg,CODE_START=code_off,CODE_BYTES=code_endoff-code_off,CODE_FIRST=first)
 modem_seg,modem_off=symbols['terminal_modem_code_start'];modem_endseg,modem_endoff=symbols['terminal_modem_code_end'];assert modem_seg==modem_endseg and modem_seg!=code_seg
 required=max(required,16+(modem_seg*16+modem_endoff+15)//16)
 defines.update(MODEM_SEG=modem_seg,MODEM_START=modem_off,MODEM_BYTES=modem_endoff-modem_off)
 ui_seg,browser_off=symbols['browser_screen'];ed_seg,ed_off=symbols['ed_screen'];program_seg,program_off=symbols['program_screen'];assert ui_seg==ed_seg==program_seg
 required=max(required,16+(ui_seg*16+max(browser_off,ed_off,program_off)+4000+15)//16)
 defines['REQUIRED_PARAS']=required
 defines.update(UI_SEG=ui_seg,BROWSER_OFF=browser_off,EDITOR_OFF=ed_off,PROGRAM_OFF=program_off)
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
 checks=proof['checks'];checks['owned_child_found_parent_and_retained_far_extent']=len(sample)==56 and struct.unpack_from('<H',sample)[0]==63
 if len(sample)==56:
  status,parent,retained,observed_required,segment,allocated,*markers=struct.unpack('<28H',sample)
  checks['MCB_covers_far_end_after_STACK']=retained>=observed_required==required
  checks['new_DOS_allocation_disjoint_from_all_retained_parent_storage']=allocated>=parent+required or allocated+0x400<=parent
  checks['new_DOS_allocation_does_not_overlap_far_parent']=not(parent+16+far<=allocated<parent+required)
  checks['shadow_and_history_canaries_survive_child_allocation_fill']=markers[:4]==[0xcafe,0xbeef,0xdead,0xbabe]
  checks['snapshot_canaries_survive_child_allocation_fill']=markers[4:7]==[parent+16+snapseg,0x1122,0x3344]
  checks['far_code_sum_and_extent_survive_child_allocation_fill']=markers[7]==markers[8] and markers[9:11]==[parent+16+code_seg,code_endoff-code_off]
  checks['modem_far_code_sum_and_extent_survive_child_allocation_fill']=markers[18:20]==[parent+16+modem_seg,modem_endoff-modem_off] and markers[20]==markers[21]
  checks['all_three_far_UI_screen_buffers_survive_child_allocation_fill']=markers[11]==parent+16+ui_seg and all(markers[i]==markers[i+1] for i in (12,14,16))
 proof['passed']=all(checks.values());proof['binary_sha256']=hashlib.sha256(a.binary.read_bytes()).hexdigest();proof['sample_hex']=sample.hex();proof['linker_defines']=defines;proof['scope']='Actual DOS livePROGRAM/COMSPEC owned child locates parent PSP, checks retainedMCB throughfarend afterSTACK and FARCODE, allocates/fills16KB separateDOSmemory and verifies full-sizedshadow/history and frozen-screen endpointcanaries plus the full controller and modem far-code byte-sums before/after allocation and sums of all three full4000-byte far UI screen owners. Parent resumes actual far controller polling after child return. NormalUART/vector cleanup verified by existing sampler. No physical modem claim.'
 (out/'checks.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof,indent=2));return 0 if proof['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
