#!/usr/bin/env python3
"""Independent field-plane reshape and repaint checks for explicit width changes."""
import argparse,hashlib,itertools,json,struct
from pathlib import Path
from unicorn import UC_HOOK_CODE
from check_reset_live import ROOT,fixture,abi,near,inject
from check_viewport_live import logical
from check_width_fields_live import reference as edit_reference
from terminal_memory import inspect_terminal_memory
import check_transport

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def seed(m,cols,rows):
 flags=bytearray(rows*cols);values=bytearray(rows*cols);carry=0x17
 # Boundaries on retained cells, column79/80, discarded columns and row starts.
 for i in range(len(flags)):
  row,col=divmod(i,cols)
  if col in(0,3,79,80,131)and(row+col)%3!=0:
   flags[i]=0x80|((row+col)&3);carry=(0x10+((row*7+col)%7)*0x10)|((row+col)&7)
  elif(i*7)%19==0:flags[i]=(i%3)+1
  values[i]=carry
 m.uc.mem_write(m.symbols['screen_attribute_cells'],bytes(flags)+b'\x55'*(4096-len(flags)))
 m.uc.mem_write(m.symbols['erase_attribute_values'],bytes(values)+b'\x66'*(4096-len(values)))
 return flags,values

def reference(flags,values,old,new,rows,wrap):
 f=bytearray();v=bytearray()
 for row in range(rows):
  f+=flags[row*old:row*old+min(old,new)];v+=values[row*old:row*old+min(old,new)]
  if new>old:f+=bytes(new-old);v+=bytes([0x27])*(new-old)
 attrs=[0x27]*len(f)
 if wrap:
  carry=v[0]if f[0]&0x80 else 0x17
  for i,flag in enumerate(f):
   if flag&0x80:carry=v[i]
   else:
    v[i]=carry
    attrs[i]=(carry&0xf8)|6 if flag&1 and not flag&2 else carry
 return f,v,struct.pack('<'+'H'*len(f),*[32|(a<<8)for a in attrs])

