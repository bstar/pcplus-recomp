#!/usr/bin/env python3
"""Build the bank-local notice recovery ABI with a foreign-CS callback probe."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/notice-checkpoint'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    sources=[Path(__file__),ROOT/'src/ui/notice_checkpoint.asm',ROOT/'standalone/notice_checkpoint_probe.asm',ROOT/'standalone/notice_checkpoint_diagnostic.c']
    objects=[]
    for source in sources[1:3]:
        obj=OUT/(source.stem+'.obj')
        subprocess.run(['nasm','-fobj','-DNOTICE_CHECKPOINT_SEGMENT=NOTICECODE','-DNOTICE_CHECKPOINT_CLASS=FARCODE',str(source),'-o',str(obj)],check=True)
        objects.append(str(obj))
    subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-fd=CHECK.lnk','-fm=CHECK.map','-fe=CHECK.EXE',str(sources[3]),*objects],cwd=OUT,check=True)
    with (OUT/'CHECK.lnk').open('a') as stream:stream.write('\noption packcode=0\n')
    subprocess.run(['wlink','@'+str(OUT/'CHECK.lnk')],cwd=OUT,check=True)
    manifest=dict(original_inputs=[],sources={str(p.relative_to(ROOT)):sha(p) for p in sources},binary_sha256=sha(OUT/'CHECK.EXE'),scope=__doc__+' Exact same recovery source as the near notice runtime. No application, arbitrary-fault or hardware acceptance.')
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('Built CHECK.EXE')
if __name__=='__main__':main()
