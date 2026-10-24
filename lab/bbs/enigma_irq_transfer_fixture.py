#!/usr/bin/env python3
"""Add a generated >64KiB download to a fresh isolated framed ENiGMA fixture."""
import argparse
import json
from pathlib import Path
import subprocess

from enigma_key_stream_fixture import ROOT,owned,pid,setup,sha


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--candidate',type=Path,required=True)
    p.add_argument('--bytes',type=int,default=65539)
    args=p.parse_args();assert 65536<args.bytes<=1048576
    candidate=owned(args.candidate)
    assert not pid(candidate)and not(candidate/'instance.json').exists()
    setup(candidate)
    path=candidate/'file_base/pcplus_transfer/IRQDATA.BIN'
    assert not path.exists()and not path.parent.is_symlink()
    payload=bytes((i*73+(i>>8)*19)&255 for i in range(args.bytes))
    with path.open('xb')as f:f.write(payload)
    scan=subprocess.run(['node','oputil.js','fb','scan','pcplus_transfer','--no-prompt'],
                        cwd=candidate,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,check=True)
    (candidate/'irq-file-scan.log').write_text(scan.stdout+scan.stderr)
    code="""const c=require('./core/oputil/oputil_common');c.initConfigAndDatabases(e=>{if(e)throw e;
const F=require('./core/file_entry');F.findByFileNameWildcard('IRQDATA.BIN',(e,entries)=>{if(e)throw e;
console.log(JSON.stringify(entries.map(f=>({fileId:f.fileId,fileName:f.fileName,areaTag:f.areaTag,storageTag:f.storageTag,filePath:f.filePath,fileSha256:f.fileSha256,meta:f.meta})))) ;process.exit(0);});});"""
    entries=json.loads(subprocess.check_output(['node','-e',code],cwd=candidate,text=True))
    assert len(entries)==1
    entry=entries[0]
    assert entry['fileName']=='IRQDATA.BIN'and entry['areaTag']=='pcplus_transfer'
    assert Path(entry['filePath']).resolve()==path and entry['fileSha256']==sha(path)
    assert int(entry['meta']['byte_size'])==len(payload)
    result=dict(passed=True,payload='IRQDATA.BIN',bytes=len(payload),sha256=sha(path),metadata=entry,
                instance_sha256=sha(candidate/'instance.json'),config_sha256=sha(candidate/'config/config.hjson'),
                sources={str(p.relative_to(ROOT)):sha(p)for p in [Path(__file__).resolve(),ROOT/'lab/bbs/enigma_key_stream_fixture.py']},
                scope='Generated all-byte payload in a fresh private fixture, indexed through official FileEntry/scan APIs; no live board or original file changed.')
    (candidate/'irq-transfer-fixture.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Prepared IRQDATA.BIN:',len(payload),'bytes through official file APIs')


if __name__=='__main__':main()
