#!/usr/bin/env python3
"""Recheck actual live-buffer fault captures, not only producer PASS flags."""
import argparse,json,shutil,struct
from pathlib import Path
import aspect_exit_watch
from build_path_session import ROOT,sha

PHASES=[17,5,6,8,10,22]
GROUPS=['own','foreign','abort','dispatcher']
def audit(report,capture,group,phase):
    checks=report['checks'];key={'own':'actual_selected_divide','foreign':'actual_selected_divide','abort':'actual_typed_abort','dispatcher':'actual_dispatcher_unwind'}[group]
    required=[key,'all_owners_retired','selected_fault_DS_SS','twelve_buffers_live_at_fault',
              'all_buffer_pointers_retired','held_files_preserved','later_calls_succeed','exact_viewport_cells']
    assert report['passed'] and all(checks.get(n) is True for n in required)
    raw=aspect_exit_watch.read(capture/'EXITSTAT.BIN');assert raw==report['exit_watch']
    exits=raw['exits'];probes=raw['program_results'];error=12 if group in ['own','foreign'] else 5
    assert len(exits)==len(probes)==4 and [e['error'] for e in exits]==[error,0,0,0]
    assert exits[0]['opcode']==155 and probes[0]['stage']==256+phase
    assert probes[0]['status']==1 and probes[0]['process_status']==0x0606
    ds,ss=probes[0]['display_status'],probes[0]['serial_status']
    assert (ds==0xb800 and ss!=ds) if group=='foreign' else (ds==ss and ds!=0)
    assert all(e[n]==0 for e in exits for n in ['cleanup_error','external_scope','display_owned','program_busy','process_busy'])
    pointers=aspect_exit_watch.read_buffers(capture/'BUFPTRS.BIN')
    assert all(v==0 for row in pointers for v in row) and pointers[:4]==report['buffer_exit_pointers']
    assert probes[3]['stage']==2 and probes[3]['status']==0
    assert all((capture/f'HOLD{i}.BIN').read_bytes()==f'HELD{i}|'.encode() for i in range(6))
    assert (capture/'NEST.LOG').read_bytes()==b'CHILD|'*(2 if phase in [10,22] else 1)
    return dict(error=error,buffers_at_fault=dict(streams=6,snapshots=6),exit_pointer_words=48)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ['pattern','child-pattern']:p.add_argument('--'+n,required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir();rows=[]
    for group in GROUPS:
      for phase in PHASES:
        path=(ROOT/a.pattern.format(kind=group,phase=phase)).resolve();assert path.is_relative_to(ROOT/'build')
        r=json.loads(path.read_text());capture=ROOT/'build/connection-dos'/path.parent.name
        child=(ROOT/a.child_pattern.format(kind=group,phase=phase)).resolve();m=json.loads(child.with_name('manifest.json').read_text())
        assert m['diagnostic_build'] and m['diagnostic_script_buffer_owners'] and m['experimental_deferred_script_buffers']
        assert m['diagnostic_lease_fault_phase']==phase and bool(m['diagnostic_lease_fault_foreign_ds'])==(group=='foreign')
        assert m['diagnostic_lease_fault_kind']==(group if group in ['abort','dispatcher'] else 'divide')
        assert m['binary_sha256']==r['interpreter_sha256']==sha(child)
        witness=audit(r,capture,group,phase)
        rows.append(dict(group=group,phase=phase,witness=witness,report=dict(path=str(path.relative_to(ROOT)),sha256=sha(path)),
                         captures={n:sha(capture/n) for n in ['EXITSTAT.BIN','BUFPTRS.BIN','NEST.LOG']},child_sha256=sha(child)))
    original=ROOT/a.pattern.format(kind='own',phase=17);r=json.loads(original.read_text());capture=ROOT/'build/connection-dos'/original.parent.name;rejected=[]
    for name in ['pointer','phase','live-count','error','missing-owner-check','missing-fault-check']:
        folder=out/name;shutil.copytree(capture,folder);copy=json.loads(json.dumps(r))
        if name.startswith('missing'):
            del copy['checks']['all_owners_retired' if name=='missing-owner-check' else 'actual_selected_divide']
        else:
            path=folder/('BUFPTRS.BIN' if name=='pointer' else 'EXITSTAT.BIN');raw=bytearray(path.read_bytes())
            offset={'pointer':4,'phase':580,'live-count':588,'error':16}[name];raw[offset]^=1;path.write_bytes(raw)
        try:audit(copy,folder,'own',17)
        except AssertionError:rejected.append(name)
        else:raise AssertionError('Accepted damaged '+name)
    sources=['standalone/check_deferred_fault_reports.py','standalone/aspect_exit_watch.py','standalone/aspect_exit_watch.asm']
    result=dict(passed=True,cases=rows,rejected_controls=rejected,sources={n:sha(ROOT/n) for n in sources},
                scope=__doc__+' Twenty-four DOS386/UMB diagnostics authenticate a live parent screen lease and six streams/six copies before selected faults; raw pointer fields retire at each exit. Separate from normal capacity, physical acceptance or arbitrary heap/kernel corruption.')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS',len(rows),'raw fault cases and',len(rejected),'rejected capture/omitted-check controls')
if __name__=='__main__':main()
