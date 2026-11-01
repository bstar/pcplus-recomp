"""Semantic assertions for the owned stock ENiGMA24-line editor recipe."""
import re


def editor_checks(output, tx, display, mode):
    assert mode in ('page-up', 'page-down')
    # SGR may appear between INS and its document coordinates. Do not strip
    # all controls and join unrelated screen text onto a numeric field.
    sgr = rb'(?:\x1b\[[0-9;]*m)*'
    positions = [tuple(map(int, p)) for p in re.findall(
        rb'(?:INS|OVR) ' + sgr + rb'(\d{2}),(\d{2})(?!\d)', display)]
    transitions = list(zip(positions, positions[1:]))
    up = ((25, 1), (14, 1))
    down = ((14, 7), (25, 1))
    video = (output / 'SCREEN.BIN').read_bytes()
    body = [video[row*160:(row+1)*160:2].decode('cp437').rstrip()
        for row in range(8, 22)]
    if mode == 'page-down':
        expected = [f'R{n:02}' if n != 14 else 'UPMARKR14'
            for n in range(12, 25)] + ['UNSAVED']
        footer = b'INS 25,08'
    else:
        expected = [f'R{n:02}' for n in range(1, 14)] + ['UPMARKUNSAVEDR14']
        footer = b'INS 14,14'
    checks = dict(all24_lines_sent=b''.join(f'R{n:02}\r'.encode() for n in range(1, 25)) in tx,
        real_page_up=b'\x1b[5~' in tx and up in transitions,
        top_edit_sent=b'UPMARK' in tx,
        real_page_down=(b'\x1b[6~' in tx and down in transitions)
            if mode == 'page-down' else b'\x1b[6~' not in tx,
        final_marker_sent=b'UNSAVED' in tx,
        exact_numbered_body_window=body == expected,
        exact_document_footer=len(video) == 4000 and footer in video[::2])
    detail = dict(mode=mode, body_lines=24, cursor_positions=positions,
        page_up_transitions=[p for p in transitions if p == up],
        page_down_transitions=[p for p in transitions if p == down],
        expected_body=expected, actual_body=body)
    return checks, detail
