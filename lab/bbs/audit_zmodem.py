#!/usr/bin/env python3
"""Independent passive ZMODEM/ZedZap wire audit. Never generates peer replies.
Input is decoded observed stream bytes, owned expected files and chunk times.
No maintained C codec/parser or session engine is an audit dependency.
"""
import binascii,hashlib,zlib
FLOW={17,19,145,147}
def crc(data,fmt):
 return zlib.crc32(data).to_bytes(4,'little') if fmt==67 else binascii.crc_hqx(data,0).to_bytes(2,'big')
def octet(stream,at,terminator=False):
 while at<len(stream) and stream[at] in FLOW:at+=1
 assert at<len(stream),'Truncated encoded byte'
 value=stream[at];at+=1
 if value!=24:return value,at,False
 while at<len(stream) and stream[at] in FLOW:at+=1
 assert at<len(stream),'Truncated escape'
 suffix=stream[at];at+=1
 if terminator and suffix in range(104,108):return suffix,at,True
 if suffix in (108,109):return (127 if suffix==108 else 255),at,False
 assert suffix&96==64,('Malformed quote',suffix,at)
 return suffix^64,at,False
def header(stream,at):
 start=at
 assert at<len(stream) and stream[at]==42
 while at<len(stream) and stream[at]==42:at+=1
 assert stream[at:at+1]==b'\x18';at+=1
 assert at<len(stream);fmt=stream[at];at+=1;assert fmt in (65,66,67)
 if fmt==66:
  text=stream[at:at+14];assert len(text)==14
  raw=bytes.fromhex(text.decode('ascii'));at+=14
  if stream[at:at+1]==b'\r':at+=1
  assert at<len(stream) and stream[at]&127==10;at+=1
  if at<len(stream) and stream[at] in FLOW:at+=1
 else:
  raw=bytearray()
  for _ in range(9 if fmt==67 else 7):value,at,_=octet(stream,at);raw.append(value)
 raw=bytes(raw);assert raw[5:]==crc(raw[:5],fmt),'Header CRC mismatch'
 return dict(offset=start,end=at,format=fmt,type=raw[0],position=int.from_bytes(raw[1:5],'little'),header=raw[:5].hex())
def scan(stream,minimum=0):
 at=minimum
 while at<len(stream):
  at=stream.find(b'*',at)
  if at<0:return
  try:item=header(stream,at)
  except (AssertionError,ValueError,UnicodeError):at+=1;continue
  yield item;at=item['end']
def packet(stream,at,fmt):
 start=at;data=bytearray()
 while True:
  v,at,end=octet(stream,at,True)
  if end:break
  data.append(v);assert len(data)<=8192,'Packet larger than ZedZap limit'
 actual=bytearray()
 for _ in range(4 if fmt==67 else 2):value,at,_=octet(stream,at);actual.append(value)
 assert bytes(actual)==crc(bytes(data)+bytes([v]),fmt),'Data CRC mismatch'
 crc_end=at
 if v==107 and at<len(stream) and stream[at] in FLOW:at+=1
 return dict(offset=start,end=at,crc_end=crc_end,ending=v,length=len(data),payload=bytes(data),sha256=hashlib.sha256(stream[start:at]).hexdigest())
def metadata(data):
 name,sep,rest=data.partition(b'\0');assert sep and name and b'\0' in rest
 length=rest.split(b'\0',1)[0].split(b' ',1)[0];assert length.isdigit()
 return name.decode('ascii').upper(),int(length)
def audit_batch(stream,expected,minimum=0):
 expected={n.upper():bytes(v) for n,v in expected.items()};first=None
 for h in scan(stream,minimum):
  if h['type']!=4:continue
  try:
   p=packet(stream,h['end'],h['format']);name,size=metadata(p['payload'])
   if name in expected and size==len(expected[name]):first=h;break
  except (AssertionError,ValueError,UnicodeError):pass
 assert first,'No validated source-matching ZFILE'
 at=first['offset'];files=[];current=None;events=[];accepted=0;file_start=None;position=0;seen=set();finish=None;eof=None;closing=None
 def close_file():
  nonlocal current,eof
  assert current is not None and eof is not None,'File never reached a verified final EOF'
  files.append(dict(name=current,length=accepted,start=file_start,end=eof,source=expected[current],sha256=hashlib.sha256(expected[current]).hexdigest(),packets=parts))
  seen.add(current);current=None;eof=None
 while at<len(stream):
  h=next(scan(stream,at),None);assert h,'Missing complete protocol header';events.append(dict(kind='header',**h));at=h['end']
  if closing is not None:assert h['type'] in (7,8),'File traffic after finishing began'
  if h['type']==4:
   p=packet(stream,at,h['format']);at=p['end'];name,size=metadata(p['payload'])
   assert name in expected and size==len(expected[name]) and p['ending']==107
   if current is not None and current!=name:close_file()
   if current is None:
    assert name not in seen;current=name;accepted=0;file_start=h['offset'];parts=[]
   else:assert name==current,'Changed active offer'
   events.append(dict(kind='metadata',name=name,**{k:v for k,v in p.items() if k!='payload'}))
  elif h['type']==10:
   assert current is not None;position=h['position'];assert position<=accepted,'Unverified offset gap'
   # A windowed sender can retransmit already verified bytes after its EOF
   # while the receiver's ZRINIT is in flight. Exact replay within the accepted
   # range does not revoke that EOF. The packet loop still checks every byte,
   # and audit_controls separately requires the receiver's completion reply.
   while True:
    p=packet(stream,at,h['format']);at=p['end'];data=p.pop('payload')
    assert data==expected[current][position:position+len(data)],'Transferred bytes differ'
    assert position+len(data)<=len(expected[current]);p['verified_before']=accepted
    p['replayed']=bool(data) and position+len(data)<=accepted
    accepted=max(accepted,position+len(data));position+=len(data)
    p['position']=position;p['after_eof']=eof is not None;parts.append(p);events.append(dict(kind='data',name=current,**p))
    if p['ending'] in (104,107):break
  elif h['type']==11:
   assert current is not None
   assert h['position']==accepted==len(expected[current]),'Unverified/mismatched EOF'
   # EOF may be rejected by the receiver. Keep the active file until a later
   # offer/finish, and audit every subsequent retransmitted source byte.
   eof=at
  elif h['type']==8 or (h['type']==7 and closing is not None):
   if current is not None:close_file()
   assert current is None and seen==set(expected)
   # SEXYZ get_zfin alternates ZFIN/ZABORT while awaiting the receiver's ZFIN.
   # An initial abort is never success; completion still requires literal OO
   # and audit_controls requires the receiver's ZFIN after this first ZFIN.
   if closing is None:closing=h['offset']
   if stream[at:at+2]==b'OO':finish=dict(offset=closing,last_header_offset=h['offset'],end=at+2);at+=2;break
  else:assert h['type'] in (0,1,3,6,9,13,14),('Unexpected sender header',h['type'])
 assert finish and seen==set(expected),'Incomplete files or missing ZFIN/OO'
 return dict(start=first['offset'],end=at,files=files,events=events,finish=finish)
