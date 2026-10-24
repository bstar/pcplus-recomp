"""Link a namespaced native reset bank beside the maintained live terminal.

The cold bank is experimental; this module does not enable peer width requests
or define the live renderer projection/transaction owner.
"""
import hashlib
from pathlib import Path
import re
import subprocess


def build_native_reset_bank(root,out,overlay=True,transaction=False):
    assert not transaction or overlay
    root=Path(root);out=Path(out)/'native-reset-bank';out.mkdir(parents=True,exist_ok=True)
    native=[]
    for module in ['screen','erase','scroll','text','cursor_shape','terminal_services','terminal_reset','viewport']:
        native+=sorted((root/'reconstruction'/module).glob('*.asm'))
    native += [root/'reconstruction/attributes/reset.asm',root/'reconstruction/ui_windows/cga_blank.asm',
        root/'reconstruction/ui_windows/cga_unblank.asm',root/'reconstruction/modes/width_request.asm',
        root/'standalone/terminal_reset_host.asm']
    if transaction:
        native+=sorted((root/'reconstruction/attribute_repair').glob('*.asm'))
        native.append(root/'reconstruction/attribute_boundary/position.asm')
    # Each recovered file is an indivisible instruction unit. Link the complete
    # dependency closure of the reset body, rather than unrelated printing and
    # scrolling units from the diagnostic's broader module inventory. Imports
    # in unreachable branches still count: this does not specialize reset paths.
    def declared(path,kind):
        return {name.strip() for names in re.findall(r'^\s*'+kind+r'\s+([^;\n]+)',path.read_text(),re.M)
                for name in names.split(',')}
    providers={}
    for path in native:
        for name in declared(path,'global'):
            if transaction and path.name=='terminal_reset_host.asm'and name=='erase_repair_attributes':continue
            assert name not in providers,name
            providers[name]=path
    if transaction:providers['erase_repair_attributes']=root/'reconstruction/attribute_repair/repair.asm'
    selected=set();pending=[root/'standalone/reset_bank_body.asm']
    while pending:
        for name in declared(pending.pop(),'extern'):
            path=providers.get(name)
            if path is not None and path not in selected:
                selected.add(path);pending.append(path)
    inventory=list(native)
    native=[path for path in native if path in selected]
    symbols=set()
    for path in native:
        for names in re.findall(r'^\s*(?:global|extern)\s+([^;\n]+)',path.read_text(),re.M):
            for name in names.split(','):
                name=name.strip();assert re.fullmatch('[A-Za-z_][A-Za-z_0-9]*',name),name
                symbols.add(name)
    namespace={name:'nreset_'+name for name in sorted(symbols)}
    if transaction:namespace['attribute_repair_native']='nreset_erase_repair_attributes'
    aliases=['-D'+name+'='+target for name,target in namespace.items()]
    objects=[]
    for number,path in enumerate(native):
        obj=out/f'native-{number}.obj';objects.append(obj)
        local_namespace=dict(namespace)
        if transaction and path==root/'reconstruction/terminal_reset/width.asm':
            local_namespace['terminal_reset_width']='nreset_terminal_reset_width_native'
        if transaction and path==root/'reconstruction/terminal_reset/geometry.asm':
            local_namespace['terminal_reset_geometry']='nreset_terminal_reset_geometry_native'
        local_aliases=['-D'+name+'='+target for name,target in local_namespace.items()]
        subprocess.run(['nasm','-fobj','-D'+path.parent.name.upper()+'_OMF',*(['-DRESET_BANK_OVERLAY']if overlay else[]),
            *(['-DRESET_BANK_TRANSACTION','-DRESET_BANK_FIELDS']if transaction else[]),
            '-DRESET_VIEWPORT','-DRESET_BANK','-DVIEWPORT_PRESERVE_DS','-DWIDTH_REQUEST_OMF',
            '-D_TEXT=RESET_CODE','-DCODE=FARCODE','-D_DATA=RESET_DATA','-DDATA=NATIVE_DATA',
            '-DSTACK=RESET_STACK','-DDGROUP=RESET_GROUP',*local_aliases,
            '-I',str(root/'reconstruction/uart')+'/',str(path.relative_to(root)),'-o',str(obj)],cwd=root,check=True)
    helpers=[root/'src/ui/reset_bank_context.asm',root/'standalone/reset_bank_body.asm']
    if transaction:helpers.append(root/'src/ui/reset_live.asm')
    for path in helpers:
        obj=out/(path.stem+'.obj');objects.append(obj)
        flags=['-DRESET_BANK_APP']+(['-DRESET_BANK_OVERLAY']if overlay else[])+(['-DRESET_BANK_TRANSACTION']if transaction else[])
        flags+=(['-Dreset_stack_top=nreset_stack_top']if path.name=='reset_bank_context.asm'else aliases if path.name=='reset_bank_body.asm'else[])
        subprocess.run(['nasm','-fobj',*flags,str(path.relative_to(root)),'-o',str(obj)],cwd=root,check=True)
    # Selection reads the full inventory, so every candidate is a build input.
    inputs=inventory+helpers+[Path(__file__).resolve(),root/'reconstruction/uart/encodings.inc']
    return dict(objects=objects,inputs=inputs,namespace=namespace,overlay=overlay,
        source_hashes={str(path.relative_to(root)):hashlib.sha256(path.read_bytes()).hexdigest()for path in inputs},
        scope=('Experimental field-aware1..25-row live transaction with status-aware geometry; normal peer width and broader UI composition remain unbound.'if transaction else
            'Namespaced cold native reset bank; live projection/commit/rollback and normal width ownership remain unbound.'))
