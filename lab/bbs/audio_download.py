"""Owned stock ENiGMA download recipe and coarse actual-artifact gates."""
from pathlib import Path
from enigma_transfer import metadata, STORAGE, HELPER
from synthmodem_vm_control import ROOT, sha


def source():
    path=STORAGE/'PCXTEST.BIN'; before=metadata('PCXTEST.BIN')
    assert len(before)==1 and Path(before[0]['filePath']).resolve()==path.resolve()
    assert path.is_file() and sha(path)==before[0]['fileSha256']
    assert path.stat().st_size==11521
    return path,before


def navigation(wait,mark):
    script='transmit "F^M"\n'+wait('File Base',150,'FILES')+'waitquiet 2 120\n'+mark('FILES')
    script+='transmit "S^M"\n'+wait('FILE SEARCH',150,'SEARCH')+'waitquiet 2 120\n'+mark('SEARCH')
    script+='transmit "PCXTEST.BIN^M"\nwaitquiet 2 120\ntransmit "^M"\n'
    script+=wait('PCXTEST.BIN',150,'RESULT')+'waitquiet 2 120\n'+mark('RESULT')
    script+='transmit "T"\nwaitquiet 2 120\ntransmit "Q"\n'
    script+=wait('FILE SEARCH',150,'BACK-SEARCH')+'waitquiet 2 120\ntransmit "^["\n'
    script+=wait('File Base',150,'BACK-FILES')+'waitquiet 2 120\ntransmit "D^M"\n'
    script+=wait('DOWNLOAD MANAGER',150,'QUEUE')+'waitquiet 2 120\n'+mark('QUEUE')+'transmit "A"\n'
    script+=wait('PROTOCOL SELECTION',150,'PROTOCOL')+'waitquiet 2 120\n'+mark('PROTOCOL')
    # No waits after starting the actual helper: the child must release its
    # receive lease so the parent's enabled automatic signature owner can run.
    script+='transmit "^M"\n'+mark('TRANSFER')
    return script


def configure_profile(profile,out):
    (out/'RECV').mkdir(); data=bytearray(profile)
    data[0x42c:0x42e]=b'\x01\0'; path=b'D:\\RECV\\\0'
    data[0x31c:0x31c+len(path)]=path
    return bytes(data)


def check(out,rows,path,before):
    expected=path.read_bytes(); target=out/'RECV/PCXTEST.BIN'
    executions=[i for i,r in enumerate(rows) if r.get('msg')=='Executing external protocol']
    exits=[i for i,r in enumerate(rows) if r.get('msg')=='Process exited' and r.get('exitCode')==0]
    after=metadata('PCXTEST.BIN')
    menus_after=[r.get('menuName') for r in rows[exits[-1]+1:]] if exits else []
    resumed=False
    try:
        a=menus_after.index('fileBaseMainMenu'); b=menus_after.index('fileBaseSearch',a+1)
        menus_after.index('fileBaseListEntries',b+1); resumed=True
    except ValueError: pass
    checks={'exact_download':target.is_file() and target.read_bytes()==expected,
            'only_expected_download':{p.name for p in (out/'RECV').iterdir()}=={'PCXTEST.BIN'},
            'no_receive_stage':not any(p.name.startswith(('PCRX.','PCZRX.')) for p in out.rglob('*')),
            'actual_helper_exit_zero':len(executions)==len(exits)==1 and executions[0]<exits[0],
            'posttransfer_search_and_list':resumed,
            'official_download_counter_advanced':len(after)==1 and after[0]['meta'].get('dl_count',0)>=before[0]['meta'].get('dl_count',0)+1}
    return checks,{'expected_path':str(path),'expected_bytes':len(expected),'expected_sha256':sha(path),
                   'metadata_before':before,'metadata_after':after,'menus_after_helper_exit':menus_after,
                   'scope':'Coarse file/helper/return gates only. Independent full protocol/control and stream audits are mandatory.'}
