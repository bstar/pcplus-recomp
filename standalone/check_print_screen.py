#!/usr/bin/env python3
"""Source-only native screen-printer cases; explicit --original instruction replay."""
import argparse,hashlib,json,struct
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
from dos_image import DosImage
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/print_screen'
PROOF=json.loads((ROOT/'reconstruction/print_screen/provenance.json').read_text())
FIELDS=['fixture_'+n for n in ['open_calls','close_calls','putc_calls','flush_calls','fallback_calls','message_calls','status_calls','wire_count','last_handle','putc_after_close','closed_handle']]+['printer_enabled','printer_stream','print_cursor_row','print_cursor_column','print_video_offset']
def image(original):
 m=DosImage(OUT/'PRINTSCR.EXE',OUT/'print_screen.map')
 if not original:return m
 old=m.data_base;data=bytes(m.uc.mem_read(old,65536));m.ds=0x4000;m.data_base=0x40000;m.uc.mem_write(m.data_base,data)
 for name,at in list(m.symbols.items()):
  if old<=at<old+65536:m.symbols[name]=m.data_base+at-old
 b=(ROOT/'analysis/pcplus-originals/PCPLUS-main-2.01.EXE').read_bytes();assert hashlib.sha256(b).hexdigest()==PROOF['source_sha256']
 m.uc.mem_write(m.base,b[0x1200:0xe2d0])
 for unit in PROOF['units']:
  st=int(unit['start'],16);off=unit['source_file_offset'];m.uc.mem_write(m.base+st,b[off:off+unit['bytes']])
 for at,name in PROOF['state'].items():m.symbols[name]=m.data_base+int(at,16)
 for at,name in PROOF['boundaries'].items():m.symbols[name]=m.base+int(at,16)
 for at,name in [('0x4688','printer_binary_mode'),('0x7a78','text_video_segment'),('0x7a8e','text_cga_status_port')]:m.symbols[name]=m.data_base+int(at,16)
 for name,raw in [('printer_device',b'PRN\0'),('printer_binary_mode',b'wb\0'),('print_text_mode',b'wb\0')]:m.uc.mem_write(m.symbols[name],raw)
 def boundary(u,at,size,_):
  target=at-m.base;mapping={0x3226:'message',0x2fb8:'status',0xd0d0:'fallback',0x841a:'open',0x8318:'close',0x8436:'putc',0x8c54:'flush',0x1bbe:'cursor'}
  if target not in mapping:return
  kind=mapping[target];sp=u.reg_read(UC_X86_REG_SP);w=struct.unpack('<3H',u.mem_read(m.data_base+sp,6))
  if kind=='cursor':
   row=u.reg_read(UC_X86_REG_AX);col=u.reg_read(UC_X86_REG_DX);m.put('print_cursor_row',row);m.put('print_cursor_column',col);m.put('print_video_offset',(row*8+col*2)&65535)
  else:
   counter='fixture_'+kind+'_calls';m.put(counter,m.get(counter)+1)
   if kind=='close':m.put('fixture_closed_handle',w[1])
   if kind=='putc':
    if m.get('fixture_close_calls'):m.put('fixture_putc_after_close',m.get('fixture_putc_after_close')+1)
    count=m.get('fixture_wire_count');assert count<4096;u.mem_write(m.symbols['fixture_wire']+count,bytes([w[1]&255]));m.put('fixture_wire_count',count+1);m.put('fixture_last_handle',w[2])
   if kind in ['open','putc','close','flush']:u.reg_write(UC_X86_REG_AX,m.get('fixture_'+kind+'_result'))
  u.reg_write(UC_X86_REG_SP,sp+2);u.reg_write(UC_X86_REG_IP,w[0])
 m.uc.hook_add(UC_HOOK_CODE,boundary);return m

