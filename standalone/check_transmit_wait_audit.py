#!/usr/bin/env python3
"""Semantic corruption controls with producer flags and capture hashes green."""
import argparse,copy,json,shutil
from pathlib import Path
import audit_aspect_transmit_wait as audit


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('software','CTS','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(audit.ROOT/'build') and not out.exists();out.mkdir(parents=True)
    rows=[]
    def exercise(name,source,cts,case,filename,change):
        folder=out/name;shutil.copytree(source,folder)
        report=audit.read(folder/'checks.json');row=next(r for r in report['cases'] if r['case']==case)
        target=folder/case/filename;target.write_bytes(change(target.read_bytes()))
        row['captures'][filename]=audit.sha(target)
        if filename=='serial.bin':row['wire_hex']=target.read_bytes().hex()
        assert report['passed'] and row['passed'] and all(row['checks'].values())
        (folder/'checks.json').write_text(json.dumps(report,indent=2)+'\n')
        try:audit.verify_run(folder,cts)
        except AssertionError:rows.append(dict(case=name,rejected=True,producer_flags_green=True,modified_capture_hash_updated=True))
        else:raise AssertionError('Corruption accepted: '+name)
    software=a.software.resolve();cts=a.CTS.resolve()
    def byte_at(data,at,value):return data[:at]+bytes([value])+data[at+1:]
    exercise('wrong-child-result',software,False,'short-timeout','RENDER.BIN',lambda b:byte_at(b,12,0))
    exercise('hardware-not-restored',software,False,'default-long','AFTER.BIN',lambda b:byte_at(b,0,b[0]^1))
    exercise('wrong-success-marker',software,False,'configured-long','WAIT.OK',lambda b:b'WRONG')
    exercise('ordinary-key-lost',software,False,'cancel-behind-key','serial.bin',lambda b:b.replace(b'qready',b'ready'))
    exercise('changed-payload',cts,True,'resume-hard','serial.bin',lambda b:b.replace(b'0123456789ABCDEF',b'X123456789ABCDEF',1))
    def short_hold(data):
        events=json.loads(data);low=next(e for e in events if e['kind']=='cts-low-go')
        next(e for e in events if e['kind']=='cts-high')['time']=low['time']+.5
        events.sort(key=lambda e:e['time']);return (json.dumps(events)+'\n').encode()
    exercise('short-stimulus-hold',cts,True,'timeout-hard','peer-events.json',short_hold)
    def bad_control(data):
        events=json.loads(data);event=next(e for e in events if e['kind']=='transport-receive' and 'ff' in e['hex'])
        raw=bytes.fromhex(event['hex']);at=raw.index(255);event['hex']=(raw[:at]+b'\xff\x7f'+raw[at+2:]).hex()
        return (json.dumps(events)+'\n').encode()
    exercise('invalid-transport-frame',cts,True,'resume-both','peer-events.json',bad_control)
    exercise('wrong-DOS-policy',cts,True,'timeout-both','dosbox.conf',lambda b:b.replace(b'PCPLUS_TXWAIT=2',b'PCPLUS_TXWAIT=30'))
    result=dict(passed=True,cases=rows,auditor_sha256=audit.sha(Path(audit.__file__)),checker_sha256=audit.sha(Path(__file__)),scope=__doc__+' Owned copied raw fixtures only. All eight semantic corruptions must be rejected; no production binary/state changes.')
    (out/'checks.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=True,rejected=len(rows))))


if __name__=='__main__':main()
