#!/usr/bin/env python3
"""Verify the selectable-IRQ Special Edition package and exact branded BBS run."""
import argparse
import json
from pathlib import Path
import socket
import struct
import sys

from package_special_edition import ROOT,PRODUCTS,products_for,sha
from check_setup_model import image
sys.path.insert(0,str(ROOT/'lab/bbs'))
from enigma_key_stream_fixture import owned,pid
from check_enigma_upload_audit import replay,catalog


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('package','proof','start','splash','setup','candidate','output'):
        p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--bbs-label',required=True);args=p.parse_args()
    package=args.package.resolve();candidate=owned(args.candidate)
    assert pid(candidate)is None
    with socket.socket()as s:s.bind(('127.0.0.1',23234))
    def read(path):return json.loads(path.read_text())
    manifest=read(package/'manifest.json');sources={};artifacts={}
    def current(mapping):
        for name,digest in mapping.items():
            assert sha(ROOT/name)==digest,name
            sources[name]=digest
    def capture(folder):
        for path in folder.rglob('*'):
            if path.is_file():artifacts[str(path.relative_to(ROOT))]=sha(path)
    assert manifest['experimental_custom_irq']and not manifest['card_written']
    assert not manifest['contains_private_configuration']and manifest['original_inputs']==[]
    assert set(manifest['files'])==set(PRODUCTS)|{'START.BAT','SETUP.BAT','README.TXT','VERSION.TXT'}
    current(manifest['sources'])
    for leaf,digest in manifest['files'].items():assert sha(package/'PCPLUSSE'/leaf)==digest
    for leaf,folder in products_for(True).items():
        product=manifest['products'][leaf];assert product['folder']==folder
        base=ROOT/'build'/folder;m=read(base/'manifest.json')
        assert product['manifest_sha256']==sha(base/'manifest.json')
        assert product['binary_sha256']==m['binary_sha256']==sha(base/leaf)==manifest['files'][leaf]
        if leaf in ('TERMINAL.EXE','ASPECT.EXE','PRMEDIT.EXE'):assert m['experimental_custom_irq']
    proof_path=args.proof.resolve();proof=read(proof_path/'result.json')
    assert proof['passed']and proof['original_inputs']==[]and proof['sources']==manifest['sources']
    assert proof['ancestor_git_unavailable']and proof['source_base_commit']==manifest['source_base_commit']
    assert proof['source_files']==len(manifest['sources'])and proof['files']==manifest['files']
    assert proof['checker_sha256']==sha(ROOT/'standalone/prove_special_package_source.py')
    assert proof['package_manifest_sha256']==sha(package/'manifest.json')
    assert proof['build_log_sha256']==sha(proof_path/'build.log')
    prior=ROOT/'build/special-irq-source-01'
    ambient=read(prior/'ambient-git-negative.json')
    assert not ambient['passed']and ambient['expected_rejection']and ambient['exit_code']!=0
    assert ambient['producer_sha256']==sha(prior/'source/standalone/package_special_edition.py')
    assert 'not a git repository'in(prior/'ambient-git-negative.log').read_text()
    assert read(ROOT/'build/special-irq-package-01/manifest.json')['files']==manifest['files']
    for leaf,digest in manifest['files'].items():assert sha(proof_path/'source/build/package/PCPLUSSE'/leaf)==digest
    for name,digest in manifest['sources'].items():assert sha(proof_path/'source'/name)==digest
    cases=[]
    for name,irq in [('start',5),('splash',7),('setup',7)]:
        folder=getattr(args,name).resolve();report=read(folder/'result.json')
        assert report['passed']and report['irq']==irq and report['cpu']=='8086'
        assert report['package_files']==manifest['files']and report['package_manifest_sha256']==sha(package/'manifest.json')
        assert report['launcher']==('SETUP'if name=='setup'else'START')
        assert report['resident_observer']==(name!='start')
        current(report['sources'])
        for leaf,digest in report['artifacts'].items():assert sha(folder/leaf)==digest
        drive=folder/'drive';app=drive/'PCPLUSSE'
        assert (drive/'RETURN.TXT').is_file()and not(drive/'FAIL.TXT').exists()
        assert (drive/'BEFORE.BIN').read_bytes()==(drive/'AFTER.BIN').read_bytes()
        assert len((drive/'BEFORE.BIN').read_bytes())==42
        raw=bytearray(image());struct.pack_into('<H',raw,0,1)
        struct.pack_into('<HH',raw,0x4e4,8,4);struct.pack_into('<H',raw,0x186,irq)
        assert(app/'PCPLUS.PRM').read_bytes()==raw
        assert(app/'PCPLUS.DIR').read_bytes()==b'PRIVATE-DIRECTORY-PRESERVATION-SENTINEL'
        assert(app/'PCPLUS.XLT').read_bytes()==bytes(range(256))
        env=(drive/'ENV.TXT').read_bytes().upper().splitlines()
        assert b'PCPLUS=C:\\ORIGINAL'in env and not any(line.startswith(b'LOC_PCPLUS=')for line in env)
        if name=='start':assert(app/'RESULT.BIN').read_bytes()==b'SPECIAL-COMPILED'
        else:
            video=(drive/'SPLASH.BIN').read_bytes();at=(9*80+27)*2
            assert len(video)==8000 and video[at:at+38:2]==b'LoC SPECIAL EDITION'
            assert video[at+1:at+38:2]==b'\x5f'*19
        for leaf,digest in manifest['files'].items():assert sha(app/leaf)==digest
        cases.append(dict(workflow=name,irq=irq,checks=report['checks']));capture(folder)
    bbs=ROOT/'build/bbs-lab/results/enigma'/args.bbs_label
    result=read(bbs/'upload-checks.json');negative=read(bbs/'upload-audit-negative-checks.json')
    assert result['passed']and all(result['checks'].values())and not result['errors']
    assert result['cpu']=='8086'and result['irq']==7 and result['compact_observer']and result['splash_key_sent']
    config=(bbs/'dosbox.conf').read_text()
    assert 'cputype=8086\n'in config and 'serial2=nullmodem irq:7 'in config
    assert struct.unpack_from('<H',(bbs/'TEST.PRM').read_bytes(),0x186)[0]==7
    aliases={name:ROOT/'lab/bbs'/leaf for name,leaf in dict(runner='enigma_upload_dos.py',harness='test_dos.py',
        observer='test_transfer_dos.py',auditor='audit_zmodem.py',time_auditor='check_enigma_upload_audit.py',
        form_observer='enigma_upload_watch.py',observer_base='zmodem_label_watch.py').items()}
    for key,product in result['products'].items():
        leaf=Path(key).name;assert leaf in manifest['products']
        path=ROOT/'build'/manifest['products'][leaf]['folder']/leaf
        assert product==dict(path=str(path.relative_to(ROOT)),sha256=manifest['files'][leaf])
        aliases[key]=path
    aliases['login']=bbs/'program/LOGON.ASP'
    fixture=read(candidate/'search-instance.json')
    for name,digest in result['input_hashes'].items():
        if name in aliases:path=aliases[name]
        elif name.startswith('staged/'):path=bbs/'program'/Path(name).name
        elif name in fixture['fixture_inputs']or name in fixture['source_modules']:path=candidate/name
        else:path=ROOT/name
        assert sha(path)==digest,name;sources[str(path.relative_to(ROOT))]=digest
    expected={path.name:path.read_bytes()for path in(bbs/'SEND').iterdir()}
    assert set(expected)=={'PCUP01.BIN','EMPTY.BIN'}and len(expected['PCUP01.BIN'])==65539 and not expected['EMPTY.BIN']
    protocol=replay((bbs/'serial-received.bin').read_bytes(),(bbs/'display.bin').read_bytes(),read(bbs/'trace.json'),expected,True)
    catalog(read(bbs/'server-upload-metadata.json'),expected,candidate,result['received_date_bounds_ns'])
    for file in protocol['files']:file.pop('source',None)
    assert negative['passed']and len(negative['cases'])==14 and all(c['rejected']for c in negative['cases'])
    assert negative['checker_sha256']==sha(ROOT/'lab/bbs/check_enigma_upload_audit.py')
    for name,digest in negative['capture_hashes'].items():assert sha(bbs/name)==digest
    assert(bbs/'BEFORE.BIN').read_bytes()==(bbs/'AFTER.BIN').read_bytes()
    assert len((bbs/'BEFORE.BIN').read_bytes())==42
    decoder=read(candidate.parent/'report.json');assert decoder['passed']and decoder['stock_client_unchanged']
    assert all(test['exit_code']==0 for test in decoder['tests'])
    assert sha(candidate/'core/client.js')==decoder['candidate_client_sha256']
    assert sha(candidate/'core/key_stream.js')==decoder['candidate_key_stream_sha256']
    capture(package);capture(bbs)
    for path in [proof_path/'result.json',proof_path/'build.log',candidate.parent/'report.json',candidate/'instance.json',
                 prior/'ambient-git-negative.json',prior/'ambient-git-negative.log',prior/'source/standalone/package_special_edition.py']:
        artifacts[str(path.relative_to(ROOT))]=sha(path)
    sources[str(Path(__file__).relative_to(ROOT))]=sha(Path(__file__))
    receipt=dict(passed=True,compatibility_complete=False,package_files=manifest['files'],products=manifest['products'],
                 source_files=proof['source_files'],original_inputs=[],dos_cases=cases,bbs_checks=result['checks'],
                 source_base_commit=manifest['source_base_commit'],ancestor_git_unavailable=True,ambient_git_failure=ambient,
                 protocol=protocol,negative_cases=negative['cases'],sources=sources,artifacts=artifacts,
                 temporary_server_stopped=True,card_written=False,
                 scope='Matching branded selectable-IRQ package: nine-file empty-tree reproduction, DOS8086 '
                 'START/nested compile on IRQ5, splash/SETUP cancel on IRQ7, exact branded terminal source login '
                 'and binary/empty ZMODEM upload plus NFO on isolated framed ENiGMA. No card/LAN deployment, '
                 'physical modem, branded reconnect/load or full application acceptance.')
    args.output.write_text(json.dumps(receipt,indent=2)+'\n')
    print('PASS IRQ Special Edition: source reproduction, launchers/splash and branded BBS upload')


if __name__=='__main__':main()
