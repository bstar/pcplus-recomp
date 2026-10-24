#!/usr/bin/env python3
"""Verify namespace separation, cold native calls and live PROGRAM retention."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import tempfile

import check_transport
from check_line_edit_live import Abort,ROOT
from check_terminal_reset_live import Live
from check_redisplay_live import Redisplay
from terminal_memory import inspect_terminal_memory
from unicorn.x86_const import *


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',type=Path,required=True)
    args=p.parse_args();binary=args.terminal.resolve();base=binary.parent
    manifest=json.loads((base/'manifest.json').read_text())
    assert manifest['experimental_native_reset_bank']and sha(binary)==manifest['binary_sha256']
    for name,digest in manifest['sources'].items():assert sha(ROOT/name)==digest,name
    memory=inspect_terminal_memory(binary,base/'terminal.map');assert memory==manifest['memory_layout']
    check_transport.BINARY=binary;check_transport.MAP=base/'terminal.map';cases=[]
    for request in (0,1,2,65535):
        m=Live();m.call('terminal_reset_capture');m.position(5,17)
        if memory['native_reset_overlay']:
            workspace=m.base+memory['native_reset_bank_start'];workspace_bytes=memory['native_reset_workspace_bytes']
            m.uc.mem_write(workspace,b'\xa5'*workspace_bytes)
        m.receive_irq(bytes(range(256))*2)
        root_end=m.offset('terminal_stack_top')-m.stack_bytes
        data=bytes(m.uc.mem_read(m.data_base,root_end))
        shadow=m.get('erase_shadow_segment')*16+m.get('erase_shadow_offset')
        root_shadow=bytes(m.uc.mem_read(shadow,8192));screen=bytes(m.uc.mem_read(0xb8000,4000))
        for register,value in[(UC_X86_REG_BX,0x9876),(UC_X86_REG_CX,0x4567),(UC_X86_REG_DX,0xabcd)]:m.uc.reg_write(register,value)
        result=m.call('reset_bank_call',ax=request,limit=2000000)
        assert result==(0 if request<=1 else 1)
        assert bytes(m.uc.mem_read(m.data_base,root_end))==data,'Native bank wrote live data/BSS'
        assert bytes(m.uc.mem_read(shadow,8192))==root_shadow,'Native bank wrote the live shadow'
        assert m.get('uart_rx_count')==512 and not m.tx
        for register,value in[(UC_X86_REG_BX,0x9876),(UC_X86_REG_CX,0x4567),(UC_X86_REG_DX,0xabcd),
            (UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678),(UC_X86_REG_ES,0xb800),
            (UC_X86_REG_DS,m.ds),(UC_X86_REG_SS,m.ds)]:assert m.uc.reg_read(register)==value,(request,register)
        assert m.uc.reg_read(UC_X86_REG_EFLAGS)&0xffff==0x202
        if request<=1:
            raw=bytes(m.uc.mem_read(m.symbols['reset_bank_observation'],20));obs=struct.unpack('<10H',raw)
            assert obs[0]==obs[1]!=m.ds and obs[4:8]==((132 if request else 80),0,0,0)
            assert bytes(m.uc.mem_read(0xb8000,3840))==b' \x07'*1920
            assert bytes(m.uc.mem_read(0xb8000+3840,160))==screen[3840:]
        else:assert bytes(m.uc.mem_read(0xb8000,4000))==screen
        if memory['native_reset_overlay']:
            used=memory['native_reset_shadow_end']-memory['native_reset_bank_start']
            assert bytes(m.uc.mem_read(workspace+used,workspace_bytes-used))==b'\xa5'*(workspace_bytes-used)
        # These cold calls do not commit a live width. Restore the owned view
        # before any ordinary parser work in this fixture, just as an eventual
        # transaction owner must commit or roll back its display operation.
        m.call('csi_reset_terminal');assert m.get('screen_attribute_row_bytes')==80
        cases.append(dict(request=request,status=result,live_data_preserved=True))
    owner_refusals=0;viewer_rebuilt=False
    if memory['native_reset_overlay']:
        owners=['_redisplay_active','_redisplay_export_pending','_redisplay_search_pending','_command_menu_active',
            'terminal_snapshot_active','terminal_program_active','terminal_program_pending','terminal_monitor_active',
            'terminal_controller_active','terminal_transfer_active','terminal_transfer_pending']
        for name in owners:
            m=Live();m.put(name,1);workspace=m.base+memory['native_reset_bank_start']
            m.uc.mem_write(workspace,b'\x5a'*memory['native_reset_workspace_bytes'])
            old=bytes(m.uc.mem_read(0xb8000,4000))
            assert m.call('reset_bank_call',ax=1)==1,name
            assert bytes(m.uc.mem_read(workspace,memory['native_reset_workspace_bytes']))==b'\x5a'*memory['native_reset_workspace_bytes'],name
            assert bytes(m.uc.mem_read(0xb8000,4000))==old,name
            owner_refusals+=1
        if not manifest.get('experimental_mouse'):
            m=Redisplay();history=b''.join(f'RESTORED {i:02d}\r'.encode()for i in range(40));m.seed(history);m.open()
            before=bytes(m.uc.mem_read(m.symbols['redisplay_snapshot'],63000))
            assert m.call('reset_bank_call',ax=1)==1
            assert bytes(m.uc.mem_read(m.symbols['redisplay_snapshot'],63000))==before
            m.key(27);assert not m.get('_redisplay_active')
            assert m.call('reset_bank_call',ax=1,limit=2000000)==0
            m.call('csi_reset_terminal');m.open()
            assert bytes(m.uc.mem_read(m.symbols['redisplay_snapshot'],len(history)))==history
            assert b'RESTORED 39'in bytes(m.uc.mem_read(0xb8000,4000))[::2]
            m.key(27);assert not m.get('_redisplay_active');viewer_rebuilt=True
    layout_refusals=[]
    if memory['native_reset_overlay']:
        original=(base/'terminal.map').read_text()
        for symbol,seg,off in [('nreset_stack_top',0,0xe710),('bank_shadow_end',0,0xffc1),
            ('redisplay_snapshot',memory['native_reset_bank_start']//16,16),
            ('nreset_screen_cursor_row',memory['near_relative_segment'],0x399c)]:
            import re
            altered,count=re.subn(r'^([0-9a-f]{4}):([0-9a-f]{4})([*+ ]+\s+'+symbol+r'\s*)$',
                lambda match:f'{seg:04x}:{off:04x}'+match[3],original,flags=re.M|re.I)
            assert count==1,symbol
            with tempfile.TemporaryDirectory()as folder:
                bad=Path(folder)/'terminal.map';bad.write_text(altered)
                try:inspect_terminal_memory(binary,bad)
                except AssertionError:layout_refusals.append(symbol)
                else:raise AssertionError('Accepted malformed native ownership: '+symbol)
    m=Live();psp=m.base_segment-16;m.call('terminal_program_initialize',ax=psp)
    assert m.get('process_keep_paragraphs')==m.get('process_minimum_paragraphs')==memory['retained_parent_paragraphs']
    try:m.feed(b'\x1b[?3h')
    except Abort as problem:assert problem.args==(0x2a6e,)
    else:raise AssertionError('Cold bank unexpectedly enabled peer width ownership')
    report=dict(passed=True,binary_sha256=manifest['binary_sha256'],cases=cases,memory_layout=memory,
        actual_PROGRAM_retention_verified=True,peer_width_still_unbound=not manifest.get('native_reset_transaction',False),uninitialized_peer_width_refused=True,workspace_owner_refusals=owner_refusals,
        viewer_rebuilt_after_native_use=viewer_rebuilt,malformed_layout_refusals=layout_refusals,checker_sha256=sha(Path(__file__)),
        sources=manifest['sources'],original_inputs=[],scope='Actual optional parent MZ with separate native symbols/bank; cold native0/1 calls preserve all live near data/BSS, RX and owned live shadow, return0/1 metadata and expected physical clear; unsupported requests refuse. Actual startup retention covers the workspace. Overlay admission excludes eleven concurrent owners and preserves the unused tail guard. The non-mouse model additionally rebuilds history after cache reuse. Malformed map ownership is refused. Hardware model and explicit test cleanup; no live projection/commit, normal peer width or broad UI/BBS acceptance.')
    (base/'native-bank-parent-checks.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS namespaced native bank in parent: four cold-call cases, full live-data preservation and actual retention')


if __name__=='__main__':main()
