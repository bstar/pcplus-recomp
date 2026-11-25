#!/usr/bin/env python3
"""Explicit analyst step: prove the VT52 sources rebuild the original bytes.

Reads the verified original only here; the default build never runs this.
Writes provenance.json with per-unit hashes and original file offsets.
"""
from pathlib import Path
import hashlib,json,subprocess,tempfile
ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'reconstruction/vt52'
ORIGINAL=ROOT/'analysis/pcplus-originals/PCPLUS-main-2.01.EXE'
EXPECTED='6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
OVERLAY14=100386-0xecd2 # file offset of overlay-14 address 0 (ansi/escape.asm at ecd2)
UNITS=[('parser',0xf02e,0xf12c,OVERLAY14,'overlay 14'),('cursor',0x1f70,0x1fa0,0x1200,'resident code')]

def main():
 image=ORIGINAL.read_bytes();assert hashlib.sha256(image).hexdigest()==EXPECTED
 manifest={'source_sha256':EXPECTED,'units':[],
  'state':{'1d18':'csi_terminal_id','321e':'csi_previous_terminal_id','3342':'csi_wrap_pending','cdec':'ansi_charset_g0_flag_graphics','334a':'csi_last_row','3258':'screen_last_column'},
  'services':{'5ca0':'ansi_next_byte','20a4':'vt52_profile_reset (native reset)','1efc':'screen_cursor_up','1e0c':'screen_cursor_down','1ea0':'screen_cursor_right','1e30':'screen_cursor_left','1bbe':'screen_set_cursor','da84':'csi_service_da84','d8b6':'csi_service_d8b6','da12':'csi_service_da12','e2f8':'vt52_print_row','d0d0':'vt52_print_controller','e3ca':'vt52_print_screen','abac':'vt52_identify (DS 755e = ESC / Z)'},
  'limitations':['Recovered names are analyst annotations. In the maintained build the native service calls bind to maintained shims in src/terminal/vt52_live.asm.']}
 with tempfile.TemporaryDirectory() as temp:
  for name,start,end,base,where in UNITS:
   blob=image[base+start:base+end];out=Path(temp)/(name+'.bin')
   subprocess.run(['nasm','-f','bin','-I',str(ROOT/'reconstruction/uart')+'/',str(SOURCE/(name+'.asm')),'-o',str(out)],check=True)
   assert out.read_bytes()==blob,(name,next(i for i in range(min(len(blob),len(out.read_bytes()))) if blob[i]!=out.read_bytes()[i]) if len(blob)==len(out.read_bytes()) else 'length')
   manifest['units'].append({'file':f'reconstruction/vt52/{name}.asm','start':start,'end':end,'bytes':len(blob),'segment':where,'file_offset':base+start,'sha256':hashlib.sha256(blob).hexdigest(),'matched_original':True})
 (SOURCE/'provenance.json').write_text(json.dumps(manifest,indent=2)+'\n')
 print('Matched',sum(u['bytes'] for u in manifest['units']),'bytes')
if __name__=='__main__':main()
