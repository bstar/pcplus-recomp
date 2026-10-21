#!/usr/bin/env python3
"""Read-only packet-arrival/cancel timing; never substitutes for transfer audit."""
import argparse,hashlib,json
from pathlib import Path
from modem import Telnet
from audit_zmodem import scan,packet,metadata


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('cohort',type=Path)
    out=parser.parse_args().cohort.resolve()
    read=lambda name:json.loads((out/name).read_text())
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    result=read('result.json');assert result['route']=='download'
    audit=read('independent-audit.json');node=read('node-result.json')
    caller=(out/'caller-decoded.bin').read_bytes()
    serial=(out/'serial-in.bin').read_bytes()
    display,_=Telnet().feed((out/'bbs-output.bin').read_bytes())
    bridge=audit['payloads']['expected_bridge_bytes'];body=caller[bridge:]
    prefix=next((i for i,(a,b) in enumerate(zip(body,display)) if a!=b),min(len(body),len(display)))
    writes=[json.loads(s) for s in (out/'serial-write-events.jsonl').read_text().splitlines()]
    reads=[json.loads(s) for s in (out/'serial-input-events.jsonl').read_text().splitlines()]
    anchor=next(e for e in node['events'] if 'monotonicNs' in e)
    def read_time(offset):
        row=next(e for e in reads if e['offset']<=offset<e['offset']+e['length'])
        return (int(row['monotonicNs'])-int(anchor['monotonicNs']))/1e9+anchor['seconds']
    serial_prefix=b'\r\nOK\r\n\r\nCONNECT 1200\r\n'
    assert (out/'serial-out.bin').read_bytes()==serial_prefix+caller
    def write_time(offset):
        if offset>=prefix:return None
        offset+=len(serial_prefix)+bridge
        return next(e['attemptedAt'] for e in writes if e['offset']<=offset<e['offset']+e['length'])
    source=Path(result['download']['expected_path']);expected=source.read_bytes()
    assert sha(source)==result['download']['expected_sha256']
    first=None
    for h in scan(display):
        if h['type']!=4:continue
        try:
            p=packet(display,h['end'],h['format']);name,size=metadata(p['payload'])
            if name=='PCXTEST.BIN' and size==len(expected):first=h;break
        except (AssertionError,ValueError,UnicodeError):pass
    packets=[];headers=[];errors=[];cursor=first['offset'] if first else len(display)
    while cursor<len(display):
        h=next(scan(display,cursor),None)
        if h is None:break
        headers.append(h);cursor=h['end']
        try:
            if h['type']==4:
                p=packet(display,cursor,h['format']);cursor=p['end']
            elif h['type']==10:
                position=h['position']
                while True:
                    p=packet(display,cursor,h['format']);cursor=p['end']
                    data=p.pop('payload');assert data==expected[position:position+len(data)],'Source mismatch'
                    position+=len(data)
                    start=write_time(p['offset']);crc=write_time(p['crc_end']-1)
                    packets.append({**p,'position':position,'source_exact':True,
                        'caller_start_seconds':start,'caller_CRC_seconds':crc,
                        'caller_duration_seconds':crc-start if crc is not None else None})
                    if p['ending'] in (104,107):break
        except (AssertionError,ValueError,UnicodeError) as e:
            errors.append({'offset':cursor,'error':repr(e)});break
    controls=[{**h,'frontend_read_seconds':read_time(h['offset'])} for h in scan(serial)]
    can=serial.find(b'\x18'*5);cancel=read_time(can) if can>=0 else None
    before=[p for p in packets if p['caller_CRC_seconds'] is not None and cancel is not None and p['caller_CRC_seconds']<cancel]
    previous=before[-1] if before else None
    names=['result.json','independent-audit.json','node-result.json','caller-decoded.bin','serial-in.bin','serial-out.bin','bbs-output.bin','serial-write-events.jsonl','serial-input-events.jsonl']
    report={'diagnostic_only':True,'caller_BBS_exact_prefix_bytes':prefix,'caller_BBS_bytes':len(body),
        'BBS_display_bytes':len(display),'caller_is_exact_BBS_prefix':prefix==len(body),
        'source_offer_found':first is not None,'packets':packets,'sender_headers':headers,
        'receiver_controls':controls,'packet_parse_errors':errors,'cancel_frontend_seconds':cancel,
        'cancel_after_previous_CRC_seconds':cancel-previous['caller_CRC_seconds'] if previous else None,
        'previous_CRC_packet_position':previous['position'] if previous else None,
        'captures_sha256':{n:sha(out/n) for n in names},'checker_sha256':sha(Path(__file__)),
        'scope':'CRC/source-verified sender packets and observed frontend byte times only. Node monotonic reads are approximately aligned through one event anchor. Successful local write callbacks and CRC arrival do not prove application consumption or storage acceptance. No complete protocol/finish, cleanup or compatibility pass follows; use the independent transfer and ownership audits.'}
    (out/'download-timing.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'prefix_bytes':prefix,'packets':len(packets),'cancel_after_previous_CRC_seconds':report['cancel_after_previous_CRC_seconds'],'parse_errors':errors}))


if __name__=='__main__':main()
