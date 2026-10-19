#!/usr/bin/env python3
"""Explicit analyst recovery; ordinary builds never read the original."""
import importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('attribute_recovery',ROOT/'reconstruction/terminal_services/recover.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
m.SOURCE=Path(__file__).resolve().parent
m.UNITS=[('boundary',0x2adc,0x2b86),('position',0x2b86,0x2bde),('offset',0x2bde,0x2c0c),('divide',0x830c,0x8318)]
m.FUNCTIONS={0x2adc:'attribute_boundary_native',0x2b86:'attribute_position_to_video',0x2bde:'attribute_offset_to_position',0x830c:'reverse_tab_signed_divide'}
m.SERVICES={0x1bbe:'screen_set_cursor',0x376d:'attribute_boundary_notice'}
m.STATE={0x39c4:'screen_attributes_base',0x325c:'erase_cell_count',0x325a:'screen_attribute_row_bytes',0xcdfa:'screen_viewport_enabled',0x3256:'screen_viewport_active',0x7a7e:'screen_viewport_right',0xce2e:'screen_viewport_left',0x7a72:'screen_columns'}
m.main()
for p in m.SOURCE.glob('*.asm'):
 source=p.read_text().replace('TERMINAL_SERVICES_OMF','ATTRIBUTE_BOUNDARY_OMF').replace('docs/TERMINAL_SERVICES.md','docs/ATTRIBUTE_BOUNDARY.md')
 source=source.replace('SEGMENT _TEXT public class=CODE use16','%ifdef KEYBOARD_ECHO_FAR\nSEGMENT ASPECT_CODE public align=16 class=FARCODE use16\n%else\nSEGMENT _TEXT public class=CODE use16\n%endif')
 p.write_text(source)
p=m.SOURCE/'provenance.json';r=json.loads(p.read_text());r.pop('derived_aliases',None)
r['rea_evidence']={'0x2adc':'ev_d75dd65a13553e4742db7f30d1a50dfe3d14b2e666f686d77d058c9a76a83e4e','0x2b86':'ev_087aa230ed995ec3a6e3e060ea79a3e8edd7592fffb7562f95cebf07eb8eb152','0x2bde':'ev_d4fdefeb3b5c08083bf2f27decd2646661bb907dce848db9102c617bd60a71f1','0x830c':'ev_b7e2aee6447f1486f524d08b70ed8284a1df9872fffb6b89775e635353848ae6'}
for u in r['units']:u['file_offset']=0x1200+u['start']
r['limitations']=['Native entry assumes a valid bounded attribute plane and nonzero row width. Application admission is separate.','Cursor positioning and the no-writable-cell notification are external services.','Viewport conversion is recovered; complete application viewport ownership remains unfinished.']
p.write_text(json.dumps(r,indent=2)+'\n')
