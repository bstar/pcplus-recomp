#!/usr/bin/env python3
"""Generate an authored HLP resource, reusing existing command-menu prose."""
import argparse,ast,hashlib,json,re,struct,textwrap,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
STRING = '"(?:\\\\.|[^"\\\\])*"'
def menu_topics(path,original_keys=False):
    # Expand the actual authored declaration block with the pinned C
    # preprocessor. No headers are needed for text; don't parse an inactive
    # #else branch or silently omit macro-based titles/concatenated prose.
    source=path.read_text();start=source.index('#define MENU_TEXT ');end=source.index('#define ROW(')
    expanded=subprocess.check_output(['cpp','-P','-undef','-nostdinc',
        *(['-DTERMINAL_ORIGINAL_KEYS'] if original_keys else []),'-'],
        input=source[start:end],text=True)
    pattern=re.compile(r'\b(\w+)_(name|help)\[\]\s*=\s*((?:'+STRING+r'\s*)+);')
    declared={};order=[]
    for m in pattern.finditer(expanded):
        if m[1] not in declared:declared[m[1]]={};order.append(m[1])
        assert m[2] not in declared[m[1]],'Duplicate help declaration'
        declared[m[1]][m[2]]=b''.join(ast.literal_eval('b'+s) for s in re.findall(STRING,m[3])).decode('cp437')
    topics=[]
    for name in order:
        assert set(declared[name])=={'name','help'},name
        title=declared[name]['name']
        title=re.split(r' {2,}',title)[0][:32]
        body=declared[name]['help']
        topics.append(dict(id='menu.'+name,title=title,lines=body.split('\n')))
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
