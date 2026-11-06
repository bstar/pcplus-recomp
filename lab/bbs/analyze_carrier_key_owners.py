#!/usr/bin/env python3
"""Explain observed browser-key ownership without inferring unobserved runs."""
import argparse
import json
from pathlib import Path
import re
import struct
from carrier_key_observer import decode
from product_inputs import ROOT,sha,select_product
from paced_bios_keys import entries


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--capture',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();cap,out=a.capture.resolve(),a.output.resolve()
    assert cap.is_relative_to(ROOT/'build') and out.is_relative_to(ROOT/'build') and not out.exists()
    report=json.loads((cap/'carrier-checks.json').read_text())
    trace=decode(cap/'LABELS.BIN');assert trace==report['guard_observer']['trace'] and trace['int16_restored']
    product=report['products']['TERMINAL.EXE'];binary,sources=select_product(ROOT/product['path'],'TERMINAL.EXE')
    assert sha(binary)==product['sha256']==sha(cap/'program/TERMINAL.EXE')
    for name,digest in report['sources'].items():assert sha(ROOT/name)==digest,name
    browser=[r for r in trace['records'] if r['key']==0x2960]
    image=binary.read_bytes();header=struct.unpack_from('<14H',image)
    mapping=binary.with_name('terminal.map').read_text()
    match=re.search(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+keyboard_bios_read\s*$',mapping,re.M|re.I)
    assert match
    read_seg,read_off=(int(v,16) for v in match.groups())
    result=dict(passed=bool(browser),carrier_workflow_passed=report['passed'],binary_sha256=sha(binary),
                trace=trace,browser_events=[],cause_for_prior_unobserved_failure_established=False)
    blockers=['terminal_transfer_active','terminal_transfer_pending','terminal_program_active',
              'terminal_program_pending','terminal_ansi_wait_active','terminal_parser_active']
    for row in browser:
        blocked={n:row[n] for n in blockers if row[n]}
        if row['connection_state'] not in (0,6):blocked['connection_state']=row['connection_state']
        item=dict(observed=row,sufficient_open_guard_blockers=blocked,
                  existing_view_owner=row['_redisplay_active'],pending_menu=row['terminal_menu_pending'])
        parent_base=row['parent_ds']-report['guard_observer']['parent_ds']
        caller_seg=row['caller_cs']-parent_base
        at=header[4]*16+caller_seg*16+row['caller_ip']-2
        assert caller_seg>=0 and image[at:at+2]==b'\xcd\x16'
        item['callsite']=dict(link_segment=caller_seg,return_offset=row['caller_ip'],
                              BIOS_interrupt_exact=True,
                              native_keyboard_read=caller_seg==read_seg and row['caller_ip']==read_off+6)
        if blocked and row['_redisplay_active']==0 and row['terminal_menu_pending']==0:
            import check_transport
            from check_redisplay_live import Redisplay
            check_transport.BINARY=binary;check_transport.MAP=binary.with_name('terminal.map')
            m=Redisplay()
            for n in row:
                if n in blockers or n in ('connection_state','_redisplay_active','_command_menu_active','terminal_menu_pending'):
                    m.put(n,row[n])
            m.call('terminal_redisplay_key',ax=0x2960,limit=3000000)
            from unicorn.x86_const import UC_X86_REG_EFLAGS
            assert m.uc.reg_read(UC_X86_REG_EFLAGS)&1 and not m.get('_redisplay_active')
            item['linked_guard_replay_refused']=True
            item['menu_pending_after_replay']=m.get('terminal_menu_pending')
        result['browser_events'].append(item)
    recipe=json.loads((cap/'recipe.json').read_text())['recipe'];ticks=0
    for wait,key in entries(recipe.replace('browser','!')):
        ticks+=wait
        if key==545:
            result['nominal_browser_schedule']=dict(ticks_after_helper_install=ticks,
                seconds_after_helper_install=ticks*65536/1193182,
                warning='Nominal BIOS timer recipe. Socket relay times use a different origin; do not directly subtract them or infer actual key-read time.')
    result['sources']={n:sha(ROOT/n) for n in ['lab/bbs/analyze_carrier_key_owners.py',
        'lab/bbs/carrier_key_observer.py','lab/bbs/paced_bios_keys.py',
        'standalone/check_transport.py','standalone/check_redisplay_live.py','standalone/dos_image.py']}
    result['capture_report_sha256']=sha(cap/'carrier-checks.json')
    result['parent_map_sha256']=sha(binary.with_name('terminal.map'))
    result['scope']=__doc__+' Parent DS and IRQ signature verified by passive observer. State recorded at BIOS read, before normalization/dispatch; linked replay uses captured sufficient blockers with modeled BIOS/UART. Missing fields/other contexts are not assumed idle. No claim about the cause of earlier unobserved failures or physical timing.'
    out.mkdir();(out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(passed=result['passed'],workflow=report['passed'],browser_events=result['browser_events']),indent=2))
    return 0 if result['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
