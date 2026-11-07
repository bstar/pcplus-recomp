#!/usr/bin/env python3
"""Build the ALARM key lease and real DOS/UART platform diagnostic."""
import argparse,json,re,subprocess
from pathlib import Path
from build_context_help import ROOT,sha

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(exist_ok=False);sources={};objects=[]
 units=[('alarm','src/aspect/alarm_native.asm',[]),('alarm-bridge','src/aspect/alarm_cooperative_bridge.asm',[]),
  ('clock','src/aspect/alarm_dos_clock.asm',[]),('speaker-backend','src/ui/speaker_native.asm',['_TEXT=SPEAKERCODE']),
  ('uart','reconstruction/uart/core.asm',['UART_OMF']),('uart-api','src/uart/api.asm',[]),
  ('serial-backend','src/aspect/serial_backend.asm',[]),
  ('keyboard','src/aspect/keyboard.asm',[]),('keyboard-bios','reconstruction/keyboard/core.asm',['KEYBOARD_BIOS_ONLY']),
  ('keyboard-detect','reconstruction/keyboard_detection/detect.asm',['KEYBOARD_DETECTION_OMF'])]
 for name,source,defines in units:
  obj=out/(name+'.obj');subprocess.run(['nasm','-fobj','-I'+str(ROOT/'reconstruction/uart')+'/',*['-D'+v for v in defines],str(ROOT/source),'-o',str(obj)],check=True);objects.append(str(obj));sources[source]=sha(ROOT/source)
 flags=['-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-dSPEAKER_BANKED','-dASPECT_RUNTIME_SERIAL','-dASPECT_ALARM_SERVICE','-i='+str(ROOT/'src/ui'),'-i='+str(ROOT/'src/aspect')]
 speaker=out/'speaker.obj';subprocess.run(['wcc',*flags,'-nt=SPEAKERCODE','-fo='+str(speaker),str(ROOT/'src/ui/speaker.c')],cwd=out,check=True);objects.append(str(speaker))
 cs=['src/ui/speaker.c','src/aspect/alarm_cooperative.c','src/aspect/alarm_dos.c','src/aspect/serial.c','standalone/alarm_when_uart_diagnostic.c','src/aspect/when_runtime.c']
 subprocess.run(['wcl',*flags,'-k8192','-fd=ALARM.lnk','-fm=ALARM.map','-fe=ALARM.EXE',*[str(ROOT/n) for n in cs if n!='src/ui/speaker.c'],*objects],cwd=out,check=True)
 with (out/'ALARM.lnk').open('a') as f:f.write('\noption packcode=0\n')
 subprocess.run(['wlink','@'+str(out/'ALARM.lnk')],cwd=out,check=True)
 symbols={n:(int(s,16),int(o,16)) for s,o,n in re.findall(r'^\s*([0-9a-f]{4}):([0-9a-f]{4,8})[*+]?\s+(\w+)\s*$',(out/'ALARM.map').read_text(),re.M|re.I)}
 assert symbols['main_'][0]!=symbols['_speaker_start'][0]
 assert symbols['_alarm_coop_run'][0]==symbols['aspect_alarm_alert'][0]==symbols['_alarm_dos_run'][0]
 names=cs+['standalone/build_alarm_when_uart.py','standalone/alarm_dos_uart_diagnostic.c','standalone/build_context_help.py','src/aspect/alarm_cooperative.h','src/aspect/alarm_dos.h','src/ui/speaker.h','src/aspect/serial.h','src/aspect/serial_handoff.h','src/aspect/resident_render.h','src/aspect/when_runtime.h','src/aspect/runtime.h','src/aspect/serial_runtime.h','src/aspect/receive_runtime.h','reconstruction/uart/encodings.inc','reconstruction/uart/layout.inc','reconstruction/directory_accounting/patch.asm']
 for n in names:sources[n]=sha(ROOT/n)
 report=dict(passed=True,diagnostic_build=True,binary_sha256=sha(out/'ALARM.EXE'),sources=sources,original_inputs=[],speaker_bank=symbols['_speaker_start'][0],main_bank=symbols['main_'][0],
  scope=__doc__+' Source-only native alert/cooperative bridge and platform, actual banked speaker/PIT/clock/BIOS keyboard plus recovered UART ISR. Diagnostic only; actual WHEN C key gates with modeled native action/renderer; no interpreter/parent/PRM or physical machine binding.')
 (out/'manifest.json').write_text(json.dumps(report,indent=2)+'\n');print('Built DOS ALARM/UART diagnostic',report['binary_sha256'])
if __name__=='__main__':main()
