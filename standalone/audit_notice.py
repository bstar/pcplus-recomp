#!/usr/bin/env python3
"""Seal composed notice cleanup and independent actual-DOS UART retention streams."""
import argparse,hashlib,itertools,json,re,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads(path.read_text())
def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['dos','uart','window-dos','source-proof','checkpoint','cohort','output']:p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();folders=[a.dos.resolve(),a.uart.resolve(),a.window_dos.resolve(),a.source_proof.resolve(),a.checkpoint.resolve()];dos,uart,window,fresh,checkpoint=folders;cohort=a.cohort.resolve();output=a.output.resolve()
    assert all(path.is_relative_to(ROOT/'build') for path in [*folders,cohort]) and not cohort.exists()
    assert output.is_relative_to(ROOT/'docs/validation') and not output.exists()
    n=read(ROOT/'build/notice/manifest.json');u=read(ROOT/'build/notice-uart/manifest.json');w=read(ROOT/'build/notice-window/manifest.json');d=read(dos/'result.json');r=read(uart/'result.json');wd=read(window/'result.json');f=read(fresh/'result.json')
    assert all(report['passed'] for report in [d,r,wd,f]) and all(m['original_inputs']==[] for m in [n,u,w])
    assert n['normal_runtime_compiled'] and w['owner_normal_compiled'] and u['clock_symbol']=='notice_seconds_recovered'
    assert d['assertions']==583 and d['allocations']==d['frees']==69 and all(d['checks'].values())
    assert re.fullmatch(r'NOTICE PASS 583 checks 69 allocations 69 frees\s*',(dos/'OUTPUT.TXT').read_text())
    assert wd['assertions']==771 and all(wd['checks'].values()) and re.fullmatch(r'WINDOW PASS 771 checks 114 allocations 114 frees\s*',(window/'OUTPUT.TXT').read_text())
    for folder,report in [(dos,d),(window,wd)]:
        for name,digest in report['captures_sha256'].items():assert sha(folder/name)==digest
        for name,digest in report['inputs'].items():assert sha(ROOT/name)==digest
    assert sha(dos/'NOTICE.EXE')==n['binary_sha256']==u['notice_binary_sha256']
    assert sha(window/'WINDOW.EXE')==w['products']['WINDOW.EXE']
    assert len(r['cases'])==16 and {(row['port'],row['flow'],row['mode']) for row in r['cases']}==set(itertools.product([1,2],'NSHB','NE'))
    payload=bytes(value for value in range(256) if value not in (17,19))*2;assert bytes.fromhex(r['payload_hex'])==payload
    cases=[];selected={Path(__file__)}
    for row in r['cases']:
        folder=ROOT/row['folder'];assert folder.is_relative_to(uart) and row['passed'] and all(row['checks'].values())
        assert row['assertions']==538 and row['maximum']==508 and row['callbacks']>1
        for name,digest in row['captures_sha256'].items():assert sha(folder/name)==digest
        assert sha(folder/'NUART.EXE')==u['binary_sha256'] and (folder/'RX.BIN').read_bytes()==payload
        assert 'cputype=8086' in (folder/'dosbox.conf').read_text() and f"NUART /S{row['port']}:0003:03:{row['flow']} {row['mode']}" in (folder/'dosbox.conf').read_text()
        text=(folder/'OUTPUT.TXT').read_text();assert re.fullmatch(rf"NOTICE UART COM{row['port']} {row['flow']} {row['mode']} 538 checks {row['callbacks']} callbacks 508 maximum\s*",text)
        peer=read(folder/'peer.json');assert not peer['errors'];events=peer['events'];assert all(x['seconds']<=y['seconds'] for x,y in zip(events,events[1:]))
        received=b''.join(bytes.fromhex(e['hex']) for e in events if e['kind']=='receive');expected=b'\x11RPF\x13' if row['flow'] in 'SB' else b'RPF'
        assert received==(folder/'wire.bin').read_bytes()==expected
        sent=[bytes.fromhex(e['hex']) for e in events if e['kind']=='send-completed'];assert sent==[(b'\x13'+payload+b'\x11') if row['flow'] in 'SB' else payload,b'READY!']
        assert sum(e['kind']=='EOF' for e in events)==1 and events[-1]['kind']=='EOF'
        cases.append(dict(port=row['port'],flow=row['flow'],mode=row['mode'],assertions=538,callbacks=row['callbacks'],retained_bytes=508,wire_hex=received.hex(),peer_sha256=sha(folder/'peer.json'),raw_input_sha256=sha(folder/'RX.BIN')))
    assert f['source_files']==len(u['sources'])==63 and len(f['products'])==33 and f['inputs']==u['sources']
    assert f['checker_sha256']==sha(ROOT/'standalone/prove_notice_source.py')
    for name,digest in f['manifest_sha256'].items():assert sha(ROOT/name)==digest
    for name,digest in f['products'].items():assert sha(ROOT/name)==digest
    for report in [r,f]:
        for name,digest in report['inputs'].items():assert sha(ROOT/name)==digest
    c=read(checkpoint/'result.json');cm=read(ROOT/'build/notice-checkpoint/manifest.json')
    assert c['passed'] and all(c['checks'].values()) and cm['original_inputs']==[]
    assert (checkpoint/'OUTPUT.TXT').read_text().strip()=='CHECKPOINT PASS 2048 calls 2048 far callbacks'
    assert (checkpoint/'PASS.TXT').exists() and not (checkpoint/'FAIL.TXT').exists()
    assert sha(checkpoint/'CHECK.EXE')==c['binary_sha256']==cm['binary_sha256']
    assert cm['sources']['src/ui/notice_checkpoint.asm']==u['sources']['src/ui/notice_checkpoint.asm']
    for name,digest in c['inputs'].items():assert sha(ROOT/name)==digest
    for name,digest in c['captures_sha256'].items():assert sha(checkpoint/name)==digest
    bank_map=(ROOT/'build/notice-checkpoint/CHECK.map').read_text()
    bank_symbols={name:int(seg,16) for seg,off,name in re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})\s+(\w+)\s*$',bank_map,re.M|re.I)}
    assert all(bank_symbols[name]==c['bank_segment'] for name in ['_notice_checkpoint_call','_notice_checkpoint_abort','_notice_checkpoint_active','_notice_call_native','_notice_checkpoint_probe'])
    assert bank_symbols['_notice_checkpoint_peer']==c['callback_segment']!=c['bank_segment']
    for name in ['build/notice/NOTICE.map','build/notice-uart/NUART.map']:
        assert not re.search(r'\b(?:_setjmp_|longjmp_)\b',(ROOT/name).read_text())
    selected.update(ROOT/name for name in c['inputs']);selected.add(ROOT/'build/notice-checkpoint/CHECK.map')
    selected.update(ROOT/name for name in u['sources']);selected.update(ROOT/name for name in d['inputs']);selected.update(ROOT/name for name in wd['inputs']);selected.update(ROOT/name for name in r['inputs']);selected.add(ROOT/'standalone/prove_notice_source.py')
    for folder in folders:selected.update(path for path in folder.rglob('*') if path.is_file())
    old=ROOT/'build/notice-uart/dos-01'
    if old.exists():
        failure=read(old/'result.json');assert not failure['passed'] and failure['cases'][-1]['checks']['wire_exact']==False
        selected.update(path for path in old.rglob('*') if path.is_file())
    for name in ['build/notice/manifest.json','build/notice-uart/manifest.json','build/notice/NOTICE.map','build/notice-uart/NUART.map']:selected.add(ROOT/name)
    cohort.mkdir();kept={}
    for path in sorted(selected):
        target=cohort/'accepted'/path.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,target);assert sha(target)==sha(path);kept[str(target.relative_to(ROOT))]=sha(target)
    result=dict(passed=True,serviced_notice_component_accepted=True,PROGRAM_binding_accepted=False,full_F02_accepted=False,full_F13_accepted=False,notice_DOS_assertions=583,notice_allocations=69,notice_frees=69,window_regression_assertions=771,UART_cases=16,UART_assertions=16*538,UART_retained_bytes=16*508,cases=cases,source_files=62,products=f['products'],inputs=u['sources'],toolchain_inputs={name:sha(ROOT/name) for name in ['nix/flake.nix','nix/flake.lock','tools/dev']},custody_sha256=kept,auditor_sha256=sha(Path(__file__)),scope='Exact native timed notice/window/text algorithms with staged bounded messages, real BIOS keys, typed service/budget/clock cleanup and retained generation-checked window ownership.583 actual8086 DOS checks include a fixed DOS2C observer with real BIOS fallback plus separate controlled tick fixtures for wrap/invalid samples.16 actual UART COM1/2 N/S/H/B sessions each retain508 peer bytes during the popup, then exchange READY! and restore selected UART IRQ/PIC/registers and screen/cursor. Nullmodem CTS stays ready and RTS timing is unproved. Sound callbacks are diagnostic record/error boundaries; original sound/macro/shared-parent policy, arbitrary external nonlocal faults, PROGRAM/BBS binding, other geometries and physical hardware remain open.')
    result.update(source_files=63,bank_local_checkpoint_accepted=True,checkpoint_calls=2048,foreign_CS_callbacks=2048,checkpoint_binary_sha256=c['binary_sha256'],checkpoint_scope=c['scope'])
    with output.open('x') as stream:stream.write(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(passed=True,notice_DOS_assertions=583,UART_cases=16,UART_assertions=16*538,custody_files=len(kept))))
if __name__=='__main__':main()
