#!/usr/bin/env python3
"""Full-parent DOS overlay I/O refusal: current binaries, owned INT21 fault.

The observer refuses one loader request only after serial attachment. It never
repairs application state. A failed recovery remains a failed receipt.
"""
import argparse,json,re,shutil,struct,subprocess,sys
from pathlib import Path
import test_aspect_renderer_dos as render
from test_aspect_parent_process_dos import prepare_observer
from directory_fixtures import directory,prm
ROOT=render.ROOT;sha=render.sha
sys.path.insert(0,str(ROOT/'src/aspect'))
from compiler import compile_source

def instrument(source,child_map,fault,phase):
 symbols={n:(int(s,16),int(o,16)) for s,o,n in re.findall(r'^\s*([0-9a-f]{4}):([0-9a-f]{4,8})[*+]?\s+(\w+)\s*$',child_map.read_text(),re.M|re.I)}
 loader=symbols['__OvlRead___'][0];data,serial=symbols['_aspect_serial_active']
 code=r'''
 cmp word [cs:exec_seen],1
 jne .overlay_done
 cmp word [cs:exec_done],0
 jne .overlay_done
 cmp byte [ss:bp+17],REQUEST
 jne .overlay_done
 mov ah,0x62
 int 0x21
 mov es,bx
 mov ax,[es:0x16]
 cmp ax,[cs:parent_psp]
 jne .overlay_done
 mov ax,bx
 add ax,16+LOADER_SEG
 cmp ax,[ss:bp+22]
 jne .overlay_done
 mov ax,bx
 add ax,16+DATA_SEG
 mov es,ax
 PHASE_CHECK
 inc word [cs:io_seen]
 cmp word [cs:io_fault],0
 jne .overlay_done
 INJECT
.overlay_done:
'''
 inject=''
 if fault!='none':inject='inc word [cs:io_fault]\n mov word [ss:bp+16],'+('0' if fault=='short' else '2' if fault=='open' else '5')+'\n '+('and word [ss:bp+24],0xfffe' if fault=='short' else 'or word [ss:bp+24],1')+'\n restore\n iret'
 phase_check=''
 if phase=='run':phase_check='cmp word [es:'+str(serial)+'],1\n jne .overlay_done\n cmp word [es:'+str(symbols['_runtime_last_opcode'][1])+'],0x9b\n jne .overlay_done'
 for n,v in dict(REQUEST='0x3d' if fault=='open' else '0x3f',LOADER_SEG=str(loader),DATA_SEG=str(data),PHASE_CHECK=phase_check,INJECT=inject).items():code=code.replace(n,v)
 marker='handler:\n save\n cld\n mov bp,sp\n';assert source.count(marker)==1
 return source.replace(marker,marker+code).replace('sample_end:','io_seen: dw 0\nio_fault: dw 0\nsample_end:')

