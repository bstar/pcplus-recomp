#!/usr/bin/env python3
"""Stage a matching source-built connection-test package; never access a card."""
import argparse,hashlib,json,re,shutil,subprocess,struct
from pathlib import Path
from package_special_edition import ROOT,dos_text,launch

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def validate_dos_directory(value):
    reserved={'CON','PRN','AUX','NUL'}|{prefix+str(n) for prefix in ('COM','LPT') for n in range(1,10)}
    if not value.isascii() or not re.fullmatch('[A-Za-z0-9_]{1,8}',value) or value.upper() in reserved:
        raise ValueError('DOS directory must be a non-device root directory name of1..8 ASCII letters, digits or underscores')
    return value.upper()

def render_capability(binary):
    """Read the actual published WORD inside the source-built prepare routine."""
    symbols={n:(int(s,16),int(o,16)) for s,o,n in re.findall(r'^\s*([0-9a-f]{4}):([0-9a-f]{4,8})[*+]?\s+(\w+)\s*$',binary.with_name('terminal.map').read_text(),re.M|re.I)}
    start=symbols['terminal_render_prepare'];end=symbols['terminal_render_revoke'];version=symbols['_script_render_version']
    assert start[0]==end[0] and start[1]<end[1] and version[1]<=65535
    data=binary.read_bytes();assert data[:2]==b'MZ';base=struct.unpack_from('<H',data,8)[0]*16
    code=data[base+start[0]*16+start[1]:base+end[0]*16+end[1]]
    signature=b'\xc7\x06'+struct.pack('<H',version[1]);assert code.count(signature)==1
    at=code.index(signature)+4;assert at+2<=len(code)
    return struct.unpack_from('<H',code,at)[0]

def validate_render_pair(capability,terminal,child):
    """Bind the published contract to both compiled product selections."""
    emulate=bool(child.get('experimental_emulate_VM'))
    assert (capability==20)==emulate,'Published parent capability and EMULATE interpreter must match'
    assert bool(terminal.get('experimental_aspect_emulate_policy'))==emulate,'EMULATE parent policy and interpreter must match'
    assert (capability in (19,20))==bool(child.get('experimental_alarm_VM')),'Published parent capability and ALARM interpreter must match'
    if emulate:
        assert terminal.get('experimental_aspect_snapshot_lease') and child.get('experimental_snapshot_lease'),'EMULATE requires matching snapshot leases'

def packed_guide(directory):
    return dos_text(
        'PROCOMM PLUS / LoC SPECIAL EDITION - CONNECTION TEST\n\n'
        'Application files only. Keep your working PCPLUS.PRM, PCPLUS.DIR,\n'
        'PCPLUS.KEY, PCPLUS.KBD, PCPLUS.XLT and PCPLUS.FON call history.\n'
        'Back up the existing installation before replacing application files.\n'
        'No private settings, dialing directory or machine recipes are included.\n\n'
        'From DOS:\n  C:\n  CD \\'+directory+'\n  START\n'
        'Keep the verified serial port, IRQ, baud and modem initialization.\n'
        'START /D:NUMBER /I:3 dials a configured telephone destination.\n'
        'Enter the BBS address or configured bridge alias after carrier connects.\n'
        'A physical modem dials telephone numbers; bridge routing is separate.\n\n'
        'Alt-Z: command reference. Backtick: command browser. Alt-X: exit.\n'
        'Alt-S/Alt-P: setup. Alt-T: elapsed time. Alt-L: printer.\n'
        'Alt-F: file directory. Alt-F7: directory change. Alt-V: file viewer.\n'
        'Alt-A: run the separately configured external editor. The external\n'
        'editor program itself is not bundled. Escape cancels its parameters.\n'
        'Alt-F4: DOS Gateway; EXIT returns. Alt-F5: choose an ASPECT script.\n'
        'Use Alt-Z then PgUp/PgDn for transfers without changing BBS key binds.\n'
        'Compile source scripts with ASPCOMP SCRIPT.ASP before starting PCPlus.\n'
        'Automatic resident compilation and nested PROGRAM remain separate gates.\n\n'
        'This build packs command-browser text without removing help or commands.\n'
        'The existing ASPECT stack, heap-growth policy and six file slots remain.\n'
        'Check login, ANSI/CP437, editor navigation, reconnect and owned-file\n'
        'transfers on the intended hardware. Full original parity and physical\n'
        'modem/SIP/audio acceptance remain open. This is a test candidate.\n')

