#!/usr/bin/env python3
"""Original-free compiler regressions against authored, frozen oracle outcomes."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src/aspect'))
from compiler import CompileError, compile_source  # noqa: E402

CORPORA = ('execution', 'arithmetic', 'parameter', 'string_command',
           'conversion', 'compiler_validation', 'console', 'serial', 'receive', 'directory')
COUNTS = {'frozen_vectors_checked': 0, 'presentation_variants_checked': 0,
          'frozen_rejections_checked': 0}


def vectors():
    for corpus in CORPORA:
        path = ROOT / f'standalone/fixtures/aspect_{corpus}_vectors.json'
        data = json.loads(path.read_text())
        for vector in data['vectors'] + data.get('compiler_only', []):
            yield corpus, vector


class CompilerTests(unittest.TestCase):
    def test_frozen_original_compiler_vectors(self):
        count = 0
        for corpus, vector in vectors():
            with self.subTest(corpus=corpus, name=vector['name']):
                actual = compile_source(vector['source'])
                self.assertEqual(hashlib.sha256(vector['source'].encode('cp437')).hexdigest(),
                                 vector['source_sha256'])
                self.assertEqual(actual, bytes.fromhex(vector['hex']))
                self.assertEqual(hashlib.sha256(actual).hexdigest(), vector['asx_sha256'])
                COUNTS['frozen_vectors_checked'] += 1
            count += 1
        self.assertGreaterEqual(count, 358)

    def test_console_and_serial_original_compiler_rejections(self):
        for corpus in ('console', 'serial', 'receive', 'directory'):
            data = json.loads((ROOT / f'standalone/fixtures/aspect_{corpus}_vectors.json').read_text())
            for vector in data['rejected']:
                with self.subTest(corpus=corpus, name=vector['name']), self.assertRaises(CompileError):
                    compile_source(vector['source'])
                COUNTS['frozen_rejections_checked'] += 1

    def test_case_whitespace_and_symbol_renaming(self):
        # Changes lexical presentation, not source line numbers or string bytes.
        replacements = {'va': 'northern', 'vb': 'southern', 'vc': 'western',
                        'outcome': 'answer', 'helper': 'worker'}
        import re
        for corpus, vector in vectors():
            def alter(match):
                token = match.group(0)
                if token.startswith('"'):
                    return token
                return replacements.get(token.lower(), token).upper()
            changed = re.sub(r'"[^"\r\n]*"|[a-zA-Z_$][a-zA-Z_0-9$]*',
                             alter, vector['source'])
            changed = '\n'.join('  \t' + line + '  ' for line in changed.splitlines())
            with self.subTest(corpus=corpus, name=vector['name']):
                self.assertEqual(compile_source(changed), bytes.fromhex(vector['hex']))
                COUNTS['presentation_variants_checked'] += 1

    def test_authored_reordered_procedures_and_new_constants(self):
        source = ('integer answer\nproc worker\nanswer = 123\nendproc\n'
                  'proc main\ncall worker\nendproc\n')
        self.assertEqual(compile_source(source), bytes.fromhex(
            '00 62 0f000000 cf 5b00 8d00 ab7b00 94 cf d0 c706000000 94'))

    def test_authored_large_absolute_target(self):
        # Crosses the 16-bit file-offset boundary with genuine emitted code.
        source = ('integer answer\nproc main\ncall worker\n' +
                  'answer = 123\n' * 10000 +
                  'endproc\nproc worker\nanswer = 42\nendproc\n')
        wire = compile_source(source)
        target = int.from_bytes(wire[4:8], 'little')
        self.assertGreater(target, 65535)
        self.assertEqual(target, 70009)
        self.assertEqual(wire[target:], bytes.fromhex('cf 5b00 8d00 ab2a00 94'))

    def test_authored_comments_and_numeric_line_endings(self):
        source = ('; source-only example\r\ninteger answer ; bank0\r\n'
                  'proc main\r\n\r\nanswer = 42 ; meaningful value\r\nendproc\r\n')
        self.assertEqual(compile_source(source), bytes.fromhex('00 cf 5b00 8d00 ab2a00 94'))

    def test_explicit_rejections(self):
        bodies = [
            'unknown 1', 'missing = 2', 'answer =', 'answer = (1+2',
            'answer = 1 2', 'answer = +1', 'answer = "bad"',
            'call missing', 'call worker with 1', 'call worker 1',
            'if 1\nanswer = 2', 'endif', 'else', 'endwhile',
            'exitwhile', 'loopwhile', 'if 1\nelse 2\nendif',
            'strcpy answer "bad"', 'strcmp "A"', 'atoi "1" msgbuf',
            'strcpy msgbuf "x" "badcount"', 'msgbuf = 1',
            'msgbuf = "' + 'A' * 81 + '"', 'answer = 1 @ 2',
        ]
        for body in bodies:
            source = ('integer answer\nstring msgbuf\nproc main\n' + body +
                      '\nendproc\nproc worker\nendproc\n')
            with self.subTest(body=body), self.assertRaises(CompileError):
                compile_source(source)
        for source in ('proc main\n', 'endproc\n', 'proc worker\nendproc\n',
                       'integer a,a\nproc main\nendproc\n',
                       'intparm a\nproc main\nendproc\n',
                       'integer x=2\nproc main\nendproc\n'):
            with self.subTest(source=source), self.assertRaises(CompileError):
                compile_source(source)
        with self.assertRaises(CompileError):
            compile_source('\n'.join(f'string x{i}' for i in range(129)) +
                           '\nproc main\nendproc\n')

    def test_independent_per_type_global_banks_and_local_limit(self):
        source = '\n'.join(f'{kind} x{kind}{i}' for kind in ('integer', 'long', 'string')
                           for i in range(128)) + '\nproc main\nendproc\n'
        self.assertEqual(compile_source(source), bytes.fromhex('80 cf 94'))
        source = ('proc main\n' + '\n'.join(f'integer x{i}' for i in range(129)) +
                  '\nendproc\n')
        with self.assertRaisesRegex(CompileError, 'local variable limit'):
            compile_source(source)

    def test_call_parameter_type_and_count(self):
        for arguments in ('7', '"string"', '7L 8L', '(7L+8L)', ''):
            source = ('proc main\ncall worker with ' + arguments +
                      '\nendproc\nproc worker\nlongparm number\nendproc\n')
            with self.subTest(arguments=arguments), self.assertRaises(CompileError):
                compile_source(source)

    def test_cli_cp437_and_failed_output_preservation(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            source, output = directory / 'NEW.ASP', directory / 'NEW.ASX'
            source.write_bytes('string msgbuf\r\nproc main\r\nmsgbuf = "éÇ"\r\nendproc\r\n'.encode('cp437'))
            result = subprocess.run([sys.executable, str(ROOT / 'src/aspect/compiler.py'),
                                     str(source), '-o', str(output)], capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(output.read_bytes(), compile_source(source.read_bytes().decode('cp437')))
            baseline = output.read_bytes()
            source.write_text('proc main\nunsupportedcommand\nendproc\n')
            result = subprocess.run([sys.executable, str(ROOT / 'src/aspect/compiler.py'),
                                     str(source), '-o', str(output)], capture_output=True)
            self.assertEqual(result.returncode, 1)
            self.assertIn(b'line 2:', result.stderr)
            self.assertEqual(output.read_bytes(), baseline)


if __name__ == '__main__':
    program = unittest.main(verbosity=1, exit=False)
    def digest(path):
        return hashlib.sha256(path.read_bytes()).hexdigest()
    report = {
        'scope': 'Host source compiler tests; frozen public original outcomes are data, no original executable is read.',
        'original_inputs': [],
        'success': program.result.wasSuccessful(),
        'test_methods': program.result.testsRun,
        **COUNTS,
        'compiler_sha256': digest(ROOT / 'src/aspect/compiler.py'),
        'checker_sha256': digest(Path(__file__)),
        'fixture_sha256': {
            corpus: digest(ROOT / f'standalone/fixtures/aspect_{corpus}_vectors.json')
            for corpus in CORPORA
        },
    }
    output = ROOT / 'build/aspect-compiler/checks.json'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + '\n')
    print(f'Compiler: {COUNTS["frozen_vectors_checked"]} frozen vectors, '
          f'{COUNTS["presentation_variants_checked"]} presentation variants; '
          f'{output.relative_to(ROOT)}')
    sys.exit(0 if program.result.wasSuccessful() else 1)
