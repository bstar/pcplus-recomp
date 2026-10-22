#!/usr/bin/env python3
"""Reproduce retained command-parser state across pre-CONNECT cancellation."""
import argparse,inspect,json,shutil,sys,types
from pathlib import Path
import test_manual_cancel_dos as base
ROOT=base.ROOT;sha=base.sha
ORIGINAL=base.adapter


def retained(out,events,gap,backend):
    text=inspect.getsource(ORIGINAL).replace('def adapter(out,events,gap,backend):','def build(out,events,gap,backend):')
    old="phase='DTR-low';line.clear();event('cancel-DTR-low')";assert text.count(old)==1
    text=text.replace(old,"phase='DTR-low';event('cancel-DTR-low')")
    old="assert value==ord('A');conn.sendall";assert text.count(old)==1
    text=text.replace(old,"assert value==ord('A');line.append(value);conn.sendall")
    old="if command==b'':event('empty-command-terminated',command);continue";assert text.count(old)==1
    text=text.replace(old,"if command==b'A':conn.sendall(b'\\r\\nERROR\\r\\n');event('stale-command-terminated',command);continue")
    old="else:checks['unexpected_modem_command']=True";assert text.count(old)==1
    text=text.replace(old,"else:checks['unexpected_modem_command']=True;conn.sendall(b'\\r\\nERROR\\r\\n');event('initialization-ERROR',command)")
    module=types.ModuleType('retained_cancel_factory');module.__dict__.update(base.__dict__)
    exec(compile(text,__file__,'exec'),module.__dict__);return module.build(out,events,gap,backend)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--label',required=True);p.add_argument('--expect-gap',action='store_true');a=p.parse_args()
    base.adapter=retained;sys.argv=[__file__,'--label',a.label]
    failed=False
    run=base.main
    if a.expect_gap:
        source=inspect.getsource(run)
        old="else b'\\rATZ\\rATDCaseTest:23\\r'";assert source.count(old)==1
        source=source.replace(old,"else b'ATZ\\rATDCaseTest:23\\r'")
        namespace=dict(base.__dict__);exec(compile(source,__file__,'exec'),namespace);run=namespace['main']
    try:run()
    except AssertionError:failed=True
    folder=ROOT/'build/manual-cancel-dos'/a.label;r=json.loads((folder/'checks.json').read_text())
    preserved=folder/'retained-inputs/standalone';preserved.mkdir(parents=True,exist_ok=False)
    for path in (Path(__file__),Path(base.__file__)):shutil.copy2(path,preserved/path.name)
    assert len(r['cases'])==2 and failed==a.expect_gap
    rows=[]
    for row in r['cases']:
        case=folder/row['case'];raw=json.loads((case/'result.json').read_text());events=json.loads((case/'peer-events.json').read_text())
        errors=[bytes.fromhex(e['hex']) for e in events if e['kind']=='initialization-ERROR']
        if a.expect_gap:
            assert not r['passed'] and not row['passed']
            assert errors==[b'AATZ'] and raw['commands']==['AATZ','ATDCaseTest:23']
            expected_failures={'no_unexpected_commands','actual_init_and_dial'}
            assert {k for k,v in row['checks'].items() if not v}==expected_failures
            assert row['sample'][4:6]==[0,0] and row['sample'][8:10]==[0,0] and row['sample'][10]>18
        else:assert r['passed'] and row['passed'] and not errors
        rows.append(dict(case=row['case'],gap_reproduced=a.expect_gap,commands=raw['commands'],initialization_errors=[b.hex() for b in errors],capture_sha256=row['captures']))
    result=dict(passed=True,gap_reproduced=a.expect_gap,compatibility_accepted=not a.expect_gap,parent_sha256=r['parent_sha256'],cases=rows,producer_report_sha256=sha(folder/'checks.json'),checker_sha256=sha(Path(__file__)),base_checker_sha256=sha(Path(base.__file__)),
        scope=__doc__+' Explicit patched DCD lab backend, owned peer retains initial A across DTR and returns ERROR for AATZ. The established flow fix can still connect after the error; this does not prove initialization succeeded. Expected-gap mode preserves the failed underlying producer, rather than relabeling it accepted. Physical Boca and stock-backend behavior remain separate.')
    (folder/'retained-checks.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=True,gap=a.expect_gap,cases=len(rows))))


if __name__=='__main__':main()
