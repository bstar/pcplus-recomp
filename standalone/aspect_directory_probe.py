#!/usr/bin/env python3
"""Optional original compiler oracle for authored directory builtin expressions.

Original compiler is private and hash-verified; no installed dialing files read.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
ROOT = Path(__file__).resolve().parents[1]
COMPILER = '5664fdfae375774da5303cc8b53c00ef773a6650132de73c7206e46ddc05039a'
def sha(data):
    return hashlib.sha256(data).hexdigest()
def corpus():
    cases = {}
    def add(name, declarations, body, *, helper='', expected=None, compiler_only=False):
        source = declarations + '\r\nproc main\r\n' + body.replace('\n','\r\n') + '\r\nendproc\r\n' + helper.replace('\n', '\r\n')
        cases[name] = dict(source=source, expected=expected, compiler_only=compiler_only)
    names = ['$D_LDATE','$D_KBDFILE','$D_METAKEY','$D_NAME','$D_NOTE','$D_PHONE','$D_PWORD','$D_SCRIPT']
    for slot, word in enumerate(names):
        add('DIR'+str(slot), 'string target', 'target = '+word)
    add('DIRNUM', 'integer target', 'target = $D_ENTRY')
    add('DIRBAUD', 'long target', 'target = $D_BAUD')
    add('DIRALL', '', '\n'.join('message '+word for word in names))
    add('DIRTX', '', 'transmit $D_PWORD')
    add('DIRLOC', '', 'string target\ntarget = $D_PWORD\nmessage target')
    add('DMCONCAT', 'string target', 'target = $D_NAME\nstrcat target $D_PHONE', expected={'string0':'SYNTHETIC NODE555-0100'})
    add('DMPARAM', 'string target', 'call worker with $D_PWORD', helper='proc worker\nstrparm value\ntarget = value\nendproc\n', expected={'string0':'sYNth42!'})
    add('DMFRAME', 'string target', 'string value\nvalue = $D_PHONE\ntarget = value', expected={'string0':'555-0100'})
    add('DMMIXED', 'string label,secret\ninteger selected', 'label = $D_NAME\nsecret = $D_PWORD\nselected = $D_ENTRY', expected={'string0':'SYNTHETIC NODE','string1':'sYNth42!','integer0':7})
    add('DMEMPTY', 'string target', 'target = $D_PWORD', expected={'string0':''})
    add('DMHIGH', 'string target', 'target = $D_PWORD', expected={'string0':'éÇÿ'})
    for i,word in enumerate(['$D_USERNAME','$D_USER','$D_PASSWORD','$D_NUMBER']):
        add('MISS'+str(i), 'string target', 'target = '+word)
    for slot, word in enumerate(names):
        add('DECL'+str(slot), 'string '+word, 'message "UNREACHABLE"')
        add('DEST'+str(slot), '', word+' = "WRITE"')
    add('DECLINT', 'integer $D_ENTRY', '')
    add('DECLLONG', 'long $D_BAUD', '')
    add('DESTINT', '', '$D_ENTRY = 1')
    add('DESTLONG', '', '$D_BAUD = 9600L')
    add('WRONGINT', 'integer target', 'target = $D_PWORD')
    add('WRONGSTR', 'string target', 'target = $D_ENTRY')
    values = ['10/19/26','KEYFILE','METAKEY','SYNTHETIC NODE','NOTE','555-0100','sYNth42!','SIGNON']
    offsets = [61,95,86,0,105,25,75,52]
    record = bytearray(114)
    for value, offset in zip(values, offsets):
        raw = value.encode('cp437') + b'\0'
        record[offset:offset+len(raw)] = raw
    for name, case in cases.items():
        case['directory'] = dict(entry=7,record_hex=record.hex())
        if name in ['DIR'+str(n) for n in range(8)]:
            case['expected'] = {'string0':values[int(name[-1])]}
        elif name == 'DIRNUM':case['expected'] = {'integer0':7}
        elif name == 'DIRTX':case['expected'] = {'tx_hex':values[6].encode('cp437').hex()}
        elif name == 'DIRLOC':case['expected'] = {'stdout_hex':(values[6]+'\r\n').encode('cp437').hex()}
        elif name == 'DMEMPTY':
            empty = bytearray(record);empty[75:86] = b'\0'*11
            case['directory']['record_hex'] = empty.hex()
        elif name == 'DMHIGH':
            high = bytearray(record);raw='éÇÿ'.encode('cp437')+b'\0';high[75:75+len(raw)]=raw
            case['directory']['record_hex'] = high.hex()
        if name == 'DIRALL':case['expected'] = {'stdout_hex':('\r\n'.join(values)+'\r\n').encode('cp437').hex()}
        if name == 'DIRBAUD':
            case['compiler_only'] = True
            if case['expected'] is None:case['expected'] = {}
        if case['expected'] is not None:
            case['expected'].setdefault('stdout_hex','')
            case['expected'].setdefault('tx_hex','')
    return cases


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    assert out.parent == ROOT / 'analysis/aspect-directory' and out.name.startswith('compiler-')
    binary = (ROOT / 'analysis/pcplus-install/ASPCOMP.EXE').read_bytes()
    assert sha(binary) == COMPILER
    out.mkdir(parents=True, exist_ok=False)
    (out / 'ASPCOMP.EXE').write_bytes(binary)
    cases = corpus()
    batch = ['@echo off']
    for name, case in cases.items():
        assert len(name) <= 8
        (out / (name + '.ASP')).write_bytes(case['source'].encode('cp437'))
        batch += [f'ASPCOMP {name}.ASP >{name}.LOG', f'if errorlevel 1 goto E{name}',
                  f'echo ZERO>{name}.RC', f'goto D{name}', f':E{name}',
                  f'echo NONZERO>{name}.RC', f':D{name}']
    batch += ['echo COMPLETE>DONE.TXT']
    (out / 'RUN.BAT').write_bytes(('\r\n'.join(batch) + '\r\n').encode('ascii'))
    config = f'[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=386\ncycles=fixed 6000\n[mixer]\nnosound=true\n[autoexec]\n@echo off\nmount c "{out}"\nc:\ncall RUN.BAT\nexit\n'
    (out / 'dosbox.conf').write_text(config)
    with (out / 'dosbox.log').open('w') as log:
        subprocess.run(['dosbox-x', '-fastlaunch', '-nogui', '-conf', str(out / 'dosbox.conf')],
                       cwd=out, env=dict(os.environ, SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy'),
                       stdout=log, stderr=log, check=True, timeout=60)
    assert (out / 'DONE.TXT').read_text().strip() == 'COMPLETE'
    records = []
    for name, case in cases.items():
        log = (out / (name + '.LOG')).read_bytes()
        compiled = out / (name + '.ASX')
        success = b'Script file successfully compiled!' in log
        rc = (out / (name + '.RC')).read_text().strip()
        assert (rc == 'ZERO') == success == compiled.exists()
        record = dict(name=name, source=case['source'], source_sha256=sha(case['source'].encode('cp437')),
                      success=success, log_sha256=sha(log),
                      errors=[s for s in log.decode('cp437').splitlines() if s.startswith('Error')])
        if success:
            data = compiled.read_bytes()
            record.update(hex=data.hex(' '), asx_sha256=sha(data))
        records.append(record)
        print(name, 'accepted' if success else record['errors'])
    report = dict(compiler_sha256=COMPILER, harness_sha256=sha(Path(__file__).read_bytes()), cases=records,
                  scope='Authored source compilation only; expected values fixed independently before runtime execution.')
    (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print('accepted', sum(r['success'] for r in records), 'of', len(records))


if __name__ == '__main__':
    main()
