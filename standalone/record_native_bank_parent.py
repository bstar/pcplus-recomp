#!/usr/bin/env python3
"""Record cold-parent evidence while preserving the failed deployment gate."""
import argparse
import hashlib
import json
from pathlib import Path
from prove_native_bank_parent_source import ROOT,SPECIAL

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--proof',type=Path,required=True);p.add_argument('--control',type=Path,required=True)
    p.add_argument('--failed',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    base=a.proof.resolve();proof=load(base/'result.json');assert proof['passed']and not proof['original_inputs']
    custody={}
    def bind(path):
        path=path.resolve();assert path.is_relative_to(ROOT)
        custody[str(path.relative_to(ROOT))]=sha(path)
    def sources(mapping):
        for name,digest in mapping.items():assert sha(ROOT/name)==digest,name
    sources(proof['sources']);bind(base/'result.json')
    for label,digest in proof['logs'].items():
        path=base/(label+'.log');assert sha(path)==digest;bind(path)
    models={}
    for folder,digest in proof['ownership_reports'].items():
        path=base/'source/build'/folder/'native-bank-parent-checks.json';assert sha(path)==digest
        report=load(path);assert report['passed']and report['workspace_owner_refusals']==11
        assert len(report['malformed_layout_refusals'])==4
        sources(report['sources']);assert sha(ROOT/'standalone/check_native_bank_parent.py')==report['checker_sha256']
        models[folder]={k:report[k]for k in ['binary_sha256','workspace_owner_refusals','malformed_layout_refusals','viewer_rebuilt_after_native_use','memory_layout']}
        bind(path)
    dos_path=base/'source/build/far-storage-dos/fresh-native-bank/checks.json';dos=load(dos_path)
    assert sha(dos_path)==proof['actual_DOS_child_report_sha256']and dos['passed']and all(dos['checks'].values());bind(dos_path)
    assert dos['binary_sha256']==proof['products'][SPECIAL]
    nested={}
    for kind,folder in [('control',a.control.resolve()),('experimental',a.failed.resolve())]:
        assert folder.is_relative_to(ROOT/'build');path=folder/'result.json';report=load(path)
        sources(report['sources']);bind(path)
        for name,digest in report['artifacts'].items():
            artifact=ROOT/name;assert sha(artifact)==digest,name;bind(artifact)
        assert report['port']==2 and report['case']=='explicit'and report['splash_key_sent']
        checks=report['checks'];assert all(checks[k]for k in ['connection_passed','post_child_parser','PRM_unchanged','hardware_restored'])
        if kind=='control':assert report['passed']and all(checks.values())
        else:
            assert not report['passed']and not checks['expected_script_output']and not checks['exact_LOGON.ASX']
            assert report['products']['TERMINAL.EXE']==proof['products'][SPECIAL]
            screen=ROOT/'build/connection-dos'/report['connection']['case']/'screen.txt'
            assert 'out of memory (error 8, opcode 00, step 0)'in screen.read_text()
        nested[kind]=dict(products=report['products'],checks=checks,passed=report['passed'])
    assert nested['control']['products']['ASPECT.EXE']==nested['experimental']['products']['ASPECT.EXE']
    assert nested['control']['products']['ASPCOMP.EXE']==nested['experimental']['products']['ASPCOMP.EXE']
    controls={}
    for folder,leaf,expected in [('reset-bank','BANK.EXE','9551b816d1f6a6fe921205236324ff4f4dae3bb42ef704dfe71750e24c690557'),
        ('terminal-reset','RESET.EXE','8bdd8c62707ef4c1761c734a9481cad18be991aeed3cadd6194c527f14408e32'),
        ('terminal-reset-viewport','RESET.EXE','066101b9dd744d9dec029ac2160decd0a3c6505c3d4f1c787e651d4c45fa5e92')]:
        product=ROOT/'build'/folder/leaf;assert sha(product)==expected;controls[folder]=expected;bind(product)
    data=dict(status='experimental; nested compiler admission failed',accepted_for_deployment=False,
        original_inputs=[],source_only_products=proof['products'],source_files=proof['source_files'],sources=proof['sources'],
        ownership=models,DOS_child_checks=dos['checks'],nested_compiler=nested,unchanged_component_controls=controls,
        artifacts=custody,recorder_sha256=sha(Path(__file__)),
        limitations=['Cold native reset only; live projection/commit/rollback and normal width requests remain unbound.',
            'Nested compilation fails in the optional branded parent; same-run control succeeds.',
            'DOS child retention is not proof of sufficient nested-execution memory.',
            'No new BBS or physical hardware acceptance; staged package and card not updated.'])
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(data,indent=2)+'\n')
    print('RECORDED experimental native parent: ownership/retention/source reproduction pass; nested compiler gate FAIL; deployment refused')
if __name__=='__main__':main()
