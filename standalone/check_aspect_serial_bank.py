#!/usr/bin/env python3
"""Audit all serial bank bridges/relocations and compare the C instruction bytes."""
import argparse,hashlib,json,re,struct
from pathlib import Path
from omf_imports import records,externals
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
    base=ROOT/'build/aspect-serial-bank-parent';old=ROOT/'build/aspect-help-resource-parent'
    m=json.loads((base/'manifest.json').read_text());baseline=json.loads((old/'manifest.json').read_text())
    assert m['experimental_serial_bank'] and not baseline['experimental_serial_bank']
    for folder,r in [(base,m),(old,baseline)]:
        assert sha(folder/'ASPECT.EXE')==r['binary_sha256']
        assert r['sources']['src/aspect/serial.c']==sha(ROOT/'src/aspect/serial.c')
    def omf(folder):return records((folder/'serial.o').read_bytes())
    # Both compiler objects have code segment index1. Compare its declared
    # length and every emitted byte, including gaps; other OMF segment names,
    # class indices and callback external names intentionally differ.
    def code(recs):
        segments=[p for k,p,_ in recs if k==0x98];assert segments[0][0]>>5!=0
        size=int.from_bytes(segments[0][1:3],'little');result=bytearray(size);seen=set()
        for kind,payload,_ in recs:
            if kind==0xa0 and payload[0]==1:
                at=int.from_bytes(payload[1:3],'little');data=payload[3:];assert at+len(data)<=size
                assert not seen.intersection(range(at,at+len(data)));seen.update(range(at,at+len(data)));result[at:at+len(data)]=data
            if kind==0xa2:assert payload[0]!=1
        assert len(seen)==size;return bytes(result)
    assert code(omf(base))==code(omf(old)) and len(code(omf(base)))==3415
    image=(base/'ASPECT.EXE').read_bytes();h=struct.unpack_from('<14H',image);start=h[4]*16
    relocations={s*16+o for o,s in (struct.unpack_from('<HH',image,h[12]+i*4) for i in range(h[3]))}
    listing=(base/'ASPECT.map').read_text();symbols={n:(int(s,16),int(o,16)) for s,o,n in re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$',listing,re.M|re.I)}
    def raw(name,n):s,o=symbols[name];return image[start+s*16+o:start+s*16+o+n]
    def farcall(name,position,target):
        seg,off=symbols[target];assert raw(name,position+5)[position:]==b'\x9a'+struct.pack('<HH',off,seg),(name,target)
        s,o=symbols[name];assert s*16+o+position+3 in relocations
    def nearcall(name,position,target):
        value=raw(name,position+3)[position:];assert value[0]==0xe8
        assert symbols[name][0]==symbols[target][0]
        assert (symbols[name][1]+position+3+struct.unpack('<h',value[1:])[0])&65535==symbols[target][1]
    abi=(ROOT/'src/aspect/serial_bank.inc').read_text();entries=re.findall(r'^SERIAL_ENTRY (\w+),(\d+)$',abi,re.M)
    callbacks=re.findall(r'^SERIAL_CALLBACK (\w+),(\w+),(\d+)$',abi,re.M);assert len(entries)==9 and len(callbacks)==14
    tail=bytes.fromhex('8d66005d');proof=[]
    for name,n in entries:
        n=int(n);prefix=bytes.fromhex('5589e5')+(bytes.fromhex('ff7604') if n else b'')
        assert raw(name,len(prefix))==prefix;farcall(name,len(prefix),name+'_far')
        assert raw(name,len(prefix)+10)[len(prefix)+5:]==tail+b'\xc3'
        far=name+'_far';prefix=bytes.fromhex('5589e5')+(bytes.fromhex('ff7606') if n else b'')
        assert raw(far,len(prefix))==prefix;nearcall(far,len(prefix),name+'_impl')
        assert raw(far,len(prefix)+8)[len(prefix)+3:]==tail+b'\xcb'
        proof.append(dict(entry=name,words=n,passed=True))
    for name,target,n in callbacks:
        n=int(n);resident=name+'_resident';prefix=bytes.fromhex('5589e5')+b''.join(bytes([0xff,0x76,8+2*i]) for i in reversed(range(n)))
        assert raw(resident,len(prefix))==prefix;nearcall(resident,len(prefix),target)
        assert raw(resident,len(prefix)+8)[len(prefix)+3:]==tail+b'\xcb'
        farcall(name,0,resident);assert raw(name,6)[5:]==b'\xc3'
        proof.append(dict(callback=name,target=target,words=n,passed=True))
    segments=[]
    for name,kind,seg,off,size in re.findall(r'^(\w+)\s+(CODE|FARCODE)\s+\S+\s+([0-9a-f]{4}):([0-9a-f]{4})\s+([0-9a-f]+)',listing,re.M|re.I):
        seg,off,size=int(seg,16),int(off,16),int(size,16);assert off+size<=65536
        segments.append(dict(name=name,kind=kind,segment=seg,offset=off,bytes=size))
    bank=next(s for s in segments if s['name']=='ASIO_CODE');near=next(s for s in segments if s['name']=='_TEXT')
    assert bank['segment']!=near['segment'] and bank['bytes']==3613 and near['bytes']==0xf360
    for name,_ in entries:assert symbols[name][0]==near['segment'] and symbols[name+'_impl'][0]==bank['segment']
    # All static code precedes the CRT DS/heap, so ordinary PSP shrink retaining
    # DGROUP cannot release this bank. Actual nested EXEC is separately tested.
    ds=re.search(r'^DGROUP\s+([0-9a-f]+):([0-9a-f]+)\s+([0-9a-f]+)',listing,re.M|re.I);assert ds
    dslinear=int(ds[1],16)*16+int(ds[2],16)
    assert bank['segment']*16+bank['offset']+bank['bytes']<=dslinear and int(ds[3],16)==0xd000
    sources=dict(m['sources'])
    for n in ['standalone/check_aspect_serial_bank.py','standalone/omf_imports.py']:sources[n]=sha(ROOT/n)
    for n,hsh in sources.items():assert sha(ROOT/n)==hsh,n
    report=dict(passed=True,bridge_pairs=23,bridges=proof,C_instruction_bytes_identical=3415,near_code_saved=3104,
        segments=segments,data_stack_bytes=0xd000,binary_sha256=m['binary_sha256'],baseline_sha256=baseline['binary_sha256'],
        baseline_object_sha256=sha(old/'serial.o'),banked_object_sha256=sha(base/'serial.o'),sources=sources,
        scope='Every declared serial near/far ABI bridge and far-call relocation, unchanged3415-byte C instructions, actual segment bounds and pre-DGROUP retention. Static placement/ABI proof, not register handback or full application acceptance.')
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS23 bridge pairs,3415 unchanged C bytes,3104 near bytes saved')
if __name__=='__main__':main()
