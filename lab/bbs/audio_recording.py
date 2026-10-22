"""Normal Record/ASP compiler/replay audio fixture and actual-artifact checks."""
import json,re,shutil,struct
from synthmodem_vm_control import ROOT,sha
from modem import Telnet

PAYLOAD=b'S\r\x1b'
ONLINE_TAIL=PAYLOAD*2+b'S\r'
# Separate the local marker from the BBS footer's late fixed-row repaint.
# MESSAGE itself appends the final CRLF; helper dwell/keys stay unchanged.
READY_MESSAGE='message "^M^JRECORDER READY^M^J^M^J"\n'


def inputs(proof):
    proof=proof.resolve();assert proof.is_relative_to(ROOT/'build')
    r=json.loads(proof.read_text())
    assert not r.get('diagnostic_marker_trace',False),'Diagnostic marker counters do not admit the ordinary helper'
    assert r['passed'] and len(r['cases'])==7 and all(c['passed'] and all(c['checks'].values()) for c in r['cases'])
    assert {c['name'] for c in r['cases']}=={'complete','missing-search-blocks','stale-pre-replay-file-screen-blocks','file-screen-without-ready-watchdog','final-form-watchdog','BIOS-queue-full-retry','final-screen-activity-restarts-dwell'}
    assert all(sha(ROOT/name)==digest for name,digest in r['inputs'].items())
    names=['lab/bbs/audio_recording.py','lab/bbs/audio_recording_keys.asm','lab/bbs/check_audio_recording_keys.py',str(proof.relative_to(ROOT))]
    for directory,binary in (('aspect-runner','ASPECT.EXE'),('aspect-compiler-dos','ASPCOMP.EXE')):
        base=ROOT/'build'/directory;m=json.loads((base/'manifest.json').read_text())
        assert not m['original_inputs'] and sha(base/binary)==m['binary_sha256']
        assert not m.get('diagnostic_build',False)
        assert all(not name.startswith(('analysis/','build/')) and sha(ROOT/name)==digest for name,digest in m['sources'].items())
        names += [str((base/binary).relative_to(ROOT)),str((base/'manifest.json').relative_to(ROOT)),*m['sources']]
    return names,r['production_helper_sha256']


def prepare(stage):
    assert not (stage/'PCPLUS.ASP').exists() and not (stage/'PCPLUS.ASX').exists()
    shutil.copy2(ROOT/'build/aspect-compiler-dos/ASPCOMP.EXE',stage/'ASPCOMP.EXE')


def check(out,rows):
    from compiler import compile_source
    stage=out/'program';source=stage/'PCPLUS.ASP';compiled=stage/'PCPLUS.ASX'
    script=source.read_bytes() if source.is_file() else b''
    payload=b''.join(bytes.fromhex(s.decode()) for s in re.findall(rb'^transmitraw "([0-9A-F]*)"\r?$',script,re.M))
    report=(out/'RECKEY.BIN').read_bytes() if (out/'RECKEY.BIN').is_file() else b''
    words=struct.unpack('<8H',report) if len(report)==16 else ()
    menus=[r['menuName'] for r in rows if r.get('menuName')]
    first=menus.index('fileBaseMainMenu') if 'fileBaseMainMenu' in menus else len(menus)
    expected=['fileBaseMainMenu','fileBaseSearch','fileBaseMainMenu','fileBaseSearch','fileBaseMainMenu','fileBaseSearch']
    sent,_=Telnet().feed((out/'bbs-input.bin').read_bytes())
    user=re.sub(rb'\x1b\[(?:\?[0-9;]*c|[0-9]+;[0-9]+R)',b'',sent)
    screen=(out/'SCREEN.BIN').read_bytes() if (out/'SCREEN.BIN').is_file() else b''
    text=screen[::2].decode('cp437') if len(screen)==4000 else ''
    checks=dict(recorded_source_complete=script.endswith(b'endproc\r\n'),
        exact_recorded_user_bytes=payload==PAYLOAD,
        DOS_compiled_exact_source=bool(script) and compiled.is_file() and compiled.read_bytes()==compile_source(script.decode('cp437')),
        no_recovery_or_compile_temporary_files=not list(stage.glob('LPR*.TMP')) and not list(stage.glob('LPR*.BAK')) and not list(stage.glob('LPC*.LOG')),
        helper_completed_recipe=bool(words) and words[0]==0x524b and words[1:4]==(14,26,1),
        exact_record_replay_and_manual_route=menus[first:]==expected,
        exact_online_navigation_tail=user.endswith(ONLINE_TAIL),
        final_manual_search_visible='ESC : cancel' in text and 'FILE SEARCH' in text)
    return checks,dict(recorded_payload_hex=payload.hex(),expected_payload_hex=PAYLOAD.hex(),
        source_sha256=sha(source) if source.is_file() else None,bytecode_sha256=sha(compiled) if compiled.is_file() else None,
        helper_report=words,menus_after_file_base=menus[first:],expected_online_tail_hex=ONLINE_TAIL.hex(),
        scope='Selected same-call File/C recording, File/A explicit ASP compilation/replay and manual Search afterward. BIOS keys only. Full stream/audio/SIP/cleanup audits remain mandatory.')
