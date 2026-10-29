#!/usr/bin/env python3
"""Stage the current branded DOS application; never access a removable card."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

from build_guarded_helper import FLAGS, LOOKUP, ROOT

SPECIAL = LOOKUP + '-special'
PRODUCTS = {
    'TERMINAL.EXE': SPECIAL,
    'ASPECT.EXE': 'aspect-register-parent',
    'ASPCOMP.EXE': 'aspect-compiler-dos',
    'PRMEDIT.EXE': 'setup-mouse-notice-sound',
    'XLTEDIT.EXE': 'xlt-editor',
}
COMMANDS = [
    [sys.executable, 'standalone/build_terminal.py', *FLAGS,
     '--hook-lookup', '--exit-guard', '--traps', '--special-edition'],
    [sys.executable, 'standalone/build_aspect_process.py', '--notice-bank',
     '--notice-sound', '--notice-input', '--notice-help', '--help-resource',
     '--serial-bank', '--register-handoff'],
    [sys.executable, 'standalone/build_aspect_compiler_dos.py'],
    [sys.executable, 'standalone/build_setup.py', '--mouse', '--notice-sound'],
    [sys.executable, 'standalone/build_xlt_editor.py'],
]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dos_text(text):
    return text.replace('\r\n', '\n').replace('\n', '\r\n').encode('ascii')


def launch(setup=False):
    return dos_text('@ECHO OFF\n'
        'SET LOC_PCPLUS=%PCPLUS%\n'
        'SET PCPLUS=C:\\PCPLUSSE\n'
        'C:\nCD \\PCPLUSSE\n'
        'TERMINAL ' + ('/S ' if setup else '') + '@PCPLUS.PRM %1 %2 %3 %4 %5 %6 %7 %8 %9\n'
        'SET PCPLUS=%LOC_PCPLUS%\nSET LOC_PCPLUS=\n')


def products_for(custom_irq=False,original_keys=False,original_reference=False,directory_view=False,directory_preview=False,directory_storage=False,directory_resource_cli=False,directory_resource_owner=False,directory_retirement=False,directory_translation=False,directory_scripts=False):
    if directory_scripts:directory_translation=True
    if directory_translation:directory_retirement=True
    if directory_retirement:directory_resource_owner=True
    if directory_resource_owner:directory_resource_cli=True
    if directory_resource_cli:directory_storage=True
    if directory_storage:directory_preview=True
    if directory_preview:directory_view=True
    if directory_view:original_reference=True
    if original_reference:original_keys=True
    products=dict(PRODUCTS)
    if custom_irq:
        products.update({'TERMINAL.EXE':LOOKUP+'-custom-irq-special',
                         'ASPECT.EXE':'aspect-register-parent-custom-irq',
                         'PRMEDIT.EXE':'setup-mouse-notice-sound-custom-irq'})
    if original_keys:
        products['TERMINAL.EXE']='terminal-original-keys-'+hashlib.sha256(products['TERMINAL.EXE'].encode('ascii')).hexdigest()[:12]
    if original_reference:
        products['TERMINAL.EXE']='terminal-reference-'+hashlib.sha256(products['TERMINAL.EXE'].encode('ascii')).hexdigest()[:12]
    if directory_view:
        products['TERMINAL.EXE']='terminal-directory-view-'+hashlib.sha256(products['TERMINAL.EXE'].encode('ascii')).hexdigest()[:12]
    if directory_preview:
        products['TERMINAL.EXE']='terminal-directory-preview-'+hashlib.sha256(products['TERMINAL.EXE'].encode('ascii')).hexdigest()[:12]
    if directory_storage:
        products['TERMINAL.EXE']='terminal-directory-storage-'+hashlib.sha256(products['TERMINAL.EXE'].encode('ascii')).hexdigest()[:12]
    if directory_resource_cli:
        products['TERMINAL.EXE']='terminal-resource-cli-'+hashlib.sha256(products['TERMINAL.EXE'].encode('ascii')).hexdigest()[:12]
    if directory_resource_owner:
        products['TERMINAL.EXE']='terminal-resource-owner-'+hashlib.sha256(products['TERMINAL.EXE'].encode('ascii')).hexdigest()[:12]
    if directory_retirement:
        products['TERMINAL.EXE']='terminal-directory-retirement-'+hashlib.sha256(products['TERMINAL.EXE'].encode('ascii')).hexdigest()[:12]
    if directory_translation:
        products['TERMINAL.EXE']='terminal-directory-translation-'+hashlib.sha256(products['TERMINAL.EXE'].encode('ascii')).hexdigest()[:12]
    if directory_scripts:
        products['TERMINAL.EXE']='terminal-directory-scripts-'+hashlib.sha256(products['TERMINAL.EXE'].encode('ascii')).hexdigest()[:12]
    return products


def commands_for(custom_irq=False,original_keys=False,original_reference=False,directory_view=False,directory_preview=False,directory_storage=False,directory_resource_cli=False,directory_resource_owner=False,directory_retirement=False,directory_translation=False,directory_scripts=False):
    return [command+(['--custom-irq']if custom_irq and index in (0,1,3)else[])+(['--original-keys']if original_keys and index==0 else[])+(['--original-reference']if original_reference and index==0 else[])+(['--directory-view']if directory_view and index==0 else[])+(['--directory-preview']if directory_preview and index==0 else[])+(['--directory-storage']if directory_storage and index==0 else[])+(['--directory-resource-cli']if directory_resource_cli and index==0 else[])+(['--directory-resource-owner']if directory_resource_owner and index==0 else[])+(['--directory-retirement']if directory_retirement and index==0 else[])+(['--directory-translation']if directory_translation and index==0 else[])+(['--directory-scripts']if directory_scripts and index==0 else[])
            for index,command in enumerate(COMMANDS)]


def stage(out,custom_irq=False,source_base_commit=None,original_keys=False,original_reference=False,directory_view=False,directory_preview=False,directory_storage=False,directory_resource_cli=False,directory_resource_owner=False,directory_retirement=False,directory_translation=False,directory_scripts=False):
    if directory_scripts:directory_translation=True
    if directory_translation:directory_retirement=True
    if directory_retirement:directory_resource_owner=True
    if directory_resource_owner:directory_resource_cli=True
    if directory_resource_cli:directory_storage=True
    if directory_storage:directory_preview=True
    if directory_preview:directory_view=True
    if directory_view:original_reference=True
    if original_reference:original_keys=True
    # Validate the complete input set before creating an output. Profiles,
    # directories and tables are never package inputs, even for local staging.
    sources = {}
    manifests = {}
    products=products_for(custom_irq,original_keys,original_reference,directory_view,directory_preview,directory_storage,directory_resource_cli,directory_resource_owner,directory_retirement,directory_translation,directory_scripts)
    for leaf, folder in products.items():
        base = ROOT / 'build' / folder
        manifest = json.loads((base / 'manifest.json').read_text())
        if manifest.get('original_inputs'):
            raise ValueError('original build input: ' + folder)
        if sha(base / leaf) != manifest['binary_sha256']:
            raise ValueError('changed binary: ' + folder)
        if leaf in ('TERMINAL.EXE','ASPECT.EXE','PRMEDIT.EXE')and bool(manifest.get('experimental_custom_irq'))!=custom_irq:
            raise ValueError('mismatched IRQ variant: '+folder)
        if leaf=='TERMINAL.EXE' and bool(manifest.get('experimental_original_keys'))!=original_keys:
            raise ValueError('mismatched keyboard variant: '+folder)
        if leaf=='TERMINAL.EXE' and bool(manifest.get('experimental_original_reference'))!=original_reference:
            raise ValueError('mismatched reference variant: '+folder)
        if leaf=='TERMINAL.EXE' and bool(manifest.get('experimental_directory_view'))!=directory_view:
            raise ValueError('mismatched directory-view variant: '+folder)
        if leaf=='TERMINAL.EXE' and bool(manifest.get('experimental_directory_preview'))!=directory_preview:
            raise ValueError('mismatched directory-preview variant: '+folder)
        if leaf=='TERMINAL.EXE' and bool(manifest.get('experimental_directory_storage'))!=directory_storage:
            raise ValueError('mismatched directory-storage variant: '+folder)
        if leaf=='TERMINAL.EXE' and bool(manifest.get('experimental_directory_resource_cli'))!=directory_resource_cli:
            raise ValueError('mismatched CLI-resource variant: '+folder)
        if leaf=='TERMINAL.EXE' and bool(manifest.get('experimental_directory_resource_owner'))!=directory_resource_owner:
            raise ValueError('mismatched resource-owner variant: '+folder)
        if leaf=='TERMINAL.EXE' and bool(manifest.get('experimental_directory_retirement'))!=directory_retirement:
            raise AssertionError('Directory retirement variant mismatch')
        if leaf=='TERMINAL.EXE' and bool(manifest.get('experimental_directory_translation'))!=directory_translation:
            raise ValueError('Translation resource variant mismatch')
        if leaf=='TERMINAL.EXE' and bool(manifest.get('experimental_directory_scripts'))!=directory_scripts:
            raise ValueError('Directory script resource variant mismatch')
        for name, digest in manifest['sources'].items():
            path = Path(name)
            if path.is_absolute() or '..' in path.parts or path.parts[0] in ('build', 'analysis'):
                raise ValueError('invalid source path: ' + name)
            if sha(ROOT / path) != digest or (name in sources and sources[name] != digest):
                raise ValueError('stale source: ' + name)
            sources[name] = digest
        manifests[leaf] = dict(folder=folder, manifest_sha256=sha(base / 'manifest.json'),
                               binary_sha256=manifest['binary_sha256'])
    help_base=ROOT/'build'/products['ASPECT.EXE']
    help_manifest=json.loads((help_base/'help-resource.json').read_text())
    if sha(help_base/'LOCHELP.HLP')!=help_manifest['sha256']:
        raise ValueError('changed authored help resource')
    for name,digest in help_manifest['sources'].items():
        path=Path(name)
        if path.is_absolute() or '..' in path.parts or path.parts[0] in ('build','analysis'):
            raise ValueError('invalid help source path: '+name)
        if sha(ROOT/path)!=digest or sources.get(name,digest)!=digest:
            raise ValueError('stale help source: '+name)
        sources[name]=digest
    out.mkdir(parents=True, exist_ok=False)
    payload = out / 'PCPLUSSE'
    payload.mkdir()
    for leaf, folder in products.items():
        shutil.copyfile(ROOT / 'build' / folder / leaf, payload / leaf)
    shutil.copyfile(help_base/'LOCHELP.HLP',payload/'LOCHELP.HLP')
    (payload / 'START.BAT').write_bytes(launch())
    (payload / 'SETUP.BAT').write_bytes(launch(setup=True))
    (payload / 'README.TXT').write_bytes(dos_text(
        'PROCOMM PLUS // LoC SPECIAL EDITION\n\n'
        'START.BAT starts the terminal with your PCPLUS.PRM.\n'
        'SETUP.BAT opens configuration. Alt-Z commands; Alt-X returns to shell.\n'
        'Keep your PCPLUS.PRM, PCPLUS.DIR, PCPLUS.XLT and other local files.\n'
        'The original C:\\PCPLUS installation is separate.\n\n'
        'Includes guarded helpers, filename lookup and the smaller DOS compiler.\n'
        'LOCHELP.HLP supplies the authored searchable helper help.\n'
        'This is an application milestone. Full original parity and physical\n'
        'modem acceptance remain unfinished.\n'+
        ('Selectable master-PIC IRQ3/4/5/7; use the modem hardware settings.\n'
         if custom_irq else 'This package uses the standard COM IRQ mapping.\n')+
        ('Alt-R records/saves; Alt-S or Alt-P opens saved settings.\n'
         'Alt-F6 redisplays. Menu send/receive always remains available.\n'
         'Assigned page keys keep their BBS bindings; unassigned keys transfer.\n'
         if original_keys else '')+
        ('Alt-Z opens the command reference; backtick opens the browser.\n'
         'Dim reference commands refuse without ending the session.\n'
         'Alt-F5 selects scripts; Alt-W edits the input translation table.\n'
         if original_reference else '')+
        ('Alt-D browses the directory read-only; the current target is retained.\n'
         'Directory dialing and profile adoption are not yet available.\n'
         if directory_view else '')+
        ('Enter on a directory entry previews its proposed settings.\n'
         'Esc returns to the directory; preview does not dial or apply.\n'
         if directory_preview else '')+
        ('Directory writes share capture/recording ownership checks.\n'
         'Held directory recovery blocks child programs until exit.\n'
         if directory_storage else '')+
        ('Experimental: original CLI keyboard/action identities are retained.\n'
         'Live resource/selection adoption is still pending; LoC.6 UI retained.\n'
         if directory_resource_cli else '')+
        ('R in directory preview checks '+('KEY/KBD/XLT' if directory_translation else 'KEY/KBD')+' under UART quiescence.\n'
         'Press a key to return; no settings are adopted and nothing is dialed.\n'
         if directory_resource_owner else '')+
        ('Call statistics save after disconnect without a return-key prompt.\n'
         'Log save errors leave pending/recovery state for shutdown.\n'
         if directory_retirement else '')+
        ('R additionally checks the proposed input translation table.\n'
         if directory_translation else '')+
        ('R also resolves ASX/ASP and fingerprints the whole script.\n'
         'ASP sources still require compilation before applying an entry.\n'
         if directory_scripts else '')))
    commit = source_base_commit or subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    if len(commit)not in (40,64)or any(c not in '0123456789abcdef'for c in commit):
        raise ValueError('source base must be a complete lowercase Git object ID')
    (payload / 'VERSION.TXT').write_bytes(dos_text(
        'LoC SPECIAL EDITION\nVersion: '+('2.01-LoC.6' if directory_storage else '2.01-LoC.5' if directory_preview else '2.01-LoC.4' if directory_view else '2.01-LoC.3' if original_reference else '2.01-LoC.2' if original_keys else '2.01-LoC.1')+'\n'
        'LoSs oF CoNtRoL / Sysop: bstar\nSource base: ' + commit + '\n'
        'TERMINAL SHA256:\n' + manifests['TERMINAL.EXE']['binary_sha256'] + '\n'))
    for name in ('standalone/package_special_edition.py', 'standalone/build_guarded_helper.py'):
        sources[name] = sha(ROOT / name)
    result = dict(kind='source-built-special-edition-package', source_base_commit=commit,
                  products=manifests, sources=sources,
                  files={p.name: sha(p) for p in sorted(payload.iterdir())},
                  original_inputs=[], contains_private_configuration=False,
                  experimental_custom_irq=custom_irq,
                  experimental_original_keys=original_keys,
                  experimental_original_reference=original_reference,
                  experimental_directory_view=directory_view,
                  experimental_directory_preview=directory_preview,
                  experimental_directory_storage=directory_storage,
                  experimental_directory_resource_cli=directory_resource_cli,
                  experimental_directory_resource_owner=directory_resource_owner,
                  experimental_directory_retirement=directory_retirement,
                  experimental_directory_translation=directory_translation,
                  experimental_directory_scripts=directory_scripts,
                  authored_help_sha256=help_manifest['sha256'],
                  card_written=False, validation='Not validated by packaging; see separate DOS receipts.')
    (out / 'manifest.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--build', action='store_true')
    parser.add_argument('--custom-irq',action='store_true',help='Package matching selectable-IRQ terminal, interpreter and setup editor')
    parser.add_argument('--original-keys',action='store_true',help='Package the original-shortcut candidate as 2.01-LoC.2')
    parser.add_argument('--original-reference',action='store_true',help='Package the original reference candidate as 2.01-LoC.3')
    parser.add_argument('--directory-view',action='store_true',help='Package the serviced read-only directory candidate as 2.01-LoC.4')
    parser.add_argument('--directory-preview',action='store_true',help='Package the validated directory preview candidate as 2.01-LoC.5')
    parser.add_argument('--directory-storage',action='store_true',help='Package shared directory persistence and held-owner EXEC admission as LoC.6')
    parser.add_argument('--directory-resource-cli',action='store_true',help='Package original CLI resource binding experiment; keeps LoC.6 UI')
    parser.add_argument('--directory-scripts',action='store_true',help='Package directory ASX/ASP resource preflight; keeps LoC.6 UI')
    parser.add_argument('--directory-translation',action='store_true',help='Package transactional KEY/KBD/XLT staging; keeps LoC.6 UI')
    parser.add_argument('--directory-retirement',action='store_true',help='Package offline call-statistics retirement; keeps LoC.6 UI')
    parser.add_argument('--directory-resource-owner',action='store_true',help='Package quiesced directory KEY/KBD preflight; no selection adoption')
    parser.add_argument('--source-base-commit',help='Explicit source-base object ID; avoids Git discovery during archive reproduction')
    args = parser.parse_args()
    if args.directory_scripts:args.directory_translation=True
    if args.directory_translation:args.directory_retirement=True
    if args.directory_retirement:args.directory_resource_owner=True
    if args.directory_resource_owner:args.directory_resource_cli=True
    if args.directory_resource_cli:args.directory_storage=True
    if args.directory_storage:args.directory_preview=True
    if args.directory_preview:args.directory_view=True
    if args.directory_view:args.original_reference=True
    if args.original_reference:args.original_keys=True
    out = args.output.resolve()
    if not out.is_relative_to(ROOT / 'build') or out.exists():
        parser.error('output must be a new directory under build/')
    if args.build:
        for command in commands_for(args.custom_irq,args.original_keys,args.original_reference,args.directory_view,args.directory_preview,args.directory_storage,args.directory_resource_cli,args.directory_resource_owner,args.directory_retirement,args.directory_translation,args.directory_scripts):
            subprocess.run(command, cwd=ROOT, check=True)
    result = stage(out,args.custom_irq,args.source_base_commit,args.original_keys,args.original_reference,args.directory_view,args.directory_preview,args.directory_storage,args.directory_resource_cli,args.directory_resource_owner,args.directory_retirement,args.directory_translation,args.directory_scripts)
    print('Staged', len(result['files']), 'files at', out / 'PCPLUSSE')
    print('No card was accessed. Private settings must be preserved during installation.')


if __name__ == '__main__':
    main()
