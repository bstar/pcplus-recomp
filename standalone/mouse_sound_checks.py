"""Decode the existing independent mouse observer around attached sound tests."""
import re,struct
from mouse_parent_probe import WORDS,BUFFER,BYTES

def verify(raw,parent_map,resource_size,folder,expected_scales=(8,4)):
    at=len(raw)-26-32*70-resource_size*2;start=at-BYTES
    values=dict(zip(WORDS,struct.unpack_from('<'+str(len(WORDS))+'H',raw,start)))
    header=struct.unpack_from('<7H',raw)
    symbols={n:(int(s,16),int(o,16)) for s,o,n in re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+]?\s+(\w+)\s*$',parent_map.read_text(),re.M|re.I)}
    seg,off=symbols['mouse_callback'];expected=(off,header[5]+0x10+seg)
    size=values['state_bytes'];before=start+len(WORDS)*2;capture=folder/'PCPLUS.SCR'
    checks=dict(mouse_resumed=values['seen']==1 and values['resume_mask']==0x0b and (values['resume_off'],values['resume_seg'])==expected,
        mouse_suspended_for_ASPECT=values['suspended_mask']==0,mouse_foreign_DS=values['returned_ds']==0x40,
        mouse_depth=values['depth_before']==values['depth_after']==65535,mouse_PRM_scales=(values['scale_x'],values['scale_y'])==expected_scales,
        mouse_neutral_event=values['count_before']==values['count_after']==0,
        mouse_menu_events=(values['menu_stage'],values['menu_count'],values['menu_code'],values['button_count'],values['button_code'])==(2,2,2,1,4),
        mouse_menu_screen_action=capture.exists() and capture.stat().st_size>0 and b'Command Menu' not in capture.read_bytes(),
        mouse_registration_restored=(values['after_mask'],values['after_off'],values['after_seg'])==(values['before_mask'],values['before_off'],values['before_seg']),
        mouse_driver_state_restored=0<size<=BUFFER and values['state_equal']==1 and raw[before:before+size]==raw[before+BUFFER:before+BUFFER+size])
    return checks,values
