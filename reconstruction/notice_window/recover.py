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
UNIT_NAMES={0x3fc7:'save',0x4015:'restore',0x7088:'expand',0x732e:'collapse',0x74f3:'restore_cell',0x7500:'collapse_delay',0x6fec:'frame',0x7d32:'shadow',0x7f4a:'vertical',0x7f62:'cell',0x79a8:'horizontal',0x6c84:'attribute',0x6cb4:'write',0x8034:'stride',0x7f76:'copy_cell',0x79c0:'offset16',0x6b42:'cursor_pop',0x6b5a:'cursor_push',0x798e:'cursor_get',0x6b72:'pace'}
NAMES={at:'window_'+name for at,name in UNIT_NAMES.items()}
NAMES.update({0x6bbe:'window_snapshot',0x7558:'window_release',0x6e78:'window_cursor',0x488f:'window_alert',0x775a:'window_sound_open',0x7764:'window_sound_close',0x6fa0:'window_read_byte',0x6c20:'window_fill',0x6edc:'window_scroll',0x7e02:'window_offset8',0x7e20:'window_snow_cell'})
STATE={at:'window_state_'+format(at,'04x') for at in [0x1d3e,0x3352,0x7a36,0x7a38,0x7a4c,0x7a4e,0x7a66,0x7a6a,0x7a72,0x7a74,0x7a78,0x7a7a,0x7a8e,0x7a94,0x7ab2,0x7ab4,0x7ac4,0x8fda,0x8fdc,0x8fde]}



def main():
    image=ORIGINAL.read_bytes();assert hashlib.sha256(image).hexdigest()==SHA
    bundle=json.loads((ROOT/'analysis/notice-window-01.rea.json').read_text())
    evidence={r['parameters']['procedure']:r for r in bundle['records'] if r['operation']=='analyze_function'}
    units=[]
    for start,name in UNIT_NAMES.items():
        row=evidence[hex(0x10000+start)];body=row['normalized_result']['procedure']['body'];assert not body['non_contiguous'] and body['ranges'][0]['start']==hex(0x10000+start)
        units.append((name,start,start+body['total_bytes']))
    proof=dict(original_sha256=SHA,units=[],state={hex(k):v for k,v in STATE.items()})
    with tempfile.TemporaryDirectory() as directory:
        work=Path(directory)
        def asm(text,at):
            (work/'one.asm').write_text(f'BITS 16\nCPU 8086\nORG {at}\n%include "encodings.inc"\n'+text+'\n')
            result=subprocess.run(['nasm','-fbin','-I'+str(ROOT/'reconstruction/uart')+'/',str(work/'one.asm'),'-o',str(work/'one.bin')],capture_output=True)
            return (work/'one.bin').read_bytes() if result.returncode==0 else None
        for name,start,end in units:
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
                call=re.fullmatch(r'(?:call|j\w+)\s+(?:(?:short|near)\s+)?(0x[0-9a-f]+)',text)
                if call:
                    target=int(call[1],16)
                    if not start<=target<end:dependencies[target]=NAMES[target]
                for token in re.findall(r'0x[0-9a-f]+',text):
                    number=int(token,16)
                    if number in STATE:states[number]=STATE[number]
            header=['; Exact PCPlus2.01 notice window service; numerical facts in provenance.json.','BITS 16','CPU 8086',
                    '%ifdef NOTICE_WINDOW_OMF','SEGMENT _TEXT public class=CODE use16','global '+NAMES[start]]
            header+=['extern '+n for n in [*dependencies.values(),*states.values()]]
            header+=['%define short','%else',f'ORG {start}']
            header+=[f'%define {n} {at}' for at,n in {**dependencies,**states}.items()]
            header+=['%endif','%include "encodings.inc"',NAMES[start]+':']
            for at,text in rows:
                branch=re.fullmatch(r'(j\w+|loop\w*|call)\s+(?:(short|near)\s+)?(0x[0-9a-f]+)',text)
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
            mapping=next(r for r in bundle['records'] if r['operation']=='address_to_file_offset' and r['parameters']['address']==hex(0x10000+start))
            assert mapping['normalized_result']['file_offset']==int.from_bytes(image[8:10],'little')*16+start
            read=next(r for r in bundle['records'] if r['operation']=='read_bytes' and r['normalized_result']['address']==hex(0x10000+start))
            assert read['subject']['digest']['sha256']==SHA and read['normalized_result']['complete'] and bytes.fromhex(read['normalized_result']['bytes_hex'])==body
            proof['units'].append(dict(file=str(path.relative_to(ROOT)),start=start,end=end,file_offset=0x1200+start,
                bytes=len(body),sha256=hashlib.sha256(body).hexdigest(),rea_evidence_id=rea['evidence_id'],read_evidence=read['evidence_id'],mapping_evidence=mapping['evidence_id']))
    proof['limitations']=['Exact native window/cursor/animation instructions; names are analyst annotations.','Sound, heap and remaining reused display/platform dependencies require explicit bindings.','Native null snapshot still permits drawing after alert; native rectangle bounds are unchecked.','No full PROGRAM, live UART, physical video timing or application acceptance.']
    (HERE/'provenance.json').write_text(json.dumps(proof,indent=2)+'\n')
    print('Recovered notice window',sum(u['bytes'] for u in proof['units']),'exact display bytes')


if __name__=='__main__':main()
