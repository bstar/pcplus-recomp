#!/usr/bin/env python3
"""Exercise the parent's zero-byte cursor-service alias across all80x25 cells."""
import argparse,json,struct,sys
from pathlib import Path
from unicorn.x86_const import UC_X86_REG_AX,UC_X86_REG_DX
import check_transport as transport
from check_chat_timing_parent import Composed
from build_path_session import ROOT,sha


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('terminal','output'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();binary=a.terminal.resolve();out=a.output.resolve()
    assert binary.is_relative_to(ROOT/'build') and out.is_relative_to(ROOT/'build') and not out.exists()
    manifest=json.loads(binary.with_name('manifest.json').read_text())
    assert sha(binary)==manifest['binary_sha256']=='5ecf87743f55c97e83a334c3a5ef9e049dc4de1558ec4d482a529cf215092846'
    transport.BINARY=binary;transport.MAP=binary.with_name('terminal.map')
    m=Composed();m.put('_redisplay_active',2);seg,off=m.entries['terminal_key_position_far']
    at=m.symbols['terminal_key_position_far'];code=bytes(m.uc.mem_read(at,4))
    assert code[0]==0xe8 and code[3]==0xcb
    target=m.base+seg*16+((off+3+struct.unpack('<h',code[1:3])[0])&65535)
    assert target==m.symbols['screen_set_cursor']
    keyboard=m.keyboard_calls;wire=bytes(m.tx)
    for row in range(25):
        for column in range(80):
            m.uc.reg_write(UC_X86_REG_AX,row);m.uc.reg_write(UC_X86_REG_DX,column)
            m.farcall(m.base_segment+seg,off,[])
            assert m.get('screen_cursor_row')==m.get('screen_previous_row')==row
            assert m.get('screen_cursor_column')==m.get('screen_visible_column')==m.get('screen_previous_column')==column
            assert m.get('screen_video_offset')==(row*80+column)*2
            assert m.get('screen_attribute_offset')==row*80+column
            assert m.cursor==(row<<8)|column
    assert m.keyboard_calls==keyboard and bytes(m.tx)==wire
    sources=dict(manifest['sources'])
    for mod in tuple(sys.modules.values()):
        q=Path(getattr(mod,'__file__','') or '/').resolve()
        if q.is_relative_to(ROOT/'standalone') and q.suffix=='.py':sources[str(q.relative_to(ROOT))]=sha(q)
    for n,h in sources.items():assert sha(ROOT/n)==h,n
    out.mkdir();(out/'result.json').write_text(json.dumps(dict(passed=True,binary_sha256=sha(binary),positions=2000,
        added_executable_bytes=0,added_near_bytes=0,register_stack_ABI=True,sources=sources,
        scope=__doc__+' Actual existing CALL screen_set_cursor/RETF instructions, cursor/cache arithmetic and BIOS call; DOS/BIOS/UART boundary model. DS=SS/BP/SI/DI/stack checked by caller, no UART or key consumption. Unchanged executable hash is required. Caller supplies valid geometry; this does not recover full echo context/parser ownership or bind foreground TEXT.'),indent=2)+'\n')
    print('PASS all2000 physical cursor/cache positions; alias adds zero executable/near bytes')


if __name__=='__main__':main()
