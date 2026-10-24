#!/usr/bin/env python3
"""Bounded wide clear: independent rectangle pixels, all other planes/caches retained."""
import argparse,hashlib,itertools,json,struct
from pathlib import Path
import check_transport
from check_protected_erase_live import ROOT,stage
from check_viewport_live import logical
from check_line_edit_live import Abort

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',type=Path,required=True);a=p.parse_args();binary=a.terminal.resolve();mf=json.loads((binary.parent/'manifest.json').read_text())
 assert sha(binary)==mf['binary_sha256']
 for name,digest in mf['sources'].items():assert sha(ROOT/name)==digest,name
 check_transport.BINARY=binary;check_transport.MAP=binary.parent/'terminal.map';cases=0
 ranges=[(0,0),(0,51),(0,52),(0,60),(0,79),(0,80),(0,131),(51,52),(51,79),(52,79),(60,60),(60,79),(60,80),(79,80),(80,131),(131,131)]
 names=['screen_cursor_row','screen_cursor_column','screen_attribute_offset','screen_video_offset','screen_visible_column','screen_viewport_active','screen_viewport_offset','csi_wrap_pending']
 for rows,hidden in [(1,0),(5,0),(24,0),(25,1)]:
  boxes=[(0,0)]if rows==1 else[(rows//2,rows//2),(0,rows-1)]
  for profile,right,wrap,(left,end),(top,bottom)in itertools.product((4,6),(False,True),(0,1),ranges,boxes):
   m,address,cells,flags,values,row=stage(132,rows,hidden,profile,right,60,2,1);m.put('screen_cursor_wrap',wrap);m.put('erase_lineflags_enabled',cases&1)
   lineflags=bytes((i%7)+1 for i in range(128));m.uc.mem_write(m.symbols['screen_line_flags'],lineflags)
   oldvideo=bytes(m.uc.mem_read(0xb8000,4000));oldshadow=bytes(m.uc.mem_read(address,8192));cursor=[m.get(n)for n in names];expected=list(cells)
   for y in range(top,bottom+1):expected[y*132+left:y*132+end+1]=[0x2720]*(end-left+1)
   expected_lines=bytearray(lineflags)
   if cases&1 and top!=bottom:expected_lines[top:bottom+1]=bytes(bottom-top+1)
   m.call('csi_service_2530',[0xab27,bottom*256+end,top*256+left,0],cleanup=8,limit=1000000)
   identity=(rows,profile,right,wrap,left,end,top,bottom)
   assert logical(m,address,rows)==struct.pack('<'+'H'*len(cells),*expected),(identity,'pixels')
   assert bytes(m.uc.mem_read(m.symbols['screen_attribute_cells'],4096))==bytes(flags)+b'\x55'*(4096-len(flags))
   assert bytes(m.uc.mem_read(m.symbols['erase_attribute_values'],4096))==bytes(values)+b'\x66'*(4096-len(values))
   assert bytes(m.uc.mem_read(m.symbols['screen_line_flags'],128))==expected_lines
   assert [m.get(n)for n in names]==cursor
   assert bytes(m.uc.mem_read(0xb8000+rows*160,4000-rows*160))==oldvideo[rows*160:]
   assert bytes(m.uc.mem_read(address+rows*264,8192-rows*264))==oldshadow[rows*264:]
   cases+=1
 rejected=0
 for top,bottom,left,end in [(4,3,0,79),(0,5,0,131),(0,4,60,59),(0,4,0,132),(255,255,0,79)]:
  m,address,*_=stage(132,5,0,6,True,60,2,1)
  before=(bytes(m.uc.mem_read(0xb8000,4000)),bytes(m.uc.mem_read(address,8192)),bytes(m.uc.mem_read(m.symbols['screen_line_flags'],128)))
  try:m.call('csi_service_2530',[0x27,bottom*256+end,top*256+left,0],cleanup=8)
  except Abort as e:assert e.args==(0x2d98,)
  else:raise AssertionError(('missing rectangle refusal',top,bottom,left,end))
  assert before==(bytes(m.uc.mem_read(0xb8000,4000)),bytes(m.uc.mem_read(address,8192)),bytes(m.uc.mem_read(m.symbols['screen_line_flags'],128)))
  rejected+=1
 r=dict(passed=True,cases=cases,pre_mutation_rejections=rejected,binary_sha256=sha(binary),sources=mf['sources'],checker_sha256=sha(Path(__file__)),original_inputs=[],scope=__doc__+' Both panes/profiles, wrapped and plain output, overlap edges52/79/80, single/multi-row rectangles, visible/hidden status and line-flag policy. Hardware modeled; actual DOS and counted scrolling require separate tests.')
 (binary.parent/'wide-clear-checks.json').write_text(json.dumps(r,indent=2)+'\n');print('PASS wide clear:',cases,'rectangles,',rejected,'pre-mutation refusals')
if __name__=='__main__':main()
