#!/usr/bin/env python3
"""Independently inspect actual VM carrier-loss frames, audio and callback logs."""
import argparse
import json
from pathlib import Path
import struct
from synthmodem_vm_control import ROOT, sha
from synthmodem_gateway import records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('cohort', type=Path); a = parser.parse_args(); out = a.cohort.resolve()
    result = json.loads((out/'result.json').read_text()); checks = {}

    def check(name, value):
        checks[name] = bool(value)
        assert value, name

    check('producer_passed', result['passed'] and result['producer_exit']==0 and all(result['checks'].values()))
    for key in ('runtime_inputs','frozen_inputs'):
        for name,digest in result[key].items():
            check(key+':'+name, sha(Path(name) if Path(name).is_absolute() else ROOT/name)==digest)
    for name,digest in result['captures_sha256'].items(): check('capture:'+name,sha(out/name)==digest)
    data=(out/'control-wire.bin').read_bytes(); at=0; frames=[]
    while at<len(data):
        assert at+3<=len(data)
        size,kind=struct.unpack_from('<HB',data,at)
        assert 1<=size<=4094 and at+size+2<=len(data)
        frames.append((kind,data[at+3:at+size+2]));at+=size+2
    statuses=[(i,json.loads(body)) for i,(kind,body) in enumerate(frames) if kind==0x13]
    connect=[i for i,event in statuses if event.get('event')=='connect' and event.get('rate')==1200]
    down=[i for i,event in statuses if event.get('event')=='nocarrier']
    check('one_ordered_connect_and_carrier_loss',len(connect)==len(down)==1 and connect[0]<down[0])
    text=b''.join(body for kind,body in frames if kind==0x12)
    check('CONNECT_result_present_and_NO_CARRIER_result_not_forwarded',b'CONNECT 1200' in text and b'NO CARRIER' not in text)
    upstream=b''.join(body for kind,body in frames if kind==0x15)
    expected_up=(out/'expected-up.bin').read_bytes();expected_down=(out/'expected-down.bin').read_bytes()
    check('raw_online_input_exact_including_literal_carrier_text',upstream[result['onlineStart']:]==expected_up and b'NO CARRIER\r\n' in expected_up)
    check('raw_DATA_RX_matches_observer',upstream==(out/'guest-data.bin').read_bytes())
    check('caller_receives_exact_all_byte_payload', (out/'caller-data.bin').read_bytes()==expected_down and bytes(range(256))[::-1] in expected_down)
    check('no_data_or_AT_frames_after_carrier_loss',not any(kind in (0x12,0x15) for kind,_ in frames[down[0]+1:]))
    for name in ('rtp-from-caller.bin','rtp-from-answer.bin'):
        packets=records((out/name).read_bytes());headers=[]
        for packet in packets:
            assert len(packet)==172 and packet[0]==0x80 and packet[1]&127==0
            headers.append(struct.unpack_from('>HII',packet,2))
        check('continuous_RTP:'+name,bool(headers) and all(seq==(headers[0][0]+i)%65536 and stamp==(headers[0][1]+160*i)%2**32 and ssrc==headers[0][2] for i,(seq,stamp,ssrc) in enumerate(headers)))
        if name=='rtp-from-caller.bin': check('caller_continues_G711_silence_after_waveform_removal',len(packets)>30 and all(packet[12:]==bytes([255])*160 for packet in packets[-30:]))
    log=(out/'qemu.log').read_text()
    stop=log.rfind('modem_stop..');exiting=log.rfind('[ctrl I] modemd-ctrl exiting')
    mode=log.rfind('new state: MODEM_IDLE');reported=log.rfind('modem report result: 3 (NO CARRIER)')
    check('actual_guest_stop_helper_retirement_then_AT_result',0<=stop<exiting<mode<reported)
    check('actual_DSP_carrier_loss', 'carrier_loss_time 700 of 700 ms' in log and 'V22STAT: --> 16' in log)
    check('no_status_channel_error',not any(text in log for text in ('carrier status acknowledgement failed','Carrier status channel failed','Carrier status output drain timed out')))
    events=result['events'];removed=[e for e in events if e['type']=='caller-waveform-removed']
    hangups=[e for e in events if e['type']=='backend-hangup'];pressure=[e for e in events if e['type']=='pressure-start']
    check('one_notification_with_already_retired_writer',len(hangups)==1 and hangups[0]['writerClosed'] and hangups[0]['retired'] and not hangups[0]['connected'])
    check('real_Node_stream_and_writer_were_pending',len(pressure)==1 and pressure[0]['retained']>0 and pressure[0]['socketBytes']>0)
    assert len(removed)==1
    latency=(int(hangups[0]['ns'])-int(removed[0]['ns']))/1e6
    check('carrier_loss_within_declared_18_second_budget',0<latency<18000)
    receipt={'passed':all(checks.values()),'checks':checks,'cohort':str(out.relative_to(ROOT)),
             'upstream_bytes':len(expected_up),'downstream_bytes':len(expected_down),'carrier_loss_latency_ms':latency,
             'producer_result_sha256':sha(out/'result.json'),'audit_sha256':sha(Path(__file__)),
             'audit_inputs':{name:sha(ROOT/name) for name in ('lab/bbs/audit_carrier_vm.py','lab/bbs/synthmodem_vm_control.py','lab/bbs/synthmodem_gateway.py')},
             'scope':'Independent actual guest control-frame/audio/log audit. A corked real Node socket creates pending transmission; those deliberately abandoned bytes are not counted as successfully transmitted. No peer-initiated SIP BYE is inferred from waveform loss, and no DOS/BBS or physical modem/ATA acceptance is established.'}
    (out/'audit.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))


if __name__=='__main__': main()
