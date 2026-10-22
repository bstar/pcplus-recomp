#!/usr/bin/env python3
"""Drive emulated physical CTS through DOSBox-X's nullmodem control framing.

The peer uses the pinned2026.07.02 FF/control protocol, not a modified product
MSR value. RTS/DTR status frames from DOSBox are separately retained. No XOFF is
sent. The actual HARD/BOTH UART transmit path must wait until CTS is reasserted.
"""
import argparse,inspect,json,re,shutil,struct,subprocess,types
from pathlib import Path
import test_aspect_flow_return_dos as flow
ROOT=flow.ROOT;sha=flow.sha;ESC=b'\x1b'
SOURCE_URL='https://github.com/joncampbell123/dosbox-x/blob/dosbox-x-v2026.07.02/src/hardware/serialport/nullmodem.cpp'


def adapter(out,events):
    # Reuse the exact owned peer/modem/file/restore driver; replace only its
    # transport encoding and hardware-flow stimulus, never UART replies.
    text=inspect.getsource(flow.adapter)
    text=text.replace('def adapter(out,events,resume_after=1.2,entry_pause=False):','def build(out,events,resume_after=1.2,entry_pause=False):')
    text=text.replace("conn.settimeout(.03);line=bytearray();", "conn.settimeout(.03);framing_escape=False;conn.sendall(b'\\xff\\x03');event('cts-ready',b'\\xff\\x03');line=bytearray();")
    needle="     wire.extend(block);event('receive',block)"
    replacement=r'''     event('transport-receive',block);decoded=bytearray()
     for value in block:
      if framing_escape:
       framing_escape=False
       if value==255:decoded.append(value)
       else:event('modem-status',bytes([value]))
      elif value==255:framing_escape=True
      else:decoded.append(value)
     block=bytes(decoded)
     wire.extend(block);event('receive',block)'''
    assert text.count(needle)==1;text=text.replace(needle,replacement)
    text=text.replace("conn.sendall(b'\\x11');event('xon',b'\\x11')", "conn.sendall(b'\\xff\\x03');event('cts-high',b'\\xff\\x03')")
    text=text.replace("conn.sendall(b'\\x13GO');event('xoff-go',b'\\x13GO')", "conn.sendall(b'\\xff\\x02GO');event('cts-low-go',b'\\xff\\x02GO')")
    text=text.replace('no_data_during_XOFF','no_data_during_CTS')
    marker="    module=types.ModuleType('flow_return_peer')"
    assert text.count(marker)==1;text=text.replace(marker,"    text=text.replace('transparent:1','transparent:0')\n"+marker)
    module=types.ModuleType('cts_adapter_factory');module.__dict__.update(flow.__dict__)
    exec(compile(text,__file__,'exec'),module.__dict__);return module.build(out,events)


