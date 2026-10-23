#!/usr/bin/env python3
"""Build maintained foreground speaker owner in a separate8086 code bank."""
import hashlib,json,re,subprocess
from pathlib import Path
from omf_imports import records,externals
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/speaker'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    OUT.mkdir(parents=True,exist_ok=True);sources={};objects=[]
    units=[('backend','src/ui/speaker_native.asm',['_TEXT=SPEAKERCODE']),('uart','reconstruction/uart/core.asm',['UART_OMF']),('api','src/uart/api.asm',[]),('serial-backend','src/aspect/serial_backend.asm',[])]
    for name,path,defines in units:
        obj=OUT/(name+'.obj');subprocess.run(['nasm','-fobj','-I'+str(ROOT/'reconstruction/uart')+'/',*['-D'+d for d in defines],str(ROOT/path),'-o',str(obj)],check=True);objects.append(str(obj));sources[path]=sha(ROOT/path)
    flags=['-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-dSPEAKER_BANKED','-i='+str(ROOT/'src/ui'),'-i='+str(ROOT/'src/aspect')]
    owner=OUT/'speaker.obj';subprocess.run(['wcc',*flags,'-nt=SPEAKERCODE','-fo='+str(owner),str(ROOT/'src/ui/speaker.c')],cwd=OUT,check=True);objects.insert(0,str(owner))
    imports={n.decode() for kind,payload,_ in records(owner.read_bytes()) if kind==0x8c for n,_ in externals(payload)}
    assert imports=={'_speaker_context','_speaker_claim','_speaker_release','_speaker_ticks','_speaker_owned','_speaker_generation_word','_small_code_'},imports
    cpaths=['src/aspect/serial.c','standalone/speaker_uart_diagnostic.c']
    subprocess.run(['wcl',*flags,'-k8192','-fd=SPEAKER.lnk','-fm=SPEAKER.map','-fe=SPEAKER.EXE',*[str(ROOT/p) for p in cpaths],*objects],cwd=OUT,check=True)
    with (OUT/'SPEAKER.lnk').open('a') as stream:stream.write('\noption packcode=0\n')
    subprocess.run(['wlink','@'+str(OUT/'SPEAKER.lnk')],cwd=OUT,check=True)
    names={n:(int(seg,16),int(off,16)) for seg,off,n in re.findall(r'^\s*([0-9a-f]{4}):([0-9a-f]{4,8})[*+]?\s+(\w+)\s*$',(OUT/'SPEAKER.map').read_text(),re.M|re.I)}
    bank=names['_speaker_start'][0];assert names['main_'][0]!=bank
    for name in ['_speaker_poll','_speaker_stop','_speaker_active','_speaker_context','_speaker_claim','_speaker_release','_speaker_ticks']:assert names[name][0]==bank,name
    for path in ['standalone/build_speaker.py','standalone/omf_imports.py','src/ui/speaker.c','src/ui/speaker.h','src/aspect/serial.h','src/aspect/serial_handoff.h','src/aspect/resident_render.h','reconstruction/uart/layout.inc','reconstruction/directory_accounting/patch.asm',*cpaths]:sources[path]=sha(ROOT/path)
    report=dict(original_inputs=[],sources=sources,binary_sha256=sha(OUT/'SPEAKER.EXE'),bank_segment=bank,owner_imports=sorted(imports),main_segment=names['main_'][0],scope=__doc__+' Real UART/ISR/flow and PIT/speaker instructions. This standalone owner is not yet bound to notice/application configuration or outer recovery.')
    (OUT/'manifest.json').write_text(json.dumps(report,indent=2)+'\n');print('Built SPEAKER.EXE',report['binary_sha256'])
if __name__=='__main__':main()
