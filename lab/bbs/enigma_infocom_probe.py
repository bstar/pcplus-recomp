"""Passive acceptance checks for DOS -> owned ENiGMA -> Zork -> menus.

The recipe visits real menus and never saves a game. No story data or reply
generator is included: the installed worker and DOS client own both sides.
"""

KEYS = (
    'D enter p1600 3 enter p1600 N enter p1000 P enter p1000 '
    '1 enter p3000 l o o k enter p1000 n o r t h enter p1000 '
    'l o o k enter p1000 q u i t enter p1200 y enter p2000 '
    'Q enter p1600 Q enter p1600'
)


def ordered(text, tokens):
    positions = []
    start = 0
    for token in tokens:
        at = text.find(token, start)
        if at < 0:
            return None
        positions.append(at)
        start = at + len(token)
    return positions


def audit(display, sent, rows, story_sha256):
    library = 'I N F O C O M   L I B R A R Y'
    path = ordered(display, (
        'D O S   D O O R S', library,
        'Page 1 / 4', 'Page 2 / 4', 'Page 1 / 4',
        'West of House', 'West of House',
        'North of House', 'North of House', library,
        'D O S   D O O R S', 'M A I N   M E N U',
    ))
    expected_name = 'LoC-Infocom-' + story_sha256
    lifecycle = [r['msg'] for r in rows if r.get('name') == expected_name
                 and r.get('msg') in ('Z-Machine VM ready', 'Z-Machine VM stopped')]
    return dict(
        infocom_route_gameplay_and_return=path is not None,
        infocom_commands_emitted=ordered(sent, (
            b'D\r', b'3\r', b'N\r', b'P\r', b'1\r',
            b'look\r', b'north\r', b'look\r', b'quit\r', b'y\r',
            b'Q\r', b'Q\r',
        )) is not None,
        infocom_worker_lifecycle=lifecycle == ['Z-Machine VM ready', 'Z-Machine VM stopped'],
        infocom_no_worker_errors=not any(
            'zmachine' in r.get('msg', '').lower()
            and ('error' in r.get('msg', '').lower()
                 or 'non-zero' in r.get('msg', '').lower()) for r in rows),
        infocom_no_save_requested=b'save\r' not in sent.lower(),
    )
