#!/usr/bin/env python3
"""Queue Alt-Z behind real input during native Chat TEXT/echo parser wait."""
import argparse,hashlib,json,re,shutil,struct,subprocess
from pathlib import Path
import test_connection_dos as harness
from directory_fixtures import prm
from build_context_help import ROOT,sha

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ('package','output'):p.add_argument('--'+name,type=Path,required=True)
 p.add_argument('--keys',type=int,choices=(1,31),default=1)
 p.add_argument('--rows',type=int,choices=(25,28,43,50),default=25)
 p.add_argument('--observer-damage',action='store_true',help='Negative control: flip the last byte of the observer copy only')
 a=p.parse_args();package=a.package.resolve();out=a.output.resolve()
 assert package.is_relative_to(ROOT/'build') and out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False)
 bundle=json.loads((package/'package.json').read_text());m=json.loads((package/'manifest.json').read_text());assert m['experimental_chat_help']
 names=['standalone/test_chat_help_busy.py','standalone/chat_help_life_watch.asm','standalone/chat_busy_watch.asm','standalone/test_connection_dos.py','standalone/directory_fixtures.py','standalone/modem_fixtures.py','standalone/terminal_config_fixtures.py','standalone/test_terminal.py','standalone/directory_test_support.py','standalone/build_path_session.py']
 sources={**bundle['sources'],**{name:sha(ROOT/name) for name in names}}
 for name,digest in sources.items():assert sha(ROOT/name)==digest,name
 stage=out/'program';stage.mkdir()
 for name,digest in bundle['products'].items():assert sha(package/name)==digest;shutil.copyfile(package/name,stage/name)
 listing=(package/'terminal.map').read_text();symbols={n:(int(seg,16),int(off,16)) for seg,off,n in re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$',listing,re.M|re.I)}
 ds=int(re.search(r'^DGROUP\s+([0-9a-f]+):0000',listing,re.M|re.I)[1],16)
 size=m['chat_loader']['module']['image_bytes'];assert size%2==0
 constants=dict(FROZEN_DELTA=symbols['redisplay_snapshot'][0]-ds,IMAGE_BYTES=size,CHAT_API_VERSION=m['chat_loader']['module']['api_version'],CHAT_STEP_OPERATION=14,PROGRAM_DELTA=symbols['program_screen'][0]-ds,PROGRAM_OFFSET=symbols['program_screen'][1])
 for label,name in [('OWNER_OFF','_redisplay_active'),('PARSER_OFF','terminal_parser_active'),('WAIT_OFF','terminal_ansi_wait_active'),('DEFERRED_OFF','terminal_deferred_count'),('STATUS_OFF','terminal_macro_status'),('ACTIVE_OFF','terminal_program_active'),('PENDING_OFF','terminal_program_pending'),('KIND_OFF','terminal_program_kind'),('CURSOR_OFF','program_cursor'),('SHAPE_OFF','program_shape')]:
  seg,off=symbols[name];assert seg==ds;constants[label]=off
 source=(ROOT/'standalone/chat_busy_watch.asm').read_text()
 source=source.replace('jmp start',"jmp near start\n db 'BW2',0\n dw parent_ds,module_copy,IMAGE_BYTES,sample",1)
 source=source.replace('\nhandler:\n','\nparent_ds: dw 0\nmodule_copy: times IMAGE_BYTES db 0xa5\nhandler:\n',1)
 marker=' mov ax,0x40\n mov es,ax\n mov ax,[es:0x6c]'
 assert source.count(marker)==2
 copy=' mov ax,ss\n mov [cs:parent_ds],ax\n test word [cs:sample+2],1\n jnz .module_saved\n push ds\n push es\n mov ax,es\n mov ds,ax\n push cs\n pop es\n xor si,si\n mov di,module_copy\n mov cx,IMAGE_BYTES/2\n cld\n rep movsw\n pop es\n pop ds\n.module_saved:\n'
 source=source.replace(marker,copy+marker,1)
 if a.observer_damage:source=source.replace(' rep movsw\n pop es',' rep movsw\n xor byte [cs:module_copy+IMAGE_BYTES-1],1\n pop es',1)
 source=source.replace('.module_saved:\n','.module_saved:\n mov ax,[ACTIVE_OFF]\n or ax,[PENDING_OFF]\n jz .no_early_program\n or word [cs:sample+2],32\n.no_early_program:\n',1)
 source=source.replace(' mov [cs:sample+20],ax\n cmp ax,0x2d58',' mov [cs:sample+20],ax\n cmp ax,0x2c00\n jne .not_help\n or word [cs:sample+2],16\n.not_help:\n cmp ax,0x2d58',1)
 total=30+size;source=source.replace('mov cx,28',f'mov cx,{total}').replace('cmp ax,28',f'cmp ax,{total}').replace('buffer: times 28 db 0',f'buffer: times {total} db 0')
 busy_source=out/'BUSYW.ASM';busy_source.write_text(source)
 for name,path in [('BUSYW',busy_source),('HELPMEM',ROOT/'standalone/chat_help_life_watch.asm')]:
  subprocess.run(['nasm','-fbin',*['-D'+k+'='+str(v) for k,v in constants.items()],str(path),'-o',str(out/(name+'.COM'))],check=True)
 settings=bytearray(prm(port=3,baud=5))
 for off,value in [(0x188,5),(0x4e4,8),(0x4e6,4),(0x1c2,0),(0x1c8,2),(0x1ca,a.rows),(0x4ec,0),(0x1bc,0),(0x1be,0),(0x1e6,0),(0x1e4,0)]:struct.pack_into('<H',settings,off,value)
 settings[0x1e2]=ord('~');records=struct.pack('<H',3)+b'GO^[TAIL^M'.ljust(52,b'\0')+bytes(54*9)
 # Full FIFO drain/echo and Help preflight take longer at43/50 rows. Leave
 # the requested UI open for passive stable-frame sampling before Escape.
 keys='p900 enter p5000 a-e p500 a-o p1800 a-1 p100 '+'X '*a.keys+'a-z p6500 escape p1000 enter p1500 escape p900 N O R M A L p1000 a-x'
 harness.BINARY=stage/'TERMINAL.EXE';label=out.name+'-main';capture=ROOT/'build/connection-dos'/label;assert not capture.exists()
 r=harness.run(label,'success',keys,prm=bytes(settings),com=3,irq=5,cpu='8086',working_drive='d',timeout=50,arguments='@TEST.PRM /D:CaseTest:23 /T:D:\\ACTIONS.KEY',observer='HELPMEM',auxiliary=('BUSYW',),files={'ACTIONS.KEY':records,**{name+'.COM':(out/(name+'.COM')).read_bytes() for name in ('BUSYW','HELPMEM')}},online_triggers=((b'GO',[(1.0,b'[31m')]),(b'NORMAL',b'BACK\x1b[6n')))
 raw=(capture/'HELPLIFE.BIN').read_bytes();words=struct.unpack_from('<25H',raw);before=raw[50:8050];helper=raw[8050:16050];after=raw[16050:24050]
 busy=(capture/'BUSYVIEW.BIN').read_bytes();bw=struct.unpack_from('<14H',busy);parent_ds=struct.unpack_from('<H',busy,28)[0];observed=busy[30:30+size]
 file=(stage/'PCCHAT.OVL').read_bytes();header=struct.unpack_from('<H',file,8)[0]*16;expected=bytearray(file[header:header+size]);count=struct.unpack_from('<H',file,6)[0];table=struct.unpack_from('<H',file,0x18)[0]
 for i in range(count):
  off,seg=struct.unpack_from('<HH',file,table+i*4);at=seg*16+off;struct.pack_into('<H',expected,at,(struct.unpack_from('<H',expected,at)[0]+words[11])&65535)
 wire=(capture/'serial.bin').read_bytes();visible=before[::2];local=(34 if a.rows>28 else 20)*80
 checks=dict(r['checks']);checks.update(observer_complete=len(raw)==24050 and words[:2]==(0x4842,3),actual_rows=words[3]==a.rows,native_wait_observed=bool(bw[1]&1) and bw[2]>0,AltZ_observed_in_busy_BIOS_queue=bool(bw[1]&16),no_PROGRAM_admission_during_native_wait=not bool(bw[1]&32),FIFO_retained_Help_and_prefix=bw[11]==a.keys+1,Help_only_after_native_wait=words[14:19]==(2,0,0,1,11),Chat_resumed_without_wait=words[19:22]==(2,0,0),same_parent_DS=words[10]==parent_ds,same_module_segment=words[11]==words[12]==words[13]==parent_ds+constants['FROZEN_DELTA'],loaded_module_matches_product=bytes(expected)==observed,loaded_image_unchanged_during_and_after_Help=words[22:24]==(1,1),Chat_PROGRAM_snapshot_restored=before==after,Chat_cursor_restored=words[4:6]==words[8:10],actual_context3_helper=helper[2:20:2]==b'Chat Mode',unfinished_prefix_in_saved_local_pane=visible[local:(a.rows-1)*80].count(b'X')==a.keys,exact_TEXT_and_retained_input_order=b'GO\x1bTAIL\r'+b'X'*a.keys+b'\r\nNORMAL' in wire,no_excess_or_Help_key_leak=wire.count(b'X')==a.keys,retired_FIFO_empty=bw[10]==0,ordinary_parser_resumed=b'BACK' in (capture/'SCREEN.BIN').read_bytes()[::2],sources_unchanged=all(sha(ROOT/n)==h for n,h in sources.items()),products_unchanged=all(sha(stage/n)==d for n,d in bundle['products'].items()))
 report=dict(passed=all(checks.values()),observer_damage=a.observer_damage,image_differences=[i for i,(x,y) in enumerate(zip(expected,observed)) if x!=y],rows=a.rows,ordinary_keys=a.keys,checks=checks,observer_words=words,busy_words=bw,constants=constants,products=bundle['products'],sources=sources,capture=str(capture.relative_to(ROOT)),loaded_image_sha256=hashlib.sha256(observed).hexdigest(),observers={name:sha(out/(name+'.COM')) for name in ('BUSYW','HELPMEM')},scope=__doc__+' Passive INT16 observes real Alt-Z/native wait/FIFO and saves the actual loaded image. Passive timer reads the real PROGRAM snapshot at Help, native busy/PROGRAM state, exact image comparison at Help/return and visible full return frame. Before-frame is the actual saved PROGRAM buffer, not an earlier VGA sample. MZ relocations replayed against source product for exact pre-wait image identity. Optional negative damages only the observer copy. No product writes or injected state, continuous-lifetime/fault/physical/SIP/audio acceptance.')
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print({k:v for k,v in checks.items() if not v});return 0 if report['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