def terminal_companions(binary,manifest):
    """Return source-verified optional runtime files required by this parent."""
    files={};sources={};base=binary.resolve().parent
    overlay=manifest.get('line_port_overlay')
    assert bool(overlay)==bool(manifest.get('experimental_line_port_overlay')),'Alt-P module declaration and feature must match'
    if overlay:
        assert manifest.get('experimental_line_port') and manifest['memory_layout']['line_port_overlay_contract_verified']
        assert sha(base/'PCLINE.OVL')==overlay['sha256'],'Alt-P module differs from the matched parent'
        files['PCLINE.OVL']=base/'PCLINE.OVL'
    meta=manifest.get('meta_editor_overlay')
    assert bool(meta)==bool(manifest.get('experimental_meta_editor_module')),'Meta module declaration and feature must match'
    assert not manifest.get('experimental_meta_editor') or meta,'Meta frontend requires its module'
    if manifest.get('experimental_meta_shared_runtime'):
        assert meta and overlay and manifest.get('experimental_meta_editor'),'Shared runtime requires both matched modules and the Meta frontend'
    if meta:
        from terminal_memory import inspect_terminal_memory
        layout=inspect_terminal_memory(binary,base/'terminal.map')
        assert layout==manifest['memory_layout'],'Meta parent layout differs from its verified manifest'
        assert not meta.get('original_inputs')
        assert layout['meta_loader_retained'] and layout['meta_overlay_DGROUP_bytes']==0
        assert layout['meta_overlay_bytes']==meta['bank_bytes'] and layout['meta_overlay_fixups']==meta['relocations']
        assert layout['meta_editor_UI_bound']==bool(manifest.get('experimental_meta_editor'))
        assert layout['meta_shared_runtime']==bool(manifest.get('experimental_meta_shared_runtime'))
        assert sha(base/'PCMETA.OVL')==meta['sha256'],'Meta module differs from the matched parent'
        files['PCMETA.OVL']=base/'PCMETA.OVL'
    if manifest.get('experimental_chat_loader'):
        module=manifest['chat_loader']['module']
        assert sha(base/'PCCHAT.OVL')==module['binary_sha256']
        files['PCCHAT.OVL']=base/'PCCHAT.OVL'
    if manifest.get('experimental_global_help'):
        bundle=json.loads((base/'package.json').read_text())
        assert bundle['passed'] and bundle['products']['TERMINAL.EXE']==sha(binary)
        for n in ('PCHELP.RTE','PCPLUS.HLP'):
            assert sha(base/n)==bundle['products'][n];files[n]=base/n
        sources.update(bundle['sources'])
    for n,h in sources.items():
        p=Path(n);assert not p.is_absolute() and '..' not in p.parts and p.parts[0] not in ('build','analysis','original','originals','install')
        assert sha(ROOT/p)==h,n
    return files,sources

def reviewed_keymap_profile(profile=None):
    if profile is None:
        profile=json.loads((ROOT/'standalone/keymap_helper_profile.json').read_text())
    assert profile['kind']=='reviewed-source-keymap-helper'
    assert profile['parent_feature']=='experimental_keymap_editor'
    assert profile['arguments']=='profile frozen-absolute-KBD-path [/LEGACY]' and profile['recovery_exit']==14
    assert profile['contract'] in (1,2,3)
    if profile['contract']==1:assert profile['KBD_bytes']==31284
    else:
        assert profile['profile_bytes']==948 and profile['minimum_profiles']==1 and profile['maximum_profiles']==33
        assert profile['maximum_KBD_bytes']==31284 and profile['preserves_file_length'] is True
        if profile['contract']==3:
            assert profile['new_file_profiles']==33 and profile['new_file_creation']=='explicit-save'
            assert profile['missing_leaf_only'] is True
    return profile

def keymap_companion(terminal,helper):
    """Require the reviewed source helper whenever the parent exposes Alt-F8."""
    enabled=bool(terminal.get('experimental_keymap_editor'))
    assert enabled==bool(helper),'Alt-F8 parent and explicit keyboard helper must be selected together'
    if not enabled:return {},{},{}
    profile_path=ROOT/'standalone/keymap_helper_profile.json'
    profile=reviewed_keymap_profile()
    helper=Path(helper).resolve()
    assert helper.is_relative_to(ROOT/'build') and helper.name=='PCKEYMAP.EXE'
    proof_path=helper.with_name('result.json');proof=json.loads(proof_path.read_text())
    assert proof['passed'] and proof['original_inputs']==[]
    assert sha(helper)==proof['binary_sha256']==profile['helper_sha256'],'Unreviewed keyboard helper or mismatched bytes'
    sources=dict(proof['sources']);sources[str(profile_path.relative_to(ROOT))]=sha(profile_path)
    for name,digest in sources.items():
        path=Path(name)
        assert not path.is_absolute() and '..' not in path.parts
        assert path.parts[0] in ('src','standalone','reconstruction')
        assert path.suffix.lower() in ('.c','.h','.py','.asm','.inc','.json')
        assert sha(ROOT/path)==digest,name
    identity=dict(folder=str(helper.parent.relative_to(ROOT/'build')),manifest_sha256=sha(proof_path),binary_sha256=sha(helper),contract=profile['contract'])
    return {'PCKEYMAP.EXE':helper},sources,identity

