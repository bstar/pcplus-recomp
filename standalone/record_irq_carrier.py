#!/usr/bin/env python3
"""Seal current IRQ link-loss/redial evidence with independent capture replay."""
import argparse
import json
from pathlib import Path
import socket
import struct
import sys

from build_guarded_helper import ROOT,LOOKUP
from package_special_edition import sha
sys.path.insert(0,str(ROOT/'lab/bbs'))
from product_inputs import select_product
from enigma_key_stream_fixture import owned,pid
from check_enigma_carrier_audit import replay
from directory_test_support import accounting_check
from directory_fixtures import directory


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--candidate',type=Path,required=True);p.add_argument('--label',required=True)
    p.add_argument('--relay-label',required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--package',type=Path,help='Verify the exact branded selectable-IRQ package instead of the ordinary IRQ parent')
    args=p.parse_args();candidate=owned(args.candidate)
    assert pid(candidate)is None
    with socket.socket()as check:check.bind(('127.0.0.1',23234))
    folder=ROOT/'build/bbs-lab/results/enigma'/args.label
    def read(name):return json.loads((folder/name).read_text())
    result=read('carrier-checks.json');negative=read('carrier-current-audit-negative-checks.json')
    assert result['passed']and all(result['checks'].values())and not result['errors']
    assert result['cpu']=='8086'and result['irq']==5
    package=None
    if args.package:
        package=args.package.resolve();assert package.is_relative_to(ROOT/'build')
        package_manifest=json.loads((package/'manifest.json').read_text())
        assert package_manifest['experimental_custom_irq'] and not package_manifest['contains_private_configuration']
        assert not package_manifest['original_inputs'] and result['splash_key_sent'] is True
        assert 'ADDKEY p900 enter p85000 ' in (folder/'dosbox.conf').read_text()
        assert set(p.name for p in(package/'PCPLUSSE').iterdir())==set(package_manifest['files'])
        for name,digest in package_manifest['files'].items():assert sha(package/'PCPLUSSE'/name)==digest
    products={'terminal/TERMINAL.EXE':ROOT/'build'/(LOOKUP+'-custom-irq'+('-special'if package else''))/'TERMINAL.EXE',
              'aspect-runner/ASPECT.EXE':ROOT/'build/aspect-register-parent-custom-irq/ASPECT.EXE',
              'aspect-compiler-dos/ASPCOMP.EXE':ROOT/'build/aspect-compiler-dos/ASPCOMP.EXE'}
    sources={}
    for key,path in products.items():
        binary,inputs=select_product(path,path.name)
        assert result['products'][key]==dict(path=str(binary.relative_to(ROOT)),sha256=sha(binary))
        assert sha(folder/'program'/binary.name)==sha(binary)
        if package:
            assert sha(binary)==package_manifest['files'][binary.name]
            assert sha(binary.parent/'manifest.json')==package_manifest['products'][binary.name]['manifest_sha256']
        for path in inputs:sources[str(path.relative_to(ROOT))]=sha(path)
    assert set(result['input_paths'])==set(result['input_hashes'])
    for name,digest in result['input_hashes'].items():
        path=ROOT/result['input_paths'][name]
        assert path.resolve().is_relative_to(ROOT)and sha(path)==digest,name
        sources[str(path.relative_to(ROOT))]=digest
    config=(folder/'dosbox.conf').read_text()
    assert 'cputype=8086\n'in config and 'serial2=modem irq:5 listenport:0\n'in config
    assert 'ASPCOMP LOGON.ASP LOGON.ASX'in config
    assert config.index('ASPCOMP LOGON.ASP')<config.index('D:\\SNAP B')
    prm=(folder/'TEST.PRM').read_bytes()
    assert struct.unpack_from('<H',prm,0x186)[0]==5 and prm[0x18:0x20]==b'AT&K3^M\0'
    assert struct.unpack_from('<HH',prm,0x4e4)==(8,4)
    assert (folder/'BEFORE.BIN').read_bytes()==(folder/'AFTER.BIN').read_bytes()
    assert len((folder/'BEFORE.BIN').read_bytes())==42
    notice_bytes=(folder/'LABELS.BIN').read_bytes()
    assert len(notice_bytes)==2566
    magic,count,ticks=struct.unpack_from('<3H',notice_bytes)
    assert magic==0x4e5a and 0<count<=16 and ticks>0
    notices=[notice_bytes[6+i*160:6+(i+1)*160:2].decode('cp437')for i in range(count)]
    assert notices==result['notices']
    rows=[json.loads(line)for line in(folder/'server-session.jsonl').read_text().splitlines()if line.strip()]
    authenticated={row['sessionId']for row in rows if row.get('msg')=='User "loclab" successfully logged in'}
    assert len(authenticated)==2
    final_book=(folder/'TEST.DIR').read_bytes();entry=250+2*114
    dial_target=final_book[entry+25:entry+46].split(b'\0',1)[0]
    assert dial_target.startswith(b'127.0.0.1:')and dial_target[10:].isdigit()
    initial_book=bytearray(directory(entry=3,target=dial_target,port=2,baud=5))
    initial_book[entry+52:entry+61]=b'LOGON\0\0\0\0'
    assert accounting_check(bytes(initial_book),final_book,3,2)
    fixture=json.loads((candidate/'search-instance.json').read_text())
    decoder=json.loads((candidate.parent/'report.json').read_text())
    assert decoder['passed']and decoder['stock_client_unchanged']
    assert all(test['exit_code']==0 for test in decoder['tests'])
    assert fixture['upstream_revision']==decoder['upstream_revision']=='237cd9743d6978a940dd66db0e78f6ab8ccd3e37'
    assert sha(candidate/'core/client.js')==decoder['candidate_client_sha256']
    assert sha(candidate/'core/key_stream.js')==decoder['candidate_key_stream_sha256']
    archive=fixture['archives'][1];source=candidate/'file_base/pcplus_games'/archive['name']
    assert sha(source)==archive['sha256']
    received=list((folder/'RECV').iterdir());assert len(received)==1
    assert received[0].read_bytes()==source.read_bytes()
    sessions=[read(f'connection-{n}/session.json')for n in (1,2)]
    assert all(s['done']and not s['errors']for s in sessions)
    assert sessions[0]['interrupted']and not sessions[1]['interrupted']
    # Every recorded byte belongs to one contiguous decoded trace range.
    for number in (1,2):
        trace=read(f'connection-{number}/trace.json')
        for direction,leaf in [('bbs','display.bin'),('dos','serial-received.bin')]:
            offset=0
            for event in(e for e in trace if e['direction']==direction):
                assert event['offset']==offset and event['size']>0
                offset+=event['size']
            assert offset==(folder/f'connection-{number}'/leaf).stat().st_size
    protocol=replay((folder/'connection-1/display.bin').read_bytes(),(folder/'connection-2/display.bin').read_bytes(),
                    (folder/'connection-2/serial-received.bin').read_bytes(),read('connection-2/trace.json'),
                    archive['name'].upper(),source.read_bytes(),result['snapshots'],result['notices'])
    for item in protocol['files']:item.pop('source',None)
    assert negative['passed']and len(negative['cases'])==13 and all(c['rejected']for c in negative['cases'])
    for field,path in [('checker_sha256','lab/bbs/check_enigma_carrier_current_audit.py'),
                       ('positive_oracle_sha256','lab/bbs/check_enigma_carrier_audit.py'),
                       ('auditor_sha256','lab/bbs/audit_zmodem.py')]:
        assert negative[field]==sha(ROOT/path);sources[path]=negative[field]
    for name,digest in negative['capture_hashes'].items():assert sha(folder/name)==digest
    relay_path=ROOT/'build/bbs-lab/carrier-relay'/args.relay_label/'checks.json'
    relay=json.loads(relay_path.read_text());assert relay['passed']and all(relay['checks'].values())
    for name,digest in relay['sources'].items():assert sha(ROOT/name)==digest;sources[name]=digest
    artifacts={str(path.relative_to(ROOT)):sha(path)for path in folder.rglob('*')if path.is_file()}
    for path in [relay_path,candidate.parent/'report.json',candidate/'instance.json',candidate/'search-instance.json',source]:
        artifacts[str(path.relative_to(ROOT))]=sha(path)
    sources[str(Path(__file__).relative_to(ROOT))]=sha(Path(__file__))
    if package:
        for path in [package/'manifest.json',*(package/'PCPLUSSE').iterdir()]:
            artifacts[str(path.relative_to(ROOT))]=sha(path)
    receipt=dict(passed=True,compatibility_complete=False,products=result['products'],checks=result['checks'],
                 protocol=protocol,snapshots=result['snapshots'],notices=result['notices'],negative=negative,
                 relay_checks=relay['checks'],sources=sources,artifacts=artifacts,temporary_server_stopped=True,
                 server_upstream_revision=decoder['upstream_revision'],
                 scope='One DOS8086 process with current IRQ5 parent/interpreter, built-in modem DCD loss after '
                 'a verified partial ZIP write, redial, second script login, exact retry and NFO return. '
                 'Script compiled in DOS before starting the terminal. Isolated framed ENiGMA; no physical '
                 'Boca/SPA2102, SIP/audio loss, saturation, card/LAN deployment or full application claim.')
    if package:
        receipt.update(package_files=package_manifest['files'],card_written=False,
                       scope=receipt['scope']+' The exact branded selectable-IRQ package products are verified; startup Enter dismisses the Special Edition splash. The separate package receipt proves splash rendering and launcher behavior; this capture proves one branded recovery cycle, not repeated in-process recovery.')
    args.output.write_text(json.dumps(receipt,indent=2)+'\n')
    print('PASS current IRQ link loss, cleanup, redial, exact retry and NFO return')


if __name__=='__main__':main()
