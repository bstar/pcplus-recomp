#!/usr/bin/env python3
"""Stage per-upload temporary ownership on an isolated checked fixture only."""
import argparse,json,subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from enigma_key_stream_fixture import ROOT,owned,pid,sha


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--candidate',type=Path,required=True);p.add_argument('--server-root',type=Path,required=True)
    a=p.parse_args();candidate=owned(a.candidate);assert not pid(candidate)
    fixture_path=candidate/'search-instance.json';fixture=json.loads(fixture_path.read_text());assert fixture['upload_fixture']
    record=candidate/'upload-temp-experiment.json';assert not record.exists()
    original={name:h for name,h in fixture['source_inputs'].items() if name.startswith('core/')}
    for name,h in original.items():assert sha(candidate/name)==h==sha(a.server_root/name)
    patch=Path(__file__).with_name('upload-temp.patch')
    subprocess.run(['git','apply','--check',str(patch)],cwd=candidate,check=True)
    subprocess.run(['git','apply',str(patch)],cwd=candidate,check=True)
    current={name:sha(candidate/name) for name in original}
    changed={name for name,h in current.items() if h!=original[name]}
    assert changed=={'core/upload.js','core/file_transfer.js','core/file_transfer_protocol_select.js'}
    metadata=dict(original_core=original,staged_core=current,changed=sorted(changed),
        inputs={str(path.relative_to(ROOT)):sha(path) for path in (Path(__file__),patch)},
        scope='Isolated per-upload tracked-session patch; the running board remains unchanged. Original source fingerprints remain in source_inputs; staged inputs are explicit.')
    record.write_text(json.dumps(metadata,indent=2)+'\n')
    fixture['fixture_inputs'].update(current)
    fixture['fixture_inputs']['upload-temp-experiment.json']=sha(record)
    fixture['upload_temp_experiment']=True
    fixture['scope']+=' Per-upload temporary ownership is staged separately; this is not an unmodified upload-core test.'
    fixture_path.write_text(json.dumps(fixture,indent=2)+'\n')
    print('Staged isolated upload ownership:',len(changed),'core modules')


if __name__=='__main__':main()
