#!/usr/bin/env python3
"""Verify complete fault images differ only at their two declared phase immediates."""
import argparse,json,re,struct
from pathlib import Path
from build_path_session import ROOT,sha

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--pattern',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir();groups={}
    for kind in ['own','foreign']:
        ref=(ROOT/a.pattern.format(kind=kind,phase=17)).resolve();assert ref.is_relative_to(ROOT/'build')
        base=ref.read_bytes();listing=ref.with_name('ASPECT.map').read_text()
        symbols={n:(int(s,16),int(o,16)) for s,o,n in re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$',listing,re.M|re.I)}
        seg,off=symbols['_runtime_external_phase'];header=struct.unpack_from('<14H',base)
        start=header[4]*16+seg*16+off;body=base[start:start+160]
        compare=b'\x83\x7e\x04\x11';probe=symbols['_runtime_external_result_probe'][1]
        marker=b'\xc7\x06'+struct.pack('<H',probe)+b'\x11\x01'
        assert body.count(compare)==body.count(marker)==1
        expected=sorted([start+body.index(compare)+3,start+body.index(marker)+4]);rows=[]
        for phase in [17,5,6,8,10,22]:
            binary=(ROOT/a.pattern.format(kind=kind,phase=phase)).resolve();assert binary.is_relative_to(ROOT/'build')
            data=binary.read_bytes();m=json.loads(binary.with_name('manifest.json').read_text())
            assert m['diagnostic_build'] and m['diagnostic_lease_fault_phase']==phase
            assert bool(m['diagnostic_lease_fault_foreign_ds'])==(kind=='foreign') and m['binary_sha256']==sha(binary)
            assert len(data)==len(base)
            delta=[i for i,(x,y) in enumerate(zip(base,data)) if x!=y]
            assert delta==([] if phase==17 else expected)
            assert all(base[i]==17 and data[i]==phase for i in delta)
            rows.append(dict(phase=phase,sha256=sha(binary),changed_file_offsets=delta))
        groups[kind]=dict(reference_sha256=sha(ref),function_file_offset=start,phase_immediate_offsets=expected,variants=rows)
    result=dict(passed=True,groups=groups,sources={'standalone/check_lease_fault_variants.py':sha(Path(__file__))},
        scope=__doc__+' Exact whole-image comparison within each own/foreign-DS group, with instruction-pattern checks inside the linked phase helper. Representative clean-source rebuilds remain separate evidence; not twelve independent export builds.')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS twelve whole images; two phase-immediate bytes per group')
if __name__=='__main__':main()
