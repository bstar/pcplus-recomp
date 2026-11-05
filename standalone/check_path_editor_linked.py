#!/usr/bin/env python3
"""Exercise actual linked editor instructions/ABI at every fixed-field position."""
import argparse,hashlib,json,struct
from pathlib import Path
from check_directory_identity import Identity
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',type=Path,required=True)
 p.add_argument('--output',type=Path,required=True);a=p.parse_args();binary=a.terminal.resolve();out=a.output.resolve()
 assert out.is_relative_to(ROOT/'build') and not out.exists()
 manifest=json.loads(binary.with_name('manifest.json').read_text());assert manifest['experimental_path_control'] and manifest['binary_sha256']==sha(binary)
 out.mkdir(parents=True);m=Identity(binary);address=m.symbols['_terminal_path_dialog_state'];cases=[]
 field=bytes(range(33,95))
 operations=(('Backspace',0x0e08),('Delete',0x5300),('Left',0x4b00),('Right',0x4d00),('Home',0x4700),('End',0x4f00),('CtrlEnd',0x7500),('Insert',0x5200),('Character',ord('Z')))
 for position,full in [(i,0) for i in range(62)]+[(61,1)]:
  for insert in (0,1):
   for name,key in operations:
    state=bytearray(144);struct.pack_into('<6H',state,0,0x5044,1,full,position,insert,0)
    state[12:74]=field;state[76:80]=b'D:\\\0';m.uc.mem_write(address,bytes(state))
    want,cur,latch,ins=field,position,full,insert
    if name=='Backspace':
     latch=0
     if cur:cur-=1;want=field[:cur]+field[cur+1:]+b' '
    elif name=='Delete':latch=0;want=field[:cur]+field[cur+1:]+b' '
    elif name=='Left':latch=0;cur=max(0,cur-1)
    elif name=='Right':cur=min(61,cur+1)
    elif name=='Home':latch=0;cur=0
    elif name=='End':latch=0;cur=61
    elif name=='CtrlEnd':latch=0;want=field[:cur]+b' '*(62-cur)
    elif name=='Insert':ins=1-insert
    elif not full:
     want=(field[:cur]+b'Z'+field[cur:61]) if insert else (field[:cur]+b'Z'+field[cur+1:])
     if cur==61:latch=1
     else:cur+=1
    result=m.bank('_path_dialog_event',[1,key,0,0xb800],far=True)
    actual=bytes(m.uc.mem_read(address,144));head=struct.unpack_from('<6H',actual)
    checks=dict(retains_dialog=result==1,state=head==(0x5044,1,latch,cur,ins,0),fixed_field=actual[12:74]==want)
    case=dict(operation=name,cursor=position,full=full,insert=insert,passed=all(checks.values()),checks=checks)
    cases.append(case)
    if not case['passed']:
     case.update(expected=want.decode('ascii'),actual=actual[12:74].decode('ascii'),actual_head=head)
     (out/'failure.json').write_text(json.dumps(case,indent=2)+'\n');raise AssertionError(case)
 shapes=[]
 for saved in (0x0607,0x0b0d,0x0d0f):
  for insert in (0,1):
   state=bytearray(144);struct.pack_into('<6H',state,0,0x5044,1,0,0,insert,0);m.uc.mem_write(address,bytes(state))
   actual=m.bank('_path_dialog_shape',[saved],far=True)
   wanted=((((saved&31)//2+1)<<8)|(saved&31)) if insert else saved
   assert actual==wanted,(saved,insert,actual,wanted);shapes.append(dict(saved=saved,insert=insert,actual=actual))
 sources=('standalone/check_path_editor_linked.py','standalone/check_directory_identity.py','standalone/dos_image.py','standalone/terminal_memory.py')
 report=dict(passed=True,binary_sha256=sha(binary),cases=cases,shape_cases=shapes,
  sources={n:sha(ROOT/n) for n in sources},scope=__doc__+' CPU execution of actual loaded/relocated application functions; no DOS/BIOS calls in these edit operations. Independent fixed-field expectations from original evidence, not compiler assembly inspection. Far cdecl return, DS=SS, SP and callee-preserved registers are checked by the loader. Actual DOS/VGA/UART remains a separate gate.')
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS',len(cases),'linked edit cases',len(shapes),'shape cases')
if __name__=='__main__':main()
