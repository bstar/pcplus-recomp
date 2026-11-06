#!/usr/bin/env python3
"""Generate authored47-context PCPLUS.HLP; no original resource input."""
import argparse,hashlib,json,struct,textwrap
from pathlib import Path
from build_help_resource import menu_topics
ROOT=Path(__file__).resolve().parents[1]
def generate(path):
 source=ROOT/'resources/help/context.json';menu=ROOT/'src/redisplay/command_menu.c'
 topics=json.loads(source.read_text());assert [t['context'] for t in topics]==list(range(47))
 commands=menu_topics(menu,original_keys=True)
 records=[];payload=[];offset=3+47*38;total=0
 for topic in topics:
  title=topic['title'].encode('cp437');assert 0<len(title)<=32
  prose=list(topic['lines'])
  if topic['context']==41:
   for command in commands:prose+=['',command['title']]+command['lines']
  lines=[]
  for paragraph in prose:
   assert not any(c in paragraph for c in '\0\r\n')
   lines+=textwrap.wrap(paragraph,width=74,break_long_words=True,break_on_hyphens=False) or ['']
  data=b''.join(line.encode('cp437')+b'\n' for line in lines)
  records.append(title.ljust(32,b'\0')+struct.pack('<HI',len(lines),offset));payload.append(data);offset+=len(data);total+=len(lines)
 assert total<=65535
 data=struct.pack('<BH',47,total)+b''.join(records+payload);assert b'retro' not in data.lower()
 path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
 sources=[source,menu,Path(__file__),ROOT/'standalone/build_help_resource.py']
 report=dict(original_inputs=[],topics=47,lines=total,bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),sources={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},scope='Authored47-context HLP. Context41 includes the authored command-menu descriptions. Context identifiers retain the observed native order; entry wiring is recorded by the parent package, not this resource generator.')
 path.with_suffix('.json').write_text(json.dumps(report,indent=2)+'\n');return report
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();print(json.dumps(generate(a.output.resolve())))
if __name__=='__main__':main()