def observer(out):
    flow.observer(out);p=out/'observer.asm';text=p.read_text()
    child=flow.window.symbols(ROOT/'build/aspect-runner/ASPECT.map')
    needle=' cmp word [es:'+str(child['uart_tx_paused'][1])+'],0\n'
    assert text.count(needle)==1
    added=' cmp word [es:'+str(child['uart_hardware_flow'][1])+'],1\n jne .hard_checked\n inc word [cs:hardware_enabled_ticks]\n.hard_checked:\n'
    text=text.replace(needle,added+needle).replace('sample_end:\nowner_table:','hardware_enabled_ticks: dw 0\nsample_end:\nowner_table:')
    p.write_text(text);subprocess.run(['nasm','-fbin',str(p),'-o',str(out/'RENDER.COM')],check=True)
    return (out/'RENDER.COM').read_bytes()


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--label',required=True);a=p.parse_args()
    assert re.fullmatch(r'[A-Za-z0-9_-]+',a.label)
    out=ROOT/'build/aspect-cts-dos'/a.label;out.mkdir(parents=True,exist_ok=False);inputs={}
    for directory,leaf in [('terminal','TERMINAL.EXE'),('aspect-runner','ASPECT.EXE')]:
        base=ROOT/'build'/directory;m=json.loads((base/'manifest.json').read_text());assert sha(base/leaf)==m['binary_sha256'];inputs.update(m['sources'])
        for f in (base/leaf,base/'manifest.json',*base.glob('*.map')):inputs[str(f.relative_to(ROOT))]=sha(f)
    for f in (Path(__file__),Path(flow.__file__),Path(flow.connection.__file__),Path(flow.renderer.__file__),Path(flow.window.__file__)):
        inputs[str(f.relative_to(ROOT))]=sha(f)
    for name,digest in inputs.items():
        assert sha(ROOT/name)==digest;target=out/'inputs'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,target)
    compiled=observer(out);rows=[]
    source='proc main\nwaitfor "LOGIN:" 5\nset duplex full\ntransmit "KEYREADY"\nwaitfor "GO" 5\n'+('transmit "0123456789ABCDEF"\n'*128)+'fopen 5 "CTS.OK" "wb"\nfputs 5 "RESUMED"\nfclose 5\nendproc\n'
    for soft in (0,1):
        name='both' if soft else 'hard';folder=out/name;folder.mkdir();events=[];peer=adapter(out,events)
        shutil.copy2(ROOT/'build/terminal/TERMINAL.EXE',folder/'TERMINAL.EXE');peer.BINARY=folder/'TERMINAL.EXE'
        payload=bytearray(flow.directory(profile=4));payload[302:311]=b'LOGIN\0\0\0\0'
        files={'LOGIN.ASP':source.encode(),'LOGIN.ASX':flow.renderer.compile_source(source),'ASPECT.EXE':(ROOT/'build/aspect-runner/ASPECT.EXE').read_bytes(),'RENDER.COM':compiled}
        try:
            r=peer.run(name,'success','p6000 r e a d y p900 a-x',directory=bytes(payload),prm=flow.prm(soft=soft,hard=1),arguments='@D:\\TEST.PRM /E:D:\\TEST.DIR /N:1 /A:NETWORK',files=files,profile=4,working_drive='d',observer='RENDER',banner=ESC+b'[2J'+ESC+b'[HFIRST BYTE SAFE'+ESC+b'[6n'+ESC+b'[0cLOGIN:')
        finally:(folder/'peer-events.json').write_text(json.dumps(events,indent=2)+'\n')
        raw=(folder/'RENDER.BIN').read_bytes();head=struct.unpack_from('<7H',raw);state=struct.unpack('<4H',raw[-8:]);wire=(folder/'serial.bin').read_bytes()
        pause=b'\x13\x11' if soft else b''
        expected=b'ATZ\rATDCaseTest:23\r'+pause+ESC+b'[1;16R'+ESC+b'[?62;2cKEYREADY'+flow.PAYLOAD+pause+b'ready'+ESC+b'[1;24R+++ATH\r'
        checks=dict(r['checks'],actual_child_exit=head[:4]==(0x524e,1,1,1) and head[6]==0,JFT_restored=raw[14:34]==raw[34:54],owners_restored=raw[54:470]==raw[470:886],hardware_owner_observed=state[3]>12,software_pause_not_used=state[0]==0,parent_return=state[1]>18 and state[2]==0,script_resumed=(folder/'CTS.OK').is_file() and (folder/'CTS.OK').read_bytes()==b'RESUMED',exact_whole_wire=wire==expected,transport_control_seen=any(e['kind']=='modem-status' for e in events))
        rows.append(dict(case=name,passed=all(checks.values()),checks=checks,observations=list(state),wire_hex=wire.hex(),captures={str(f.relative_to(folder)):sha(f) for f in folder.rglob('*') if f.is_file()}))
        print(json.dumps(dict(case=name,passed=rows[-1]['passed'],checks=checks,observations=list(state))),flush=True)
    report=dict(passed=all(r['passed'] for r in rows),cases=rows,inputs=inputs,parent_sha256=sha(ROOT/'build/terminal/TERMINAL.EXE'),runner_sha256=sha(ROOT/'build/aspect-runner/ASPECT.EXE'),emulator_source=SOURCE_URL,scope=__doc__+' Actual8086 DOSBox-X2026.07.02 nullmodem transport. Does not establish physical ISA UART/modem timing, sustained pressure, timeout/cancel CTS handback or every application gate.')
    (out/'checks.json').write_text(json.dumps(report,indent=2)+'\n');assert report['passed']


if __name__=='__main__':main()
