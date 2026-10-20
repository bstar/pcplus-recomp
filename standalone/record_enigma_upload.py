#!/usr/bin/env python3
"""Publish sanitized upload workflow, actual catalog and unchanged DOS products."""
import argparse,json,re,sys
from datetime import date
from pathlib import Path
from build_native_mouse import ROOT,sha


def read(path):return json.loads(path.read_text())
def current(sources):
    for p,h in sources.items():assert not Path(p).is_absolute() and '..' not in Path(p).parts and sha(ROOT/p)==h,p


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('small-label','large-label'):parser.add_argument('--'+name,required=True)
    for name in ('small-candidate','large-candidate','server-root','output'):parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args()
    for label in (args.small_label,args.large_label):assert re.fullmatch(r'[A-Za-z0-9_-]+',label)
    sys.path.insert(0,str(ROOT/'lab/bbs'))
    from enigma_upload_dos import metadata
    from check_enigma_upload_audit import catalog,replay
    binary=ROOT/'build/terminal/TERMINAL.EXE';digest=sha(binary);evidence=[];workflows=[]
    root=ROOT/'build/bbs-lab/results/enigma'
    for label,candidate,size in [(args.small_label,args.small_candidate,1501),(args.large_label,args.large_candidate,65539)]:
        candidate=candidate.resolve();assert candidate.is_relative_to(ROOT/'build')
        folder=root/label;r=read(folder/'upload-checks.json');negative=read(folder/'upload-audit-negative-checks.json')
        assert r['passed'] and all(r['checks'].values()) and not r['errors'] and r['terminal_sha256']==digest
        assert r['expected']['PCUP01.BIN']['bytes']==size and r['expected']['EMPTY.BIN']['bytes']==0
        assert negative['passed'] and len(negative['cases'])==13 and all(c['rejected'] for c in negative['cases'])
        assert negative['checker_sha256']==sha(ROOT/'lab/bbs/check_enigma_upload_audit.py')
        assert negative['auditor_sha256']==r['input_hashes']['auditor']==sha(ROOT/'lab/bbs/audit_zmodem.py')
        for p,h in negative['capture_hashes'].items():assert sha(folder/p)==h
        if size>8192:assert r['input_hashes']['runner']==sha(ROOT/'lab/bbs/enigma_upload_dos.py')
        for key,p in [('harness','test_dos.py'),('observer','test_transfer_dos.py')]:assert r['input_hashes'][key]==sha(ROOT/'lab/bbs'/p)
        setup=read(candidate/'search-instance.json');assert setup['upload_fixture']
        assert {'fileBaseUploadFiles','recvFilesFromUser','fileBaseNoUploadAreasAvail'}<=set(setup['selected_menus'])
        for p,h in {**setup['fixture_inputs'],**setup['source_modules']}.items():assert sha(candidate/p)==h==r['input_hashes'][p]
        for p,h in setup['source_inputs'].items():assert sha(args.server_root/p)==h
        expected={p.name:p.read_bytes() for p in (folder/'SEND').iterdir()}
        assert {p:sha(folder/'SEND'/p) for p in expected}=={p:v['sha256'] for p,v in r['expected'].items()}
        actual=metadata(candidate,list(expected));catalog(actual,expected,candidate)
        saved=read(folder/'server-upload-metadata.json');assert actual==saved,'Installed catalog changed after capture'
        replay((folder/'serial-received.bin').read_bytes(),(folder/'display.bin').read_bytes(),read(folder/'trace.json'),expected)
        rows=[json.loads(l) for l in (folder/'server-session.jsonl').read_text().splitlines() if l.strip()]
        executions=[i for i,v in enumerate(rows) if v.get('msg')=='Executing external protocol']
        exits=[i for i,v in enumerate(rows) if v.get('msg')=='Process exited' and v.get('exitCode')==0]
        assert len(executions)==len(exits)==1 and executions[0]<exits[0]
        files={}
        for row in actual:
            entry=row['entries'][0];files[row['name']]=dict(bytes=entry['meta']['byte_size'],sha256=entry['fileSha256'],
                area=entry['areaTag'],storage=entry['storageTag'],uploader=entry['meta']['upload_by_username'],description=entry['desc'],
                filesystem_mtime_ns=str(Path(entry['filePath']).stat().st_mtime_ns))
        workflows.append(dict(label=label,checks=r['checks'],files=files,menus=r['menus'],corruptions_rejected=len(negative['cases']),producer_sha256=r['input_hashes']['runner']))
        evidence += [folder/'upload-checks.json',folder/'upload-audit-negative-checks.json',folder/'server-upload-metadata.json',candidate/'search-instance.json']
    failures=[]
    for label,size,reason in [
        ('owned-upload-02',1501,'Protocol completed; the three-Tab details recipe did not accept/persist the batch.'),
        ('owned-upload-large-01',65539,'Protocol completed; queued processing/details output outlasted the keyboard schedule. No files were persisted or NFO reached.')]:
        failed_path=root/label/'upload-checks.json';failed=read(failed_path)
        assert not failed['passed'] and failed['checks']['DOS_harness'] and not failed['checks']['all_server_files_and_metadata']
        assert len(failed['protocol']['files'])==2 and failed['protocol']['controls']
        assert sorted(f['length'] for f in failed['protocol']['files'])==[0,size]
        failures.append(dict(label=label,checks=failed['checks'],menus=failed['menus'],reason=reason))
        evidence.append(failed_path)
    preceding=read(ROOT/'docs/validation/enigma-carrier.json');assert preceding['passed'];current(preceding['source_hashes'])
    for p,h in preceding['source_products'].items():assert sha(ROOT/'build'/p)==h
    assert len(preceding['source_products'])==31 and preceding['source_products']['terminal/TERMINAL.EXE']==digest
    evidence.append(ROOT/'docs/validation/enigma-carrier.json')
    output=dict(date=date.today().isoformat(),passed=True,whole_application_gates_closed=[],workflows=workflows,
        unchanged_source_products=preceding['source_products'],unchanged_application_products=31,original_build_inputs=[],
        retained_failures=failures,
        evidence=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in evidence],
        sources={p:sha(ROOT/p) for p in ('lab/bbs/enigma_search_fixture.py','lab/bbs/enigma_upload_dos.py','lab/bbs/check_enigma_upload_audit.py','lab/bbs/audit_zmodem.py','lab/bbs/enigma_script_login.py')},
        recorder_sha256=sha(Path(__file__)),nix_inputs={p:sha(ROOT/p) for p in ('nix/flake.nix','nix/flake.lock')},
        limitations=['Isolated staged ENiGMA decoder, synthetic accounts/areas/files and modeled19200/HARD modem. No live deployment or physical Wi-Fi firmware acceptance.',
            'The smaller capture predates the optional size argument; its producer hash is retained separately. Both captures are re-audited by current code.',
            'Filesystem timestamp acceptance remains open: both empty uploads have invalid future dates. The sender omits optional mtime; no timestamp preservation claim is made.',
            'Upload cancellation/carrier loss and other protocols remain open. Current application/source proof is unchanged from the preceding carrier checkpoint.'])
    with args.output.open('x') as f:f.write(json.dumps(output,indent=2)+'\n')
    print(args.output)


if __name__=='__main__':main()
