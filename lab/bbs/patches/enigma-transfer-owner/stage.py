#!/usr/bin/env python3
"""Stage explicit upload/list owners on a fresh isolated owned BBS fixture."""
import argparse,json,shutil,subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from enigma_key_stream_fixture import ROOT,owned,pid,sha


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--candidate',type=Path,required=True);p.add_argument('--server-root',type=Path,required=True)
    a=p.parse_args();candidate=owned(a.candidate);assert not pid(candidate)
    fixture_path=candidate/'search-instance.json';fixture=json.loads(fixture_path.read_text());assert fixture['upload_fixture']
    record=candidate/'transfer-owner-experiment.json';assert not record.exists()
    original={n:h for n,h in fixture['source_inputs'].items() if n.startswith('core/')}
    for n,h in original.items():assert sha(candidate/n)==h==sha(a.server_root/n)
    here=Path(__file__).resolve().parent;patch=here/'transfer-owner.patch';helper=here/'transfer_temp_owner.js'
    target=candidate/'core/transfer_temp_owner.js';assert not target.exists()
    subprocess.run(['git','apply','--check',str(patch)],cwd=candidate,check=True)
    shutil.copyfile(helper,target)
    subprocess.run(['git','apply',str(patch)],cwd=candidate,check=True)
    staged={n:sha(candidate/n) for n in [*original,'core/transfer_temp_owner.js']}
    changed={n for n,h in staged.items() if original.get(n)!=h}
    assert changed=={'core/upload.js','core/file_transfer.js','core/file_transfer_protocol_select.js','core/transfer_temp_owner.js'}
    metadata=dict(original_core=original,staged_core=staged,changed=sorted(changed),
        authored_core={'core/transfer_temp_owner.js':dict(source=str(helper.relative_to(ROOT)),sha256=sha(helper))},
        inputs={str(n.relative_to(ROOT)):sha(n) for n in (Path(__file__).resolve(),patch,helper)},
        scope='Isolated explicit transfer owners. Callback/throw cleanup errors retire only their owner and remain retryable. Running board and DOS products are unchanged.')
    record.write_text(json.dumps(metadata,indent=2)+'\n')
    fixture['fixture_inputs'].update(staged);fixture['fixture_inputs']['transfer-owner-experiment.json']=sha(record)
    fixture['transfer_owner_experiment']=True
    fixture['scope']+=' Explicit transfer-owner helper and three core changes are staged separately.'
    fixture_path.write_text(json.dumps(fixture,indent=2)+'\n')
    print('Staged transfer owners:',len(changed),'core inputs')


if __name__=='__main__':main()
