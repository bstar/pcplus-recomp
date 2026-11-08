#!/usr/bin/env python3
"""Copy an explicit current SynthModem Telnet-only closure for owned BBS labs.

No runtime installation, npm, SIP/audio process or live configuration is changed.
Copied configuration remains under ignored build storage, never public source.
"""
import argparse,hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
FILES=('config.js','src/telnet/TelnetProxy.js','src/telnet/TelnetCodec.js',
       'src/telnet/InputSequenceFramer.js','src/telnet/WindowSizeReply.js','src/logger.js','COPYING')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--runtime',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
 a=p.parse_args();source=a.runtime.resolve();out=a.output.resolve()
 assert out.is_relative_to(ROOT/'build') and not out.exists()
 before={}
 for name in FILES:
  path=(source/name).resolve();assert path.is_relative_to(source) and path.is_file(),name
  before[name]=sha(path)
 out.mkdir(parents=True)
 for name in FILES:
  path=out/name;path.parent.mkdir(parents=True,exist_ok=True)
  shutil.copyfile(source/name,path);assert sha(path)==before[name],name
 assert before=={name:sha(source/name) for name in FILES}
 result=dict(passed=True,source_root=str(source),files=before,stager_sha256=sha(Path(__file__)),
  source_unchanged=True,installed_changed=False,scope=__doc__)
 (out/'stage.json').write_text(json.dumps(result,indent=2)+'\n');print('Staged Telnet-only proxy:',len(FILES),'matched files')


if __name__=='__main__':main()
