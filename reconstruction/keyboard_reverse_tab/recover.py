#!/usr/bin/env python3
"""Explicit analyst recovery; ordinary builds never invoke this script."""
import importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('recover_support',ROOT/'reconstruction/terminal_services/recover.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
source=Path(m.__file__).read_text()
old='if k in calls}'
assert source.count(old)==1
exec(compile(source.replace(old,'if k in calls and k != start}'),m.__file__,'exec'),m.__dict__)
m.SOURCE=Path(__file__).resolve().parent
m.UNITS=[('reverse_tab',0xbc0,0xca2)]
m.FUNCTIONS={0xbc0:'keyboard_reverse_tab'}
m.SERVICES={0x1e30:'screen_cursor_left',0x2adc:'screen_adjust_attribute_boundary',0x830c:'reverse_tab_signed_divide',0x1bbe:'screen_set_cursor',0x1ea0:'screen_cursor_right',0x1f56:'reverse_tab_protected_home'}
m.STATE={0x900c:'screen_cursor_wrap',0x3734:'screen_attribute_checks',0x3346:'screen_attribute_offset',0x9038:'screen_reverse_wrap_blocked',0x39c4:'screen_attributes_base',0x325a:'screen_attribute_row_bytes',0xce10:'terminal_tab_stops',0x903e:'terminal_tab_wrap',0x904c:'scroll_skip_attribute_scan',0x8ff8:'terminal_tab_mode_8ff8',0x399e:'screen_cursor_column',0x399c:'screen_cursor_row'}
m.main()
p=m.SOURCE/'reverse_tab.asm'
source=p.read_text().replace('TERMINAL_SERVICES_OMF','KEYBOARD_REVERSE_TAB_OMF').replace('docs/TERMINAL_SERVICES.md','docs/KEYBOARD_REVERSE_TAB.md')
source=source.replace('SEGMENT _TEXT public class=CODE use16','%ifdef KEYBOARD_ECHO_FAR\nSEGMENT ASPECT_CODE public align=16 class=FARCODE use16\n%else\nSEGMENT _TEXT public class=CODE use16\n%endif')
p.write_text(source)
p=m.SOURCE/'provenance.json';proof=json.loads(p.read_text())
proof.pop('derived_aliases',None)
proof['rea_evidence']={'bytes':'ev_18c8c70cf3ca03428dbba938dcd9734175e4633b2374c73b2277463a36d018e0','file_mapping':'ev_e1ead9b45f6bb15a132bb0ee8b82e26c2c73d6ad7baf4413fbe0b05fa715173f','undefined_listing':'ev_642fb8fa9d9a12470cd8535e3d4aab08919280f44dd810ceed8a10acad3cf792'}
proof['units'][0]['file_offset']=0x1dc0
proof['limitations']=['REA reports no defined instruction/procedure at this entry; complete mapped bytes were decoded independently with ndisasm and byte-checked after assembly.','Native table search assumes an FE terminator; malformed tables are not bounded by the original routine.','External cursor, attribute-repair, division and protected-home services require separate binding and validation. No production integration or full keyboard gate claim.']
p.write_text(json.dumps(proof,indent=2)+'\n')
