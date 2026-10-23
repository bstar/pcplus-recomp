#!/usr/bin/env python3
"""Source-only exact native notice sound component build."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/program-sound'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    OUT.mkdir(parents=True,exist_ok=True);proof=json.loads((ROOT/'reconstruction/program_sound/provenance.json').read_text())
    units=proof['units']+[dict(name='delay',file=proof['reused_delay'],sha256='')]
    sources={};products={};objects=[]
    for unit in units:
        path=ROOT/unit['file'];name=unit['name'];sources[unit['file']]=sha(path)
        flat=OUT/(name+'.bin');obj=OUT/(name+'.obj');flags=['-I'+str(ROOT/'reconstruction/uart')+'/']
        subprocess.run(['nasm','-fbin',*flags,str(path),'-o',str(flat)],check=True)
        expected=unit['sha256'] if name!='delay' else next(u['sha256'] for u in json.loads((ROOT/'reconstruction/notice_window/provenance.json').read_text())['units'] if u['file']==unit['file'])
        assert sha(flat)==expected,name;products[flat.name]=sha(flat)
        extra=['-DNOTICE_WINDOW_OMF','-Dwindow_pace=sound_delay','-Dwindow_state_7a4e=sound_delay_floor','-Dwindow_state_7ac4=sound_delay_count'] if name=='delay' else ['-DPROGRAM_SOUND_OMF']
        subprocess.run(['nasm','-fobj',*flags,*extra,str(path),'-o',str(obj)],check=True);objects.append(str(obj))
    host=ROOT/'standalone/program_sound_diagnostic.asm';obj=OUT/'diagnostic.obj';subprocess.run(['nasm','-fobj',str(host),'-o',str(obj)],check=True)
    subprocess.run(['wlink','system','dos','option','quiet','option','start=sound_test','option','map='+str(OUT/'SOUND.map'),'name',str(OUT/'SOUND.EXE'),'file',','.join([str(obj),*objects])],check=True)
    products['SOUND.EXE']=sha(OUT/'SOUND.EXE')
    for name in ['standalone/build_program_sound.py','standalone/program_sound_diagnostic.asm','reconstruction/program_sound/provenance.json','reconstruction/notice_window/provenance.json','reconstruction/uart/encodings.inc']:sources[name]=sha(ROOT/name)
    report=dict(original_inputs=[],sources=sources,products=products,recovered_bytes=proof['recovered_bytes'],reused_bytes=38,scope=__doc__+' No CRT sound or timing substitute. Original artifacts/REA databases are not build inputs. Component only, without maintained sound policy or application binding.')
    (OUT/'manifest.json').write_text(json.dumps(report,indent=2)+'\n');print('Built SOUND.EXE:',products['SOUND.EXE'])
if __name__=='__main__':main()
