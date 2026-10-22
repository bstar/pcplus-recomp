#!/usr/bin/env python3
"""Actual DOS control for the unchanged audio Record/compile/replay BIOS driver."""
import argparse,asyncio,contextlib,json,shutil,subprocess,types
from pathlib import Path
import audio_recording,enigma,test_dos
from enigma_script_login import source as login_source
from synthmodem_vm_control import ROOT,sha
import sys
sys.path.insert(0,str(ROOT/'src/aspect'))
from compiler import compile_source


async def main(args):
    assert args.label and all(c.isalnum() or c in '-_' for c in args.label)
    out=ROOT/'build/bbs-lab/results/enigma'/args.label
    assert not out.exists();out.mkdir(parents=True);stage=out/'program';stage.mkdir()
    names,helper_sha=audio_recording.inputs(args.keys)
    names += ['lab/bbs/check_audio_recording_tcp.py','lab/bbs/test_dos.py','lab/bbs/modem.py','lab/bbs/enigma_script_login.py',
        'lab/bbs/audio_get_vector.asm','standalone/test_terminal.py','standalone/terminal_config_fixtures.py',
        'standalone/modem_fixtures.py','standalone/directory_fixtures.py','standalone/directory_test_support.py']
    for directory,binary in (('terminal','TERMINAL.EXE'),('aspect-runner','ASPECT.EXE'),('aspect-compiler-dos','ASPCOMP.EXE')):
        base=ROOT/'build'/directory;m=json.loads((base/'manifest.json').read_text())
        assert m['binary_sha256']==sha(base/binary)
        assert all(sha(ROOT/name)==digest for name,digest in m['sources'].items())
        names += [str((base/binary).relative_to(ROOT)),str((base/'manifest.json').relative_to(ROOT)),*m['sources']]
        shutil.copy2(base/binary,stage/binary)
    script=login_source();marker='cwhen 0\ncwhen 1\ncwhen 2\nendproc\n'
    assert script.count(marker)==1
    script=script.replace(marker,'cwhen 0\ncwhen 1\ncwhen 2\nwaitquiet 1 10\ntransmit "F^M"\nwaitfor "File Base" 30\nwaitquiet 1 10\nendproc\n')
    (stage/'AUDIO.ASP').write_text(script);(stage/'AUDIO.ASX').write_bytes(compile_source(script))
    for name,leaf in (('audio_recording_keys.asm','EXITKEY.COM'),('audio_get_vector.asm','KEYVEC.COM')):
        subprocess.run(['nasm','-fbin',str(ROOT/'lab/bbs'/name),'-o',str(stage/leaf)],check=True)
    assert sha(stage/'EXITKEY.COM')==helper_sha
    frozen={name:sha(ROOT/name) for name in names}
    for name,digest in frozen.items():
        target=out/'frozen-source'/name;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(ROOT/name,target);assert sha(target)==digest
    (out/'start.json').write_text(json.dumps(dict(inputs=frozen,
        staged={p.name:sha(p) for p in stage.iterdir()},scope=__doc__),indent=2)+'\n')
    # Only test fixture integration changes: helper installation/collection
    # replaces ADDKEY. The maintained modem/serial/hardware checks remain.
    path=ROOT/'lab/bbs/test_dos.py';text=path.read_text()
    before='D:'+chr(92)*2+'SNAP B';after='D:'+chr(92)*2+'SNAP S'
    assert text.count(before)==text.count(after)==text.count('ADDKEY {keys}')==1
    text=text.replace(before,before+'\nEXITKEY').replace('ADDKEY {keys}','')
    text=text.replace(after,'EXITKEY R\nKEYVEC\n'+after)
    module=types.ModuleType('recording_TCP_control');module.__file__=str(path)
    exec(compile(text,str(path),'exec'),module.__dict__)
    directory=module.directory_image
    def contact(**options):
        data=bytearray(directory(**options));at=250+(options['entry']-1)*114
        data[at+52:at+61]=b'AUDIO\0\0\0\0';return bytes(data)
    module.directory_image=contact
    # Match the audio fixture's deliberate empty hangup string. The local
    # Hayes model forwards +++/ATH online instead of modeling escape mode;
    # preserve the same configured shutdown rather than filtering its bytes.
    directory_prm=module.directory_prm
    def profile(**options):
        data=bytearray(directory_prm(**options));data[0x79:0x79+25]=bytes(25);return bytes(data)
    module.directory_prm=profile
    options=argparse.Namespace(name='enigma',label=args.label,port=23233,com=2,baud=19200,flow='HARD',packet_delay_ms=0,
        dial_fixture=False,directory_fixture=True,directory_browser=False,entry=3,binary=stage/'TERMINAL.EXE',
        config_fixture=False,keymap_fixture=None,server_log=None,keys='',wait=2,timeout=340)
    with (out/'harness.log').open('w') as capture,contextlib.redirect_stdout(capture):code=await module.run(options)
    run=json.loads((out/'result.json').read_text())
    # The modem harness names this direction bbs-sent; the audio relay uses
    # bbs-input. Preserve an exact alias for the shared artifact checker.
    shutil.copy2(out/'bbs-sent.bin',out/'bbs-input.bin')
    assert sha(out/'bbs-input.bin')==sha(out/'bbs-sent.bin')
    boundary=json.loads((out/'server-log-start.json').read_text())
    with Path(boundary['path']).open('rb') as f:
        f.seek(boundary['byte_offset']);rows=[json.loads(line) for line in f if line.strip()]
    sessions={r['sessionId'] for r in rows if r.get('menuName')=='telnetConnected'}
    own=[r for r in rows if r.get('sessionId') in sessions]
    (out/'server-session.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in own))
    checks,recording=audio_recording.check(out,own)
    read=lambda name:(out/name).read_bytes() if (out/name).is_file() else b''
    checks.update(harness_normal_exit=code==0 and run['passed'],single_session=len(sessions)==1,
        timer_restored=len(read('KEYOLD.BIN'))==4 and read('KEYOLD.BIN')==read('KEYNEW.BIN'),
        unchanged_helper=sha(stage/'EXITKEY.COM')==helper_sha,
        inputs_unchanged=all(sha(ROOT/name)==digest for name,digest in frozen.items()))
    result=dict(passed=all(checks.values()),checks=checks,recording=recording,inputs=frozen,
        binary_sha256=run['binary_sha256'],helper_sha256=helper_sha,
        captures_sha256={str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file() and not p.is_relative_to(out/'frozen-source')},
        scope=__doc__+' Real local Telnet BBS and emulated UART; source-built DOS programs and actual BIOS keys. No SIP/audio/physical acceptance.')
    (out/'recording-checks.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(passed=result['passed'],checks=checks)),flush=True)
    assert result['passed'],'Preserve and inspect failed actual DOS helper/control run'


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--label',required=True);p.add_argument('--keys',type=Path,required=True)
    asyncio.run(main(p.parse_args()))
