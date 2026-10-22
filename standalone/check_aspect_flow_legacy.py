#!/usr/bin/env python3
"""Prove an earlier source-built child refuses v5 before UART acquisition."""
import argparse,json,shutil
from pathlib import Path
from check_aspect_flow_handoff import Flow,q,ROOT,sha


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--baseline',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--version',type=int,choices=[5,6],default=5);a=p.parse_args()
    baseline=a.baseline.resolve();out=a.output.resolve()
    assert baseline.is_relative_to(ROOT/'build') and out.is_relative_to(ROOT/'build') and not out.exists()
    report=json.loads((baseline/'checks.json').read_text());assert report['passed'] and report['gap_reproduced']
    q.BINARY=baseline/('timeout-soft/ASPECT.EXE' if (baseline/'timeout-soft/ASPECT.EXE').exists() else 'soft/ASPECT.EXE');q.MAP=baseline/'inputs/build/aspect-runner/ASPECT.map'
    assert sha(q.BINARY)==report['runner_sha256'] and sha(q.MAP)==report['inputs']['build/aspect-runner/ASPECT.map']
    m=Flow();m.words[1]=a.version;m.publish();m.mode(b'S');before=bytes(m.uc.mem_read(m.desc,50))
    assert m.open()==1 and not m.writes and not m.get('_aspect_serial_active') and not m.requests
    assert bytes(m.uc.mem_read(m.desc,50))==before
    out.mkdir(parents=True);inputs={}
    for source in [Path(__file__),ROOT/'standalone/check_aspect_flow_handoff.py',ROOT/'standalone/check_aspect_render_client.py',q.BINARY,q.MAP]:
        target=out/'inputs'/source.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
        inputs[str(source.relative_to(ROOT))]=sha(source)
    result=dict(passed=True,runner_sha256=sha(q.BINARY),descriptor_version=a.version,typed_status=1,UART_writes=0,renderer_requests=0,descriptor_unchanged=True,
                inputs=inputs,scope=__doc__+' Real old parser instructions with modeled DOS/MCB/UART boundaries. Earlier owned source build, not an original proprietary executable. No actual DOS wrong-version launch claim.')
    (out/'checks.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=True,typed_status=1,UART_writes=0)))


if __name__=='__main__':main()
