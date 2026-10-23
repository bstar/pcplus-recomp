#!/usr/bin/env python3
"""Build native mouse/BIOS input with the banked timed-notice controller."""
import json,subprocess
import build_notice_bank as notice
from build_native_mouse import sha
ROOT=notice.ROOT;OUT=ROOT/'build/notice-input'
def main():
    notice.main();OUT.mkdir(parents=True,exist_ok=True)
    nm=json.loads((ROOT/'build/notice-bank/manifest.json').read_text());sources=dict(nm['sources'])
    objects=[str(ROOT/p) for p in nm['production_objects']]
    flags=['-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-dNOTICE_BANKED','-dNOTICE_NATIVE_INPUT','-dMOUSE_NOTICE_INPUT','-i='+str(ROOT/'src/ui'),'-i='+str(ROOT/'src/mouse')]
    runtime=OUT/'runtime.obj'
    subprocess.run(['wcc',*flags,'-nt=NOTICECODE','-fo='+str(runtime),str(ROOT/'src/ui/notice.c')],cwd=OUT,check=True)
    objects[objects.index(str(ROOT/'build/notice-bank/runtime.obj'))]=str(runtime)
    native=json.loads((ROOT/'reconstruction/program_mouse/provenance.json').read_text())
    keyboard=json.loads((ROOT/'reconstruction/keyboard/provenance.json').read_text())
    include='-I'+str(ROOT/'reconstruction/uart')+'/'
    assembly=[(u['file'],['PROGRAM_MOUSE_OMF']) for u in native['units']]
    assembly += [('reconstruction/program_mouse/defaults.asm',['PROGRAM_MOUSE_OMF']),('reconstruction/keyboard/core.asm',['KEYBOARD_OMF']),
        ('src/mouse/state.asm',[]),('src/mouse/platform.asm',[]),('standalone/mouse_keyboard_bridge.asm',[])]
    for i,(path,defines) in enumerate(assembly):
        obj=OUT/f'mouse-{i}.obj';subprocess.run(['nasm','-fobj',include,*['-D'+x for x in defines],str(ROOT/path),'-o',str(obj)],check=True);objects.append(str(obj));sources[path]=sha(ROOT/path)
    for i,u in enumerate(native['units']):
        target=OUT/f'native-{i}.bin';subprocess.run(['nasm','-fbin',include,str(ROOT/u['file']),'-o',str(target)],check=True);assert sha(target)==u['sha256']
    for i,u in enumerate(keyboard['ranges']):
        target=OUT/f'keyboard-{i}.bin';subprocess.run(['nasm','-fbin',include,'-DKEYBOARD_REGION='+str(i),str(ROOT/'reconstruction/keyboard/core.asm'),'-o',str(target)],check=True);assert sha(target)==u['sha256']
    target=OUT/'defaults.bin';subprocess.run(['nasm','-fbin',str(ROOT/'reconstruction/program_mouse/defaults.asm'),'-o',str(target)],check=True)
    assert sha(target)==json.loads((ROOT/'reconstruction/program_mouse/defaults.json').read_text())['sha256']
    c_paths=['src/mouse/owner.c','src/ui/notice_input.c','standalone/notice_input_diagnostic.c']
    subprocess.run(['wcl',*flags,'-k8192','-fd=NINPUT.lnk','-fm=NINPUT.map','-fe=NINPUT.EXE',*[str(ROOT/x) for x in c_paths],*objects],cwd=OUT,check=True)
    with (OUT/'NINPUT.lnk').open('a') as f:f.write('\noption packcode=0\n')
    subprocess.run(['wlink','@'+str(OUT/'NINPUT.lnk')],cwd=OUT,check=True)
    for path in c_paths+['src/mouse/owner.h','src/ui/notice_input.h','standalone/build_notice_input.py','standalone/build_native_mouse.py','reconstruction/program_mouse/provenance.json','reconstruction/program_mouse/defaults.json','reconstruction/keyboard/provenance.json']:sources[path]=sha(ROOT/path)
    assert all(sha(ROOT/n)==h for n,h in sources.items())
    manifest=dict(original_inputs=[],binary_sha256=sha(OUT/'NINPUT.EXE'),sources=sources,
        scope=__doc__+' Separate component; guarded non-consuming peek, actual native mouse/BIOS normalization and child-local driver ownership. Debug/display gate remains disabled; no KEY macro playback, attached ASPECT or full application acceptance.')
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print('Built NINPUT.EXE',manifest['binary_sha256'])
if __name__=='__main__':main()
