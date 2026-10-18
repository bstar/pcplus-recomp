#!/usr/bin/env python3
"""Audit DOS interaction against the owned ENiGMA server's session log."""
import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SERVER = ROOT / 'build/bbs-lab/enigma/source'


def audit(label):
    out = ROOT / 'build/bbs-lab/results/enigma' / label
    start = json.loads((out / 'server-log-start.json').read_text())['byte_offset']
    with (SERVER / 'logs/enigma-bbs.log').open('rb') as stream:
        stream.seek(start)
        rows = [json.loads(line) for line in stream if line.strip()]
    sessions = {row['sessionId'] for row in rows if row.get('menuName') == 'telnetConnected'}
    assert len(sessions) == 1, f'Expected one isolated lab session: {sessions}'
    session = sessions.pop()
    rows = [row for row in rows if row.get('sessionId') == session]
    menus = [row['menuName'] for row in rows if 'menuName' in row]
    wanted = iter(['mainMenu', 'messageBaseMainMenu', 'mainMenu', 'fileBaseMainMenu'])
    next_menu = next(wanted)
    for menu in menus:
        if menu == next_menu:
            next_menu = next(wanted, None)
    run = json.loads((out / 'result.json').read_text())
    sent = (out / 'serial-received.bin').read_bytes()
    display = (out / 'display.bin').read_bytes()
    screen = (out / 'screen.txt').read_text()
    stock = SERVER / 'art/themes/luciano_blocktronics/ONELINER.ANS'
    checks = {
        'DOS_connection_hardware_and_directory_checks': run['passed'],
        'server_confirmed_login': any('successfully logged in' in row.get('msg', '') for row in rows),
        'server_confirmed_main_messages_main_files': next_menu is None,
        'actual_DOS_device_attributes_reply': b'\x1b[?1;2c' in sent,
        'actual_DOS_cursor_position_reply': bool(re.search(rb'\x1b\[[0-9]+;[0-9]+R', sent)),
        'actual_DOS_arrow_keys': b'\x1b[B' in sent and b'\x1b[A' in sent,
        'final_file_menu_visible': 'file base' in screen.lower(),
        'stock_problematic_art_unchanged': hashlib.sha256(stock.read_bytes()).hexdigest() == '2adc57a2fd56e0862d1ab206d8d988e2f7454158457abc98303f43ca90ca80c9',
        'no_unsupported_terminal_failure': 'unsupported terminal' not in screen.lower(),
    }
    result = {
        'passed': all(checks.values()), 'checks': checks,
        'binary_sha256': run['binary_sha256'], 'session_id': session,
        'menus': menus, 'serial': run['serial'],
        'terminal_queries': sorted({m.decode('ascii') for m in re.findall(rb'\x1b\[[?0-9;]*[cn]', display)}),
        'scope': 'Actual local ENiGMA login and named menu paths, authoritative server log and DOS UART/video. No physical modem, transfers, doors or full-screen editor claim.',
    }
    (out / 'server-session.jsonl').write_text(''.join(json.dumps(row) + '\n' for row in rows))
    (out / 'semantic-audit.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--label', required=True)
    raise SystemExit(audit(parser.parse_args().label))
