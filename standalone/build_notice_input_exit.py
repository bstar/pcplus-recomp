#!/usr/bin/env python3
"""Build actual EXEC, native input retention and ordinary ASPECT exit fixtures."""
import json,re,shutil,subprocess
from pathlib import Path
import build_aspect_process as aspect
from build_notice_input_bank import build as input_bank
ROOT=aspect.ROOT;OUT=ROOT/'build/notice-input-exit';sha=aspect.sha
def main():
    cli=ROOT/'build/aspect-notice-input-parent'
    aspect.main(parent_render=True,output=cli,notice_bank=True,notice_sound=True,notice_input=True)
    OUT.mkdir(parents=True,exist_ok=True)
    cm=json.loads((cli/'manifest.json').read_text());nm=json.loads((ROOT/'build/notice-bank/manifest.json').read_text())
    native=aspect.program.display.process;pm=json.loads((native.OUT/'manifest.json').read_text())
    sources={**cm['sources'],**nm['sources'],**pm['sources']}
    symbols={n:(int(s,16),int(o,16)) for s,o,n in re.findall(r'^\s*([0-9a-f]{4}):([0-9a-f]{4,8})[*+]?\s+(\w+)\s*$',(cli/'ASPECT.map').read_text(),re.M|re.I)}
    code,callback=symbols['mouse_callback'];data,count=symbols['_mouse_count']
    assert symbols['_program_notice_result'][0]==symbols['_native_program_busy'][0]==data
    constants={'CHILD_CODE':code,'CHILD_CALLBACK':callback,'CHILD_DATA':data,'CHILD_COUNT':count}
    objects,extra=input_bank(OUT)
    for name in extra:sources[name]=sha(ROOT/name)
    common=['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-k8192','-i='+str(ROOT/'src/ui'),'-i='+str(ROOT/'src/mouse'),'-i='+str(ROOT/'src/process')]
    subprocess.run([*common,'-dNOTICE_BANKED','-dMOUSE_NOTICE_INPUT','-fd=NIKID.lnk','-fm=NIKID.map','-fe=NIKID.EXE',str(ROOT/'standalone/notice_input_exit_child.c'),*[str(ROOT/x) for x in nm['production_objects']],*objects],cwd=OUT,check=True)
    parent_objects=[]
    for path,defines in [('standalone/notice_input_exit_emit.asm',{}),('standalone/notice_input_retention_probe.asm',constants)]:
        obj=OUT/(Path(path).stem+'.obj');subprocess.run(['nasm','-fobj',*['-D'+k+'='+str(v) for k,v in defines.items()],str(ROOT/path),'-o',str(obj)],check=True);parent_objects.append(str(obj));sources[path]=sha(ROOT/path)
    process=[str(native.OUT/(Path(u['file']).stem+'.obj')) for u in pm['units']]+[str(native.OUT/'native_process_state.obj')]
    subprocess.run([*common,'-DNATIVE_PROCESS_DIAGNOSTIC','-DASPECT_NOTICE_RESULT='+str(symbols['_program_notice_result'][1]),'-DASPECT_NATIVE_BUSY='+str(symbols['_native_program_busy'][1]),'-fd=NIPAR.lnk','-fm=NIPAR.map','-fe=NIPAR.EXE',str(ROOT/'src/process/native_process.c'),str(ROOT/'standalone/notice_input_exit_parent.c'),*parent_objects,*process],cwd=OUT,check=True)
    for name in ['NIKID','NIPAR']:
        with (OUT/(name+'.lnk')).open('a') as f:f.write('\noption packcode=0\n')
        subprocess.run(['wlink','@'+str(OUT/(name+'.lnk'))],cwd=OUT,check=True)
    shutil.copyfile(cli/'ASPECT.EXE',OUT/'ASPECT.EXE')
    for name in ['standalone/build_notice_input_exit.py','standalone/notice_input_exit_child.c','standalone/notice_input_exit_parent.c','src/process/native_process.c']:sources[name]=sha(ROOT/name)
    assert all(sha(ROOT/n)==h for n,h in sources.items())
    m=dict(original_inputs=[],sources=sources,products={n:sha(OUT/n) for n in ['NIPAR.EXE','NIKID.EXE','ASPECT.EXE']},
        ordinary_ASPECT_sha256=cm['binary_sha256'],ASPECT_symbols={n:symbols[n] for n in ['mouse_callback','_mouse_count','_program_notice_result','_native_program_busy']},
        scope=__doc__+' Same banked PSP/floor guard as the ordinary CLI. Standalone child sets unrelated VM lease words to zero; actual ASPECT case injects a controlled vector change after verifying its callback/PSP. Retained child code is exercised after largest-free-block pressure; no general unload or physical driver acceptance.')
    (OUT/'manifest.json').write_text(json.dumps(m,indent=2)+'\n');print('Built input exit fixtures',m['products'])
if __name__=='__main__':main()
