#!/usr/bin/env python3
"""Stage a matching source-built connection-test package; never access a card."""
import argparse,hashlib,json,shutil,subprocess
from pathlib import Path
from package_special_edition import ROOT,dos_text,launch

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def stage(output,products,source_base_commit=None):
    assert output.is_relative_to(ROOT/'build') and not output.exists()
    sources={};identities={};manifests={}
    for leaf,binary in products.items():
        binary=binary.resolve();assert binary.is_relative_to(ROOT/'build') and binary.name==leaf
        path=binary.parent/'manifest.json';m=json.loads(path.read_text())
        assert not m.get('original_inputs') and sha(binary)==m['binary_sha256']
        for n,h in m['sources'].items():
            p=Path(n);assert not p.is_absolute() and '..' not in p.parts and p.parts[0] not in ('build','analysis','original','originals','install')
            assert sha(ROOT/p)==h and sources.get(n,h)==h,n;sources[n]=h
        if leaf in ('TERMINAL.EXE','ASPECT.EXE','PRMEDIT.EXE'):assert m.get('experimental_custom_irq')
        manifests[leaf]=m;identities[leaf]={'folder':str(binary.parent.relative_to(ROOT/'build')),'manifest_sha256':sha(path),'binary_sha256':sha(binary)}
    terminal=manifests['TERMINAL.EXE']
    assert terminal.get('special_edition') and terminal.get('experimental_original_reference') and terminal.get('experimental_phone_log_controls') and terminal.get('experimental_status_geometry')
    assert terminal['memory_layout']['initial_terminal_rows']==24
    assert manifests['ASPECT.EXE'].get('experimental_register_handoff') and manifests['ASPECT.EXE'].get('experimental_help_resource')
    help_base=products['ASPECT.EXE'].resolve().parent;help_record=json.loads((help_base/'help-resource.json').read_text())
    assert sha(help_base/'LOCHELP.HLP')==help_record['sha256']
    for n,h in help_record['sources'].items():
        p=Path(n);assert not p.is_absolute() and '..' not in p.parts and p.parts[0] not in ('build','analysis')
        assert sha(ROOT/p)==h and sources.get(n,h)==h;sources[n]=h
    output.mkdir();payload=output/'PCPLUSSE';payload.mkdir()
    for leaf,binary in products.items():shutil.copyfile(binary,payload/leaf)
    shutil.copyfile(help_base/'LOCHELP.HLP',payload/'LOCHELP.HLP')
    (payload/'START.BAT').write_bytes(launch());(payload/'SETUP.BAT').write_bytes(launch(True))
    revision=source_base_commit or subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    assert len(revision)==40 and all(c in '0123456789abcdef' for c in revision)
    (payload/'VERSION.TXT').write_bytes(dos_text('LoC SPECIAL EDITION / CONNECTION TEST\nSysop: bstar\nSource base: '+revision+'\nTERMINAL SHA256: '+sha(products['TERMINAL.EXE'])+'\n'))
    (payload/'README.TXT').write_bytes(dos_text(
        'PROCOMM PLUS / LoC SPECIAL EDITION - CONNECTION TEST\n\n'
        'Keep your existing PCPLUS.PRM, PCPLUS.DIR, PCPLUS.XLT and key files.\n'
        'Preserve PCPLUS.FON call history, KEY/KBD and your custom files too.\n'
        'This package contains no private configuration or dialing directory.\n'
        'Back up an existing C:\\PCPLUSSE before replacing application files.\n'
        'Before START, place a copy of your known working PCPLUS.PRM here.\n'
        'Preserve the Boca settings: COM3,3E8h,IRQ5 as previously established.\n'
        'Keep the initialization/flow settings that worked on this modem.\n'
        'AT+MS in the Linux bridge config is not a Boca initialization command.\n\n'
        'Connection test from the DOS prompt:\n'
        '  C:\n  CD \\PCPLUSSE\n  START /D:555 /I:3\n'
        '/I:3 waits for initialization ACKs with a selectable3-second bound.\n'
        '555 is the local telephone destination routed by the SPA2102.\n'
        'After carrier, wait for CONNECT>, then type LOC or1 and Enter.\n'
        'LoSs oF CoNtRoL is selected after carrier; do not dial its hostname.\n'
        'The bridge and status-enabled terminal must agree on80x24.\n\n'
        'Alt-Z: original command reference. L: call log status/retry.\n'
        'Alt-L: printer. Alt-R: record. Alt-S/Alt-P: setup. Alt-X: exit.\n'
        'Use Alt-Z then PgUp/PgDn for send/receive without changing BBS bindings.\n'
        'Backtick opens the browser; Connection/Redial repeats the target.\n'
        + ('Alt-T: serviced elapsed-time window; any dismissal key stays local.\n' if terminal.get('experimental_elapsed_view') else '')
        + ('Alt-J: send configured initialization only; Escape cancels.\n' if terminal.get('experimental_manual_init') else '')
        + 'Dim commands remain unavailable. This is a test candidate.\n\n'
        'Check login/input, ANSI/CP437, editor navigation and reconnect first.\n'
        'Then use owned small files to verify transfers in both directions.\n\n'
        'For source scripts, compile at the DOS prompt before starting PCPlus:\n'
        '  ASPCOMP SCRIPT.ASP\n'
        'Then select SCRIPT.ASX with Alt-F5. Automatic ASP compilation while\n'
        'the terminal and interpreter are resident can run out of conventional\n'
        'RAM in this candidate. The standalone compiler remains included.\n'
        'Physical modem/SIP/audio and complete original feature acceptance\n'
        'remain unverified. Building/staging does not update a card.\n'))
    for n in ('standalone/package_connection_test.py','standalone/package_special_edition.py','standalone/build_guarded_helper.py'):sources[n]=sha(ROOT/n)
    record={'kind':'source-built-special-edition-package','source_base_commit':revision,'products':identities,'sources':sources,
        'files':{p.name:sha(p) for p in sorted(payload.iterdir())},'original_inputs':[],
        'experimental_custom_irq':True,'experimental_original_keys':True,'experimental_original_reference':True,
        'experimental_local_controls':bool(terminal.get('experimental_local_controls')),
        'experimental_keyboard_bank':bool(terminal.get('experimental_keyboard_bank')),
        'experimental_screen_pause':bool(terminal.get('experimental_screen_pause')),
        'experimental_call_timer':bool(terminal.get('experimental_call_timer')),
        'experimental_elapsed_view':bool(terminal.get('experimental_elapsed_view')),
        'experimental_manual_init':bool(terminal.get('experimental_manual_init')),
        'experimental_directory_resource_owner':False,'experimental_phone_log_controls':True,'experimental_status_geometry':True,
        'authored_help_sha256':help_record['sha256'],'card_written':False,'validation':'Staged only; requires separate DOS/package and hardware acceptance.'}
    (output/'manifest.json').write_text(json.dumps(record,indent=2)+'\n');return record

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--source-base-commit',help='Explicit source identity for isolated reproduction without Git metadata')
    for name in ('terminal','runner','compiler','setup','translation'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();products=dict(zip(('TERMINAL.EXE','ASPECT.EXE','ASPCOMP.EXE','PRMEDIT.EXE','XLTEDIT.EXE'),(a.terminal,a.runner,a.compiler,a.setup,a.translation)))
    r=stage(a.output.resolve(),products,a.source_base_commit);print('Staged',len(r['files']),'files; sources and shared inputs agree; no card/configuration writes.')
if __name__=='__main__':main()
