#!/usr/bin/env python3
"""Verify all four size-probed binary transfer results and their capture identities."""
import argparse
import json
from pathlib import Path
from product_inputs import ROOT,sha


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();run=a.run.resolve();out=a.output.resolve()
    assert run.is_relative_to(ROOT/'build') and out.is_relative_to(ROOT/'build')
    report=json.loads((run/'result.json').read_text());assert report['passed']
    assert len(report['cases'])==4 and {(r['mode'],r['physical_rows'],r['status_hidden']) for r in report['cases']}=={
        (mode,rows,hidden) for mode in ('upload','download') for rows,hidden in [(25,0),(50,1)]}
    for n,h in report['sources'].items():assert sha(ROOT/n)==h,n
    pairs={}
    for case in report['cases']:
        path=ROOT/case['audit_path'];assert sha(path)==case['audit_sha256'] and case['passed']
        r=json.loads(path.read_text());assert r['passed'] and r['terminal_sha256']==report['terminal_sha256']
        assert r['mode']==case['mode'] and r['payload_sha256']==case['payload_sha256']
        assert r['payload_bytes']==65539 and r['all256_values'] and r['payload_size_lookalikes']>0
        assert r['exact_proxy_streams'] and r['only_owned_menu_prefix_consumed'] and r['exact_destination']
        assert r['NAWS']==[[80,case['physical_rows']-(not case['status_hidden'])]]
        for group in ('sources','captures'):
            for n,h in r[group].items():assert sha(ROOT/n)==h,n
        wrapper=ROOT/'build/bbs-lab'/(case['label']+'-transfer')
        producer=json.loads((wrapper/'result.json').read_text());assert producer['passed'] and all(producer['checks'].values())
        for group in ('product_inputs','server_inputs'):
            for n,h in producer[group].items():assert sha(ROOT/n)==h,n
        pairs.setdefault(case['physical_rows'],[]).append(r['payload_sha256'])
    assert all(len(h)==2 and h[0]==h[1] for h in pairs.values())
    out.mkdir(parents=True,exist_ok=False)
    r=dict(passed=True,DOS_workflows=4,payload_bytes_per_workflow=65539,transferred_payload_bytes=262156,
        terminal_sha256=report['terminal_sha256'],report_sha256=sha(run/'result.json'),
        sources={str(Path(__file__).relative_to(ROOT)):sha(Path(__file__))},
        scope=__doc__+' Complete separate-process upload/download pairs at25-visible and50-hidden layouts. Real stock helper/official metadata,raw application equality and actualNAWS/BIOS/CRC/finish/menu. Does not establish cancellation,carrier/reconnect,alllayouts/protocols,SIP/DSP/analog/physical acceptance.')
    (out/'result.json').write_text(json.dumps(r,indent=2)+'\n')
    print('PASS four size-proxy transfers:262156 exact payload bytes')


if __name__=='__main__':main()