def stage(output,products,source_base_commit=None,dos_directory='PCPLUSSE',keymap_helper=None):
    dos_directory=validate_dos_directory(dos_directory)
    assert output.is_relative_to(ROOT/'build') and not output.exists()
    sources={};identities={};manifests={}
    for leaf,binary in products.items():
        binary=binary.resolve();assert binary.is_relative_to(ROOT/'build') and binary.name==leaf
        path=binary.parent/'manifest.json';m=json.loads(path.read_text())
        assert not m.get('diagnostic_build'),'Diagnostic executable is not an application payload'
        assert not (m.get('diagnostic_status_probe') or m.get('diagnostic_display_row_probe') or m.get('diagnostic_session_rows_probe')),'Startup diagnostic is not an application payload'
        assert not m.get('original_inputs') and sha(binary)==m['binary_sha256']
        for n,h in m['sources'].items():
            p=Path(n);assert not p.is_absolute() and '..' not in p.parts and p.parts[0] not in ('build','analysis','original','originals','install')
            assert sha(ROOT/p)==h and sources.get(n,h)==h,n;sources[n]=h
        if leaf in ('TERMINAL.EXE','ASPECT.EXE','PRMEDIT.EXE'):assert m.get('experimental_custom_irq')
        manifests[leaf]=m;identities[leaf]={'folder':str(binary.parent.relative_to(ROOT/'build')),'manifest_sha256':sha(path),'binary_sha256':sha(binary)}
    terminal=manifests['TERMINAL.EXE']
    keymap_files,keymap_sources,keymap_identity=keymap_companion(terminal,keymap_helper)
    for n,h in keymap_sources.items():assert sources.get(n,h)==h;sources[n]=h
    if keymap_identity:identities['PCKEYMAP.EXE']=keymap_identity
    capability=render_capability(products['TERMINAL.EXE'].resolve())
    validate_render_pair(capability,terminal,manifests['ASPECT.EXE'])
    companions,companion_sources=terminal_companions(products['TERMINAL.EXE'],terminal)
    for n,h in companion_sources.items():assert sources.get(n,h)==h;sources[n]=h
    assert terminal.get('special_edition') and terminal.get('experimental_original_reference') and terminal.get('experimental_phone_log_controls') and terminal.get('experimental_status_geometry')
    assert terminal['memory_layout']['initial_terminal_rows']==24
    assert manifests['ASPECT.EXE'].get('experimental_register_handoff') and manifests['ASPECT.EXE'].get('experimental_help_resource')
    assert bool(terminal.get('experimental_aspect_snapshot_lease'))==bool(manifests['ASPECT.EXE'].get('experimental_snapshot_lease')),'Parent and ASPECT snapshot lease must match'
    help_base=products['ASPECT.EXE'].resolve().parent;help_record=json.loads((help_base/'help-resource.json').read_text())
    assert sha(help_base/'LOCHELP.HLP')==help_record['sha256']
    for n,h in help_record['sources'].items():
        p=Path(n);assert not p.is_absolute() and '..' not in p.parts and p.parts[0] not in ('build','analysis')
        assert sha(ROOT/p)==h and sources.get(n,h)==h;sources[n]=h
    output.mkdir();payload=output/dos_directory;payload.mkdir()
    for leaf,binary in products.items():shutil.copyfile(binary,payload/leaf)
    for leaf,binary in companions.items():shutil.copyfile(binary,payload/leaf)
    for leaf,binary in keymap_files.items():shutil.copyfile(binary,payload/leaf)
    shutil.copyfile(help_base/'LOCHELP.HLP',payload/'LOCHELP.HLP')
    for name,setup in [('START.BAT',False),('SETUP.BAT',True)]:
        data=launch(setup);assert data.count(b'PCPLUSSE')==2
        (payload/name).write_bytes(data.replace(b'PCPLUSSE',dos_directory.encode('ascii')))
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
        + ('Alt-Y: send configured answer-on; follows local echo. Escape cancels.\n' if terminal.get('experimental_auto_answer') else '')
        + ('Alt-F7: change directory; startup directory returns on final exit.\n' if terminal.get('experimental_path_control') else '')
        + ('Alt-F: File Directory; Enter selects *.*, Escape returns.\n' if terminal.get('experimental_file_directory') else '')
        + ('Alt-V: read-only file viewer; Escape returns to the live terminal.\n' if terminal.get('experimental_file_viewer') else '')
        + ('A saved external viewer command instead opens Enter parameters.\n'
           'Enter runs that command; Escape cancels. Browser redial is separate.\n' if terminal.get('experimental_external_viewer') else '')
        + ('Alt-F4: DOS Gateway; EXIT returns without a return-key prompt.\n'
           'Gateway keeps serial reception, capture/HOLD and printer owners.\n' if terminal.get('experimental_gateway_frontend') else '')
        + 'Dim commands remain unavailable. This is a test candidate.\n\n'
        'Check login/input, ANSI/CP437, editor navigation and reconnect first.\n'
        'Then use owned small files to verify transfers in both directions.\n\n'
        'For source scripts, compile at the DOS prompt before starting PCPlus:\n'
        '  ASPCOMP SCRIPT.ASP\n'
        'Then select SCRIPT.ASX with Alt-F5. Automatic ASP compilation while\n'
        'the terminal and interpreter are resident can run out of conventional\n'
        'RAM in this candidate. The standalone compiler remains included.\n'
        'Physical modem/SIP/audio and complete original feature acceptance\n'
        'remain unverified. Building/staging does not update a card.\n').replace(b'PCPLUSSE',dos_directory.encode('ascii')))
    if terminal.get('experimental_packed_command_ui'):
        (payload/'README.TXT').write_bytes(packed_guide(dos_directory))
    if terminal.get('experimental_global_help'):
        with (payload/'README.TXT').open('ab') as guide:
            guide.write(dos_text('\nContextual Help: press Alt-Z twice from the terminal.\n'
                'Keep PCHELP.RTE and the authored PCPLUS.HLP beside TERMINAL.EXE.\n'))
    if terminal.get('experimental_chat_loader'):
        with (payload/'README.TXT').open('ab') as guide:
            guide.write(dos_text('\nAlt-O: Chat; Alt-F6: Redisplay. Keep PCCHAT.OVL beside TERMINAL.EXE.\n'
                +('Alt-Z in Chat opens Help and retains unfinished input.\n' if terminal.get('experimental_chat_help') else '')))
    if manifests['ASPECT.EXE'].get('experimental_alarm_VM'):
        with (payload/'README.TXT').open('ab') as guide:
            guide.write(dos_text('\nASPECT scripts: DATE, TIME and ALARM are available.\n'
                'ALARM accepts an optional duration from0 through32767.\n'
                'Omitting it uses the saved duration; sound follows saved settings.\n'
                'An explicit duration is temporary. Press a key to end the alert.\n'
                'The complete original ASPECT language remains under reconstruction.\n'))
    if manifests['ASPECT.EXE'].get('experimental_emulate_VM'):
        with (payload/'README.TXT').open('ab') as guide:
            guide.write(dos_text('\nASPECT EMULATE: ANSI and VT220 are available.\n'
                'A successful switch resets the display, modes and keyboard map.\n'
                'Other named profiles compile but return an unsupported error.\n'
                'An explicit keyboard file must remain available during scripts.\n'
                'The parent and interpreter must be updated together.\n'))
    if terminal.get('experimental_line_port_overlay'):
        with (payload/'README.TXT').open('ab') as guide:
            guide.write(dos_text('\nAlt-P: native Line/Port setup. Escape applies session changes;\n'
                'Alt-S saves the line prefix and applies it. COM1 through COM4.\n'
                'Keep the matching PCLINE.OVL beside TERMINAL.EXE. Missing or\n'
                'mismatched modules are refused; do not mix package versions.\n'))
    if terminal.get('experimental_meta_editor'):
        with (payload/'README.TXT').open('ab') as guide:
            guide.write(dos_text('\nAlt-M: Meta Keys. Enter edits; Escape returns to the terminal.\n'
                'Keep the matching PCMETA.OVL beside TERMINAL.EXE. The shared\n'
                'command reference also needs this module. Update all package\n'
                'companions together; do not mix parent and module versions.\n'))
    for n in ('standalone/package_connection_test.py','standalone/package_special_edition.py','standalone/build_guarded_helper.py'):sources[n]=sha(ROOT/n)
    if keymap_files:
        with (payload/'README.TXT').open('ab') as guide:
            guide.write(dos_text('\nAlt-F8: source keyboard mapping helper beside TERMINAL.EXE.\n'
                +('The selected KBD must contain all33 profiles (31284 bytes).\n' if keymap_identity['contract']==1 else
                'KBD files may contain1 through33 complete948-byte profiles.\n'
                'The selected profile must exist. Save preserves the file length.\n')+
                'Do not overwrite private bindings or append invented defaults.\n'
                'Save updates the selected profile on return. Recovery exit14 stops PCPlus.\n'))
        if keymap_identity['contract']==3:
            with (payload/'README.TXT').open('ab') as guide:
                guide.write(dos_text('An absent KBD leaf opens a blank33-profile table in memory.\n'
                    'Alt-S or confirmed save creates it. Exit/discard creates nothing.\n'
                    'Other load errors do not become blank replacement files.\n'))
    record={'kind':'source-built-special-edition-package','source_base_commit':revision,'dos_directory':dos_directory,'products':identities,'sources':sources,
        'files':{p.name:sha(p) for p in sorted(payload.iterdir())},'original_inputs':[],
        'experimental_custom_irq':True,'experimental_original_keys':True,'experimental_original_reference':True,
        'experimental_local_controls':bool(terminal.get('experimental_local_controls')),
        'experimental_keyboard_bank':bool(terminal.get('experimental_keyboard_bank')),
        'experimental_screen_pause':bool(terminal.get('experimental_screen_pause')),
        'experimental_call_timer':bool(terminal.get('experimental_call_timer')),
        'experimental_elapsed_view':bool(terminal.get('experimental_elapsed_view')),
        'experimental_manual_init':bool(terminal.get('experimental_manual_init')),
        'experimental_auto_answer':bool(terminal.get('experimental_auto_answer')),
        'experimental_directory_resource_owner':bool(terminal.get('experimental_directory_resource_owner')),'experimental_phone_log_controls':True,'experimental_status_geometry':True,
        'authored_help_sha256':help_record['sha256'],'card_written':False,'validation':'Staged only; requires separate DOS/package and hardware acceptance.'}
    record.update(parent_render_capability=capability,experimental_alarm_VM=bool(manifests['ASPECT.EXE'].get('experimental_alarm_VM')))
    if manifests['ASPECT.EXE'].get('experimental_emulate_VM'):record['experimental_emulate_VM']=True
    if terminal.get('experimental_path_control') or terminal.get('experimental_gateway_frontend'):
        record.update(experimental_path_control=bool(terminal.get('experimental_path_control')),experimental_gateway_frontend=bool(terminal.get('experimental_gateway_frontend')))
    if terminal.get('experimental_file_directory'):
        record['experimental_file_directory']=True
    if terminal.get('experimental_file_viewer'):
        record['experimental_file_viewer']=True
    if terminal.get('experimental_external_viewer'):
        record['experimental_external_viewer']=True
    if terminal.get('experimental_external_editor'):record['experimental_external_editor']=True
    if keymap_files:record['experimental_keymap_editor']=True
    if terminal.get('experimental_packed_command_ui'):record['experimental_packed_command_ui']=True
    for flag in ('experimental_chat_loader','experimental_global_help','experimental_chat_help'):
        if terminal.get(flag):record[flag]=True
    if terminal.get('experimental_line_port_overlay'):record['experimental_line_port_overlay']=True
    for flag in ('experimental_meta_editor_module','experimental_meta_editor','experimental_meta_shared_runtime'):
        if terminal.get(flag):record[flag]=True
    (output/'manifest.json').write_text(json.dumps(record,indent=2)+'\n');return record

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--source-base-commit',help='Explicit source identity for isolated reproduction without Git metadata')
    p.add_argument('--dos-directory',default='PCPLUSSE',help='DOS8.3 root directory on drive C:; default PCPLUSSE')
    for name in ('terminal','runner','compiler','setup','translation'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--keymap-helper',type=Path,help='Explicit reviewed source PCKEYMAP companion, required by an Alt-F8 parent')
    a=p.parse_args();products=dict(zip(('TERMINAL.EXE','ASPECT.EXE','ASPCOMP.EXE','PRMEDIT.EXE','XLTEDIT.EXE'),(a.terminal,a.runner,a.compiler,a.setup,a.translation)))
    r=stage(a.output.resolve(),products,a.source_base_commit,a.dos_directory,a.keymap_helper);print('Staged',len(r['files']),'files for C:\\'+r['dos_directory']+'; sources and shared inputs agree; no card/configuration writes.')
if __name__=='__main__':main()
