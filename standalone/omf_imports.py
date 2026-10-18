"""Rename selected EXTDEF imports in newly compiled checksummed DOS OMF objects.

Record identities: Open Watcom bld/watcom/h/pcobj.h. EXTDEF name/type-index
layout: bld/wl/c/objomf.c UseSymbols/SkipIdx. Indices and all other records stay
unchanged; compiler-generated near helper calls can then bind to local thunks.
"""
import struct

def records(blob):
    at=0;result=[]
    while at<len(blob):
        if len(blob)-at<3:raise ValueError('Truncated OMF record header')
        kind,length=struct.unpack_from('<BH',blob,at)
        end=at+3+length
        if not length or end>len(blob):raise ValueError('Invalid OMF record extent')
        raw=blob[at:end]
        if sum(raw)&255:raise ValueError('Invalid OMF record checksum')
        result.append((kind,raw[3:-1],raw));at=end
    if not result or result[0][0]!=0x80 or result[-1][0] not in (0x8a,0x8b):
        raise ValueError('Expected one complete OMF object module')
    if any(kind in (0x80,0x8a,0x8b) for kind,_,_ in result[1:-1]):
        raise ValueError('Multiple or prematurely ended OMF modules')
    return result

def externals(payload):
    at=0;result=[]
    while at<len(payload):
        size=payload[at];at+=1
        if not size or at+size>=len(payload):raise ValueError('Invalid EXTDEF name/type extent')
        name=payload[at:at+size];at+=size
        end=at+(2 if payload[at]&128 else 1)
        if end>len(payload):raise ValueError('Truncated EXTDEF type index')
        result.append((name,payload[at:end]));at=end
    return result

def rename_imports(blob,names):
    """Return normalized bytes and occurrence counts; require every requested name.

    Accept one freshly generated module. Only global EXTDEF names are changed.
    Preserve symbol order, type-index bytes, local symbols, fixups and content.
    Invalid/missing requests fail before the caller writes any output.
    """
    encoded={}
    for old,new in names.items():
        old,new=old.encode('ascii'),new.encode('ascii')
        if not old or not new or len(old)>255 or len(new)>255 or old==new:
            raise ValueError('Invalid import rename')
        encoded[old]=new
    if not encoded or len(set(encoded.values()))!=len(encoded) or set(encoded)&set(encoded.values()):
        raise ValueError('Ambiguous import renames')
    parsed=records(blob);counts={old:0 for old in encoded};output=[]
    for kind,payload,raw in parsed:
        if kind!=0x8c:output.append(raw);continue
        changed=False;parts=[]
        for name,index in externals(payload):
            replacement=encoded.get(name,name)
            if name in encoded:counts[name]+=1;changed=True
            elif name in encoded.values():raise ValueError('Replacement import already exists')
            parts.extend((bytes([len(replacement)]),replacement,index))
        if not changed:output.append(raw);continue
        payload=b''.join(parts);length=len(payload)+1
        if length>65535:raise ValueError('Renamed OMF record too large')
        head=struct.pack('<BH',kind,length)+payload
        output.append(head+bytes([-sum(head)&255]))
    if not all(counts.values()):raise ValueError('Requested compiler import missing')
    normalized=b''.join(output);after=records(normalized)
    # Independently enforce the transformation boundary before returning bytes.
    if len(after)!=len(parsed):raise ValueError('OMF record count changed')
    for before,now in zip(parsed,after):
        if before[0]!=now[0] or (before[0]!=0x8c and before[2]!=now[2]):
            raise ValueError('Non-import OMF record changed')
        if before[0]==0x8c:
            wanted=[(encoded.get(name,name),index) for name,index in externals(before[1])]
            if externals(now[1])!=wanted:raise ValueError('Import order/type changed')
    return normalized,{old.decode('ascii'):n for old,n in counts.items()}
