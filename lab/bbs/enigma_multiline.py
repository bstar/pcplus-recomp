"""Semantic assertions for the owned stock ENiGMA24-line editor recipe."""
import re


def editor_checks(output, tx, display, mode):
    assert mode in ('page-up', 'page-down', 'navigation')
    # SGR may appear between INS and its document coordinates. Do not strip
    # all controls and join unrelated screen text onto a numeric field.
    sgr = rb'(?:\x1b\[[0-9;]*m)*'
    positions = [tuple(map(int, p)) for p in re.findall(
        rb'(?:INS|OVR) ' + sgr + rb'(\d{2}),(\d{2})(?!\d)', display)]
    transitions = list(zip(positions, positions[1:]))
    up = ((25, 1), (14, 1))
    down = ((14, 7), (25, 1))
    video = (output / 'SCREEN.BIN').read_bytes()
    # The owned geometry harness also captures a second video page. Document
    # body/footer semantics concern the first page; full geometry is audited
    # independently by the caller. Never search the second page for a footer.
    page = video[:4000]
    body = [page[row*160:(row+1)*160:2].decode('cp437').rstrip()
        for row in range(8, 22)]
    if mode in ('page-down','navigation'):
        expected = [f'R{n:02}' if n != 14 else 'UPMARKR14'
            for n in range(12, 25)] + ['UNSAVED']
        footer = b'INS 25,08'
        if mode == 'navigation':expected[-2]='RX4'
    else:
        expected = [f'R{n:02}' for n in range(1, 14)] + ['UPMARKUNSAVEDR14']
        footer = b'INS 14,14'
    checks = dict(all24_lines_sent=b''.join(f'R{n:02}\r'.encode() for n in range(1, 25)) in tx,
        real_page_up=b'\x1b[5~' in tx and up in transitions,
        top_edit_sent=b'UPMARK' in tx,
        real_page_down=(b'\x1b[6~' in tx and down in transitions)
            if mode in ('page-down','navigation') else b'\x1b[6~' not in tx,
        final_marker_sent=b'UNSAVED' in tx,
        exact_numbered_body_window=body == expected,
        exact_document_footer=len(video) in (4000,8000) and footer in page[::2])
    navigation = {}
    if mode == 'navigation':
        wanted = [(25,1),(24,1),(24,2),(24,3),(24,2),(24,3),(24,1),
                  (25,1),(24,1),(25,1),(14,1)]
        start = positions.index((25,1)) if (25,1) in positions else len(positions)
        actual = []
        for position in positions[start:]:
            if not actual or position != actual[-1]:actual.append(position)
            if position == (14,1):break
        right = b'\x1b[C' if b'\x1b[C' in tx else b'\x1bOC'
        up_key = b'\x1b[A' if b'\x1b[A' in tx else b'\x1bOA'
        down_key = b'\x1b[B' if b'\x1b[B' in tx else b'\x1bOB'
        navigation_wire = tx[tx.index(b'R24\r')+4:] if b'R24\r' in tx else b''
        checks.update(navigation_after_last_numbered_line=bool(navigation_wire),
            exact_navigation_cursor_history=actual==wanted,
            backspace_moves_and_removes_character=bool(re.search(re.escape(up_key+right+right)+rb'[\x08\x7f]X',navigation_wire)),
            explicit_up_down_right_wire=all(key in navigation_wire for key in (up_key,down_key,right)),
            edited_last_numbered_line=body[-2]=='RX4')
        navigation = dict(expected_cursor_history=wanted,actual_cursor_history=actual,
                          final_edited_line='RX4',wire_hex=navigation_wire.hex())
    detail = dict(mode=mode, body_lines=24, cursor_positions=positions,
        page_up_transitions=[p for p in transitions if p == up],
        page_down_transitions=[p for p in transitions if p == down],
        expected_body=expected, actual_body=body,navigation=navigation)
    return checks, detail
