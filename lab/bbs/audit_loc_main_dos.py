#!/usr/bin/env python3
"""Compare copied LoC menu source cells, actual focused input and raw NAWS.

Independent ANSI oracle plus the art's source glyph/palette model. No live board,
font-pixel, full transfer/SIP/DSP/analog or physical acceptance.
"""
import argparse
import json
import struct
from pathlib import Path

from product_inputs import ROOT, sha
from audit_screen_reference import audit
from audit_size_probe_screen import telnet
from enigma_loc_menu_fixture import verify

PALETTE = [('#000000',0),('#555555',8),('#aaaaaa',7),('#ffffff',15),
           ('#0000aa',1),('#5555ff',9),('#00aaaa',3),('#55ffff',11),('#aa5500',6),('#ffff55',14)]


def rgb(value):
    value = value.lstrip('#')
    if len(value)==3:
        value = ''.join(c*2 for c in value)
    n = int(value,16)
    return n>>16, n>>8&255, n&255


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--bridge', type=Path, required=True)
    a = p.parse_args()
    out, bridge = a.output.resolve(), a.bridge.resolve()
    assert out.is_relative_to(ROOT/'build') and bridge.is_relative_to(ROOT/'build')
    producer = json.loads((out/'proxy-integration.json').read_text())
    assert producer['passed'] and all(producer['checks'].values())
    for name,digest in producer['product_inputs'].items():
        assert sha(ROOT/name)==digest, name
    candidate = ROOT/producer['fixture']
    verify(candidate)
    cells = audit(out,bridge)
    assert cells['passed'] and cells['different_cells']==0
    raw = (out/'TEST.PRM').read_bytes()
    hidden,selector,physical,mode = [struct.unpack_from('<H',raw,at)[0] for at in (0x1c2,0x1c8,0x1ca,0x4ec)]
    assert (selector,mode)==(2,0) and hidden in (0,1) and physical in (25,28,43,50)
    logical = physical-(not hidden)
    layout_path = candidate/'mods/loc_main_menu/classic-pillars.json'
    layout = json.loads(layout_path.read_text())
    art = layout['cells']
    assert len(art)==25 and all(len(row)==80 for row in art)
    if logical==24:
        art = art[:9]+art[10:]
    prompt_row = layout['prompt']['row']-(logical==24)
    prompt_col, width = layout['prompt']['col'], layout['prompt']['width']
    assert (prompt_col,width)==(46,14) and 1<=prompt_row<=logical
    expected = bytearray(b' \x07'*(logical*80))
    for row, line in enumerate(art):
        for col, cell in enumerate(line):
            value = rgb(cell['color'])
            attr = min(PALETTE,key=lambda p:sum((a-b)**2 for a,b in zip(value,rgb(p[0]))))[1]
            glyph = cell['ch'].replace('Ð','D').encode('cp437')
            assert len(glyph)==1
            at = (row*80+col)*2
            expected[at:at+2] = glyph+bytes([attr])
    screen = (out/'SCREEN.BIN').read_bytes()
    first = (prompt_row-1)*80+prompt_col-1
    excluded = set(range(first,first+width))
    differences = [index for index in range(logical*80) if index not in excluded
                   and screen[index*2:index*2+2]!=expected[index*2:index*2+2]]
    assert not differences, ('source art mismatch',differences[:20])
    field = screen[first*2:(first+width)*2]
    assert field[::2]==b'LOCSNAP'+b' '*7
    assert field[1:14:2]==bytes([15])*7
    assert cells['actual_CPR']==[prompt_row,prompt_col+7]
    wire = (bridge/'1-serial-input.bin').read_bytes()
    application,subs,options = telnet((bridge/'1-telnet-input.bin').read_bytes())
    naws = [struct.unpack('>HH',sub[1:]) for sub in subs if sub[0]==31 and len(sub)==5]
    assert naws==[(80,logical)]
    report = b'\x1b'+f'[8;{logical};80t'.encode()
    assert wire.count(report)==1 and report not in application
    assert b'M\rQ\rLOCSNAP' in application
    assert b'\x00' not in application  # No local Alt-Z BIOS key leaked into BBS input.
    session = [json.loads(line) for line in (out/'server-session.jsonl').read_text().splitlines()]
    sizes = [[r['width'],r['height']] for r in session if r.get('source')=='NAWS' and r.get('msg')=='Telnet: Windows size updated']
    assert sizes==[[80,logical]]
    paths = [out/'proxy-integration.json',out/'screen-reference-audit.json',out/'SCREEN.BIN',
             out/'REFVIEW.BIN',out/'TEST.PRM',out/'server-session.jsonl',
             bridge/'1-telnet-input.bin',bridge/'1-telnet-output.bin',
             bridge/'1-serial-input.bin',bridge/'1-serial-output.bin',layout_path]
    result = dict(passed=True, binary_sha256=producer['binary_sha256'], physical_rows=physical,
                  logical_rows=logical,status_hidden=hidden,matched_reference_cells=logical*80,
                  matched_source_art_cells=logical*80-width,field_cells=width,
                  field_text='LOCSNAP',field_foreground=15,actual_CPR=cells['actual_CPR'],NAWS=naws,
                  native_reference_observed=True,all_39_native_labels=True,message_menu_return=True,
                  captures={str(path.relative_to(ROOT)):sha(path) for path in paths},
                  sources={str(Path(__file__).relative_to(ROOT)):sha(Path(__file__))},scope=__doc__+
                  ' Every logical cell matches actual delivered ANSI; all except14 live field cells also match independent source art/palette, including blank extension rows. Field text/intensity/cursor checked separately. Explicit Ð->D CP437 fallback; source24-row blank-separator projection. Real modal witness and authenticated M/Q return; selected menu only.')
    (out/'loc-main-audit.json').write_text(json.dumps(result,indent=2)+'\n')
    print('PASS LoC source art/focus/modal return:',logical*80,'reference cells,',logical*80-width,'source cells')


if __name__=='__main__':
    main()