def audit_controls(audit,opposite,trace,sender,post_time,unused=False):
 from test_transfer_dos import timestamp
 assert not unused
 other='dos' if sender=='bbs' else 'bbs';headers=list(scan(opposite));records=[]
 def match(kind,pos,lower,upper):
  selected=[h for h in headers if h['type']==kind and (pos is None or h['position']==pos) and lower<=timestamp(trace,other,h['offset'])<=upper]
  assert selected,('Missing opposite header',kind,pos,lower,upper)
  result=selected[0];records.append(dict(type=kind,position=result['position'],offset=result['offset'],seconds=timestamp(trace,other,result['offset'])));return result
 for f in audit['files']:
  lower=timestamp(trace,sender,f['start']);upper=timestamp(trace,sender,f['end']-1)
  match(9,0,lower,upper)
  for p in f['packets']:
   if p.get('after_eof'):
    # Already committed, byte-exact replay may still be in flight. Require
    # the observed completion reply before that replay packet finishes;
    # an ACK to a closed file is not a required receiver response.
    match(1,None,timestamp(trace,sender,f['end']-1),timestamp(trace,sender,p['crc_end']-1))
    continue
   if p['ending'] in (106,107):
    lower=timestamp(trace,sender,p['crc_end']-1)
    # A slow receiver may ACK after a timeout-driven retransmission starts.
    # Require a reply before new forward data or EOF, not before replay of
    # bytes whose CRC/source range has already been verified.
    ceiling=max(p['position'],p.get('verified_before',0))
    forward=[q['offset'] for q in f['packets'] if q['offset']>=p['end'] and q['position']>ceiling]
    forward += [e['offset'] for e in audit['events'] if e['offset']>=p['end'] and e['kind']=='header' and e['type'] in (4,8,11)]
    upper=min(post_time,timestamp(trace,sender,min(forward))) if forward else post_time
    if p.get('replayed'):
     original=next(q for q in f['packets'] if q['offset']<p['offset'] and q['position']>=p['position'])
     lower=timestamp(trace,sender,original['crc_end']-1)
    # ZCRCQ requests an asynchronous/cumulative ACK. It need not precede the
    # next subpacket. ZCRCW still requires its exact boundary before continuing.
    if p['ending']==106:upper=post_time
    def valid_ack(h):
     if p.get('replayed') and h['type'] in (3,9):
      when=timestamp(trace,other,h['offset'])
      verified=max((q['position'] for q in f['packets'] if timestamp(trace,sender,q['crc_end']-1)<=when),default=0)
      return p['position']<=h['position']<=verified
     if h['type']!=3:return False
     if p['ending']==107:return h['position']==p['position']
     when=timestamp(trace,other,h['offset'])
     transmitted=max((q['position'] for q in f['packets'] if timestamp(trace,sender,q['crc_end']-1)<=when),default=0)
     return p['position']<=h['position']<=transmitted
    candidates=[h for h in headers if lower<=timestamp(trace,other,h['offset'])<=upper and
                (valid_ack(h) or (h['type']==9 and h['position']<=p['position']-p['length']))]
    assert candidates,('No ACK or verified-position recovery for subpacket',p['offset'],p['position'])
    item=candidates[0];records.append(dict(type=item['type'],position=item['position'],offset=item['offset'],seconds=timestamp(trace,other,item['offset']),recovery=item['type']==9))
  match(1,None,timestamp(trace,sender,f['end']-1),post_time)
 # A sender can emit OO even when its get_zfin retry budget expires. Require
 # the actual receiver's ZFIN before those OO bytes, not merely before a later
 # menu key. Exact stored bytes alone do not confirm the final handshake.
 match(8,0,timestamp(trace,sender,audit['finish']['offset']),timestamp(trace,sender,audit['end']-2))
 return records
def self_check():
 # Literal primary CRC vectors, with independent Python reference functions.
 assert binascii.crc_hqx(b'123456789',0)==0x31c3 and zlib.crc32(b'123456789')==0xcbf43926
 print('Independent ZMODEM CRC vectors pass; no session executed')
