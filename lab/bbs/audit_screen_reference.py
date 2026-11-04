#!/usr/bin/env python3
"""Compare a CPR-bounded stock-BBS stream with the final DOS cell snapshot."""
import argparse
import importlib.metadata
import inspect
import json
from pathlib import Path
import re
import struct
import sys
from product_inputs import ROOT,sha
sys.path.insert(0,str(ROOT/'standalone'))
from test_ansi_reference_dos import reference

CSI=re.compile(rb'\x1b\[([0-?]*)([ -/]*)([@-~])')

def cell_projection(payload):
    """FNT0;0 selects the primary CP437 font; font pixels are not VGA cells.

    pyte0.8.2 drops the intermediate and calls CUB with two parameters. Only
    the exact default-font probe is projected out, with every offset retained.
    The pinned RIP query passes unchanged; other intermediate controls refuse.
    Nothing else is stripped/rewritten.
    ECMA-48 fifth edition8.3.53 defines FNT separately from cursor movement.
    """
    projections=[];parts=[];start=0
    for match in CSI.finditer(payload):
        params,intermediate,final=match.groups()
        if not intermediate:continue
        # Pinned Synchronet answer.cpp sends this RIP capability query. It
        # has no ANSI cell action; pyte's unknown-final path ignores it too.
        # Pass it through unchanged rather than projecting away input bytes.
        if (params,intermediate,final)==(b'',b'!',b'_'):continue
        assert (params,intermediate,final)==(b'0;0',b' ',b'D'),('Unsupported reference intermediate',match.start(),match.group().hex())
        parts.append(payload[start:match.start()]);start=match.end()
        projections.append(dict(offset=match.start(),bytes_hex=match.group().hex(),reason='Default primary CP437 font selection; font pixels excluded'))
    parts.append(payload[start:])
    return b''.join(parts),projections

