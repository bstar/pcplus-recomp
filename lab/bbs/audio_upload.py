"""Owned stock ENiGMA upload recipe and preliminary storage/return gates.

No server configuration changes, file replacement or invented protocol replies.
Actual audio acceptance additionally requires independent wire/control audits.
"""
from pathlib import Path
import enigma_transfer
from enigma_upload_dos import metadata as file_metadata
from synthmodem_vm_control import ROOT,sha
import enigma

NAME='AUDIOUP.BIN'

def helper():return enigma_transfer.HELPER
def storage():return enigma_transfer.STORAGE


def payload():
    return bytes(((i*73+(i>>8)*19)&255)^0x5a for i in range(11521))


def metadata():
    result=file_metadata(enigma.SOURCE,[NAME])
    assert len(result)==1 and result[0]['name']==NAME
    return result[0]['entries']


def prepare(out):
    out=Path(out).resolve();assert out.is_relative_to(ROOT/'build')
    before=metadata()
    assert not before and not (storage()/NAME).exists(),'Preserve existing uploads; this first-run fixture must be absent'
    send=out/'SEND';send.mkdir()
    path=send/NAME;path.write_bytes(payload())
    return {'source_path':str(path),'source_bytes':path.stat().st_size,'source_sha256':sha(path),
        'source_stat':[path.stat().st_ino,path.stat().st_size,path.stat().st_mtime_ns],
        'metadata_before':before,'target_path':str(storage()/NAME)}


def navigation(wait,mark):
    script='transmit "F^M"\n'+wait('File Base',150,'FILES')+'waitquiet 2 120\n'+mark('FILES')
    script+='transmit "U^M"\n'+wait('(blind - filename ignored)',150,'UPLOAD-OPTIONS')+'waitquiet 2 120\n'+mark('UPLOAD-OPTIONS')
    # The unchanged stock blind form retains its filename view in the initial
    # focus cycle. Match the separately observed three-Tab path to Continue.
    for _ in range(3):script+='transmit "^I"\nwaitquiet 2 120\n'
    script+='transmit "^M"\n'+wait('PROTOCOL SELECTION',150,'PROTOCOL')+'waitquiet 2 120\n'+mark('PROTOCOL')
    # The BIOS helper starts local Alt-S/F2/file input after the real receiver's
    # banner. Release the ASPECT child lease before that modal terminal owner.
    return script+'transmit "^M"\n'+mark('TRANSFER')


def check(out,rows,before):
    source=Path(before['source_path']);expected=payload();entries=metadata()
    installed=False
    if len(entries)==1:
        entry=entries[0];target=Path(entry['filePath'])
        installed=(entry['fileName']==NAME and entry['areaTag']==entry['storageTag']=='pcplus_transfer'
            and target.resolve()==(storage()/NAME).resolve() and target.is_file() and target.read_bytes()==expected
            and entry['fileSha256']==before['source_sha256'] and entry['meta'].get('byte_size')==len(expected)
            and entry['meta'].get('upload_by_username')=='loclab')
    executions=[i for i,r in enumerate(rows) if r.get('msg')=='Executing external protocol']
    exits=[i for i,r in enumerate(rows) if r.get('msg')=='Process exited' and r.get('exitCode')==0]
    tail=[r.get('menuName') for r in rows[exits[-1]+1:]] if exits else []
    resumed=False
    try:
        first=tail.index('fileBaseMainMenu');search=tail.index('fileBaseSearch',first+1)
        tail.index('fileBaseListEntries',search+1);resumed=True
    except ValueError:pass
    checks={'fresh_owned_upload':before['metadata_before']==[],
        'exact_official_installed_file':installed,
        'unchanged_DOS_source':source.is_file() and source.read_bytes()==expected and sha(source)==before['source_sha256']
            and [source.stat().st_ino,source.stat().st_size,source.stat().st_mtime_ns]==before['source_stat'],
        'real_owned_receive_helper':len(executions)==1 and rows[executions[0]].get('cmd')==str(helper())
            and rows[executions[0]].get('direction')=='recv',
        'helper_exit_zero':len(executions)==len(exits)==1 and executions[0]<exits[0],
        'postupload_search_and_list':resumed}
    return checks,{'prepared':before,'metadata_after':entries,'menus_after_helper_exit':tail,
        'scope':'Preliminary exact source/storage/official-metadata/helper/return gates. Independent complete CRC/control/finish, byte identity and DOS cleanup remain mandatory; no standalone acceptance.'}
