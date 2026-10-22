#!/usr/bin/env python3
"""DOS strict initialization retry after cancellation and retained/cleared commands."""
import argparse,inspect,json,shutil,sys,time
from pathlib import Path
import test_manual_cancel_dos as base
import test_manual_cancel_retained_dos as retained
from audit_aspect_transmit_wait import ROOT,sha,read
ORIGINAL=base.adapter


def factory(keep):
    def build(out,events,gap,backend):
        module=retained.retained(out,events,gap,backend) if keep else ORIGINAL(out,events,gap,backend)
        # Observe owned peer submissions without replacing UART/product code.
        original_socket=module.socket
        class SocketProxy:
            def __init__(self,socket):self.socket=socket
            def __getattr__(self,name):return getattr(self.socket,name)
            def __enter__(self):self.socket.__enter__();return self
            def __exit__(self,*args):return self.socket.__exit__(*args)
            def accept(self):
                connection,address=self.socket.accept();return SocketProxy(connection),address
            def sendall(self,data):
                self.socket.sendall(data)
                events.append(dict(kind='peer-send-completed',time=time.monotonic(),hex=data.hex()))
        class SocketModule:
            def __getattr__(self,name):return getattr(original_socket,name)
            def socket(self,*args,**kwargs):return SocketProxy(original_socket.socket(*args,**kwargs))
        module.socket=SocketModule()
        run=module.run
        def configured(*args,**kwargs):
            kwargs['arguments']+=' /I:3'
            return run(*args,**kwargs)
        module.run=configured;return module
    return build


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
    rows=[]
    for keep,label in [(False,out.name+'-cleared'),(True,out.name+'-retained')]:
        base.adapter=factory(keep);sys.argv=[__file__,'--label',label];base.main()
        folder=ROOT/'build/manual-cancel-dos'/label;r=read(folder/'checks.json');assert r['passed'] and len(r['cases'])==2
        for row in r['cases']:
            case=folder/row['case'];events=read(case/'peer-events.json');assert read(case/'result.json')['command'].endswith(' /I:3')
            wire=b'';times=[]
            for event in events:
                if event['kind']=='receive':
                    data=bytes.fromhex(event['hex']);wire+=data;times.extend([event['time']]*len(data))
            assert wire==(case/'serial.bin').read_bytes() and wire.startswith(b'A\rATZ\rATDCaseTest:23\r')
            guard=times[2]-times[1];assert 2.8<=guard<=5
            assert sum(e['kind']=='stale-command-terminated' for e in events)==int(keep)
            assert not any(e['kind']=='initialization-ERROR' for e in events)
            errors=[e for e in events if e['kind']=='peer-send-completed' and bytes.fromhex(e['hex'])==b'\r\nERROR\r\n']
            assert len(errors)==int(keep)
            if errors:assert times[1]<=errors[0]['time']<times[2]
            rows.append(dict(case=('retained-' if keep else 'cleared-')+row['case'],passed=True,cohort=str(case.relative_to(ROOT)),guard_seconds=guard,sample=row['sample'],wire_hex=wire.hex(),captures=row['captures'],producer_report_sha256=sha(folder/'checks.json')))
        for path in (Path(__file__),Path(base.__file__),Path(retained.__file__)):
            target=out/'inputs'/path.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,target)
    binary=ROOT/'build/terminal/TERMINAL.EXE';result=dict(passed=True,parent_sha256=sha(binary),cases=rows,checker_sha256=sha(Path(__file__)),inputs={str(path.relative_to(ROOT)):sha(path) for path in (Path(__file__),Path(base.__file__),Path(retained.__file__))},
        scope=__doc__+' Four actual8086 DOS SOFT/BOTH cases on explicit patched DCD lab backend. Real Escape after first A, DTR/cancel cleanup, Alt-D, separately emitted CR and full3s stale-result drain, configured ATZ/OK/dial/CONNECT and manual query. Retained peer returns ERROR for old A; cleared peer sends no empty-command response. The unchanged source-built observer is read-only. Not physical modem timing, late responses beyond configured guard, SIP/audio or full application acceptance.')
    (out/'checks.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=True,cases=len(rows))))


if __name__=='__main__':main()