def audit(output,bridge):
    output=Path(output).resolve();bridge=Path(bridge).resolve()
    assert output.is_relative_to(ROOT/'build') and bridge.is_relative_to(ROOT/'build')
    producer=json.loads((output/'proxy-integration.json').read_text());assert producer['passed']
    proof=json.loads((bridge/'1-screen-reference.json').read_text())
    ready=json.loads((bridge/'ready.json').read_text());closed=json.loads((bridge/'1-closed.json').read_text())
    assert proof['enabled'] and proof['armed'] and proof['frozen'] and proof['reply']
    assert producer['screen_reference']==proof
    layout=producer.get('display_layout')
    if layout:
        raw=(output/'TEST.PRM').read_bytes()
        hidden,selector,physical,mode=[struct.unpack_from('<H',raw,at)[0] for at in (0x1c2,0x1c8,0x1ca,0x4ec)]
        assert hidden in (0,1) and physical in (25,28,43,50) and (selector,mode)==(2,0)
        rows=physical-(not hidden)
        assert layout==dict(physical_rows=physical,logical_rows=rows,status_hidden=hidden)
        actual_rows,font,mode_cols,page=struct.unpack('<4H',(output/'GEOM.BIN').read_bytes())
        assert (actual_rows,font,mode_cols,page>>8)==(physical,14 if physical==28 else 8 if physical in (43,50) else 16,0x5003,0)
    else:
        rows=producer['terminal_geometry']['rows'];physical=25;hidden=0
        assert rows==24
    assert rows==ready['terminalRows']==proof['terminalRows']
    payload=(bridge/'1-screen-prefix.bin').read_bytes()
    delivered=(output/'serial-sent.bin').read_bytes()
    assert payload==delivered==(bridge/'1-serial-output.bin').read_bytes(),'Snapshot must pair with exactly the delivered prefix'
    assert len(payload)==proof['prefixBytes'] and sha(bridge/'1-screen-prefix.bin')==proof['prefixSha256']
    assert payload.endswith(b'\x1b[6n')
    input_wire=(bridge/'1-serial-input.bin').read_bytes();probe_input=(bridge/'1-probe-input.bin').read_bytes()
    replies=[[int(a),int(b)] for a,b in re.findall(rb'\x1b\[(\d+);(\d+)R',probe_input)]
    assert replies==[proof['reply']] and input_wire.endswith(probe_input)
    if 'probeReplyConsumed' in proof:
        assert proof['probeReplyConsumed'] and not proof.get('probeTimeout') and not proof.get('probeOverflow')
        raw=bytes.fromhex(proof['probeReplyHex']);assert raw==f'\x1b[{proof["reply"][0]};{proof["reply"][1]}R'.encode()
        assert probe_input.count(raw)==1
        without_reply=input_wire[:-len(probe_input)]+probe_input.replace(raw,b'',1)
        forwarded=(bridge/'1-proxy-input.bin').read_bytes()
        assert without_reply==forwarded,'Only the fixture query reply may be removed before the actual proxy; preserve all other TX'
    actual=(output/'SCREEN.BIN').read_bytes();assert len(actual)==(8000 if layout else 4000)
    assert sha(output/'SCREEN.BIN')==producer['screen_sha256']
    projected,projections=cell_projection(payload)
    expected,cursor=reference(projected,rows=rows)
    (output/'reference-input.bin').write_bytes(projected)
    (output/'reference-cells.bin').write_bytes(expected)
    differences=[dict(row=i//80+1,column=i%80+1,actual=list(actual[2*i:2*i+2]),expected=list(expected[2*i:2*i+2])) for i in range(rows*80) if actual[2*i:2*i+2]!=expected[2*i:2*i+2]]
    checks=dict(producer_passed=producer['passed'],runtime_unchanged=closed['source_unchanged'],
                exact_delivered_prefix=True,real_single_CPR_boundary=True,
                cursor_matches_reference=list(cursor)==proof['reply'],all_cells_match=not differences,
                hardware_restored=(output/'BEFORE.BIN').read_bytes()==(output/'AFTER.BIN').read_bytes(),
                status_ownership=bool(hidden) or b'Disconnected' in actual[(physical-1)*160:physical*160:2],font_probe_projection_explicit=all(p['bytes_hex']=='1b5b303b302044' for p in projections),
                held_output_exact=len((bridge/'1-held-output.bin').read_bytes())==proof['heldBytes'])
    peer=producer.get('server','ENiGMA');assert peer in ('ENiGMA','Synchronet')
    result=dict(passed=all(checks.values()),checks=checks,binary_sha256=producer['binary_sha256'],
                matched_cells=rows*80-len(differences),logical_rows=rows,physical_rows=physical,status_hidden=hidden,
                different_cells=len(differences),first_differences=differences[:40],reference_cursor=cursor,actual_CPR=proof['reply'],
                delivered_bytes=len(payload),held_after_boundary=proof['heldBytes'],font_projections=projections,
                pyte_version=importlib.metadata.version('pyte'),wcwidth_version=importlib.metadata.version('wcwidth'),
                captures={str(p):sha(p) for p in [output/'proxy-integration.json',output/'SCREEN.BIN',output/'serial-sent.bin',output/'reference-input.bin',output/'reference-cells.bin',bridge/'1-screen-reference.json',bridge/'1-screen-prefix.bin',bridge/'1-held-output.bin',bridge/'1-probe-input.bin',bridge/'1-serial-input.bin',bridge/'1-serial-output.bin',bridge/'1-closed.json',bridge/'ready.json']},
                sources={p:sha(ROOT/p) for p in ['lab/bbs/audit_screen_reference.py','lab/bbs/terminal_geometry.py','lab/bbs/synthmodem_proxy_serial.js','lab/bbs/test_synthmodem_proxy_dos.py','standalone/test_ansi_reference_dos.py','nix/flake.nix','nix/flake.lock']},
                scope='One actual stock '+peer+' editor snapshot after the complete delivered stream prefix, at independently verified physical/logical geometry. Independent pyte cell/cursor interpretation; only explicitly recorded default-font probes are projected out. A real final CPR proves ordered parser consumption; later BBS output is held by the owned fixture until DOS exits. No font-pixel, every-intermediate-frame, unframed/SIP/DSP/analog or physical acceptance.')
    if layout:
        result['captures'].update({str(p):sha(p) for p in [output/'TEST.PRM',output/'GEOM.BIN',output/'GEOM.COM',output/'SNAP.COM',output/'sampler.asm']})
    result['reference_modules']={name:sha(Path(inspect.getfile(__import__(name,fromlist=['_'])))) for name in ['pyte.screens','pyte.streams','pyte.graphics','pyte.charsets','pyte.modes','pyte.control','pyte.escape','wcwidth.wcwidth']}
    result['known_non_cell_probes_passed_unchanged']=[dict(offset=m.start(),bytes_hex=m.group().hex(),reason='Stock Synchronet RIP capability query') for m in CSI.finditer(payload) if m.group()==b'\x1b[!_']
    if 'probeReplyConsumed' in proof:
        result.update(fixture_CPR_consumed=True,proxy_input_bytes=len(forwarded),unforwarded_tail_bytes=len(without_reply)-len(forwarded))
        result['captures'][str(bridge/'1-proxy-input.bin')]=sha(bridge/'1-proxy-input.bin')
    (output/'screen-reference-audit.json').write_text(json.dumps(result,indent=2)+'\n')
    print('PASS' if result['passed'] else 'FAIL',len(payload),'delivered bytes;',len(differences),'different cells; reference cursor',cursor,'actual',proof['reply'])
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--bridge',type=Path,required=True);a=p.parse_args()
    assert audit(a.output,a.bridge)['passed']

if __name__=='__main__':main()