WRITABLE=['attributes_current','screen_attribute_row_bytes','screen_last_column','erase_cell_count',
 'screen_cursor_row','screen_cursor_column','screen_visible_column','screen_previous_row','screen_previous_column',
 'screen_video_offset','screen_attribute_offset','screen_viewport_enabled','screen_viewport_active',
 'screen_viewport_offset','screen_viewport_left','csi_saved_row','csi_saved_column','csi_wrap_pending','cursor_state_saved_3342',
 'csi_row_count','csi_last_row','screen_first_row','screen_last_row']

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',type=Path,required=True);a=p.parse_args()
 binary=a.terminal.resolve();manifest=json.loads((binary.parent/'manifest.json').read_text())
 assert manifest['native_reset_transaction']and sha(binary)==manifest['binary_sha256']
 for name,digest in manifest['sources'].items():assert sha(ROOT/name)==digest,name
 check_transport.BINARY=binary;check_transport.MAP=binary.parent/'terminal.map'
 memory=inspect_terminal_memory(binary,binary.parent/'terminal.map');cases=0;repainted=0;post_edits=0
 modes=[(w,c,e)for w,c,e in itertools.product((0,1),repeat=3)if w or c or e]
 layouts=[(1,0),(5,0),(24,0),(25,0),(25,1)]
 for (rows,hidden),profile,(wrap,checks,protection),(old,right),request in itertools.product(layouts,(4,6),modes,[(80,False),(132,False),(132,True)],(0,1)):
  m,shadow=fixture(profile,0x27,rows=rows,hidden=hidden)
  # Entering wide first also normalizes the legacy visible25-row startup.
  if old==132:assert m.call('terminal_native_width',ax=1,limit=2000000)==0
  current_rows=m.get('csi_row_count');target_rows=24 if rows==25 and not hidden else rows
  m.position(current_rows-1,old-1 if right else 17)
  for name,value in dict(screen_cursor_wrap=wrap,screen_attribute_checks=checks,erase_protection_mode=protection,attributes_preset_value=0x4e).items():m.put(name,value)
  m.uc.mem_write(m.symbols['csi_erase_attribute'],b'\x17')
  flags,values=seed(m,old,current_rows);before=near(m);video=bytes(m.uc.mem_read(0xb8000,4000));oldshadow=bytes(m.uc.mem_read(shadow,8192))
  width=132 if request else 80;expected_flags,expected_values,pixels=reference(flags,values,old,width,target_rows,wrap)
  assert m.call('terminal_native_width',ax=request,limit=3000000)==0,(rows,hidden,profile,wrap,checks,protection,old,right,request)
  abi(m);size=target_rows*width
  identity=(rows,hidden,profile,wrap,checks,protection,old,right,request)
  actual=logical(m,shadow,target_rows)if request else bytes(m.uc.mem_read(0xb8000,target_rows*160))
  assert actual==pixels,(identity,'logical pixels')
  for name,expected in [('screen_attribute_cells',expected_flags),('erase_attribute_values',expected_values)]:
   prior=before[m.offset(name):m.offset(name)+4096]
   assert bytes(m.uc.mem_read(m.symbols[name],4096))==bytes(expected)+prior[size:],(identity,name)
  assert bytes(m.uc.mem_read(0xb8000+target_rows*160,4000-target_rows*160))==video[target_rows*160:],(identity,'status')
  assert bytes(m.uc.mem_read(shadow+target_rows*264,8192-target_rows*264))==oldshadow[target_rows*264:],(identity,'shadow tail')
  assert(m.get('screen_cursor_wrap'),m.get('screen_attribute_checks'),m.get('erase_protection_mode'))==(wrap,checks,protection)
  assert m.get('attributes_preset_value')==0x4e and bytes(m.uc.mem_read(m.symbols['csi_erase_attribute'],1))==b'\x17'
  mask=set()
  for name in WRITABLE:mask.update(range(m.offset(name),m.offset(name)+2))
  for name,n in [('screen_attribute_cells',3300),('erase_attribute_values',3300),('screen_line_flags',128),('terminal_tab_stops',30)]:mask.update(range(m.offset(name),m.offset(name)+n))
  assert all(x==y for i,(x,y)in enumerate(zip(before,near(m)))if i not in mask),(identity,'unowned near data')
  assert(m.get('screen_cursor_row'),m.get('screen_cursor_column'),m.get('screen_attribute_offset'))==(0,0,0)
  assert(m.get('csi_row_count'),m.get('screen_first_row'),m.get('screen_last_row'))==(target_rows,0,target_rows-1)
  if wrap:
   row=target_rows//2;col=3
   m.uc.mem_write(m.symbols['screen_line_flags'],bytes(128));m.position(row,col)
   words=list(struct.unpack('<'+'H'*size,pixels))
   words,f,v,_,_=edit_reference(words,expected_flags,expected_values,target_rows,row,col,1,False,3,wrap,checks,cols=width)
   m.feed(b'\x1b[3P')
   edited=logical(m,shadow,target_rows)if request else bytes(m.uc.mem_read(0xb8000,target_rows*160))
   assert edited==struct.pack('<'+'H'*size,*words),(identity,'post-width DCH')
   for name,expected in [('screen_attribute_cells',f),('erase_attribute_values',v)]:
    prior=before[m.offset(name):m.offset(name)+4096]
    assert bytes(m.uc.mem_read(m.symbols[name],4096))==bytes(expected)+prior[size:],(identity,'post-width',name)
   post_edits+=1
  cases+=1;repainted+=bool(wrap)
 irq_cases=0;failures=0;payload=bytes(range(256))*2
 for request,fault in itertools.product((0,1),(None,'metadata','readonly','plane','cursor')):
  m,shadow=fixture(rows=5);control,_=fixture(rows=5)
  for state in(m,control):
   if not request:assert state.call('terminal_native_width',ax=1,limit=3000000)==0
   for name,value in dict(screen_cursor_wrap=1,screen_attribute_checks=1,erase_protection_mode=1,attributes_preset_value=0x4e).items():state.put(name,value)
   state.uc.mem_write(state.symbols['csi_erase_attribute'],b'\x17')
   seed(state,80 if request else 132,5)
  control.receive_irq(payload);expected=near(control);oldshadow=bytes(m.uc.mem_read(shadow,8192));video=bytes(m.uc.mem_read(0xb8000,4000));bios=(m.bios_cursor,m.bios_shape)
  fired=inject(m,payload,'nreset_erase_repair_attributes');changed=[]
  def corrupt(u,at,size,_):
   if not fault or changed or at!=m.symbols['reset_live_validate']:return
   changed.append(True)
   field,value={'metadata':('screen_attribute_row_bytes',133),'readonly':('attributes_preset_value',0x27),'plane':('screen_attributes_base',0),'cursor':('screen_previous_row',5)}[fault]
   bank=m.base+memory['native_reset_bank_start'];u.mem_write(bank+m.symbols['nreset_'+field]-m.base,struct.pack('<H',value))
  m.uc.hook_add(UC_HOOK_CODE,corrupt)
  assert m.call('terminal_native_width',ax=request,limit=3000000)==(3 if fault else 0)
  assert fired and m.get('uart_rx_count')==512 and not m.rx;abi(m)
  assert bytes(m.uc.mem_read(m.symbols['uart_rx_buffer'],512))==payload
  if fault:
   assert changed and near(m)==expected and bytes(m.uc.mem_read(shadow,8192))==oldshadow
   assert bytes(m.uc.mem_read(0xb8000,4000))==video and(m.bios_cursor,m.bios_shape)==bios
   assert m.call('terminal_native_width',ax=request,limit=3000000)==0
   failures+=1
  else:irq_cases+=1
 report=dict(passed=True,binary_sha256=sha(binary),cases=cases,native_repaint_cases=repainted,post_width_field_edits=post_edits,private_repair_IRQ_cases=irq_cases,native_fault_rollbacks=failures,sources=manifest['sources'],checker_sha256=sha(Path(__file__)),original_inputs=[],scope=__doc__+' Seven active field-mode combinations, both profiles and directions, same-width resets, row/status ownership and discarded-column markers. Exact root/metadata/video guards and real private-stack ISR. Hardware modeled; peer width and broader UI remain unbound.')
 (binary.parent/'reset-field-checks.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS width fields:',cases,'commits,',repainted,'native repaints,',irq_cases,'private repair IRQ cases,',failures,'rollbacks')
if __name__=='__main__':main()
