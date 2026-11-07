"""Deterministically pack authored C UI literals with a bounded byte-pair table."""
import ast
from collections import Counter
import hashlib
import re

TOKENS = re.compile(r'/\*.*?\*/|//[^\n]*|"(?:\\.|[^"\\])*"', re.S)

def pack(source, output, pair_limit=64, meta_editor=False):
    assert pair_limit in (0,64,128)
    text = source.read_text()
    # Exclude the optional entry before dictionary construction. Otherwise its
    # inactive literals change every existing packed label in disabled builds.
    if not meta_editor:
        text = re.sub(r'(?m)^#ifdef TERMINAL_META_EDITOR\nENTRY\(meta_keys,.*?^#endif\n', '', text, flags=re.S)
    literals = []
    for match in TOKENS.finditer(text):
        token = match.group()
        prefix = text[text.rfind('\n', 0, match.start()) + 1:match.start()]
        if not token.startswith('"') or re.match(r'\s*#\s*(?:include|pragma)\b', prefix) or '__segname' in prefix:continue
        value = ast.literal_eval(token).encode('ascii')
        assert all(c < 128 for c in value)
        if not value or 0 in value:continue
        literals.append((match.start(), match.end(), value))
    streams = [value for _, _, value in literals]
    pairs = []
    for number in range(pair_limit):
        counts = Counter(pair for data in streams for pair in zip(data, data[1:]))
        if not counts:break
        pair, count = min(counts.items(), key=lambda item: (-item[1], item[0]))
        if count < 3:break
        streams = [data.replace(bytes(pair), bytes([128 + number])) for data in streams]
        pairs.append(pair)
    depth = [0] * 128
    for left, right in pairs:depth.append(1 + max(depth[left], depth[right]))
    assert len(pairs) <= 128 and max(depth) <= 64
    def expand(data):
        result = bytearray();pending = list(reversed(data))
        while pending:
            c = pending.pop()
            if c < 128:result.append(c)
            else:
                left, right = pairs[c - 128];pending.extend((right, left))
        return bytes(result)
    pieces, previous = [], 0
    for (start, end, original), encoded in zip(literals, streams):
        assert expand(encoded) == original
        quoted = '"' + ''.join(chr(c) if 32 <= c < 127 and c not in (34, 92) else '\\%03o' % c for c in encoded) + '"'
        pieces.extend((text[previous:start], quoted));previous = end
    pieces.append(text[previous:])
    generated = output / 'command_menu_packed.c'
    generated.write_text('#define UI_PACKED_TEXT 1\n' + ''.join(pieces))
    header = output / 'command_ui_pairs.h'
    header.write_text('#define UI_PAIR_COUNT %d\n' % len(pairs) + 'static const byte MENU_TEXT command_ui_pairs[][2]={\n' + (',\n'.join('{%d,%d}' % pair for pair in pairs) if pairs else '{0,0}') + '\n};\n')
    return generated, dict(literals=len(literals), pairs=len(pairs), max_depth=max(depth), original_literal_bytes=sum(len(v) for _, _, v in literals), packed_literal_bytes=sum(map(len, streams)), dictionary_bytes=len(pairs) * 2, generated_sha256=hashlib.sha256(generated.read_bytes()).hexdigest(), dictionary_sha256=hashlib.sha256(header.read_bytes()).hexdigest())
