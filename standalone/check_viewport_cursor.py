#!/usr/bin/env python3
"""Join actual cursor, viewport, hidden-status refresh and width/reset adapters."""
import hashlib,json
from pathlib import Path
import check_terminal_reset as reset

ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    reset.OUT=ROOT/'build/terminal-reset-viewport'
    manifest=json.loads((reset.OUT/'manifest.json').read_text())
    assert manifest['viewport_bound']and sha(reset.OUT/'RESET.EXE')==manifest['binary_sha256']
    for name,digest in manifest['sources'].items():assert sha(ROOT/name)==digest
    m=reset.Reset()
    for name,value in dict(screen_viewport_enabled=1,viewport_physical_columns=80,viewport_rows=24,
        screen_viewport_left=52,screen_viewport_right=79,screen_viewport_active=1,
        screen_attribute_row_bytes=132,screen_last_column=131,erase_shadow_segment=0x6000,erase_shadow_offset=32).items():m.put(name,value)
    video=bytearray(m.uc.mem_read(0xb8000,4000));shadow=bytearray((i*13+7)&255 for i in range(132*24*2));guard=b'\xa5'*32
    m.uc.mem_write(0x60000,guard+shadow+guard);active=1;cases=[]
    for row,column in [(4,131),(8,0),(23,120),(0,10),(15,80),(2,51)]:
        next_active=1 if column<52 else 0 if column>79 else active
        if next_active!=active:
            # Save the currently visible pane, then restore the newly selected one.
            old_offset=0 if active else 52;new_offset=0 if next_active else 52
            for r in range(24):
                v=r*160;s=(r*132+old_offset)*2;shadow[s:s+160]=video[v:v+160]
            for r in range(24):
                v=r*160;s=(r*132+new_offset)*2;video[v:v+160]=shadow[s:s+160]
        active=next_active;m.position(row,column)
        assert m.rowcol()==(row,column)and m.get('screen_viewport_active')==active
        offset=0 if active else 52
        assert m.get('screen_visible_column')==column-offset and m.get('screen_viewport_offset')==offset
        assert m.get('screen_video_offset')==row*160+(column-offset)*2
        assert m.get('screen_attribute_offset')==row*132+column
        assert bytes(m.uc.mem_read(0xb8000,4000))==video
        assert bytes(m.uc.mem_read(0x60000,len(shadow)+64))==guard+shadow+guard
        cases.append(dict(cursor=(row,column),active_pane=active,passed=True))
    for old in (0,1):
        for request in (0,1):
            m=reset.Reset();m.put('reset_configured_wide',old);m.put('reset_width_request_argument',request)
            m.call('terminal_width_request_test',limit=1000000)
            assert m.get('reset_configured_wide')==old and m.cells()==[0x0720]*2000 and m.rowcol()==(0,0)
            # The native ANSI/non-DEC branch requests ordinary geometry even
            # when its temporary configuration word is nonzero.
            assert m.get('screen_attribute_row_bytes')==80
            cases.append(dict(native_reset_request=request,original_configuration=old,passed=True))
    m=reset.Reset();m.put('terminal_dec_keys',1);m.put('reset_width_request_argument',1)
    try:m.call('terminal_width_request_test',limit=1000000)
    except reset.Dependency as error:assert error.args==(0x860f,)
    else:raise AssertionError('Wide allocation boundary must remain explicit')
    assert m.get('reset_configured_wide')==1 # Native adapter did not return.
    result=dict(passed=True,cases=cases,wide_allocation_boundary=0x860f,
                binary_sha256=manifest['binary_sha256'],sources={**manifest['sources'],
                    'standalone/check_viewport_cursor.py':sha(Path(__file__)),
                    'standalone/check_terminal_reset.py':sha(ROOT/'standalone/check_terminal_reset.py')},
                scope='Six actual cursor transitions use real pane-copy and hidden-status refresh; four full stable80 native reset calls pass. DEC wide request still traps at allocation and leaves its temporary setting, so an unwind owner is required. CPU hardware model; no live terminal width claim.')
    (reset.OUT/'viewport-checks.json').write_text(json.dumps(result,indent=2)+'\n')
    print('PASS real cursor/viewport composition and native reset; wide allocation remains explicit')


if __name__=='__main__':main()
