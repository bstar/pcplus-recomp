#!/usr/bin/env python3
"""Build opt-in GET keyboard lease with actual DOS BIOS/UART and source field."""
import argparse,hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
 units=[('uart','reconstruction/uart/core.asm',['UART_OMF']),('uart-api','src/uart/api.asm',[]),('serial-backend','src/aspect/serial_backend.asm',[]),('keyboard','src/aspect/keyboard.asm',[]),('keyboard-bios','reconstruction/keyboard/core.asm',['KEYBOARD_BIOS_ONLY']),('keyboard-detect','reconstruction/keyboard_detection/detect.asm',['KEYBOARD_DETECTION_OMF'])]
 objects=[]
 for name,source,defines in units:
  obj=out/(name+'.obj');subprocess.run(['nasm','-fobj','-I'+str(ROOT/'reconstruction/uart')+'/',*['-D'+v for v in defines],str(ROOT/source),'-o',str(obj)],check=True);objects.append(str(obj))
 flags=['-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-dASPECT_RUNTIME_SERIAL','-dASPECT_ALARM_SERVICE','-dASPECT_GET_SERVICE','-i='+str(ROOT/'src/aspect')]
 subprocess.run(['wcc',*flags,'-nt=GET_FIELD_CODE','-nc=FARCODE','-fo='+str(out/'field.obj'),str(ROOT/'src/aspect/get_field.c')],check=True);objects.append(str(out/'field.obj'))
 cs=['src/aspect/serial.c','src/aspect/when_runtime.c','standalone/get_when_uart_diagnostic.c']
 subprocess.run(['wcl',*flags,'-k8192','-fd=GETUART.lnk','-fm=GETUART.map','-fe=GETUART.EXE',*[str(ROOT/n) for n in cs],*objects],cwd=out,check=True)
 with (out/'GETUART.lnk').open('a') as f:f.write('\noption packcode=0\n')
 subprocess.run(['wlink','@'+str(out/'GETUART.lnk')],cwd=out,check=True)
 names=[s for _,s,_ in units]+cs+['src/aspect/get_field.c','src/aspect/get_field.h','standalone/build_get_when_uart.py','src/aspect/serial.h','src/aspect/serial_handoff.h','src/aspect/resident_render.h','src/aspect/when_runtime.h','src/aspect/runtime.h','src/aspect/serial_runtime.h','src/aspect/receive_runtime.h','reconstruction/uart/encodings.inc','reconstruction/uart/layout.inc','reconstruction/directory_accounting/patch.asm']
 result=dict(passed=True,diagnostic_build=True,binary_sha256=sha(out/'GETUART.EXE'),sources={n:sha(ROOT/n) for n in names},original_inputs=[],scope=__doc__+' Actual WHEN C admission/key/transport gates. Native WHEN action and parent receive/render entry modeled; no ASPECT opcode/compiler, live parent display, native abort unwind or physical hardware acceptance.')
 (out/'manifest.json').write_text(json.dumps(result,indent=2)+'\n');print('Built GET/UART diagnostic',result['binary_sha256'])

if __name__=='__main__':main()
