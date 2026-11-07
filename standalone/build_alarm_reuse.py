#!/usr/bin/env python3
"""Build a marked ALARM VM-reuse diagnostic with all normal backend objects."""
import argparse
import json
from pathlib import Path
import build_aspect_process as builder
import build_aspect_runner as runner
from build_context_help import ROOT, sha


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--reference',type=Path,required=True)
    args=parser.parse_args();out=args.output.resolve();reference=args.reference.resolve()
    assert out.is_relative_to(ROOT/'build') and not out.exists()
    baseline=json.loads((reference/'manifest.json').read_text())
    assert not baseline['diagnostic_build'] and sha(reference/'ASPECT.EXE')==baseline['binary_sha256']
    out.mkdir()
    wrapper=out/'runner.c'
    wrapper.write_text('#include "'+str(ROOT/'standalone/alarm_reuse_driver.c')+'"\n')
    original=runner.subprocess.run;changed=[]
    def run(arguments,*positional,**kwargs):
        arguments=list(map(str,arguments))
        if Path(arguments[0]).name=='wcl' and '-fe=ASPECT.EXE' in arguments and Path(kwargs['cwd']).resolve()==out:
            old=str(ROOT/'src/aspect/runner.c');assert arguments.count(old)==1
            arguments[arguments.index(old)]=str(wrapper);changed.append(arguments)
        return original(arguments,*positional,**kwargs)
    runner.subprocess.run=run
    try:
        builder.main(parent_render=True,output=out,notice_bank=True,notice_sound=True,notice_input=True,
                     notice_help=True,help_resource=True,serial_bank=True,register_handoff=True,
                     custom_irq=True,snapshot_lease=True,defer_script_buffers=True,alarm_vm=True)
    finally:
        runner.subprocess.run=original
    assert len(changed)==1
    path=out/'manifest.json';manifest=json.loads(path.read_text())
    assert set(manifest['objects'])==set(baseline['objects'])
    assert all(digest==baseline['objects'][name] for name,digest in manifest['objects'].items() if name!='runner.o')
    assert manifest['objects']['runner.o']!=baseline['objects']['runner.o']
    for name in ('standalone/alarm_reuse_driver.c','standalone/build_alarm_reuse.py'):
        manifest['sources'][name]=sha(ROOT/name)
    manifest.update(diagnostic_build=True,diagnostic_alarm_reuse=True,main_source='standalone/alarm_reuse_driver.c',
                    diagnostic_compile_commands=changed,reference_binary_sha256=baseline['binary_sha256'],
                    scope=__doc__+' Only runner.o differs from the reference; actual VM/UART/renderer/ALARM/WHEN objects are exact. First script then RECOVER.ASX twice under one serial/render lifetime. Never package or deploy this diagnostic.')
    path.write_text(json.dumps(manifest,indent=2)+'\n');print('PASS marked reuse diagnostic',manifest['binary_sha256'])


if __name__=='__main__':main()
