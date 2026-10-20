#!/usr/bin/env python3
"""Analyst-only regeneration from the pinned original and retained REA evidence.

Normal builds use the committed assembly/facts and never invoke this script.
"""
import hashlib,json,re,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
ORIGINAL=ROOT/'analysis/pcplus-originals/PCPLUS-main-2.01.EXE'
SHA='6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
UNITS=[('snapshot',0x6bbe,0x6bf0),('restore',0x7558,0x7589),
       ('geometry',0x6d1a,0x6dca),('snow_enable',0x77ae,0x77bd),('snow_disable',0x77be,0x77d2)]
NAMES={start:'display_'+name for name,start,end in UNITS}
NAMES.update({0x860f:'display_allocate',0x85fc:'display_free'})
STATE={at:'display_'+name for at,name in [
 (0x7a66,'legacy'),(0x7a72,'columns'),(0x7a74,'rows'),(0x7a76,'mode'),
 (0x7a78,'segment'),(0x7a7a,'stride'),(0x7a7c,'bytes'),(0x7a7e,'last_column'),
 (0x7a80,'last_row'),(0x7a82,'last_line'),(0x7a85,'cursor_row'),(0x7a86,'mono'),
 (0x7a88,'cursor_start'),(0x7a8a,'cursor_end'),(0x7a8c,'cells'),
 (0x7a8e,'status_port'),(0x7a90,'crt'),(0x7a92,'snow')]}


def main():
    image=ORIGINAL.read_bytes();assert hashlib.sha256(image).hexdigest()==SHA
    bundle=json.loads((ROOT/'analysis/program-display-02.rea.json').read_text())
    evidence={r['parameters']['procedure']:r for r in bundle['records'] if r['operation']=='analyze_function'}
    proof=dict(original_sha256=SHA,units=[],state={hex(k):v for k,v in STATE.items()})
    with tempfile.TemporaryDirectory() as directory:
        work=Path(directory)
        def asm(text,at):
            (work/'one.asm').write_text(f'BITS 16\nCPU 8086\nORG {at}\n%include "encodings.inc"\n'+text+'\n')
            result=subprocess.run(['nasm','-fbin','-I'+str(ROOT/'reconstruction/uart')+'/',str(work/'one.asm'),'-o',str(work/'one.bin')],capture_output=True)
            return (work/'one.bin').read_bytes() if result.returncode==0 else None
        for name,start,end in UNITS:
            body=image[0x1200+start:0x1200+end];(work/'part').write_bytes(body)
            rows=[]
            for line in subprocess.check_output(['ndisasm','-b16',f'-o{start}',str(work/'part')],text=True).splitlines():
                match=re.fullmatch(r'([0-9A-F]+)\s+([0-9A-F]+)\s+(.*)',line);assert match,line
                at,raw,text=int(match[1],16),bytes.fromhex(match[2]),match[3]
                if raw[0]==0xeb:text=text.replace('jmp ','jmp short ',1)
                elif raw[0]==0xe9:text=text.replace('jmp ','jmp near ',1)
                elif 0x70<=raw[0]<=0x7f:text=text.replace(' ',' short ',1)
                if asm(text,at)!=raw:
                    variants=[]
                    if len(raw)==2 and raw[1]>=0xc0 and raw[0] in (2,3,10,11,18,19,26,27,34,35,42,43,50,51,58,59,138,139):
                        op,operands=text.split(' ',1);variants.append(op+'_load '+operands)
                    for width in ('word','byte'):variants.append(re.sub(r',(-?0x[0-9a-f]+)$',rf',strict {width} \1',text))
                    text=next((v for v in variants if asm(v,at)==raw),None);assert text,(hex(at),raw.hex())
                rows.append((at,text))
            dependencies={};states={}
            for at,text in rows:
                call=re.fullmatch(r'call (0x[0-9a-f]+)',text)
                if call:
                    target=int(call[1],16);dependencies[target]=NAMES[target]
                for token in re.findall(r'0x[0-9a-f]+',text):
                    number=int(token,16)
                    if number in STATE:states[number]=STATE[number]
            header=['; Exact PCPlus2.01 display service; numerical facts in provenance.json.','BITS 16','CPU 8086',
                    '%ifdef PROGRAM_DISPLAY_OMF','SEGMENT _TEXT public class=CODE use16','global '+NAMES[start]]
            header+=['extern '+n for n in [*dependencies.values(),*states.values()]]
            header+=['%define short','%else',f'ORG {start}']
            header+=[f'%define {n} {at}' for at,n in {**dependencies,**states}.items()]
            header+=['%endif','%include "encodings.inc"',NAMES[start]+':']
            for at,text in rows:
                branch=re.fullmatch(r'(j\w+|call)\s+(?:(short|near)\s+)?(0x[0-9a-f]+)',text)
                if branch:
                    target=int(branch[3],16)
                    label=f'L_{target:04x}' if start<=target<end else NAMES[target]
                    text=branch[1]+' '+(branch[2]+' ' if branch[2] else '')+label
                for address,symbol in states.items():text=re.sub(r'(?<![\da-f])0x'+f'{address:x}'+r'(?![\da-f])',symbol,text)
                header.append(f'L_{at:04x}: '+text)
            path=HERE/(name+'.asm');path.write_text('\n'.join(header)+'\n')
            subprocess.run(['nasm','-fbin','-I'+str(ROOT/'reconstruction/uart')+'/',str(path),'-o',str(work/'whole.bin')],check=True)
            assert (work/'whole.bin').read_bytes()==body
            rea=evidence[hex(0x10000+start)]
            assert rea['subject']['digest']['sha256']==SHA
            proof['units'].append(dict(file=str(path.relative_to(ROOT)),start=start,end=end,file_offset=0x1200+start,
                bytes=len(body),sha256=hashlib.sha256(body).hexdigest(),rea_evidence_id=rea['evidence_id']))
    proof['limitations']=['Names are analyst annotations. Geometry preserves native byte writes and16-bit arithmetic.',
        'Native CGA snow wait is unbounded; live hardware timing is not established.',
        'Heap, geometry admission and owned snapshot lifetime are maintained platform bindings.',
        'Full PROGRAM UI/WAIT/cursor/font/UART controller remains unintegrated.']
    (HERE/'provenance.json').write_text(json.dumps(proof,indent=2)+'\n')
    print('Recovered',sum(u['bytes'] for u in proof['units']),'exact display bytes')


if __name__=='__main__':main()
