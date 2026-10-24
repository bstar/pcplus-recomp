#!/usr/bin/env python3
"""Actual DOS PROGRAM child validates retained far metadata/history allocation."""
import argparse,hashlib,json,re,struct,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('--binary',type=Path,default=ROOT/'build/terminal/TERMINAL.EXE');p.add_argument('--map',type=Path)
 p.add_argument('--label',help='Use fresh output folders instead of the legacy fixed fixture paths')
 a=p.parse_args();a.binary=a.binary.resolve();a.map=a.map or a.binary.parent/'terminal.map'
 assert a.label is None or re.fullmatch('[A-Za-z0-9_-]+',a.label)
 listing=a.map.read_text();symbols={name:(int(seg,16),int(off,16)) for seg,off,name in re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$',listing,re.M|re.I)}
 group=re.search(r'^DGROUP\s+([0-9a-f]+):',listing,re.M|re.I);assert group;dg=int(group[1],16)
 def near(name):seg,off=symbols[name];return seg*16+off-dg*16
 far,shadow=symbols['erase_shadow_cells'];hseg,history=symbols['terminal_history_buffer'];endseg,endoff=symbols['terminal_far_storage_end'];assert hseg==endseg and far!=hseg and endoff-history==63000
 snapseg,snapoff=symbols['terminal_snapshot_image'];snapendseg,snapendoff=symbols['terminal_snapshot_image_end'];assert snapseg==snapendseg and snapendoff-snapoff==2000
 required=16+(max(endseg*16+endoff,snapendseg*16+snapendoff,symbols['terminal_stack_top'][0]*16+symbols['terminal_stack_top'][1])+15)//16
 defines={'DGROUP_SEG':dg,'FAR_SEG':far,'SHADOW_OFFSET':shadow,'HISTORY_OFFSET':history,'HISTORY_SEG':hseg,'FAR_END_OFFSET':endoff,'PROCESS_PSP_OFFSET':near('process_psp'),'SHADOW_SEGMENT_OFFSET':near('erase_shadow_segment'),'HISTORY_POINTER_OFFSET':near('terminal_history_pointer')}
 code_seg,code_off=symbols['terminal_controller_code_start'];code_endseg,code_endoff=symbols['terminal_controller_code_end'];assert code_seg==code_endseg
 image=a.binary.read_bytes();header=struct.unpack_from('<14H',image);first=struct.unpack_from('<H',image,header[4]*16+code_seg*16+code_off)[0]
 required=max(required,16+(code_seg*16+code_endoff+15)//16)
 defines.update(SNAPSHOT_SEG=snapseg,SNAPSHOT_OFFSET=snapoff,REQUIRED_PARAS=required,CODE_SEG=code_seg,CODE_START=code_off,CODE_BYTES=code_endoff-code_off,CODE_FIRST=first)
 modem_seg,modem_off=symbols['terminal_modem_code_start'];modem_endseg,modem_endoff=symbols['terminal_modem_code_end'];assert modem_seg==modem_endseg and modem_seg!=code_seg
 required=max(required,16+(modem_seg*16+modem_endoff+15)//16)
 defines.update(MODEM_SEG=modem_seg,MODEM_START=modem_off,MODEM_BYTES=modem_endoff-modem_off)
 config_seg,config_off=symbols['terminal_config_code_start'];config_endseg,config_endoff=symbols['terminal_config_code_end'];assert config_seg==config_endseg and config_seg not in (code_seg,modem_seg)
 required=max(required,16+(config_seg*16+config_endoff+15)//16)
 defines.update(CONFIG_SEG=config_seg,CONFIG_START=config_off,CONFIG_BYTES=config_endoff-config_off)
 ui_seg,browser_off=symbols['browser_screen'];ed_seg,ed_off=symbols['ed_screen'];program_seg,program_off=symbols['program_screen'];assert ui_seg==ed_seg==program_seg
 required=max(required,16+(ui_seg*16+max(browser_off,ed_off,program_off)+4000+15)//16)
 defines['REQUIRED_PARAS']=required
 defines.update(UI_SEG=ui_seg,BROWSER_OFF=browser_off,EDITOR_OFF=ed_off,PROGRAM_OFF=program_off)
 has_native='nreset_reset_data_image'in symbols
 if has_native:
  native_topseg,native_topoff=symbols['nreset_stack_top']
  if native_topseg==0:
   native_seg,native_off=symbols['redisplay_snapshot'];private_seg=native_seg
   private_off=symbols['bank_shadow'][1];private_endseg=native_seg;private_endoff=symbols['bank_shadow_end'][1]
  else:
   native_group=re.search(r'^RESET_GROUP\s+([0-9a-f]+):([0-9a-f]+)',listing,re.M|re.I);assert native_group
   native_seg=int(native_group[1],16);native_off=int(native_group[2],16);assert native_seg==native_topseg
   private_seg,private_off=symbols['bank_shadow'];private_endseg,private_endoff=symbols['bank_shadow_end'];assert private_seg==private_endseg
  required=max(required,16+(native_seg*16+native_topoff+15)//16,16+(private_endseg*16+private_endoff+15)//16)
  defines.update(NATIVE_BANK_SEG=native_seg,NATIVE_BANK_OFFSET=native_off,NATIVE_BANK_BYTES=native_topoff-native_off,
   NATIVE_SHADOW_SEG=private_seg,NATIVE_SHADOW_OFFSET=private_off,NATIVE_SHADOW_BYTES=private_endoff-private_off,REQUIRED_PARAS=required)
 out=ROOT/'build/far-storage-dos'
 if a.label:out=out/a.label
 out.mkdir(parents=True,exist_ok=a.label is None);child=out/'FARTEST.COM'
 subprocess.run(['nasm','-fbin',*[f'-D{k}={v}' for k,v in defines.items()],str(ROOT/'standalone/far_storage_child.asm'),'-o',str(child)],check=True)
 import test_connection_dos
 test_connection_dos.BINARY=a.binary
 from modem_fixtures import fixture
 manifest=json.loads((a.binary.parent/'manifest.json').read_text())
 settings=bytearray(fixture(timeout=5));overrides={}
 if manifest.get('experimental_custom_irq'):
  struct.pack_into('<H',settings,0x186,4);overrides['irq']=4
 if manifest.get('experimental_mouse'):
  struct.pack_into('<HH',settings,0x4e4,8,4);overrides['mouse_scales']=[8,4]
 keys=bytearray(540)
 for i in range(10):struct.pack_into('<H',keys,i*54,3)
 command=b'D:\\FARTEST.COM';struct.pack_into('<H',keys,0,1);keys[2:2+len(command)]=command
 case='far-storage'+('-'+a.label if a.label else'')
 folder=ROOT/'build/connection-dos'/case;folder.mkdir(parents=True,exist_ok=a.label is None);(folder/'FARTEST.BIN').unlink(missing_ok=True)
 key_recipe=('p900 enter 'if manifest.get('special_edition')else'')+'p3000 a-1 p2000 space p1200 a-x'
 proof=test_connection_dos.run(case,'success',key_recipe,prm=bytes(settings),arguments='@D:\\TEST.PRM /D:CaseTest:23 /T:D:\\TEST.KEY COM1 38400 HARD',files={'TEST.KEY':bytes(keys),'FARTEST.COM':child.read_bytes()},cpu='8086'if has_native else'386')
 sample=(folder/'FARTEST.BIN').read_bytes() if (folder/'FARTEST.BIN').exists() else b''
 checks=proof['checks'];checks['owned_child_found_parent_and_retained_far_extent']=len(sample)==(80 if has_native else 64) and struct.unpack_from('<H',sample)[0]==(255 if has_native else 127)
 if len(sample)==(80 if has_native else 64):
  status,parent,retained,observed_required,segment,allocated,*markers=struct.unpack('<'+str(len(sample)//2)+'H',sample)
  checks['MCB_covers_far_end_after_STACK']=retained>=observed_required==required
  checks['new_DOS_allocation_disjoint_from_all_retained_parent_storage']=allocated>=parent+required or allocated+0x400<=parent
  checks['new_DOS_allocation_does_not_overlap_far_parent']=not(parent+16+far<=allocated<parent+required)
  checks['shadow_and_history_canaries_survive_child_allocation_fill']=markers[:4]==[0xcafe,0xbeef,0xdead,0xbabe]
  checks['snapshot_canaries_survive_child_allocation_fill']=markers[4:7]==[parent+16+snapseg,0x1122,0x3344]
  checks['far_code_sum_and_extent_survive_child_allocation_fill']=markers[7]==markers[8] and markers[9:11]==[parent+16+code_seg,code_endoff-code_off]
  checks['modem_far_code_sum_and_extent_survive_child_allocation_fill']=markers[18:20]==[parent+16+modem_seg,modem_endoff-modem_off] and markers[20]==markers[21]
  checks['configuration_far_code_sum_and_full_C_extent_survive_child_allocation_fill']=markers[22:24]==[parent+16+config_seg,config_endoff-config_off] and markers[24]==markers[25]
  checks['all_three_far_UI_screen_buffers_survive_child_allocation_fill']=markers[11]==parent+16+ui_seg and all(markers[i]==markers[i+1] for i in (12,14,16))
  if has_native:
   checks['native_bank_extent_and_sum_survive_child_allocation_fill']=markers[26:28]==[parent+16+native_seg,native_topoff-native_off] and markers[28]==markers[29]
   checks['native_shadow_extent_and_sum_survive_child_allocation_fill']=markers[30:32]==[parent+16+private_seg,private_endoff-private_off] and markers[32]==markers[33]
   checks['allocation_excludes_native_bank']=allocated+0x400<=parent+16+native_seg or allocated>=parent+16+native_seg+(native_topoff+15)//16
   checks['allocation_excludes_native_shadow']=allocated+0x400<=parent+16+private_seg or allocated>=parent+16+private_seg+(private_endoff+15)//16
 proof['passed']=all(checks.values());proof['binary_sha256']=hashlib.sha256(a.binary.read_bytes()).hexdigest();proof['sample_hex']=sample.hex();proof['linker_defines']=defines;proof['scope']='Actual DOS livePROGRAM/COMSPEC owned child locates parent PSP, checks retainedMCB throughfarend afterSTACK and FARCODE, allocates/fills16KB separateDOSmemory and verifies full-sizedshadow/history and frozen-screen endpointcanaries plus the full controller, modem and configuration C far-code byte-sums before/after allocation and sums of all three full4000-byte far UI screen owners. Parent resumes actual far controller polling after child return. NormalUART/vector cleanup verified by existing sampler. No physical modem claim.'
 proof['fixture_overrides']=overrides
 (out/'checks.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof,indent=2));return 0 if proof['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
