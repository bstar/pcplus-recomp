#!/usr/bin/env python3
"""Compose real HOOK adoption, native ASPECT reset/handback and another HOOK."""
import argparse
import inspect
import json
from pathlib import Path
import sys
import test_hook_apply_dos as base

ROOT=base.ROOT
sys.path.insert(0,str(ROOT/'src/aspect'))
from compiler import compile_source


def reset_frame(raw):
    result=bytearray(raw);result[:20]=bytes(20)
    for index in range(10):result[20+index*81]=0
    return bytes(result)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--port',type=int,choices=[1,2],default=1);args=parser.parse_args()
    child=ROOT/'build/aspect-register-parent';manifest=json.loads((child/'manifest.json').read_text())
    assert base.sha(child/'ASPECT.EXE')==manifest['binary_sha256']
    source=inspect.getsource(base.main).replace('def main():','def run_roundtrip():',1)
    needle="    if args.mode==4:(out/'PCPLUS.XLT').write_bytes(bytes(range(256)))"
    replacement='''    child=ROOT/'build/aspect-register-parent'
    shutil.copyfile(child/'ASPECT.EXE',out/'ASPECT.EXE')
    shutil.copyfile(child/'LOCHELP.HLP',out/'LOCHELP.HLP')
    (out/'SCRIPT.ASX').write_bytes(compile_source('proc main\\ntransmit "SCRIPT^M"\\nendproc\\n'))
    definitions=bytearray((out/'ACTIONS.KEY').read_bytes())
    definitions[54:56]=struct.pack('<H',0)
    definitions[56:108]=b'SCRIPT.ASX\\0'.ljust(52,b'\\0')
    (out/'ACTIONS.KEY').write_bytes(definitions)
'''+needle
    assert source.count(needle)==1;source=source.replace(needle,replacement)
    needle='ADDKEY p700 a-1 p700 space p400 a-1 p700 space p400 a-1 p700 space p500 a-x'
    replacement='ADDKEY p700 a-1 p700 space p400 a-2 p1700 space p400 a-1 p700 space p400 a-1 p700 space p500 a-x'
    assert source.count(needle)==1;source=source.replace(needle,replacement)
    needle="assert before[1]==(after[0] if committed else before[0]),(args.mode,'whole returned frame')"
    assert source.count(needle)==1;source=source.replace(needle,"assert before[1]==reset_frame(after[0]),'HOOK->ASPECT native reset and retained string tails'")
    needle="assert epoch==(i if committed else i-1),(args.mode,epoch)"
    assert source.count(needle)==1;source=source.replace(needle,"assert epoch==i+1,('HOOK->ASPECT->HOOK epoch',i,epoch)")
    namespace=dict(base.__dict__);namespace.update(compile_source=compile_source,reset_frame=reset_frame)
    exec(compile(source,__file__,'exec'),namespace)
    original=sys.argv;sys.argv=[__file__,'--output',str(args.output),'--port',str(args.port)]
    try:namespace['run_roundtrip']()
    finally:sys.argv=original
    path=args.output.resolve()/'result.json';report=json.loads(path.read_text())
    for name,digest in manifest['sources'].items():
        assert name not in report['sources'] or report['sources'][name]==digest,name
        assert base.sha(ROOT/name)==digest,name
        report['sources'][name]=digest
    report['sources']['standalone/test_hook_aspect_roundtrip_dos.py']=base.sha(Path(__file__))
    report.update(combined_ASPECT=True,aspect_sha256=manifest['binary_sha256'],
        scope='Actual source-built8086 KEY kind2 HOOK -> KEY kind0 ASPECT -> HOOK. Nonzero accepted HOOK bank '
        'undergoes native per-script integer/first-string-byte reset with opaque tails retained and successful parent handback. '
        'Accepted epoch advances across both APIs; no synthetic descriptor or original executable. Script transmits but makes '
        'no integer assignments, so this does not claim a missing compiler bank-selection feature. Harness scheduling/oracle '
        'composition only; normal product is unchanged. Dummy serial, no physical/BBS acceptance.')
    path.write_text(json.dumps(report,indent=2)+'\n');print('PASS HOOK->ASPECT->HOOK',args.port)


if __name__=='__main__':main()
