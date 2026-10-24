#!/usr/bin/env python3
"""Rebuild the experimental parent without originals and replay its ownership checks.

This deliberately does not certify nested compiler admission: the optional
parent currently fails that separate conventional-memory acceptance gate.
"""
import argparse
import ast
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
from build_guarded_helper import FLAGS

ROOT=Path(__file__).resolve().parents[1]
SPECIAL='terminal-directory-keys-process-bank-session-capture-projection-bound-registers-controls-return-execute-modem-input-apply-lookup-guarded-traps-custom-irq-special-native-bank'
SPECIAL_FLAGS=FLAGS+['--hook-lookup','--exit-guard','--traps','--custom-irq','--special-edition','--native-reset-bank']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path);a=p.parse_args()
    out=(a.output or ROOT/'build/native-bank-parent-source'/datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S-%f')).resolve()
    assert out.is_relative_to(ROOT/'build')and not out.exists();out.mkdir(parents=True)
    products=[('terminal',[]),('terminal-native-bank',['--native-reset-bank']),(SPECIAL,SPECIAL_FLAGS)]
    sources={};expected={}
    for folder,flags in products:
        m=json.loads((ROOT/'build'/folder/'manifest.json').read_text())
        assert sha(ROOT/'build'/folder/'TERMINAL.EXE')==m['binary_sha256']
        expected[folder]=m['binary_sha256']
        for name,digest in m['sources'].items():
            assert sha(ROOT/name)==digest,name
            assert name not in sources or sources[name]==digest,name
            sources[name]=digest
    # Follow local Python imports used by the hardware model and DOS fixture;
    # every copied helper is source, never a cached object or product binary.
    pending=[Path(__file__),ROOT/'standalone/check_native_bank_parent.py',ROOT/'standalone/test_far_storage_dos.py']
    visited=set()
    while pending:
        path=pending.pop().resolve()
        if path in visited:continue
        visited.add(path);sources[str(path.relative_to(ROOT))]=sha(path)
        tree=ast.parse(path.read_text())
        for node in ast.walk(tree):
            names=[x.name for x in node.names]if isinstance(node,ast.Import)else[node.module]if isinstance(node,ast.ImportFrom)else[]
            for name in names:
                if not name:continue
                local=ROOT/'standalone'/(name.split('.')[0]+'.py')
                if local.is_file():pending.append(local)
    for name in ['standalone/far_storage_child.asm','nix/flake.nix','nix/flake.lock','tools/dev']:
        sources[name]=sha(ROOT/name)
    fresh=out/'source'
    for name,digest in sources.items():
        path=Path(name);assert not path.is_absolute()and'..'not in path.parts
        assert path.parts[0]not in('build','analysis','original','originals','install')
        assert path.suffix.lower()not in('.exe','.obj','.img','.o','.prm','.dir','.xlt')
        target=fresh/path;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/path,target)
    assert not(fresh/'build').exists()
    logs={};reports={}
    def run(label,argv):
        log=out/(label+'.log')
        with log.open('w')as stream:
            subprocess.run([sys.executable,*argv],cwd=fresh,stdout=stream,stderr=stream,check=True,timeout=120)
        logs[label]=sha(log)
    for folder,flags in products:
        run('build-'+folder,['standalone/build_terminal.py',*flags])
        binary=fresh/'build'/folder/'TERMINAL.EXE';assert sha(binary)==expected[folder],folder
        if flags:
            run('check-'+folder,['standalone/check_native_bank_parent.py','--terminal',str(binary)])
            report=binary.parent/'native-bank-parent-checks.json';data=json.loads(report.read_text())
            assert data['passed']and data['workspace_owner_refusals']==11 and len(data['malformed_layout_refusals'])==4
            reports[folder]=sha(report)
    assert expected['terminal']=='01f55dfbf5385136931c96700be3173cf8594be1c17677e9852fb0f1d025e447'
    # DOSBox-X's DOS path adapter can abort on deeply nested host paths. Use
    # a short owned product directory, preserving the exact rebuilt bytes and
    # metadata; this copies no preexisting product into the fresh source tree.
    short=fresh/'build/dos-parent';short.mkdir()
    for leaf in ['TERMINAL.EXE','terminal.map','manifest.json']:
        shutil.copyfile(fresh/'build'/SPECIAL/leaf,short/leaf)
    assert sha(short/'TERMINAL.EXE')==expected[SPECIAL]
    run('DOS-child',['standalone/test_far_storage_dos.py','--binary',str(short/'TERMINAL.EXE'),'--label','fresh-native-bank'])
    dos=fresh/'build/far-storage-dos/fresh-native-bank/checks.json'
    data=json.loads(dos.read_text());assert data['passed']and all(data['checks'].values())
    for name,digest in sources.items():assert sha(ROOT/name)==sha(fresh/name)==digest,name
    result=dict(passed=True,sources=sources,source_files=len(sources),products=expected,ownership_reports=reports,
        actual_DOS_child_report_sha256=sha(dos),logs=logs,checker_sha256=sha(Path(__file__)),original_inputs=[],
        scope=__doc__,limitations=['Nested compiler admission remains failed for the experimental branded parent.',
            'Cold native calls only; no live width transaction, rollback, peer activation or BBS acceptance.'])
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print('PASS experimental native parent: three exact source-only products, ownership models and DOS child; nested compiler gate remains FAILED')
if __name__=='__main__':main()
