#!/usr/bin/env python3
"""Audit sustained DOS reception and the collector's8086 instruction correction."""
import argparse,json
from pathlib import Path
from audit_aspect_transmit_wait import ROOT,sha,read
from test_terminal_monitor_dos import AFTER


def custody(folder,r,current):
    for name,digest in r['inputs'].items():
        assert sha(folder/'inputs'/name)==digest
        if current:assert sha(ROOT/name)==digest
    for name,digest in r.get('captures',{}).items():assert sha(folder/name)==digest


def verify(folder,cpu):
    r=read(folder/'checks.json');assert r['passed'] and r['selected_DOS_sustained_capture_accepted'] and r['CPU_mode']==cpu;custody(folder,r,True)
    assert not r['actual_DOS_receive_watermarks_accepted'] and not r['physical_flow_timing_accepted']
    assert r['parent_sha256']==sha(ROOT/'build/terminal/TERMINAL.EXE')==sha(folder/'program/TERMINAL.EXE')
    case=folder/'run/hard-unthrottled-64k';payload=bytes(range(256))*256
    assert (case/'PCPLUS.DMP').read_bytes()==payload and sha(case/'PCPLUS.DMP')==r['payload_sha256']
    assert r['exact_dump'] and r['exact_wire'] and all(r['case']['checks'].values())
    assert (case/'serial.bin').read_bytes()==b'\x1b[0nm1m2m3\x1b[0nready\x1b[0n'
    prefix,separator,tail=(case/'peer.bin').read_bytes().partition(payload)
    # Readiness probes may precede UART acquisition; preserve their exact count.
    assert separator==payload and 1<=len(prefix)//4<=20 and prefix==b'\x1b[5n'*(len(prefix)//4)
    assert tail==AFTER+b'\x1b[5n\x1b[5n'
    assert (case/'BEFORE.BIN').read_bytes()==(case/'AFTER.BIN').read_bytes() and (case/'BEFORE.BIN').stat().st_size==42
    assert (case/'PASS.TXT').read_bytes().strip()==b'PASS' and not (case/'FAIL.TXT').exists()
    raw=(case/'MONVIEW.BIN').read_bytes();assert len(raw)==4036 and raw[:14]==b'MV16\x0f\x00\x3a\xc5\x01\x00\x01\x00\x00\x00'
    observer=read(case/'view-oracle.json');assert observer['passed'] and observer['observer_chain_verified_restored']
    events=read(case/'events.json');assert all(x['seconds']<=y['seconds'] for x,y in zip(events,events[1:]))
    assert [e['hex'] for e in events if e['event']=='actual-BIOS-marker']==['6d31','6d32','6d33','7265616479']
    cfg=(case/'dosbox.conf').read_text();assert 'cputype='+cpu in cfg and '38400 8N1 HARD' in cfg and 'transparent:1' in cfg
    for name in ('MONOBS.asm','MONDUMP.asm','SNAP.asm'):assert 'CPU 8086' in (case/name).read_text()
    return dict(CPU_mode=cpu,report=str(folder/'checks.json'),report_sha256=sha(folder/'checks.json'),passed=True,payload_bytes=65536,payload_sha256=r['payload_sha256'],observer_entry_DF=observer['entry_DF_set'],initial_readiness_queries=len(prefix)//4,captures=r['captures'],source_inputs=r['inputs']),r


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('accepted-386','accepted-8086','failed-8086','collector','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();v386,r=verify(a.accepted_386,'386');v8086,new=verify(a.accepted_8086,'8086');assert r['parent_sha256']==new['parent_sha256']
    old=read(a.failed_8086/'checks.json');assert not old['passed'] and not old['selected_DOS_sustained_capture_accepted'];custody(a.failed_8086,old,False)
    assert old['parent_sha256']==r['parent_sha256'] and old['exact_dump'] and old['exact_wire']
    old_case=a.failed_8086/'run/hard-unthrottled-64k';assert 'cputype=8086' in (old_case/'dosbox.conf').read_text()
    assert not (old_case/'MONVIEW.BIN').exists() and (old_case/'PASS.TXT').exists()
    gap=read(a.collector/'checks.json');assert gap['passed'] and gap['helper_encoding_gap_reproduced'] and gap['collector_8086_accepted'];custody(a.collector,gap,True)
    assert [row['collector_accepted'] for row in gap['cases']]==[True,False,True,True]
    for row in gap['cases']:
        folder=a.collector/(row['assembler_variant']+'-'+row['CPU_mode'])
        for name,digest in row['artifacts'].items():assert sha(folder/name)==digest
    for variant in ('legacy','fixed'):
        for name in ('MONOBS.COM','MONDUMP.COM','PROBE.COM'):assert sha(a.collector/(variant+'-386')/name)==sha(a.collector/(variant+'-8086')/name)
    assert (a.collector/'legacy-8086/MONDUMP.COM').read_bytes()[17:19]==bytes.fromhex('0f85')
    assert (a.collector/'fixed-8086/MONDUMP.COM').read_bytes()[17:20]==bytes.fromhex('7403e9')
    result=dict(passed=True,selected_DOS_sustained_capture_accepted=True,collector_8086_accepted=True,actual_DOS_receive_watermarks_accepted=False,physical_flow_timing_accepted=False,full_F03_accepted=False,
        parent_sha256=r['parent_sha256'],cases=[v386,v8086],collector_evidence=gap,
        failed8086=dict(report=str(a.failed_8086/'checks.json'),sha256=sha(a.failed_8086/'checks.json'),passed=False,failed_checks=[key for key,value in old['case']['checks'].items() if not value]),auditor_sha256=sha(Path(__file__)),
        scope='Two selected DOS raw-monitor foreground/logging sessions,8086/386 modes:65,536 exact all-byte input each, normal ANSI/query/keyboard return, normal application/emulator exit, UART and observer16/2F restoration. Stock transparent nullmodem holds CTS and ignores RTS; no watermark/physical throughput claim. Collector legacy default NASM near Jcc386 encoding is reproduced in a no-PCPlus fixture; explicit CPU8086 changes it to inverse short Jcc plus near JMP and restores collection in both modes. Failed predecessors remain separate. No application binary change, physical hardware or full application acceptance.')
    assert not a.output.exists();a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=True,DOS_cases=2,exact_bytes=131072,collector_8086_accepted=True)))


if __name__=='__main__':main()
