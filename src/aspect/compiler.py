#!/usr/bin/env python3
"""Source-only host compiler for the documented ASPECT reconstruction subset.

Produces PCPlus ASX bytecode, not a replacement interpreter. No original compiler,
fixture database, executable image, or generated analysis is a build input.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from pathlib import Path
import re
import struct


class CompileError(ValueError):
    """Unsupported or malformed source, with a physical source line."""


TYPES = {"integer": 0, "long": 1, "float": 2, "string": 3}
PARMS = {"intparm": 0, "longparm": 1, "floatparm": 2, "strparm": 3}
BUILTINS = {'comdata': 20, 'failure': 21, 'forever': 22, 'found': 23,
            'success': 27, 'waitfor': 28, '$d_entry': 3}
STRING_BUILTINS = {'$d_ldate': 0, '$d_kbdfile': 1, '$d_metakey': 2,
                   '$d_name': 3, '$d_note': 4, '$d_phone': 5,
                   '$d_pword': 6, '$d_script': 7, '$null': 19,
                   '$fattr': 9, '$fdate': 10, '$fext': 11, '$filename': 12, '$fname': 13, '$ftime': 14}
LONG_BUILTINS = {'$d_baud': 0, '$fsize': 1}
TYPED_BUILTINS = {**{name: (0, slot) for name, slot in BUILTINS.items()},
                  **{name: (1, slot) for name, slot in LONG_BUILTINS.items()},
                  **{name: (3, slot) for name, slot in STRING_BUILTINS.items()}}
SIZES = (2, 4, 8, 81)
SET_BOOLEAN = {'display': 0x12, 'findcase': 0x23, 'switchcase': 0x44,
               'waitcase': 0x55, 'whencase': 0x56, 'keys': 0x29,
               'rxdata': 0x3B, 'msg_crlf': 0x2E, 'fgets_crlf': 0x22}
SET_INTEGER = {'pausechar': 0x30, 'txpace': 0x4C, 'break': 0x09}
# Proved FETCH families have integer destinations, including byte/boolean fields.
# Keep this whitelist separate from future SET additions.
FETCH_SETTINGS = {'break': 0x09, 'display': 0x12, 'duplex': 0x18,
                  'findcase': 0x23, 'keys': 0x29, 'msg_crlf': 0x2E,
                  'pausechar': 0x30, 'rxdata': 0x3B, 'switchcase': 0x44,
                  'txpace': 0x4C, 'waitcase': 0x55, 'whencase': 0x56, 'fgets_crlf': 0x22}
OPS = {"+": 0x00, "-": 0xB5, "*": 0x7D, "/": 0x26, "%": 0x7B,
       "==": 0x32, "!=": 0x7F, "<": 0x6D, ">": 0x54,
       "<=": 0x68, ">=": 0x48}
PRIORITY = {"=": 1, "||": 2, "&&": 3, "==": 4, "!=": 4,
            "<": 4, ">": 4, "<=": 4, ">=": 4,
            "+": 5, "-": 5, "*": 6, "/": 6, "%": 6}
TOKEN = re.compile(r'\s*("[^"\r\n]*"|0[xX][0-9a-fA-F]+[lL]?|'
                   r'\d+(?:\.\d+)?(?:[eE][+-]?\d+)?[lL]?|'
                   r'[a-zA-Z_$][a-zA-Z_0-9$]*|\+\+|--|&&|\|\||'
                   r'==|!=|<=|>=|[+*/%\-]=|[(),=+*/%<>\-])')


def tokenize(line: str, number: int) -> list[str]:
    tokens = []
    pos = 0
    while pos < len(line):
        if not line[pos:].strip() or line[pos:].lstrip().startswith(';'):
            break
        match = TOKEN.match(line, pos)
        if not match:
            raise CompileError(f"line {number}: unrecognized text {line[pos:]!r}")
        token = match.group(1)
        tokens.append(token if token.startswith('"') else token.lower())
        pos = match.end()
    return tokens


@dataclass
class Symbol:
    kind: int
    space: str
    index: int

    def wire(self) -> bytes:
        if self.space == "global":
            return bytes(((0x8D, 0x8E, 0x8F, 0x8C)[self.kind], self.index))
        if self.space == "local":
            return bytes(((0xA1, 0xA2, 0xA3, 0xA0)[self.kind],)) + word(self.index)
        return bytes(((0x97, 0x98, 0x99, 0x96)[self.kind],)) + word(self.index)


@dataclass
class Procedure:
    name: str
    lines: list = field(default_factory=list)
    symbols: dict = field(default_factory=dict)
    params: list = field(default_factory=list)
    initializers: list = field(default_factory=list)
    size: int = 0
    address: int = 0


def word(value: int) -> bytes:
    return struct.pack('<H', value & 0xFFFF)


def dword(value: int) -> bytes:
    return struct.pack('<I', value & 0xFFFFFFFF)


def number(token: str):
    suffix = token.endswith('l')
    text = token[:-1] if suffix else token
    if not text.startswith('0x') and ('.' in text or 'e' in text):
        return 2, float(text)
    value = int(text, 16 if text.startswith('0x') else 10)
    return (1 if suffix or value > 32767 else 0), value


class Expression:
    def __init__(self, tokens, line):
        self.tokens, self.line, self.pos = tokens, line, 0

    def parse(self, minimum=1):
        if self.pos == len(self.tokens):
            raise CompileError(f"line {self.line}: missing expression")
        token = self.tokens[self.pos]
        self.pos += 1
        if token in ('-', '++', '--'):
            node = ('unary', token, self.parse(7))
        elif token == '(':
            node = self.parse()
            if self.pos == len(self.tokens) or self.tokens[self.pos] != ')':
                raise CompileError(f"line {self.line}: missing closing parenthesis")
            self.pos += 1
        elif token[0].isdigit():
            node = ('constant', *number(token), token.endswith('l'))
        elif token.startswith('"'):
            node = ('string', token[1:-1])
        elif re.fullmatch(r'[a-z_$][a-z_0-9$]*', token):
            node = ('symbol', token)
        else:
            raise CompileError(f"line {self.line}: unexpected token {token!r}")
        while self.pos < len(self.tokens):
            op = self.tokens[self.pos]
            priority = PRIORITY.get(op, 0)
            if priority < minimum:
                break
            self.pos += 1
            right = self.parse(priority if op == '=' else priority + 1)
            node = ('binary', op, node, right)
        return node


class Compiler:
    def __init__(self):
        self.globals = {}
        self.counts = [0] * 4
        self.procedures = {}
        self.output = bytearray()
        self.fixups = []
        self.line = 1
        self.proc = None
        self.declaration_lines = []

    def error(self, message):
        raise CompileError(f"line {self.line}: {message}")

    def emit(self, *values):
        for value in values:
            self.output.extend(bytes((value,)) if isinstance(value, int) else value)

    def jump(self, opcode):
        self.emit(opcode)
        offset = len(self.output)
        self.emit(dword(0))
        return offset

    def patch(self, offset, target=None):
        self.output[offset:offset + 4] = dword(len(self.output) if target is None else target)

    def declarations(self, tokens, proc, line):
        kind = (TYPES | PARMS)[tokens[0]]
        is_param = tokens[0] in PARMS
        if is_param and proc is None:
            self.error('parameter outside procedure')
        parts, current, depth = [], [], 0
        for token in tokens[1:] + [',']:
            if token == ',' and not depth:
                parts.append(current)
                current = []
            else:
                current.append(token)
                depth += (token == '(') - (token == ')')
        for part_index, part in enumerate(parts):
            if not part or not re.fullmatch(r'[a-z_$][a-z_0-9$]*', part[0]):
                self.error('expected declaration name')
            name = part[0]
            if name == 'text' or name in TYPED_BUILTINS:
                self.error(f'{name.upper()} is a reserved ASPECT keyword')
            symbols = self.globals if proc is None else proc.symbols
            if name in symbols:
                self.error(f'duplicate declaration {name}')
            if proc is None:
                if len(part) != 1:
                    self.error('global initializers are not supported')
                if self.counts[kind] >= 128:
                    self.error('global variable limit is 128 per type')
                symbols[name] = Symbol(kind, 'global', self.counts[kind])
                self.counts[kind] += 1
            elif is_param:
                if len(part) != 1:
                    self.error('parameter initializer is not supported')
                symbols[name] = Symbol(kind, 'param', 0)
                proc.params.append(symbols[name])
            else:
                if sum(s.space == 'local' for s in symbols.values()) >= 128:
                    self.error('local variable limit is 128')
                symbols[name] = Symbol(kind, 'local', proc.size)
                proc.size += SIZES[kind]
                if len(part) > 1:
                    if part[1] != '=':
                        self.error('expected initializer assignment')
                    proc.initializers.append((line, [name, '='] + part[2:],
                                              kind != 3 and part_index < len(parts) - 1))

    def symbol(self, name):
        symbol = self.proc.symbols.get(name, self.globals.get(name))
        if symbol is None:
            self.error(f'unknown variable {name}')
        return symbol

    def tree(self, tokens):
        parser = Expression(tokens, self.line)
        node = parser.parse()
        if parser.pos != len(tokens):
            self.error(f'unexpected expression token {tokens[parser.pos]!r}')
        return node

    def kind(self, node):
        tag = node[0]
        if tag == 'constant':
            return node[1]
        if tag == 'string':
            return 3
        if tag == 'symbol':
            if node[1] in TYPED_BUILTINS:
                return TYPED_BUILTINS[node[1]][0]
            if node[1] == '$null' or re.fullmatch(r's[0-9]', node[1]):
                return 3
            return self.symbol(node[1]).kind
        if tag == 'unary':
            return self.kind(node[2])
        if node[1] in ('==', '!=', '<', '>', '<=', '>=', '&&', '||'):
            return 0
        if node[1] == '=':
            return self.kind(node[2])
        return max(self.kind(node[2]), self.kind(node[3]))

    def lvalue(self, node):
        if node[0] != 'symbol' or node[1] in TYPED_BUILTINS:
            self.error('variable destination required')
        if re.fullmatch(r's[0-9]', node[1]):
            return 3, bytes((0x64, int(node[1][1])))
        symbol = self.symbol(node[1])
        return symbol.kind, symbol.wire()

    def operand(self, node, compact=False):
        tag = node[0]
        if tag == 'constant':
            kind, value = node[1:3]
            if kind == 2:
                self.emit(0xAD, struct.pack('<d', value))
            elif kind == 1:
                self.emit(0xAC, dword(value))
            elif compact and 0 <= value <= 255:
                self.emit(0xB5, int(value))
            else:
                self.emit(0xAB, word(value))
        elif tag == 'string':
            plain = node[1].encode('cp437')
            if not plain:
                self.emit(0x6E, 19)
                return
            if len(plain) > 80 or b'\0' in plain:
                self.error('string literals require 1..80 non-NUL CP437 bytes')
            self.emit(0xAA)
            position = len(self.output)
            parity = position & 1
            stride = ((position + self.line) & 0xFFFFFFFF) % 12 + 1
            table = (0xB3, 0x35, 0x0B, 0xC7, 0x47, 0x29, 0x1D,
                     0xFB, 0x1F, 0x7F, 0x05, 0x59, 0x17)
            self.emit((0xB3 + len(plain)) & 255, (parity << 7) | (stride + len(plain)))
            for index, char in enumerate(plain, 1):
                i = (index * stride) % 13
                self.emit((char + (table[i] if (i + parity) % 2 == 0 else -table[i])) & 255)
        elif tag == 'symbol':
            if node[1] in TYPED_BUILTINS:
                kind, slot = TYPED_BUILTINS[node[1]]
                self.emit({0: 0x6F, 1: 0x70, 3: 0x6E}[kind], slot)
            else:
                self.emit(self.lvalue(node)[1])
        elif tag == 'temporary':
            self.emit(0x79 + node[1], node[2])
        else:
            self.error('internal non-atomic operand')

    def expression(self, node, slot=0):
        if slot > 255:
            self.error('expression temporary index exceeds one byte')
        tag = node[0]
        if tag in ('constant', 'string', 'symbol'):
            return node
        if tag == 'unary':
            op, child = node[1:]
            if op == '-' and child[0] == 'constant':
                return ('constant', child[1], -child[2])
            # A parenthesized negative constant is folded just like the original.
            value = self.expression(child, slot)
            kind = self.kind(child)
            if kind == 3:
                self.error('numeric operand required')
            if op in ('++', '--'):
                _, dest = self.lvalue(child)
                self.emit(0x5A if op == '++' else 0x1E, dest)
                self.emit(0x5B, kind * 5, bytes((0x79 + kind, slot)))
                self.operand(child)
            elif value[0] == 'constant':
                return ('constant', value[1], -value[2])
            else:
                self.emit(0x7E, kind * 5)
                self.operand(value)
                self.emit(0x79 + kind, slot)
            return ('temporary', kind, slot)
        op, left, right = node[1:]
        if op in ('&&', '||'):
            self.boolean(node, slot)
            return ('temporary', 0, slot)
        if op == '=':
            value = self.expression(right, slot)
            destkind, dest = self.lvalue(left)
            sourcekind = self.kind(right)
            if 3 in (destkind, sourcekind):
                self.error('chained string assignment is not supported')
            self.emit(0x5C, destkind * 4 + sourcekind, dest)
            self.operand(value)
            self.emit(0x79 + destkind, slot)
            return ('temporary', destkind, slot)
        leftvalue = self.expression(left, slot)
        rightvalue = self.expression(right, slot + int(leftvalue[0] == 'temporary'))
        sourcekind = max(self.kind(left), self.kind(right))
        if sourcekind == 3:
            self.error('numeric expressions do not accept strings')
        resultkind = self.kind(node)
        self.emit(OPS[op], resultkind * 4 + sourcekind)
        self.operand(leftvalue)
        self.operand(rightvalue)
        self.emit(0x79 + resultkind, slot)
        return ('temporary', resultkind, slot)

    def boolean_branch(self, node, wanted, fixups, slot):
        if node[0] == 'binary' and node[1] in ('&&', '||'):
            natural = node[1] == '||'
            branches = fixups if wanted == natural else []
            self.boolean_branch(node[2], natural, branches, slot)
            self.boolean_branch(node[3], natural, branches, slot)
            if wanted != natural:
                fixups.append(self.jump(0x62))
                for offset in branches:
                    self.patch(offset)
            return
        if self.kind(node) == 3:
            self.error('numeric boolean operand required')
        value = self.expression(node, slot)
        if value[0] == 'constant':
            if bool(value[2]) == wanted:
                fixups.append(self.jump(0x62))
        else:
            fixups.append(self.jump(0xBC if wanted else 0xBD))
            self.operand(value)

    def boolean(self, node, slot):
        wanted = node[1] == '||'
        fixups = []
        self.boolean_branch(node, wanted, fixups, slot)
        self.emit(0x5B, 0, 0x79, slot, 0xAB, word(not wanted))
        end = self.jump(0x62)
        for offset in fixups:
            self.patch(offset)
        self.emit(0x5B, 0, 0x79, slot, 0xAB, word(wanted))
        self.patch(end)

    def assign(self, tokens, chained=False):
        destnode = ('symbol', tokens[0])
        destkind, dest = self.lvalue(destnode)
        rhs = self.tree(tokens[2:])
        if tokens[1] != '=':
            rhs = ('binary', tokens[1][0], destnode, rhs)
        value = self.expression(rhs)
        sourcekind = self.kind(rhs)
        if destkind == 3:
            if sourcekind != 3:
                self.error('string source required')
            self.emit(0xAC, dest)
            self.operand(value)
            self.emit(0)
        else:
            if sourcekind == 3:
                self.error('numeric source required')
            self.emit(0x5C if chained else 0x5B, destkind * 4 + sourcekind, dest)
            self.operand(value)
            if chained:
                self.emit(0x79 + destkind, 0)

    def arguments(self, tokens):
        parser = Expression([t for t in tokens if t != ','], self.line)
        args = []
        while parser.pos < len(parser.tokens):
            args.append(parser.parse(7))
        return args

    def set_command(self, tokens):
        if len(tokens) < 3:
            self.error('SET requires a setting and value')
        setting = tokens[1]
        if setting in SET_BOOLEAN or setting == 'duplex':
            values = ('full', 'half') if setting == 'duplex' else ('off', 'on')
            index = 3 if setting == 'fgets_crlf' and len(tokens) > 2 and tokens[2] == ',' else 2
            if len(tokens) != index + 1 or tokens[index] not in values:
                self.error(f'SET {setting.upper()} requires {"/".join(values).upper()}')
            self.emit(0x9E, 0x18 if setting == 'duplex' else SET_BOOLEAN[setting],
                      values.index(tokens[index]))
        elif setting in SET_INTEGER:
            # Range checks belong to the native runtime reader. The original
            # compiler also emits out-of-range integer constants unchanged.
            operands = tokens[3:] if tokens[2] == ',' else tokens[2:]
            parser = Expression(operands, self.line)
            node = parser.parse(7)
            if parser.pos != len(parser.tokens) or operands[0] == '(':
                self.error(f'SET {setting.upper()} requires an atomic integer operand')
            value = self.word_argument(node)
            self.emit(0x9E, SET_INTEGER[setting])
            self.operand(value, compact=True)
        else:
            self.error(f'unsupported SET setting {setting}')

    def fetch_command(self, tokens):
        # FETCH queries a setting; GET is an unrelated interactive input command.
        # Other native FETCH families remain outside the maintained subset.
        if len(tokens) < 3 or tokens[1] not in FETCH_SETTINGS:
            self.error('unsupported or incomplete FETCH setting')
        operands = tokens[3:] if tokens[2] == ',' else tokens[2:]
        if not operands or operands[0] == '(':
            self.error('FETCH requires an integer destination')
        parser = Expression(operands, self.line)
        node = parser.parse(7)
        if parser.pos != len(parser.tokens):
            self.error('unexpected FETCH operands')
        kind, wire = self.lvalue(node)
        if kind != 0:
            self.error('FETCH requires an integer destination')
        self.emit(0x37, FETCH_SETTINGS[tokens[1]], wire)

    def execute_command(self, tokens):
        # Native source spelling is EXECUTE; CHAIN is not a compiler keyword.
        # File resolution belongs to the loader, not this string emission.
        operands = tokens[1:]
        if not operands or operands[0] in ('(', ','):
            self.error('EXECUTE requires one atomic string operand')
        parser = Expression(operands, self.line)
        node = parser.parse(7)
        if parser.pos != len(parser.tokens) or self.kind(node) != 3:
            self.error('EXECUTE requires one atomic string operand')
        self.emit(0xCB)
        self.operand(self.atomic(node), compact=True)

    def when_command(self, tokens):
        command = tokens[0]
        # Commas are separators in native compiler input. They cannot replace
        # the required slot itself, and a slot expression/parenthesis is not
        # part of this atomic-operand command grammar.
        operands = tokens[1:]
        if not operands or operands[0] == ',':
            self.error(f'{command} requires a slot or DISCONNECT')
        operands = [token for token in operands if token != ',']
        disconnected = operands[0] == 'disconnect'
        parser = Expression(operands, self.line)
        self.emit(0xD6 if command == 'when' else 0x1C, int(not disconnected))
        if disconnected:
            parser.pos = 1
        else:
            if operands[0] == '(':
                self.error('WHEN/CWHEN slot must be an atomic integer operand')
            slot = parser.parse(7)
            self.operand(self.word_argument(slot), compact=True)
        if command == 'cwhen':
            if parser.pos != len(operands):
                self.error('CWHEN accepts one slot or DISCONNECT')
            return
        if not disconnected:
            pattern = parser.parse(7)
            if self.kind(pattern) != 3:
                self.error('WHEN requires a string pattern')
            self.operand(self.atomic(pattern), compact=True)
        if parser.pos >= len(operands):
            self.error('WHEN requires TRANSMIT or CALL action')
        action = operands[parser.pos]
        parser.pos += 1
        if action == 'transmit':
            response = parser.parse(7)
            if self.kind(response) != 3:
                self.error('WHEN TRANSMIT requires a string response')
            self.emit(0x32)
            self.operand(self.atomic(response), compact=True)
        elif action == 'call':
            if parser.pos >= len(operands) or operands[parser.pos] not in self.procedures:
                self.error('unknown WHEN called procedure')
            callee = self.procedures[operands[parser.pos]]
            parser.pos += 1
            if callee.params:
                self.error('WHEN CALL does not accept procedure parameters')
            self.emit(7)
            offset = self.jump(0xC8 if callee.size else 0xC7)
            self.fixups.append((offset, callee))
        else:
            self.error('WHEN action must be TRANSMIT or CALL')
        if parser.pos != len(operands):
            self.error('unexpected WHEN action operands')

    def command(self, tokens):
        command = tokens[0]
        if command == 'break' and len(tokens) != 1:
            self.error('BREAK does not accept operands or punctuation')
        if command == 'execute':
            self.execute_command(tokens)
            return
        if command == 'fetch':
            self.fetch_command(tokens)
            return
        if command == 'find':
            self.find_command(tokens)
            return
        if command == 'set':
            self.set_command(tokens)
            return
        if command in ('when', 'cwhen'):
            self.when_command(tokens)
            return
        if command in ('chdir', 'mkdir', 'rmdir', 'delete'):
            parser = Expression(tokens[1:], self.line)
            if not parser.tokens or parser.tokens[0] in ('(', ','):
                self.error(f'{command} requires one atomic string')
            node = parser.parse(7)
            if parser.pos != len(parser.tokens) or self.kind(node) != 3:
                self.error(f'{command} requires one atomic string')
            self.emit({'chdir': 0x11, 'mkdir': 0x79, 'rmdir': 0x99, 'delete': 0x20}[command])
            self.operand(self.atomic(node), compact=True)
            return
        file_commands = {
            'diskfree': (0x25, 'vl'), 'dosver': (0x29, 'd'), 'getdir': (0x4B, 'vd'),
            'getfdate': (0x4E, 'sd'), 'getftime': (0x51, 'sd'),
            'setfdate': (0xA0, 'ss'), 'setftime': (0xA1, 'ss'),
            'getfattr': (0x4D, 'sd'), 'setfattr': (0x9F, 'ss'),
            'findfirst': (0x3C, 'sS'), 'findnext': (0x3D, ''),
            'isfile': (0x60, 's'), 'getfsize': (0x50, 'sl'), 'rename': (0x93, 'ss'),
            'eof': (0x31, 'vi'), 'fclear': (0x35, 'v'), 'fclose': (0x36, 'v'),
            'fflush': (0x38, 'v'), 'fgetc': (0x39, 'vi'), 'fgets': (0x3A, 'vd'),
            'fopen': (0x3F, 'vss'), 'fputc': (0x40, 'vv'), 'fputs': (0x41, 'vs'),
            'fread': (0x42, 'vdvi'), 'fseek': (0x43, 'vqv'),
            'ftell': (0x45, 'vl'), 'fwrite': (0x47, 'vsv'),
        }
        if command in file_commands:
            opcode, signature = file_commands[command]
            parser = Expression(tokens[1:], self.line)
            self.emit(opcode)
            for index, role in enumerate(signature):
                if role == 'S':
                    present = parser.pos < len(parser.tokens)
                    self.emit(int(present))
                    if not present:
                        break
                    role = 's'
                if index and parser.pos < len(parser.tokens) and parser.tokens[parser.pos] == ',':
                    parser.pos += 1
                if parser.pos == len(parser.tokens) or parser.tokens[parser.pos] in ('(', ','):
                    self.error(f'{command} requires atomic operands')
                node = parser.parse(7)
                if role in 'dil':
                    expected = {'d': 3, 'i': 0, 'l': 1}[role]
                    kind, wire = self.lvalue(node)
                    if kind != expected:
                        self.error(f'{command} destination type mismatch')
                    self.emit(wire)
                elif role == 'v':
                    self.operand(self.word_argument(node), compact=True)
                else:
                    value = self.atomic(node)
                    if role == 's' and self.kind(node) != 3:
                        self.error(f'{command} requires a string')
                    if role == 'q':
                        if value[0] == 'constant' and value[1] != 2:
                            value = ('constant', 1, value[2])
                        elif self.kind(node) != 1:
                            self.error('FSEEK requires a long offset')
                    self.operand(value, compact=True)
            if parser.pos != len(parser.tokens):
                self.error(f'unexpected {command} operands')
            return
        args = self.arguments(tokens[1:])
        if command in ('rget', 'waitquiet'):
            destination = int(command == 'rget')
            if not destination <= len(args) <= destination + 2:
                self.error(f'{command} operand count mismatch')
            self.emit(0xCE if destination else 0xD5)
            if destination:
                kind, wire = self.lvalue(args[0])
                if kind != 3:
                    self.error('RGET requires string destination')
                self.emit(wire)
            for index in range(destination, destination + 2):
                if index >= len(args):
                    self.emit(0)
                    break
                self.emit(1)
                if command == 'waitquiet' and index == 1 and args[index] == ('symbol', 'forever'):
                    self.emit(0x1A)
                else:
                    self.operand(self.word_argument(args[index]), compact=True)
            return
        # (opcode, mandatory operand types, optional numeric count)
        commands = {
            'comgetc': (0xC9, 'i', False), 'comgetcd': (0xCA, 'i', False),
            'message': (0x76, 's', False), 'exit': (0x33, '', False),
            'break': (0x0D, '', False),
            'transmit': (0xBF, 's', False), 'waitfor': (0xD4, 's', True),
            'rstrcmp': (0x9A, 'ss', True),
            'atoi': (0x06, 'si', False), 'atol': (0x07, 'sl', False),
            'itoa': (0x61, 'wd', False), 'ltoa': (0x6E, 'qd', False),
            'strcat': (0xAA, 'ds', True), 'strcmp': (0xAB, 'ss', True),
            'strcpy': (0xAC, 'ds', True), 'strlen': (0xAE, 'si', False),
            'strlwr': (0xAF, 'd', False), 'strpeek': (0xB0, 'sni', False),
            'strpoke': (0xB1, 'dnn', False), 'strset': (0xB2, 'dn', True),
            'strupdt': (0xB3, 'dsnn', False), 'strupr': (0xB4, 'd', False),
            'substr': (0xB6, 'dsnn', False), 'pause': (0x88, 'v', False),
        }
        if command not in commands:
            self.error(f'unsupported command {command}')
        opcode, signature, optional = commands[command]
        if not len(signature) <= len(args) <= len(signature) + int(optional):
            self.error(f'{command} operand count mismatch')
        self.emit(opcode)
        for role, arg in zip(signature, args):
            kind = self.kind(arg)
            if role in 'ds' and kind != 3:
                self.error(f'{command} requires string operand')
            if role == 'd':
                self.emit(self.lvalue(arg)[1])
            elif role in 'il':
                expected = 0 if role == 'i' else 1
                if self.lvalue(arg)[0] != expected:
                    self.error(f'{command} requires {("integer", "long")[expected]} destination')
                self.emit(self.lvalue(arg)[1])
            else:
                if role in 'nvwq' and kind == 3:
                    self.error(f'{command} requires numeric operand')
                value = self.atomic(arg)
                if role == 'v':
                    value = self.word_argument(arg)
                if role in 'wq':
                    expected = 0 if role == 'w' else 1
                    if value[0] == 'constant' and value[1] != 2:
                        value = ('constant', expected, value[2])
                    elif kind != expected:
                        self.error(f'{command} requires {("integer", "long")[expected]} source')
                self.operand(value, compact=True)
        if optional:
            self.emit(int(len(args) > len(signature)))
            if len(args) > len(signature):
                if command == 'waitfor' and args[-1] == ('symbol', 'forever'):
                    self.emit(0x1A)
                else:
                    if self.kind(args[-1]) == 3:
                        self.error('numeric count required')
                    value = (self.word_argument(args[-1]) if command == 'waitfor'
                             else self.atomic(args[-1]))
                    self.operand(value, compact=True)

    def word_argument(self, node):
        value = self.atomic(node)
        # -32768 is the sole accepted unsigned-token boundary crossing: its
        # positive token is long-classified, but this command expects a word.
        minimum = (node[0] == 'unary' and node[1] == '-' and
                   node[2][0] == 'constant' and node[2][2] == 32768 and
                   node[2][1] != 2 and not node[2][3])
        if self.kind(node) != 0 and not minimum:
            self.error('integer command operand required')
        if value[0] == 'constant':
            if not -32768 <= value[2] <= 32767:
                self.error('integer command constant outside -32768..32767')
            return ('constant', 0, value[2])
        return value

    def atomic(self, node):
        if node[0] == 'unary' and node[1] == '-' and node[2][0] == 'constant':
            return ('constant', node[2][1], -node[2][2])
        if node[0] not in ('constant', 'symbol', 'string'):
            self.error('command and call operands must be atomic')
        return node

    def switch_operand(self, tokens, expected=None):
        if not tokens or tokens[0] in ('(', ','):
            self.error('SWITCH/CASE requires one atomic integer or string operand')
        parser = Expression(tokens, self.line)
        node = parser.parse(7)
        if parser.pos != len(tokens):
            self.error('unexpected SWITCH/CASE operands')
        kind = self.kind(node)
        value = self.atomic(node) if kind == 3 else self.word_argument(node)
        kind = 3 if kind == 3 else 0
        if expected is not None and kind != expected:
            self.error('CASE operand type differs from SWITCH')
        return kind, value

    def switch_statement(self, tokens, blocks):
        command = tokens[0]
        if command == 'switch':
            kind, value = self.switch_operand(tokens[1:])
            self.emit(0xB8)
            self.operand(value, compact=True)
            offset = len(self.output)
            self.emit(dword(0))
            blocks.append(['switch', dict(kind=kind, first=offset, next=None,
                                          default=None, exits=[], opened=False)])
            return
        if not blocks or blocks[-1][0] != 'switch':
            self.error(f'unmatched {command}')
        state = blocks[-1][1]
        if command in ('case', 'default'):
            if command == 'default' and (len(tokens) != 1 or state['default'] is not None):
                self.error('invalid or duplicate DEFAULT')
            # An implicit CASE boundary falls into the following body, skipping
            # its match record. DEFAULT has no record, so needs no such jump.
            shared = self.jump(0x62) if state['opened'] and command == 'case' else None
            if command == 'case':
                _, value = self.switch_operand(tokens[1:], state['kind'])
                target = len(self.output)
                self.patch(state['next'] if state['next'] is not None else state['first'], target)
                self.emit(0x0F)
                state['next'] = len(self.output)
                self.emit(dword(0))
                self.operand(value, compact=True)
                if shared is not None:
                    self.patch(shared)
            else:
                state['default'] = len(self.output)
            state['opened'] = True
        elif command == 'endcase':
            if len(tokens) != 1 or not state['opened']:
                self.error('unmatched ENDCASE')
            state['exits'].append(self.jump(0x62))
            state['opened'] = False
        else:
            if len(tokens) != 1 or state['opened']:
                self.error('ENDSWITCH requires preceding ENDCASE')
            target = state['default'] if state['default'] is not None else len(self.output)
            self.patch(state['next'] if state['next'] is not None else state['first'], target)
            for offset in state['exits']:
                self.patch(offset)
            blocks.pop()

    def find_command(self, tokens):
        parser = Expression(tokens[1:], self.line)
        self.emit(0x3B)
        for index in range(2):
            if index and parser.pos < len(parser.tokens) and parser.tokens[parser.pos] == ',':
                parser.pos += 1
            if parser.pos == len(parser.tokens) or parser.tokens[parser.pos] in ('(', ','):
                self.error('FIND requires two atomic strings')
            node = parser.parse(7)
            if self.kind(node) != 3:
                self.error('FIND requires string source and pattern')
            self.operand(self.atomic(node), compact=True)
        optional = parser.pos < len(parser.tokens)
        self.emit(int(optional))
        if optional:
            if parser.tokens[parser.pos] == ',':
                parser.pos += 1
            if parser.pos == len(parser.tokens) or parser.tokens[parser.pos] in ('(', ','):
                self.error('FIND requires an integer destination')
            node = parser.parse(7)
            kind, wire = self.lvalue(node)
            if kind != 0:
                self.error('FIND destination must be integer')
            self.emit(wire)
        if parser.pos != len(parser.tokens):
            self.error('unexpected FIND operands')

    def condition(self, tokens):
        node = self.tree(tokens)
        if self.kind(node) == 3:
            self.error('numeric condition required')
        value = self.expression(node)
        if value[0] != 'temporary':
            kind = self.kind(node)
            self.emit(0x5B, kind, 0x79, 0)
            self.operand(value)
        branch = self.jump(0x15)
        self.emit(0x79, 0)
        return branch

    def statements(self, proc):
        blocks = []
        for self.line, tokens in proc.lines:
            command = tokens[0]
            if command in ('else', 'endif', 'endwhile', 'exitwhile', 'loopwhile') and len(tokens) != 1:
                self.error(f'{command} does not accept operands')
            switch_commands = ('switch', 'case', 'default', 'endcase', 'endswitch')
            if (blocks and blocks[-1][0] == 'switch' and
                    not blocks[-1][1]['opened'] and command not in ('case', 'default', 'endswitch')):
                self.error('SWITCH requires CASE/DEFAULT or ENDSWITCH')
            if command in switch_commands:
                self.switch_statement(tokens, blocks)
            elif command == 'if':
                blocks.append(['if', self.condition(tokens[1:]), []])
            elif command in ('else', 'elseif'):
                if not blocks or blocks[-1][0] != 'if' or blocks[-1][1] is None:
                    self.error('unmatched else/elseif')
                block = blocks[-1]
                block[2].append(self.jump(0x62))
                self.patch(block[1])
                block[1] = self.condition(tokens[1:]) if command == 'elseif' else None
            elif command == 'endif':
                if not blocks or blocks[-1][0] != 'if':
                    self.error('unmatched endif')
                block = blocks.pop()
                if block[1] is not None:
                    self.patch(block[1])
                for offset in block[2]:
                    self.patch(offset)
            elif command == 'while':
                start = len(self.output)
                blocks.append(['while', self.condition(tokens[1:]), [], start])
            elif command in ('exitwhile', 'loopwhile'):
                block = next((b for b in reversed(blocks) if b[0] == 'while'), None)
                if block is None:
                    self.error('loop command outside while')
                offset = self.jump(0x62)
                if command == 'exitwhile':
                    block[2].append(offset)
                else:
                    self.patch(offset, block[3])
            elif command == 'endwhile':
                if not blocks or blocks[-1][0] != 'while':
                    self.error('unmatched endwhile')
                block = blocks.pop()
                self.patch(self.jump(0x62), block[3])
                self.patch(block[1])
                for offset in block[2]:
                    self.patch(offset)
            elif command in ('call', 'gosub'):
                if len(tokens) < 2 or tokens[1] not in self.procedures:
                    self.error('unknown called procedure')
                callee = self.procedures[tokens[1]]
                if len(tokens) > 2 and tokens[2] != 'with':
                    self.error('call arguments require WITH')
                args = self.arguments(tokens[3:])
                if len(args) != len(callee.params):
                    self.error('call parameter count mismatch')
                self.emit(0xD0)
                for arg, param in zip(args, callee.params):
                    if self.kind(arg) != param.kind:
                        self.error('call parameter type mismatch')
                    self.emit(0xCD if param.kind == 3 else 0xCC)
                    self.operand(self.atomic(arg), compact=True)
                offset = self.jump(0xC8 if callee.size or callee.params else 0xC7)
                self.fixups.append((offset, callee))
                if args:
                    self.emit(0xD2, word(-sum(SIZES[p.kind] for p in callee.params)))
            elif len(tokens) == 2 and (command in ('++', '--') or tokens[1] in ('++', '--')):
                op, name = tokens if command in ('++', '--') else tokens[::-1]
                kind, dest = self.lvalue(('symbol', name))
                if kind == 3:
                    self.error('numeric increment destination required')
                self.emit(0x5A if op == '++' else 0x1E, dest)
            elif len(tokens) > 2 and tokens[1] in ('=', '+=', '-=', '*=', '/=', '%='):
                self.assign(tokens)
            else:
                self.command(tokens)
        if blocks:
            self.error('unterminated conditional or loop')

    def emitted_procedures(self):
        # Original compiler discards zero-reference procedures repeatedly,
        # preserving MAIN and mutually referenced dead cycles. This is not a
        # reachability-only rewrite; emitted order remains declaration order.
        references = {}
        for name, proc in self.procedures.items():
            called = set()
            for _, tokens in proc.lines:
                if tokens[0] in ('call', 'gosub') and len(tokens) > 1:
                    called.add(tokens[1])
                elif tokens[0] == 'when':
                    for index, token in enumerate(tokens[:-1]):
                        if token == 'call':
                            called.add(tokens[index + 1])
            references[name] = called & self.procedures.keys()
        included = set(self.procedures)
        while True:
            referenced = set().union(*(references[name] for name in included))
            discard = included - referenced - {'main'}
            if not discard:
                break
            included -= discard
        return [proc for name, proc in self.procedures.items() if name in included]

    def emit_procedures(self, procedures):
        # The inventory can omit a trailing part with unmatched parentheses.
        # Native compiler C037/C038 still reject it, including unused bodies.
        for self.line, tokens in self.declaration_lines:
            depth = 0
            for token in tokens:
                depth += (token == '(') - (token == ')')
                if depth < 0:
                    self.error('missing left parenthesis in declaration')
            if depth:
                self.error('missing right parenthesis in declaration')
        self.emit(self.counts[3])
        # The original retains this prefix when the first declared procedure
        # is unused and removed, leaving a jump to the following MAIN.
        if next(iter(self.procedures)) != 'main':
            self.fixups.append((self.jump(0x62), self.procedures['main']))
        for proc in procedures:
            self.proc = proc
            proc.address = len(self.output)
            if proc.size:
                self.emit(0xD2, word(proc.size))
            for self.line, tokens, chained in proc.initializers:
                self.assign(tokens, chained)
            self.emit(0xCF)
            self.statements(proc)
            self.emit(0x95 if proc.size or proc.params else 0x94)
        for offset, proc in self.fixups:
            self.patch(offset, proc.address)

    def compile(self, source: str) -> bytes:
        current = None
        for self.line, text in enumerate(source.splitlines(), 1):
            if len(text.encode('cp437')) > 253:
                self.error('physical source lines over 253 bytes are outside this compiler subset')
            tokens = tokenize(text, self.line)
            if not tokens:
                continue
            if tokens[0] == 'proc':
                if (current or len(tokens) != 2 or tokens[1] in self.procedures or
                        not re.fullmatch(r'[a-z_$][a-z_0-9$]*', tokens[1])):
                    self.error('invalid or duplicate procedure declaration')
                current = Procedure(tokens[1])
                self.procedures[current.name] = current
            elif tokens[0] == 'endproc':
                if current is None or len(tokens) != 1:
                    self.error('unmatched endproc')
                current = None
            elif tokens[0] in TYPES or tokens[0] in PARMS:
                self.declaration_lines.append((self.line, tokens))
                self.declarations(tokens, current, self.line)
            elif current is None:
                self.error('statement outside procedure')
            else:
                current.lines.append((self.line, tokens))
        if current:
            self.error('unterminated procedure')
        if 'main' not in self.procedures:
            self.error('missing main procedure')
        for proc in self.procedures.values():
            offset = sum(SIZES[p.kind] for p in proc.params) + 6
            for param in proc.params:
                param.index = offset
                offset -= SIZES[param.kind]
        selected = self.emitted_procedures()
        if len(selected) != len(self.procedures):
            # Native compiler still rejects malformed unused bodies. Validate
            # them before the final offset/literal-position emission pass.
            self.emit_procedures(self.procedures.values())
            self.output = bytearray()
            self.fixups = []
        self.emit_procedures(selected)
        return bytes(self.output)


def compile_source(source: str) -> bytes:
    """Compile one CP437-representable ASPECT source, returning complete ASX."""
    source.encode('cp437')
    return Compiler().compile(source)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('-o', '--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        result = compile_source(args.source.read_bytes().decode('cp437'))
    except (CompileError, UnicodeError) as error:
        parser.exit(1, f'{args.source}: {error}\n')
    args.output.write_bytes(result)


if __name__ == '__main__':
    main()
