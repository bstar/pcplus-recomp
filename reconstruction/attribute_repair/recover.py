#!/usr/bin/env python3
"""Explicit analyst recovery. Ordinary builds never read the original."""
import importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('repair_recovery',ROOT/'reconstruction/terminal_services/recover.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
m.SOURCE=Path(__file__).resolve().parent
m.UNITS=[('write',0x2c3a,0x2c72),('advance',0x2cf2,0x2d37),('repair',0x2d98,0x2eaa)]
m.FUNCTIONS={0x2c3a:'attribute_repair_write',0x2cf2:'attribute_repair_advance',0x2d98:'attribute_repair_native'}
m.SERVICES={0x2b86:'attribute_position_to_video',0x2d38:'erase_default_attribute',0x2d4c:'erase_previous_attribute',0x6c84:'text_write_char'}
m.STATE={0x900c:'screen_cursor_wrap',0x399c:'screen_cursor_row',0x399e:'screen_cursor_column',0x325c:'erase_cell_count',0x3346:'screen_attribute_offset',0x1f70:'attributes_current',0x39c4:'screen_attributes_base',0x39c2:'erase_attribute_values_base',0x1d36:'attributes_protected_value',0x1d32:'attributes_normal_value',0xcdfa:'screen_viewport_enabled',0x5dea:'erase_shadow_offset',0xce2e:'screen_viewport_left',0x7a72:'screen_columns',0x325a:'screen_attribute_row_bytes'}
m.main()
for p in m.SOURCE.glob('*.asm'):
 source=p.read_text().replace('TERMINAL_SERVICES_OMF','ATTRIBUTE_REPAIR_OMF').replace('docs/TERMINAL_SERVICES.md','docs/ATTRIBUTE_REPAIR.md')
 source=source.replace('SEGMENT _TEXT public class=CODE use16','%ifdef ATTRIBUTE_REPAIR_FAR\nSEGMENT ASPECT_CODE public align=16 class=FARCODE use16\n%else\nSEGMENT _TEXT public class=CODE use16\n%endif')
 p.write_text(source)
p=m.SOURCE/'provenance.json';r=json.loads(p.read_text());r.pop('derived_aliases',None)
r['rea_evidence']={'0x2c3a':'ev_d63e7b7d265d17bf760c635ad693f9e334d37416eba14e47425126b55ad1281d','0x2cf2':'ev_4f8f8f3ebcf4e0586108151870cc92586265a163247141a2592b4082c9629a1d','0x2d98':'ev_4ab18267a860061b33b0bdd2abff5eebfe38b8a8c31cac2c6c1126d9f006f8cf'}
for u in r['units']:u['file_offset']=0x1200+u['start']
r['limitations']=['Native routines require valid geometry, bounded cursor offset and metadata/value storage. Application admission is separate.','Repaint delegates visible writes to recovered text_write_char and hidden viewport writes to the supplied shadow far pointer.','Flat component evidence alone does not establish application integration or protected scrolling correctness; separate linked and DOS reports are required.']
p.write_text(json.dumps(r,indent=2)+'\n')
