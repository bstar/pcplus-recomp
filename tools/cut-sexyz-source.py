#!/usr/bin/env python3
"""Reproduce the pinned standalone source closure without Git or Docker."""
import hashlib,json,re,shlex,shutil,subprocess,sys
from pathlib import Path

def main():
 root=Path(sys.argv[1]).resolve();out=Path(sys.argv[2]).resolve()
 assert not out.exists();out.mkdir()
 release=root/'src/sbbs3/sexyz_release';trees=[root/p for p in ('src/sbbs3','src/xpdev','src/hash','src/smblib')]
 def find(name):
  matches=[p/name for p in trees if (p/name).is_file()];assert matches,name
  return matches[0]
 # Dependency scanning needs the generated headers. Fixed stamps identify the
 # pinned source, not a local checkout or a claimed original binary build date.
 stamps={'git_branch.h':'#define GIT_BRANCH "pinned-e7a8257"\n',
  'git_hash.h':'#define GIT_HASH "e7a825704e"\n#define GIT_DATE "source-pinned"\n#define GIT_TIME 0\n'}
 for name,body in stamps.items():(root/'src/sbbs3'/name).write_text(body)
 makefile=(release/'GNUmakefile').read_text()
 match=re.search(r'^SRCS = (.*?)(?=\n\n)',makefile,re.M|re.S);assert match
 names=match[1].replace('\\\n',' ').split();assert len(names)==22
 headers=set()
 for name in names:
  source=find(name);shutil.copyfile(source,out/name)
  deps=subprocess.check_output(['gcc','-MM',*[v for t in trees for v in ('-I',str(t))],str(source)],text=True)
  headers.update(Path(v).name for v in shlex.split(deps.replace('\\\n',' ')) if v.endswith('.h'))
 for name in headers-set(stamps):shutil.copyfile(find(name),out/name)
 for name,body in stamps.items():(out/name).write_text(body)
 for name in ('COMPILING.md','FILE_ID.DIZ','GNUmakefile','Makefile.vc'):shutil.copyfile(release/name,out/name)
 for name in ('sexyz.txt','sexyz_changes.md'):shutil.copyfile(root/'docs'/name,out/name)
 shutil.copyfile(root/'LICENSE',out/'LICENSE')
 hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.iterdir()) if p.suffix in ('.c','.h') and p.name not in stamps}
 digest=hashlib.sha256(''.join(h+'  '+n+'\n' for n,h in hashes.items()).encode()).hexdigest()
 assert digest=='79bbd980581e7b90c4bc4506d948b0554919e40634b0bde84b3e67d76c660455',digest
 (out/'source-manifest.json').write_text(json.dumps({'upstream_commit':'e7a825704ef5329c7ef8408749671291a85ef7f2','source_digest':digest,'files':hashes},indent=2)+'\n')
 print('Pinned standalone source digest',digest)

if __name__=='__main__':main()