def run(original=False):
 cases=[]
 for mode in [1,2,3]:
  for opened in [0,0x1111]:
   for errors in [0,65535]:cases.append(dict(kind='screen',mode=mode,opened=opened,errors=errors))
 for region in [0,1]:
  for ff in [0,1]:cases.append(dict(kind='selection',region=region,ff=ff))
 for policy in [0,1]:
  for params in [[],[0],[1],[2],[3],[4],[5],[6],[4,5],[5,4],[1,1]]:cases.append(dict(kind='media',params=params,policy=policy))
 results=[]
 for case in cases:
  m=image(original)
  for n,v in {'print_cursor_row':1,'print_cursor_column':2,'print_row_limit':3,'print_region_top':1,'print_region_bottom':2,'print_last_column':3,'print_region_mode':case.get('region',0),'print_formfeed':case.get('ff',0),'print_copy_policy':case.get('policy',0),'printer_enabled':1,'printer_stream':0x2222,'text_video_segment':0xb800,'text_cga_status_port':0,'fixture_open_result':case.get('opened',0x1111),'fixture_putc_result':case.get('errors',0),'fixture_flush_result':case.get('errors',0),'fixture_close_result':case.get('errors',0)}.items():m.put(n,v)
  pixels=bytes([0,7,26,7,255,7,32,7,65,7,66,7,67,7,68,7,69,7,70,7,71,7,72,7]);m.uc.mem_write(0xb8000,pixels)
  params=case.get('params',[]);m.put('print_parameter_count',len(params));m.uc.mem_write(m.symbols['print_parameters'],struct.pack('<16H',*(params+[0]*(16-len(params)))))
  entry={'screen':'print_screen_original','selection':'print_selection_original','media':'print_media_copy_original'}[case['kind']]
  m.call(entry,(case['mode'],) if case['kind']=='screen' else (),limit=200000)
  for reg,value in [(UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678),(UC_X86_REG_DS,m.ds),(UC_X86_REG_SS,m.ds)]:assert m.uc.reg_read(reg)==value
  assert m.get('print_cursor_row')==1 and m.get('print_cursor_column')==2
  wire=bytes(m.uc.mem_read(m.symbols['fixture_wire'],m.get('fixture_wire_count')))
  if case['kind'] in ['screen','selection']:
   mode=case.get('mode',2 if case.get('region') else 1);rows={1:[0,1,2],2:[1,2],3:[1]}[mode];expected=b''.join(pixels[row*8:row*8+8:2]+b'\r\n' for row in rows)+(b'\x0c' if case.get('ff') else b'')
   assert wire==expected,(case,wire,expected)
   assert m.get('fixture_open_calls')==1 and m.get('fixture_close_calls')==1 and m.get('fixture_flush_calls')==len(rows)+case.get('ff',0)
  else:
   modes=[1] if not params else [1 if p==0 else 3 for p in params if p in (0,1)]
   expected=b''.join(b''.join(pixels[row*8:row*8+8:2]+b'\r\n' for row in ([0,1,2] if mode==1 else [1])) for mode in modes)
   assert wire==expected
   opens=len(modes)+(sum(p==5 for p in params) if case['policy'] else 0)
   closes=len(modes)+(sum(p==4 for p in params) if case['policy'] else 0)
   assert m.get('fixture_open_calls')==opens and m.get('fixture_close_calls')==closes
   assert m.get('fixture_fallback_calls')==(sum(p==5 for p in params) if not case['policy'] else 0)
  if case['kind']=='selection':assert m.get('fixture_putc_after_close')==case['ff'] and m.get('fixture_closed_handle')==0x1111
  results.append({'case':case,'wire_hex':wire.hex(),'state':{n:m.get(n) for n in FIELDS}})
 return results
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--original',action='store_true');a=p.parse_args();linked=run();raw=run(True) if a.original else None
 if raw is not None:assert linked==raw,'Original and source-built results differ'
 result={'passed':True,'binary_sha256':hashlib.sha256((OUT/'PRINTSCR.EXE').read_bytes()).hexdigest(),'linked_cases':len(linked),'original_cases':len(raw) if raw else 0,'cases':linked,'scope':'Real recovered instructions and native video reads; explicit cursor/CRT/UI fixtures, no physical printer or original application execution.'}
 (OUT/'checks.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS',len(linked),'linked,',len(raw) if raw else 0,'original instruction cases')
