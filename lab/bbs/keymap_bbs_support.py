"""Owned Alt-F8 fixture and passive complete editor-frame return audit."""
import json
from pathlib import Path
import shutil
import struct
import subprocess
import sys
from product_inputs import ROOT, sha, stage_companions

SOURCES = ['lab/bbs/keymap_bbs_support.py', 'standalone/file_directory_bbs_watch.asm',
           'standalone/build_keyboard_profiles.py', 'src/terminal/key_configuration.asm','standalone/dos_status_runner.asm']
KEYS = 'a-f8 p4000 f1 p200 tab Z Z Z enter p300 a-s p2000 escape p2000 '
def key_sequence(help_roundtrip=False):
    return KEYS.replace('enter p300 ','enter p300 a-z p1200 escape ') if help_roundtrip else KEYS


def prepare(folder, binary, helper, profiles=33,help_roundtrip=False):
    assert profiles in (7,33)
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=False)
    assert json.loads(binary.with_name('manifest.json').read_text())['experimental_keymap_editor']
    helper = helper.resolve()
    assert helper.is_relative_to(ROOT / 'build') and helper.name == 'PCKEYMAP.EXE'
    proof = json.loads(helper.with_name('result.json').read_text())
    assert proof['passed'] and sha(helper) == proof['binary_sha256']
    for name, digest in proof['sources'].items():
        assert sha(ROOT / name) == digest, name
    stage = folder / 'program'
    stage.mkdir()
    shutil.copyfile(binary, stage / 'TERMINAL.EXE')
    stage_companions(binary, stage)
    shutil.copyfile(helper, stage / 'PCKEYMAP.EXE')
    (folder / 'inputs.json').write_text(json.dumps(dict(helper_sha256=sha(helper), sources=proof['sources'],profiles=profiles,help_roundtrip=help_roundtrip), indent=2)+'\n')
    sys.path.insert(0, str(ROOT / 'standalone'))
    from build_keyboard_profiles import profiles as network_profiles
    base = network_profiles()['NETWORK.KBD'][:948] * profiles
    expected = bytearray(base)
    expected[6*948+16*12:6*948+17*12] = b'ZZZ'.ljust(12, b'\0')
    (folder / 'BOARD.KBD').write_bytes(base)
    (folder / 'EXPECT.KBD').write_bytes(expected)
    observer = folder / 'KMWATCH.COM'
    subprocess.run(['nasm', '-fbin', '-DKEYMAP_ROUNDTRIP',*(['-DKEYMAP_HELP_ROUNDTRIP'] if help_roundtrip else []),str(ROOT / SOURCES[1]), '-o', str(observer)], check=True)
    return stage / 'TERMINAL.EXE', observer


def audit(output, folder, binary, require_high=False):
    output, folder = Path(output), Path(folder)
    raw = (output / 'KMVIEW.BIN').read_bytes()
    fixture=json.loads((folder/'inputs.json').read_text());help_roundtrip=fixture.get('help_roundtrip',False)
    words = struct.unpack_from('<12H', raw) if len(raw) == 12024+2*help_roundtrip else None
    dialog = raw[8024:12024]
    status = struct.unpack('<3H',(output/'EXITCODE.BIN').read_bytes())
    wire = (output / 'serial-received.bin').read_bytes()
    checks = dict(preserved_KBD_length=(output/'BOARD.KBD').stat().st_size==fixture['profiles']*948,application_exit_zero=status==(0,0,0),
                  no_save_residue=not any((output/n).exists() for n in ('KBDSTG.$$$','KBDBAK.$$$')),
                  observer_complete=words is not None and words[:4] == (0x5657, 1, 1, 1),
                  exact_editor_frame=words is not None and raw[24:4024] == raw[4024:8024],
                  cursor_shape=words is not None and words[6] == words[7] and words[8] == words[9],
                  mode_rows=words is not None and words[4:6] == (25,25) and words[10:12] == (0x5003,0x5003),
                  actual_mapper=b'KEYBOARD MAPPING' in dialog[::2],
                  actual_F1_notation=dialog[224:230:2] == b'ZZZ',
                  only_intended_KBD_edit=(output / 'BOARD.KBD').read_bytes() == (folder / 'EXPECT.KBD').read_bytes(),
                  local_edit_never_sent=b'ZZZ' not in wire,
                  subsequent_editor_keys=b'ABCDE' in wire and b'UNSAVED' in wire,
                  helper_unchanged=sha(binary.with_name('PCKEYMAP.EXE')) == json.loads((folder / 'inputs.json').read_text())['helper_sha256'])
    if require_high:
        for leaf in ('KMSEG.BIN','KEYSEG.BIN'):
            data=(output/leaf).read_bytes()
            checks[leaf+'_in_UMB']=len(data)==2 and struct.unpack('<H',data)[0]>=0xa000
    if help_roundtrip:checks['actual_context17_Help']=len(raw)==12026 and raw[12024:]==b'\x01\0'
    result = dict(passed=all(checks.values()), checks=checks, observer_words=words, application_exit_status=status,
                  profiles=fixture['profiles'],file_bytes=fixture['profiles']*948,help_roundtrip=help_roundtrip,parent_sha256=sha(binary), helper_sha256=sha(binary.with_name('PCKEYMAP.EXE')),
                  capture_sha256=sha(output / 'KMVIEW.BIN'), sources={n:sha(ROOT/n) for n in SOURCES},
                  scope='Actual Alt-F8/helper edit/save/Escape inside stock BBS editor; exact whole KBD mutation and passive 4000-byte frame/cursor/shape return, ordinary editor input resumes. No physical modem/SIP/audio acceptance.')
    (output / 'keymap-audit.json').write_text(json.dumps(result, indent=2) + '\n')
    return result
