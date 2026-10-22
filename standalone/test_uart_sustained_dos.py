#!/usr/bin/env python3
"""Actual DOS sustained raw reception/file ownership; no hardware-flow timing claim."""
import argparse,inspect,json,shutil,types
from pathlib import Path
import test_terminal_monitor_dos as monitor
from audit_aspect_transmit_wait import ROOT,sha


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--cpu',choices=('8086','386'),default='8086');a=p.parse_args()
    out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
    product=ROOT/'build/terminal';m=json.loads((product/'manifest.json').read_text());assert sha(product/'TERMINAL.EXE')==m['binary_sha256'];inputs=dict(m['sources'])
    for path in (Path(__file__),Path(monitor.__file__),ROOT/'standalone/test_terminal_transfer_dos.py',ROOT/'standalone/test_terminal_capture_dos.py',ROOT/'standalone/test_terminal.py',ROOT/'standalone/terminal_config_fixtures.py'):
        inputs[str(path.relative_to(ROOT))]=sha(path)
    for name,digest in inputs.items():
        assert sha(ROOT/name)==digest;target=out/'inputs'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,target)
    program=out/'program';program.mkdir();shutil.copy2(product/'TERMINAL.EXE',program/'TERMINAL.EXE')
    collector=monitor.OBSERVER_DUMP
    assert collector.count('org 100h')==1
    collector=collector.replace('org 100h','org 100h\n pushf\n pop ax\n mov [entry_flags],ax\n cld')
    collector=collector.replace('mov cx,4034','mov cx,4036').replace('cmp ax,4034','cmp ax,4036')+'\nentry_flags dw 0\n'
    namespace=dict(monitor.__dict__);namespace.update(OUT=out,BINARY=program/'TERMINAL.EXE',OBSERVER_DUMP=collector)
    peer=inspect.getsource(monitor.MonitorPeer).replace('time.monotonic()+25','time.monotonic()+65')
    exec(compile(peer,__file__,'exec'),namespace)
    run=inspect.getsource(monitor.run_case)
    assert run.count("'p1700'")==1
    run=run.replace("'p1700'","'p15000 p15000'").replace('cputype=386','cputype='+a.cpu)
    run=run.replace("checks=dict(peer.checks);","(out/'serial.bin').write_bytes(peer.wire);(out/'peer.bin').write_bytes(peer.sent);(out/'events.json').write_text(json.dumps(peer.events,indent=2)+'\\n');checks=dict(peer.checks);")
    run=run.replace('actual_raw_display_chars_and_attrs','actual_BIOS_observation_and_chain_restoration')
    run=run.replace("allowed={'MONOBS.asm'","allowed={'serial.bin','peer.bin','events.json','MONOBS.asm'")
    # Bulk file continuity has a different oracle from the small prefix-display
    # tests: a full64KiB stream scrolls the screen many times. Preserve the
    # actual BIOS observation/vector checks, then check normal ANSI on resume.
    def observation(folder,data,normal=7,special=15):
        raw=(folder/'MONVIEW.BIN').read_bytes() if (folder/'MONVIEW.BIN').exists() else b''
        valid=len(raw)==4036 and raw[:4]==b'MV16' and raw[4:6]==b'\x0f\x00' and raw[6:14]==b'\x3a\xc5\x01\x00\x01\x00\x00\x00'
        report=dict(passed=valid,observer_chain_verified_restored=valid,entry_flags=int.from_bytes(raw[-2:],'little') if len(raw)==4036 else None,entry_DF_set=bool(int.from_bytes(raw[-2:],'little')&0x400) if len(raw)==4036 else None,scope='Bulk DOS capture: actual INT16/2F observation and chain restoration; no full raw-screen rendering oracle.')
        (folder/'view-oracle.json').write_text(json.dumps(report,indent=2)+'\n');return report
    namespace['audit_view']=observation;exec(compile(run,__file__,'exec'),namespace)
    options=types.SimpleNamespace(label='run',com=1,baud=38400,flow='HARD',timeout=90,sha256=m['binary_sha256'])
    payload=bytes(range(256))*256;recipe=dict(name='hard-unthrottled-64k',choice='y',data=payload)
    r=namespace['run_case'](recipe,options);folder=out/'run'/recipe['name']
    exact_dump=(folder/'PCPLUS.DMP').exists() and (folder/'PCPLUS.DMP').read_bytes()==payload
    exact_wire=(folder/'serial.bin').read_bytes()==b'\x1b[0nm1m2m3\x1b[0nready\x1b[0n'
    passed=r['passed'] and all(r['checks'].values()) and exact_dump and exact_wire
    for name,digest in inputs.items():assert sha(ROOT/name)==sha(out/'inputs'/name)==digest
    result=dict(passed=passed,CPU_mode=a.cpu,selected_DOS_sustained_capture_accepted=passed,exact_dump=exact_dump,exact_wire=exact_wire,actual_DOS_receive_watermarks_accepted=False,physical_flow_timing_accepted=False,parent_sha256=m['binary_sha256'],inputs=inputs,
        case=r,payload_bytes=len(payload),payload_sha256=sha(folder/'PCPLUS.DMP') if (folder/'PCPLUS.DMP').exists() else None,captures={str(path.relative_to(out)):sha(path) for path in folder.rglob('*') if path.is_file()},
        checker_sha256=sha(Path(__file__)),scope=__doc__+f' Actual DOS CPU mode{a.cpu}, raw monitor logs65,536 bytes exactly at configured38400 DTE with HARD selected, then resumes normal ANSI/query/keyboard. Stock transparent nullmodem holds CTS; peer does not obey RTS and no RX-high-water observation is claimed. Actual foreground/UI/DOS file/logger/observer/UART restoration; not physical throughput, full application display or software-audio pressure.')
    (out/'checks.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=passed,bytes=len(payload),failed=[k for k,v in r['checks'].items() if not v])));assert passed


if __name__=='__main__':main()
