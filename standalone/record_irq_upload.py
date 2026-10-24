#!/usr/bin/env python3
"""Bind a current IRQ upload to independent wire, catalog and DOS evidence."""
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
from enigma_upload_watch import SAMPLER,compact_sampler,compact_events
from check_enigma_upload_audit import replay,catalog


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--candidate',type=Path,required=True)
    p.add_argument('--label',required=True);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();candidate=owned(args.candidate)
    assert pid(candidate)is None
    with socket.socket()as s:s.bind(('127.0.0.1',23234))
    folder=ROOT/'build/bbs-lab/results/enigma'/args.label
    def read(name):return json.loads((folder/name).read_text())
    result=read('upload-checks.json');harness=read('result.json');audit=read('upload-audit-negative-checks.json')
    assert result['passed']and all(result['checks'].values())and not result['errors']
    assert harness['passed']and all(harness['checks'].values())
    assert result['cpu']==harness['cpu']=='8086'and result['irq']==7 and result['compact_observer']
    assert harness['serial']['irq']==7
    products={'terminal/TERMINAL.EXE':ROOT/'build'/(LOOKUP+'-custom-irq')/'TERMINAL.EXE',
              'aspect-runner/ASPECT.EXE':ROOT/'build/aspect-register-parent-custom-irq/ASPECT.EXE',
              'aspect-compiler-dos/ASPCOMP.EXE':ROOT/'build/aspect-compiler-dos/ASPCOMP.EXE'}
    sources={}
    for key,product in products.items():
        binary,inputs=select_product(product,product.name)
        assert result['products'][key]==dict(path=str(binary.relative_to(ROOT)),sha256=sha(binary))
        assert sha(folder/'program'/binary.name)==sha(binary)
        for path in inputs:sources[str(path.relative_to(ROOT))]=sha(path)
    fixture=json.loads((candidate/'search-instance.json').read_text())
    decoder=json.loads((candidate.parent/'report.json').read_text())
    assert decoder['passed']and decoder['stock_client_unchanged']
    assert fixture['upstream_revision']==decoder['upstream_revision']=='237cd9743d6978a940dd66db0e78f6ab8ccd3e37'
    assert all(test['exit_code']==0 for test in decoder['tests'])
    assert sha(candidate/'core/client.js')==decoder['candidate_client_sha256']
    assert sha(candidate/'core/key_stream.js')==decoder['candidate_key_stream_sha256']
    aliases={name:ROOT/'lab/bbs'/leaf for name,leaf in dict(runner='enigma_upload_dos.py',harness='test_dos.py',
        observer='test_transfer_dos.py',auditor='audit_zmodem.py',time_auditor='check_enigma_upload_audit.py',
        form_observer='enigma_upload_watch.py',observer_base='zmodem_label_watch.py').items()}
    aliases.update(products);aliases['login']=folder/'program/LOGON.ASP'
    aliases['time_auditor']=folder/'auditor-before-nfo-mutation-fix.py'
    for name,digest in result['input_hashes'].items():
        if name in aliases:path=aliases[name]
        elif name.startswith('staged/'):path=folder/'program'/Path(name).name
        elif name in fixture['fixture_inputs']or name in fixture['source_modules']:path=candidate/name
        else:path=ROOT/name
        assert sha(path)==digest,name
        sources[str(path.relative_to(ROOT))]=digest
    assert (folder/'BEFORE.BIN').read_bytes()==(folder/'AFTER.BIN').read_bytes()
    assert len((folder/'BEFORE.BIN').read_bytes())==42
    config=(folder/'dosbox.conf').read_text()
    assert 'cputype=8086\n'in config and 'serial2=nullmodem irq:7 'in config
    assert struct.unpack_from('<H',(folder/'TEST.PRM').read_bytes(),0x186)[0]==7
    assert (folder/'sampler.asm').read_text().replace('0x2f8','0x3f8').replace('0x2f9','0x3f9').replace('0x2fb','0x3fb').replace('0x2fc','0x3fc')==compact_sampler()
    forms=compact_events((folder/'LABELS.BIN').read_bytes())
    assert forms==read('upload-form-events.json')and(folder/'SNAP.COM').stat().st_size<2048
    expected={p.name:p.read_bytes()for p in(folder/'SEND').iterdir()}
    assert set(expected)=={'PCUP01.BIN','EMPTY.BIN'}and len(expected['PCUP01.BIN'])==65539 and not expected['EMPTY.BIN']
    protocol=replay((folder/'serial-received.bin').read_bytes(),(folder/'display.bin').read_bytes(),
                    read('trace.json'),expected,True)
    catalog(read('server-upload-metadata.json'),expected,candidate,result['received_date_bounds_ns'])
    for item in protocol['files']:item.pop('source',None)
    assert audit['passed']and all(case['rejected']for case in audit['cases'])and len(audit['cases'])>=14
    assert audit['checker_sha256']==sha(ROOT/'lab/bbs/check_enigma_upload_audit.py')
    assert audit['auditor_sha256']==sha(ROOT/'lab/bbs/audit_zmodem.py')
    negative=read('negative-audit-first-failure.json')
    assert not negative['passed']and negative['nfo_headings']==2
    assert negative['producer_sha256']==sha(aliases['time_auditor'])
    old_auditor=aliases['time_auditor'].read_text()
    changed_line="    at=opposite.rindex(b'NFO | lines');reject('missing-post-upload-NFO',received=damage(opposite,at))\n"
    replacement=("    # A page change can redraw the heading. Remove every copy to model a\n"
                 "    # genuinely missing NFO response rather than damaging one valid redraw.\n"
                 "    assert b'NFO | lines'in opposite\n"
                 "    reject('missing-post-upload-NFO',received=opposite.replace(b'NFO | lines',b'XFO | lines'))\n")
    assert old_auditor.count(changed_line)==1
    assert old_auditor.replace(changed_line,replacement)==(ROOT/'lab/bbs/check_enigma_upload_audit.py').read_text()
    sources['lab/bbs/check_enigma_upload_audit.py']=audit['checker_sha256']
    for name,digest in audit['capture_hashes'].items():assert sha(folder/name)==digest
    failed=folder.with_name('irq7-framed-upload-01')
    old=json.loads((failed/'upload-checks.json').read_text())
    assert not old['passed']and not old['checks']['script_login_trace']and not old['checks']['DOS_compiler_exact']
    assert sha(failed/'producer-before-compact.py')==old['input_hashes']['runner']
    assert sha(failed/'observer-before-compact.py')==old['input_hashes']['form_observer']
    assert (failed/'operator-stop.json').is_file()
    original_sampler=(failed/'sampler.asm').read_text()
    assert original_sampler.replace('0x2f8','0x3f8').replace('0x2f9','0x3f9').replace('0x2fb','0x3fb').replace('0x2fc','0x3fc')==SAMPLER
    assert (failed/'SNAP.COM').stat().st_size==6087 and(folder/'SNAP.COM').stat().st_size==1159
    assert SAMPLER.split('handler:',1)[1].split('resident_end:',1)[0]==compact_sampler().split('handler:',1)[1].split('resident_end:',1)[0]
    diagnostic=folder.with_name('irq7-upload-startup-diagnostic-01')
    d=json.loads((diagnostic/'upload-checks.json').read_text())
    assert not d['passed']and not d['checks']['DOS_compiler_exact']
    artifacts={str(path.relative_to(ROOT)):sha(path)for root in(folder,failed,diagnostic)
               for path in root.rglob('*')if path.is_file()}
    for path in [candidate.parent/'report.json',candidate/'instance.json',candidate/'search-instance.json',
                 ROOT/'build/irq-upload-prepare-01.log',ROOT/'build/irq-upload-prepare-02.log']:
        artifacts[str(path.relative_to(ROOT))]=sha(path)
    sources[str(Path(__file__).relative_to(ROOT))]=sha(Path(__file__))
    receipt=dict(passed=True,compatibility_complete=False,label=args.label,products=result['products'],
                 checks=result['checks'],forms=forms,protocol=protocol,independent_audit=audit,
                 sources=sources,artifacts=artifacts,retained_failed_labels=[failed.name,diagnostic.name],
                 temporary_server_stopped=True,server_upstream_revision=decoder['upstream_revision'],
                 decoder_tests=decoder['tests'],negative_audit_first_failure=negative,
                 scope='DOS8086 IRQ7 source login, 65539-byte plus empty ZMODEM upload, exact official catalog/storage, '
                 'current creation dates and same-session NFO return. Bounded resident observer; earlier startup '
                 'failures retained, first deliberately interrupted. No reconnect/load/physical/card/LAN or full application claim.')
    args.output.write_text(json.dumps(receipt,indent=2)+'\n')
    print('PASS current IRQ upload, binary/empty batch, form observer, catalog and NFO return')


if __name__=='__main__':main()
