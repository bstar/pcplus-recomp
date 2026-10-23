#!/usr/bin/env python3
"""Opt-in banked notice/speaker composition; normal notice builds stay quiet."""
import json,subprocess,re
from pathlib import Path
import build_notice_bank as notice
import build_speaker as speaker
ROOT=speaker.ROOT;OUT=ROOT/'build/speaker-notice';sha=speaker.sha

def main():
    notice.main();speaker.main();OUT.mkdir(parents=True,exist_ok=True)
    nm=json.loads((ROOT/'build/notice-bank/manifest.json').read_text());sm=json.loads((speaker.OUT/'manifest.json').read_text());sources={**nm['sources'],**sm['sources']}
    objects=[str(ROOT/p) for p in nm['production_objects']]
    flags=['-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-dNOTICE_BANKED','-dNOTICE_SPEAKER','-dSPEAKER_BANKED','-i='+str(ROOT/'src/ui')]
    runtime=OUT/'runtime.obj';subprocess.run(['wcc',*flags,'-nt=NOTICECODE','-fo='+str(runtime),str(ROOT/'src/ui/notice.c')],cwd=OUT,check=True)
    objects[objects.index(str(ROOT/'build/notice-bank/runtime.obj'))]=str(runtime)
    objects += [str(speaker.OUT/'speaker.obj'),str(speaker.OUT/'backend.obj')]
    subprocess.run(['wcl',*flags,'-k8192','-fd=NSOUND.lnk','-fm=NSOUND.map','-fe=NSOUND.EXE',str(ROOT/'standalone/speaker_notice_diagnostic.c'),*objects],cwd=OUT,check=True)
    with (OUT/'NSOUND.lnk').open('a') as stream:stream.write('\noption packcode=0\n')
    subprocess.run(['wlink','@'+str(OUT/'NSOUND.lnk')],cwd=OUT,check=True)
    for name in ['standalone/build_speaker_notice.py','standalone/speaker_notice_diagnostic.c','src/ui/notice_speaker.h']:sources[name]=sha(ROOT/name)
    symbols={name:int(seg,16) for seg,off,name in re.findall(r'^\s*([0-9a-f]{4}):([0-9a-f]{4,8})[*+]?\s+(\w+)\s*$',(OUT/'NSOUND.map').read_text(),re.I|re.M)}
    assert len({symbols[n] for n in ('main_','_notice_show','_speaker_start')})==3
    report=dict(original_inputs=[],sources=sources,binary_sha256=sha(OUT/'NSOUND.EXE'),segments={n:symbols[n] for n in ('main_','_notice_show','_speaker_start')},scope=__doc__+' Actual bank crossings, window, speaker and synchronous outer longjmp cleanup. This does not publish PROGRAM sound/configuration or full application policy.')
    (OUT/'manifest.json').write_text(json.dumps(report,indent=2)+'\n');print('Built NSOUND.EXE',report['binary_sha256'])
if __name__=='__main__':main()
