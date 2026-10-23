#!/usr/bin/env python3
"""Generate an authored HLP resource, reusing existing command-menu prose."""
import argparse,ast,hashlib,json,re,struct,textwrap
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
STRING = '"(?:\\\\.|[^"\\\\])*"'
def menu_topics(path):
    pattern=re.compile(r'^ENTRY\((\w+),\s*('+STRING+r'),\s*((?:'+STRING+r'\s*)+)\);',re.M)
    topics=[]
    for m in pattern.finditer(path.read_text()):
        title=ast.literal_eval('b'+m[2]).decode('cp437')
        title=re.split(r' {2,}',title)[0][:32]
        body=b''.join(ast.literal_eval('b'+s) for s in re.findall(STRING,m[3])).decode('cp437')
        topics.append(dict(id='menu.'+m[1],title=title,lines=body.split('\n')))
    assert len(topics)==24,'Command-menu declaration changed; review extraction'
    return topics
def generate(path):
    source=ROOT/'resources/help/notice.json';menu=ROOT/'src/redisplay/command_menu.c'
    topics=json.loads(source.read_text())+menu_topics(menu);records=[];texts=[];total=0
    offset=3+38*len(topics);assert 0<len(topics)<=255
    for topic in topics:
        title=topic['title'].encode('cp437');assert 0<len(title)<=32
        lines=[]
        for paragraph in topic['lines']:
            assert '\0' not in paragraph and '\r' not in paragraph and '\n' not in paragraph
            lines.extend(textwrap.wrap(paragraph,width=74,break_long_words=True,break_on_hyphens=False) or [''])
        payload=b''.join(line.encode('cp437')+b'\n' for line in lines)
        records.append(title.ljust(32,b'\0')+struct.pack('<HI',len(lines),offset))
        texts.append(payload);offset+=len(payload);total+=len(lines)
    assert total<=65535
    data=struct.pack('<BH',len(topics),total)+b''.join(records)+b''.join(texts)
    path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
    return dict(bytes=len(data),topics=len(topics),lines=total,sha256=hashlib.sha256(data).hexdigest(),
        topic_ids=[t['id'] for t in topics],sources={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [source,menu,Path(__file__)]},original_inputs=[])
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    out=a.output.resolve();assert out.is_relative_to(ROOT/'build')
    m=generate(out);out.with_suffix('.json').write_text(json.dumps(m,indent=2)+'\n');print(json.dumps({k:v for k,v in m.items() if k in ('topics','lines','bytes','sha256')}))
if __name__=='__main__':main()
