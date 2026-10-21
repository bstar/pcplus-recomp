#!/usr/bin/env python3
"""Add only existing PCM-export plumbing to the accepted carrier runtime."""
import argparse
import gzip
import json
from pathlib import Path
import shutil
from synthmodem_vm_control import ROOT,sha,records,archive
from synthmodem_carrier_runtime import validate as validate_carrier

LEDGER=ROOT/'docs/validation/synthmodem-carrier-trace-runtime.json'
REFERENCE=ROOT/'build/bbs-lab/synthmodem-carrier-runtime-01/runtime'


def validate(runtime):
    accepted=json.loads(LEDGER.read_text());assert accepted['passed']
    expected=accepted['files']
    assert {str(p.relative_to(runtime)) for p in runtime.rglob('*') if p.is_file()}==set(expected)
    for name,digest in expected.items():assert sha(runtime/name)==digest,name
    return {str(runtime/name):digest for name,digest in expected.items()}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    out=parser.parse_args().output.resolve();assert out.is_relative_to(ROOT/'build')
    inputs=validate_carrier(REFERENCE)
    names=['lab/bbs/synthmodem_carrier_trace_runtime.py','lab/bbs/synthmodem_carrier_runtime.py',
           'lab/bbs/synthmodem_vm_control.py','lab/bbs/receive_trace_export.sh',
           'lab/bbs/qemu_trace_wrapper.py','docs/validation/synthmodem-carrier-runtime.json']
    frozen={name:sha(ROOT/name) for name in names}
    out.mkdir(parents=True,exist_ok=False);runtime=out/'runtime';shutil.copytree(REFERENCE,runtime)
    original=records(gzip.decompress((REFERENCE/'candidate.cpio.gz').read_bytes()))
    entries=[];changed=[]
    for name,fields,body in original:
        replacement=body
        if name=='etc/init.d/S99modem-pjsip':
            marker=b'    echo "S99modem-pjsip: starting backend B"'
            assert body.count(marker)==1
            replacement=body.replace(marker,b'    /bin/sh /lab-trace-export.sh &\n'+marker)
        if replacement!=body:changed.append(name)
        entries.append((name,fields,replacement))
    assert changed==['etc/init.d/S99modem-pjsip']
    export=(ROOT/'lab/bbs/receive_trace_export.sh').read_bytes()
    assert 'lab-trace-export.sh' not in {name for name,_,_ in original}
    inode=max(fields[0] for _,fields,_ in original)+1
    entries.append(('lab-trace-export.sh',[inode,0o100755,0,0,1,0,len(export),0,0,0,0,0,0],export))
    entries.append(('TRAILER!!!',[0]*13,b''))
    image=runtime/'candidate.cpio.gz';image.write_bytes(gzip.compress(archive(entries),mtime=0))
    rebuilt=records(gzip.decompress(image.read_bytes()));assert len(rebuilt)==len(original)+1
    for (name,fields,body),(nn,ff,bb) in zip(original,rebuilt):
        assert name==nn and fields[:6]+fields[7:]==ff[:6]+ff[7:]
        assert name in changed or body==bb,name
    assert rebuilt[-1][0]=='lab-trace-export.sh' and rebuilt[-1][2]==export
    changed_files=[str(Path(name).relative_to(REFERENCE)) for name,h in inputs.items()
                   if sha(runtime/Path(name).relative_to(REFERENCE))!=h]
    assert changed_files==['candidate.cpio.gz']
    assert all(sha(Path(name))==h for name,h in inputs.items())
    assert all(sha(ROOT/name)==h for name,h in frozen.items())
    result={'passed':True,'runtime_inputs':inputs,'frozen_inputs':frozen,
            'changed_files':changed_files,'changed_archive_entries':changed,'added_archive_entries':['lab-trace-export.sh'],
            'files':{str(p.relative_to(runtime)):sha(p) for p in runtime.rglob('*') if p.is_file()},
            'scope':'Diagnostic PCM-export daemon/init hook only. All actual carrier-runtime modem binaries, kernel, backend and other files remain byte-identical. Separate export chardev supplied by the existing QEMU wrapper; no installed service or runtime acceptance.'}
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'passed':True,'runtime':str(runtime),'changed_files':changed_files},indent=2))


if __name__=='__main__':main()