def final_lease_probe(source,parent_map):
 symbols={n:(int(s,16),int(o,16)) for s,o,n in re.findall(r'^\s*([0-9a-f]{4}):([0-9a-f]{4,8})[*+]?\s+(\w+)\s*$',parent_map.read_text(),re.M|re.I)}
 seg,off=symbols['render_program_owned']
 code=f'''
 cmp byte [ss:bp+17],0x4c
 jne .io_exit_done
 cmp word [cs:exec_done],1
 jne .io_exit_done
 cmp word [cs:io_parent_exit],0
 jne .io_exit_done
 mov ah,0x62
 int 0x21
 cmp bx,[cs:parent_psp]
 jne .io_exit_done
 mov ax,bx
 add ax,16+{seg}
 mov es,ax
 inc word [cs:io_parent_exit]
 mov ax,[es:{off}]
 mov [cs:io_exit_owned],ax
 mov ax,[es:{symbols['render_snapshot_owned'][1]}]
 mov [cs:io_exit_snapshot],ax
 mov ax,[es:{symbols['render_attached'][1]}]
 mov [cs:io_exit_attached],ax
.io_exit_done:
'''
 marker='handler:\n save\n cld\n mov bp,sp\n';assert source.count(marker)==1
 return source.replace(marker,marker+code).replace('sample_end:','io_parent_exit: dw 0\nio_exit_owned: dw 0\nio_exit_snapshot: dw 0\nio_exit_attached: dw 0\nsample_end:')

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('parent','child','output'):p.add_argument('--'+n,type=Path,required=True)
 p.add_argument('--fault',choices=('none','read','open','short'),default='read');p.add_argument('--phase',choices=('startup','run'),default='run');a=p.parse_args()
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
 shutil.copyfile(Path(__file__),out/'checker.py')
 parent=a.parent.resolve();child=a.child.resolve();manifests=[];sources={}
 for folder,leaf in ((parent,'TERMINAL.EXE'),(child,'ASPECT.EXE')):
  m=json.loads((folder/'manifest.json').read_text());assert not m.get('original_inputs') and sha(folder/leaf)==m['binary_sha256'];manifests.append(m)
  for n,h in m['sources'].items():assert sha(ROOT/n)==h;sources[n]=h
 assert manifests[1]['experimental_standard_overlays']
 for n in ['standalone/test_aspect_overlay_io_dos.py','standalone/test_aspect_parent_process_dos.py','standalone/test_aspect_renderer_dos.py','standalone/mouse_parent_probe.py','standalone/mouse_sound_checks.py','standalone/test_connection_dos.py','standalone/test_terminal.py','standalone/directory_fixtures.py','standalone/directory_test_support.py','standalone/terminal_config_fixtures.py','standalone/modem_fixtures.py','src/aspect/compiler.py']:sources[n]=sha(ROOT/n)
 render.OUT=out
 _,size=prepare_observer(out,render.map_offsets(parent/'terminal.map'),parent/'terminal.map',sound_probe=True,mouse_probe=True)
 source=instrument((out/'observer.asm').read_text(),child/'ASPECT.map',a.fault,a.phase)
 source=final_lease_probe(source,parent/'terminal.map');(out/'observer.asm').write_text(source)
 subprocess.run(['nasm','-fbin',str(out/'observer.asm'),'-o',str(out/'RENDER.COM')],check=True)
 folder=out/'ordinary';folder.mkdir()
 for path in (parent/'TERMINAL.EXE',child/'ASPECT.EXE'):shutil.copyfile(path,folder/path.name)
 script='proc main\nwaitfor "LOGIN:" 5\ntransmit "LOADREADY"\nrun "ABSENT.COM"\ntransmit "AFTERLOAD"\ntransmit $D_PWORD\ntransmit "^M"\npause 1\nendproc\n'
 files={'LOGIN.ASP':script.encode(),'LOGIN.ASX':compile_source(script),'RENDER.COM':(out/'RENDER.COM').read_bytes()}
 modules={}
 for leaf in ('PCMETA.OVL','PCLINE.OVL','PCCOMP.OVL','PCCHAT.OVL'):
  if (parent/leaf).exists():files[leaf]=(parent/leaf).read_bytes();modules[leaf]=sha(parent/leaf)
 settings=bytearray(prm(port=1,soft=0,hard=1))
 for at,value in [(0x1bc,1),(0x1c2,0),(0x1c8,2),(0x1ca,25),(0x4ec,0),(0x1be,4),(0x1e6,0),(0x1e4,0),(0x4e4,8),(0x4e6,4)]:struct.pack_into('<H',settings,at,value)
 book=bytearray(directory(port=0));book[302:311]=b'LOGIN\0\0\0\0';book[325:336]=b'Synth42\0\0\0\0'
 harness=render.adapter(timeout_seconds=30);harness.BINARY=folder/'TERMINAL.EXE'
 try:result=harness.run('ordinary','success','p1000 space p7000 space p700 ` p1500 r e a d y p700 a-x',directory=bytes(book),prm=bytes(settings),com=1,arguments='@D:\\TEST.PRM /E:D:\\TEST.DIR /N:1 /A:NETWORK',files=files,banner=b'\x1b[2J\x1b[HFIRST BYTE SAFE\x1b[6n\x1b[0cLOGIN:',working_drive='d',observer='RENDER',cpu='386',observer_high=True)
 except subprocess.TimeoutExpired:
  result=dict(passed=False,error='Owned DOS emulator timed out; normal return/recovery unproven',fault=a.fault,phase=a.phase,parent_sha256=sha(parent/'TERMINAL.EXE'),child_sha256=sha(child/'ASPECT.EXE'),sources=sources,original_inputs=[],physical_verified=False,scope=__doc__)
  (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(result['error']);return 1
 raw=(folder/'RENDER.BIN').read_bytes();final_lease=list(struct.unpack('<4H',raw[-8:]));raw=raw[:-8];seen,injected=struct.unpack('<2H',raw[-4:]);raw=raw[:-4]
 head=struct.unpack_from('<7H',raw);owners=struct.unpack_from('<13H',raw,len(raw)-26-32*70-size*2)
 from mouse_sound_checks import verify
 mouse_checks,mouse=verify(raw,parent/'terminal.map',size,folder)
 wire=(folder/'serial.bin').read_bytes();checks=result['checks'];checks.update(mouse_checks)
 checks.update(owned_child_returned=head[:4]==(0x524e,1,1,1),loader_request_seen=seen>0,fault_injected_once=injected==int(a.fault!='none'),child_exit_expected=head[6]==(0 if a.fault=='none' else 255),parent_JFT_retained=raw[14:34]==raw[34:54],parent_files_retained=raw[54:470]==raw[470:886],parent_resources=owners[2]==0 and raw[-size*2:-size]==raw[-size:],parent_lease_retired=final_lease==[1,0,0,0],script_boundary=(b'LOADREADY' in wire)==(a.phase=='run' or a.fault=='none') and (b'AFTERLOAD' in wire)==(a.fault=='none'),parent_input_resumes=b'ready' in wire,sources_unchanged=all(sha(ROOT/n)==h for n,h in sources.items()))
 if a.fault=='none':checks['normal_child_closes_lease']=owners[7]==0 and owners[8]==owners[9]
 result.update(passed=all(checks.values()),fault=a.fault,phase=a.phase,loader_requests=seen,injections=injected,child_exit=head[6],lease_at_EXEC_return=list(owners[7:11]),lease_at_parent_exit=final_lease,parent_sha256=sha(parent/'TERMINAL.EXE'),child_sha256=sha(child/'ASPECT.EXE'),sources=sources,modules=modules,mouse=mouse,original_inputs=[],physical_verified=False,scope=__doc__)
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(result['passed'],head,seen,injected,[n for n,v in checks.items() if not v]);return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
