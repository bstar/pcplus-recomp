#!/usr/bin/env python3
"""Read-only stock-server navigation prerequisite; stops before upload starts."""
import argparse,json,sys
from pathlib import Path
import enigma_transfer
import enigma
from audio_upload import NAME,payload,navigation,metadata
from synthmodem_vm_control import ROOT,sha


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--fixture-lab',type=Path);a=p.parse_args()
    server_fixture=None
    if a.fixture_lab:
        from enigma_receive_finish_instance import bind
        server_fixture=bind(a.fixture_lab)
    out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False)
    pid=enigma.process_pid();assert pid and Path(f'/proc/{pid}/cwd').resolve()==enigma.SOURCE.resolve()
    before=metadata();assert not before and not (enigma_transfer.STORAGE/NAME).exists()
    config=enigma_transfer.SOURCE/'config/config.hjson';config_before=sha(config)
    log=enigma_transfer.SOURCE/'logs/enigma-bbs.log';boundary=(log.stat().st_ino,log.stat().st_size)
    enigma_transfer.OUT=out
    # Existing independent socket reference logs into the same owned server.
    # No final protocol Enter: the real receive helper must never start.
    enigma_transfer.reference(['460d','550d','09','09','09','0d'])
    assert log.stat().st_ino==boundary[0]
    with log.open('rb') as stream:stream.seek(boundary[1]);all_rows=[json.loads(s) for s in stream if s.strip()]
    sessions={r['sessionId'] for r in all_rows if r.get('msg')=='User "loclab" successfully logged in'}
    assert len(sessions)==1
    rows=[r for r in all_rows if r.get('sessionId') in sessions]
    (out/'reference-server-rows.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows))
    menus=[r['menuName'] for r in rows if r.get('menuName')]
    text=(out/'reference.txt').read_text()
    sys.path.insert(0,str(ROOT/'src/aspect'));from compiler import compile_source
    def wait(token,timeout,label):return f'waitfor "{token}" {timeout}\n'
    def mark(label):return f'; {label}\n'
    script='proc main\n'+navigation(wait,mark)+'endproc\n'
    (out/'UPLOAD.ASP').write_text(script);compiled=compile_source(script);(out/'UPLOAD.ASX').write_bytes(compiled)
    checks={'observed_stock_protocol_selection':'PROTOCOL SELECTION' in text,
        'actual_upload_options_and_protocol_menus':'fileBaseUploadFiles' in menus and menus[-1]=='fileTransferProtocolSelection',
        'receive_helper_never_started':not any(r.get('msg')=='Executing external protocol' for r in rows),
        'no_installed_upload':metadata()==before and not (enigma_transfer.STORAGE/NAME).exists(),
        'server_configuration_unchanged':sha(config)==config_before,
        'maintained_upload_route_compiles':bool(compiled),'binary_fixture_covers_all_octets':set(payload())==set(range(256))}
    report={'passed':all(checks.values()),'checks':checks,'menus':menus,'server_PID':pid,'server_config_sha256':config_before,'server_fixture':server_fixture,
        'server_rows_sha256':sha(out/'reference-server-rows.jsonl'),'script_sha256':sha(out/'UPLOAD.ASP'),
        'source_sha256':{str(f.relative_to(ROOT)):sha(f) for f in [Path(__file__).resolve(),ROOT/'lab/bbs/audio_upload.py',ROOT/'lab/bbs/enigma_transfer.py']},
        'scope':'Unchanged ENiGMA upload-options/protocol navigation on the explicitly recorded server via independent fast TCP reference, plus ASPECT compilation and fixture preconditions. A modified receiver candidate is identified separately when selected. Stops before selecting protocol/launching helper; no real upload, native DOS, modem audio or physical acceptance.'}
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));assert report['passed']


if __name__=='__main__':main()
