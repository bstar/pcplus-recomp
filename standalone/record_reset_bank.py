#!/usr/bin/env python3
"""Seal private native-reset context, real IRQ evidence and source reproduction."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

ROOT=Path(__file__).resolve().parents[1]


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--dos',type=Path,required=True);p.add_argument('--proof',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    dos=args.dos.resolve();proof=args.proof.resolve()
    assert dos.is_relative_to(ROOT/'build')and proof.is_relative_to(ROOT/'build')
    def read(path):return json.loads(path.read_text())
    base=ROOT/'build/reset-bank';manifest=read(base/'manifest.json');binary=sha(base/'BANK.EXE')
    assert binary==manifest['binary_sha256'];sources=dict(manifest['sources']);artifacts={}
    for name,digest in sources.items():assert sha(ROOT/name)==digest,name
    reports=[]
    for folder in [dos,proof/'source/build/reset-bank-dos/fresh']:
        report=read(folder/'checks.json');assert report['passed']and all(report['checks'].values())and not report['events']
        assert report['binary_sha256']==binary==sha(folder/'BANK.EXE')
        assert len(report['checks'])==18 and report['groups']==manifest['groups']
        raw=(folder/'BANK.BIN').read_bytes();assert len(raw)==32
        words=list(struct.unpack('<16H',raw));assert words==report['observation']
        assert words[0]==words[1]and words[10]==words[11]and words[0]!=words[10]
        assert words[2]==manifest['context_layout']['stack_top_offset']-2
        assert words[12]==manifest['context_layout']['root_stack_top_offset']
        assert words[4:10]==[132,0,0,0,0,512]and words[14:]==[20,7]
        assert(folder/'echo.bin').read_bytes()==bytes(range(256))*2
        assert(folder/'BEFORE.BIN').read_bytes()==(folder/'AFTER.BIN').read_bytes()
        assert len((folder/'BEFORE.BIN').read_bytes())==42
        for name,digest in report['sources'].items():
            assert sha(folder/'inputs'/name)==sha(ROOT/name)==digest,name;sources[name]=digest
        for path in folder.rglob('*'):
            if path.is_file():artifacts[str(path.relative_to(ROOT))]=sha(path)
        reports.append(report)
    reproduction=read(proof/'result.json')
    assert reproduction['passed']and reproduction['actual_DOS_passed']and reproduction['binary_sha256']==binary
    assert reproduction['source_files']==len(reproduction['sources'])
    assert reproduction['checker_sha256']==sha(ROOT/'standalone/prove_reset_bank_source.py')
    for name,digest in reproduction['sources'].items():assert sha(ROOT/name)==sha(proof/'source'/name)==digest,name;sources[name]=digest
    assert sha(proof/'source/build/reset-bank/BANK.EXE')==binary
    assert sha(proof/'build.log')==reproduction['build_log_sha256']and sha(proof/'DOS.log')==reproduction['DOS_log_sha256']
    assert sha(proof/'source/build/reset-bank-dos/fresh/checks.json')==reproduction['DOS_report_sha256']
    assert reproduction['controls']=={'terminal-reset':'8bdd8c62707ef4c1761c734a9481cad18be991aeed3cadd6194c527f14408e32',
        'terminal-reset-viewport':'066101b9dd744d9dec029ac2160decd0a3c6505c3d4f1c787e651d4c45fa5e92'}
    for kind,digest in reproduction['controls'].items():assert sha(ROOT/'build'/kind/'RESET.EXE')==sha(proof/'source/build'/kind/'RESET.EXE')==digest
    failed_dos=ROOT/'build/reset-bank-dos-01';failed=read(failed_dos/'checks.json')
    assert not failed['passed']and failed['checks']['DOS_normal_exit']and failed['checks']['every_binary_byte_received_and_echoed']
    assert {key for key,value in failed['checks'].items()if not value}=={'private_stack_bounded'}
    assert '0xd600<=n_sp<0xe600'in(failed_dos/'inputs/standalone/test_reset_bank_dos.py').read_text()
    assert sha(failed_dos/'BANK.EXE')==failed['binary_sha256']
    failed_source=ROOT/'build/reset-bank-source-01'
    assert not(failed_source/'source/reconstruction/uart/layout.inc').exists()
    assert 'unable to open include file `layout.inc\x27'in(failed_source/'build.log').read_text()
    assert not(failed_source/'source/build/reset-bank/BANK.EXE').exists()
    for path in [base/'BANK.EXE',base/'bank.map',base/'manifest.json',proof/'result.json',proof/'build.log',proof/'DOS.log',
        failed_dos/'checks.json',failed_dos/'BANK.BIN',failed_dos/'BANK.EXE',
        failed_dos/'inputs/standalone/test_reset_bank_dos.py',failed_source/'build.log',failed_source/'source/standalone/build_reset_bank.py']:
        artifacts[str(path.relative_to(ROOT))]=sha(path)
    for path in [Path(__file__),ROOT/'standalone/prove_reset_bank_source.py',ROOT/'Makefile']:sources[str(path.relative_to(ROOT))]=sha(path)
    receipt=dict(passed=True,compatibility_complete=False,binary_sha256=binary,checks=reports[0]['checks'],
        groups=manifest['groups'],context_layout=manifest['context_layout'],source_files=reproduction['source_files'],
        fresh_DOS_repeated=True,controls=reproduction['controls'],sources=sources,artifacts=artifacts,card_written=False,
        retained_failures=['Incorrect fixed stack-origin observation; real driver/IRQ workflow passed but report remained failed.',
            'Fresh build missing an undeclared UART layout include; corrected source closure reproduces exactly.'],
        scope='Separate native reset DS=SS image/stack and real root UART IRQ:512 binary bytes arrive while private stack is active;20 checked entries preserve caller registers/FLAGS, typed abandonment/retry and private reentry refusal pass, IF/DF/foreignDS refusals and root canary/hardware restoration pass. Selected native24-row hidden-status soft reset with static diagnostic shadow. Full live projection/commit, namespace/retained-parent/child memory admission, display rollback, full profile/error/UI/BBS and physical acceptance remain open; interactive package/card unchanged.')
    args.output.write_text(json.dumps(receipt,indent=2)+'\n')
    print('PASS native reset private context: realIRQ, exact source/controls, frozen failures and freshDOS replay')


if __name__=='__main__':main()
