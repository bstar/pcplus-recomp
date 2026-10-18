"""Validate small-model near ABI and all retained static far extents from MZ/map."""
from pathlib import Path
import re,struct

def inspect_terminal_memory(binary,map_path):
 image=Path(binary).read_bytes();header=struct.unpack_from('<14H',image)
 assert image[:2]==b'MZ'
 size=(header[2]-1)*512+(header[1] or 512);start=header[4]*16
 assert start<=size<=len(image)
 module_bytes=size-start
 listing=Path(map_path).read_text()
 group=re.search(r'^DGROUP\s+([0-9a-f]+):([0-9a-f]+)\s+([0-9a-f]+)',listing,re.M|re.I);assert group
 ds=int(group[1],16);near_start=ds*16+int(group[2],16);near_size=int(group[3],16)
 assert near_size<65536,'DS=SS near data/stack exceeds64KiB'
 symbols={name:(int(seg,16),int(off,16)) for seg,off,name in re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$',listing,re.M|re.I)}
 def address(name):seg,off=symbols[name];return seg*16+off
 def word(name):
  at=start+address(name);assert at+2<=size,(name,'not in initialized image')
  return struct.unpack_from('<H',image,at)[0]
 shadow=address('erase_shadow_cells');history=address('terminal_history_buffer');far_end=address('terminal_far_storage_end');stack_end=address('terminal_stack_top')
 far_seg,shadow_off=symbols['erase_shadow_cells'];history_seg,history_off=symbols['terminal_history_buffer']
 assert far_seg==history_seg==symbols['terminal_far_storage_end'][0]
 assert history-shadow==8192 and far_end-shadow==12288
 assert far_end<=near_start or shadow>=near_start+near_size,'Far storage overlaps DGROUP'
 assert shadow_off+12288<=65536,'Far storage wraps itssegment'
 assert stack_end==near_start+near_size,'STACK end must cover all near data'
 assert word('erase_shadow_segment')==far_seg and word('erase_shadow_offset')==shadow_off
 assert word('terminal_history_start')==history_off and word('terminal_history_end')==history_off+4096
 assert word('terminal_history_pointer')==history_off
 assert struct.unpack_from('<H',image,start+address('terminal_history_pointer')+2)[0]==far_seg
 # Every serialized segment pointer must actually have an MZ relocation.
 relocations={seg*16+off for off,seg in (struct.unpack_from('<HH',image,header[12]+i*4) for i in range(header[3]))}
 assert address('erase_shadow_segment') in relocations
 assert address('terminal_history_pointer')+2 in relocations
 extra={};static_end=max(stack_end,far_end)
 if 'terminal_snapshot_image' in symbols:
  frozen=address('terminal_snapshot_image');frozen_end=address('terminal_snapshot_image_end')
  frozen_seg,frozen_off=symbols['terminal_snapshot_image']
  assert frozen_end-frozen==2000 and frozen_off+2000<=65536
  assert frozen_end<=near_start or frozen>=near_start+near_size,'Frozen screen overlapsDGROUP'
  assert frozen_end<=shadow or frozen>=far_end,'Frozen screen overlaps shadow/history'
  assert word('terminal_snapshot_image_segment')==frozen_seg
  assert address('terminal_snapshot_image_segment') in relocations
  static_end=max(static_end,frozen_end)
  extra={'snapshot_relative_segment':frozen_seg,'snapshot_image_offset':frozen_off,'snapshot_bytes':2000,'snapshot_end_linear':frozen_end}
 retained=(static_end+15)//16
 assert retained*16>=module_bytes,'PROGRAM retention would free serialized application data'
 allocated=((module_bytes+15)//16+header[5])*16
 assert allocated>=static_end,'MZ minimum allocation does not cover static storage'
 assert header[7]*16+header[8]==stack_end,'MZ SS:SP differs from linkedSTACK'
 assert retained+16<0xa000,'Static DOS parent cannot fit conventional memory'
 return {'near_bytes':near_size,'near_relative_segment':ds,'far_relative_segment':far_seg,'shadow_offset':shadow_off,'history_offset':history_off,'far_bytes':12288,'far_end_linear':far_end,'stack_end_linear':stack_end,'loaded_module_bytes':module_bytes,'minimum_allocated_module_bytes':allocated,'retained_parent_paragraphs':retained+16,'far_pointer_relocations_verified':True,**extra}
