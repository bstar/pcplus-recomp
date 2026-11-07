#!/usr/bin/env python3
"""Passive timer capture of matched overlay state; diagnostic, no product writes."""
import argparse,json,re,struct,subprocess
from pathlib import Path
import test_connection_dos as lab
from directory_fixtures import prm
from build_context_help import ROOT,sha


def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('terminal','output'):p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();binary=a.terminal.resolve();out=a.output.resolve()
 assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False)
 symbols={n:(int(s,16),int(o,16))for s,o,n in re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$',binary.with_name('terminal.map').read_text(),re.M|re.I)}
 ds=symbols['terminal_program_kind'][0];config,state=symbols['_line_overlay_state'];_,expected=symbols['_line_overlay_expected']
 m=json.loads(binary.with_name('manifest.json').read_text());assert m['binary_sha256']==sha(binary)
 source=(ROOT/'standalone/path_dialog_watch.asm').read_text()
 source=source.replace('last_sum: dw 0','state_record: times 16 dw 0\nlast_sum: dw 0')
 begin=source.index(' cmp word [es:806]');end=source.index('%if WATCH_KIND',begin)
 source=source[:begin]+f''' mov ax,ss
 sub ax,{ds}
 add ax,{config}
 mov es,ax
 cmp word [es:{expected}],{m['line_port_overlay']['bank_bytes']}
 jne .done
 cmp word [es:{expected+2}],{m['line_port_overlay']['relocations']}
 jne .done
 mov si,{state}
 mov di,state_record
 mov cx,16
.state_copy:
 mov ax,[es:si]
 mov [di],ax
 add si,2
 add di,2
 loop .state_copy
 cmp word [state_record],3
 je .observe
 cmp word [sample+4],160
 jb .done
.observe:
 mov ax,0xb800
 mov es,ax
'''+source[end:]
 source=source.replace('4071','4103')
 source=source.replace(' popf\n mov dx,[es:old_vector]', ''' popf
 mov si,state_record
 mov di,buffer+4071
 mov cx,32
.state_export:
 mov al,[es:si]
 mov [di],al
 inc si
 inc di
 loop .state_export
 mov dx,[es:old_vector]''',1)
 (out/'observer.asm').write_text(source)
 subprocess.run(['nasm','-fbin','-DWATCH_KIND=0',str(out/'observer.asm'),'-o',str(out/'LOSTATE.COM')],check=True)
 settings=bytearray(prm(port=3,baud=5))
 for at,value in ((0x188,5),(0x4e4,8),(0x4e6,4),(0x1c2,0),(0x1c8,2),(0x1ca,25),(0x4ec,0),(0x1bc,0),(0x1be,0),(0x1e6,0),(0x3e4,7),(0x3e6,11),(0x3e8,113)):
  struct.pack_into('<H',settings,at,value)
 lab.BINARY=binary
 r=lab.run(out.name,'success','p900 enter p3500 a-p p10000 escape p1000 r e a d y enter p1000 a-x',prm=bytes(settings),arguments='@TEST.PRM /D:CaseTest:23',com=3,irq=5,cpu='8086',working_drive='d',observer='LOSTATE',files={'LOSTATE.COM':(out/'LOSTATE.COM').read_bytes()},timeout=35)
 capture=ROOT/'build/connection-dos'/out.name;raw=(capture/'PATHVIEW.BIN').read_bytes()
 words=struct.unpack_from('<16H',raw,4071)
 state_values=dict(zip(('phase','stage','handle','at','fix','busy','fatal','crc_low','crc_high','frame_offset','frame_segment','reason','last_base','last_segment','last_offset','dirty'),words))
 frame=raw[6:4006];text='\n'.join(frame[i*160:(i+1)*160:2].decode('cp437')for i in range(25))
 (out/'observed-screen.txt').write_text(text)
 result=dict(diagnostic=True,binary_sha256=sha(binary),base_result=r,state=state_values,
  observer_sha256=sha(out/'LOSTATE.COM'),sources={n:sha(ROOT/n)for n in ('standalone/test_line_port_overlay_state_dos.py','standalone/path_dialog_watch.asm')})
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(state_values)


if __name__=='__main__':main()
