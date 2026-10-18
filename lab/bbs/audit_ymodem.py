#!/usr/bin/env python3
"""Independent passive YMODEM CRC block0/data/EOT/end-header audit.

No protocol bytes are generated. The caller supplies decoded actual wire bytes,
known owned source fixtures and observation-only chunk timestamps.
"""
import binascii,hashlib,re
NAME=re.compile(rb'[A-Za-z0-9!#$%&\x27()@^_`{}~-]{1,8}(?:\.[A-Za-z0-9!#$%&\x27()@^_`{}~-]{1,3})?\Z')
def frame(stream,at):
 if at>=len(stream) or stream[at] not in (1,2):return None
 size=128 if stream[at]==1 else 1024;end=at+size+5
 if end>len(stream) or stream[at+1]^stream[at+2]!=255:return None
 body=stream[at+3:end-2]
 if binascii.crc_hqx(body,0).to_bytes(2,'big')!=stream[end-2:end]:return None
 return dict(offset=at,end=end,number=stream[at+1],size=size,payload=body,sha256=hashlib.sha256(stream[at:end]).hexdigest())
def header(item):
 assert item['number']==0 and item['size']==128,'Expected128-byte CRC block0'
 body=item['payload'];name,sep,rest=body.partition(b'\0');assert sep,'Header has no filename terminator'
 if not name:
  assert body==bytes(128),'Nonzero empty batch header';return None
 assert NAME.fullmatch(name),'Unsafe/nonDOS83 wire filename'
 stem=name.split(b'.')[0].upper();assert stem not in (b'CON',b'AUX',b'PRN',b'NUL',b'CLOCK$') and not re.fullmatch(rb'(?:COM|LPT)[1-9]',stem),'Device filename'
 token=re.split(rb'[\0 ]',rest,maxsplit=1)[0];assert re.fullmatch(rb'[0-9]{1,10}',token),'Missing unsigned decimal length'
 size=int(token);assert size<=0x7ffffbff,'Unsupported oversized source'
 return name.decode('ascii').upper(),size

def audit_batch(stream,expected,minimum=0):
 """expected maps unique DOS83 names to exact known bytes, including empty."""
 expected={name.upper():bytes(data) for name,data in expected.items()};start=None
 for at in range(minimum,min(len(stream),minimum+1048576)):
  candidate=frame(stream,at)
  if not candidate or candidate['number']!=0:continue
  try:h=header(candidate)
  except AssertionError:continue
  if h is None and not expected or h and h[0] in expected and h[1]==len(expected[h[0]]):start=at;break
 assert start is not None,'No valid source-matching YMODEM block0'
 at=start;files=[];events=[];seen=set()
 while True:
  hframe=frame(stream,at);assert hframe,'Missing/malformed next block0'
  h=header(hframe);events.append(dict(kind='end-header' if h is None else 'header',**{k:v for k,v in hframe.items() if k!='payload'}));at=hframe['end']
  if h is None:break
  name,size=h;assert name in expected and name not in seen,'Unexpected/duplicate batch filename';assert size==len(expected[name]),'Wrong declared size';seen.add(name)
  # Exact retransmission of header0 is permitted before data, and audited.
  while True:
   candidate=frame(stream,at)
   if not candidate or candidate['number']!=0:break
   assert candidate['payload']==hframe['payload'],'Changed retransmitted block0'
   events[-1]['retry']=True;events.append(dict(kind='header',**{k:v for k,v in candidate.items() if k!='payload'}));at=candidate['end']
  number=1;accepted=[];previous=None;eots=0
  while at<len(stream) and stream[at] in (1,2):
   item=frame(stream,at);assert item,'Invalid CRC/complement inside file'
   if item['number']==number&255:accepted.append(item);previous=item;number+=1
   else:
    assert previous and item['number']==previous['number'] and item['payload']==previous['payload'],'Invalid sequence/retry'
    events[-1]['retry']=True
   events.append(dict(kind='data',**{k:v for k,v in item.items() if k!='payload'}));at=item['end']
  while at<len(stream) and stream[at]==4:
   eots+=1;events.append(dict(kind='EOT',offset=at,end=at+1));at+=1
  assert 1<=eots<=10,'Missing/excessive per-file EOT'
  data=b''.join(item['payload'] for item in accepted)
  assert data[:size]==expected[name] and len(data)>=size,'Known file bytes differ/truncated'
  assert len(data)-size<=1023 and all(b in (0,26) for b in data[size:]),'Invalid final block padding'
  files.append(dict(name=name,size=size,wire_payload_bytes=len(data),padding_bytes=len(data)-size,sha256=hashlib.sha256(data[:size]).hexdigest(),accepted_blocks=len(accepted),eots=eots,source=data[:size]))
 assert seen==set(expected),'Batch omitted files'
 return dict(start=start,end=at,files=files,events=events)

def audit_controls(batch,opposite,trace,sender,post_time,expect_final_ack_missing=False):
 from test_transfer_dos import timestamp
 other='dos' if sender=='bbs' else 'bbs';events=batch['events'];cursor=0;records=[]
 first_time=timestamp(trace,sender,batch['start'])
 # Require real receiver CRC request before header0, not just a header sender.
 candidates=[i for i,b in enumerate(opposite) if b==67 and timestamp(trace,other,i)<=first_time]
 assert candidates,'Missing initial receiver C request';cursor=candidates[-1]+1
 for index,event in enumerate(events):
  lower=timestamp(trace,sender,event['end']-1)
  upper=timestamp(trace,sender,events[index+1]['offset']) if index+1<len(events) else post_time
  upper=min(upper,lower+16);kind=event['kind'];retry=event.get('retry',False)
  required=([6,67] if kind=='header' else [6])
  if kind=='end-header' and expect_final_ack_missing:
   assert index==len(events)-1 and cursor<len(opposite),'Missing final application boundary'
   when=timestamp(trace,other,cursor)
   assert lower<=when<=upper and opposite[cursor]==27,'Expected actual application ESC instead of final ACK'
   records.append(dict(kind=kind,response=[],final_ACK_confirmed=False,
    application_byte=27,application_offset=cursor))
   continue
  if kind=='EOT':required=[21] if index+1<len(events) and events[index+1]['kind']=='EOT' else [6,67]
  if retry:required=None
  got=[]
  while cursor<len(opposite) and len(got)<(len(required) if required is not None else 1):
   when=timestamp(trace,other,cursor)
   if when>upper:break
   value=opposite[cursor];cursor+=1
   assert when>=lower,('Unmatched early protocol control',kind,value)
   assert value in (6,21,24,67),('Unexpected receiver byte',kind,value)
   got.append(value)
  if required is not None:assert got==required,('Missing/wrong header/data/EOT ACK,C',kind,got,required)
  else:assert not got or got in ([21],[6]),('Unexpected retry response',got)
  records.append(dict(kind=kind,response=got,retry=retry))
 return records

def self_check():
 def packet(n,body):return bytes([1 if len(body)==128 else 2,n,255-n])+body+binascii.crc_hqx(body,0).to_bytes(2,'big')
 expected={'ONE.BIN':b'\0\x1a\xff','EMPTY.BIN':b''}
 def hdr(n,size):return packet(0,(n+b'\0'+str(size).encode()+b'\0').ljust(128,b'\0'))
 wire=hdr(b'ONE.BIN',3)+packet(1,expected['ONE.BIN'].ljust(128,b'\x1a'))+b'\4\4'+hdr(b'EMPTY.BIN',0)+b'\4\4'+packet(0,bytes(128))
 batch=audit_batch(wire,expected);assert len(batch['files'])==2
 controls=b'C\6C\6\x15\6C\6C\x15\6C\6';trace=[];time=1.;trace.append(dict(direction='dos',seconds=0,offset=0,size=1));pos=1
 for event,response in zip(batch['events'],[b'\6C',b'\6',b'\x15',b'\6C',b'\6C',b'\x15',b'\6C',b'\6']):
  trace.append(dict(direction='bbs',seconds=time,offset=event['offset'],size=event['end']-event['offset']))
  trace.append(dict(direction='dos',seconds=time+1,offset=pos,size=len(response)));pos+=len(response);time+=2
 assert audit_controls(batch,controls,trace,'bbs',time+2)
 missing=controls[:-1]+b'\x1b[0m';missing_trace=[dict(t) for t in trace];missing_trace[-1]['size']=4
 assert audit_controls(batch,missing,missing_trace,'bbs',time+2,True)[-1]['final_ACK_confirmed'] is False
 bad=[wire[:-133],wire[:-1]+b'X',wire.replace(b'ONE.BIN',b'CON.BIN',1)]
 for stream in bad:
  try:audit_batch(stream,expected)
  except AssertionError:pass
  else:raise AssertionError('Malformed batch accepted')
 for bytes_ in [controls[:-1],controls.replace(b'\6C',b'\6X',1)]:
  try:audit_controls(batch,bytes_,trace,'bbs',time+2)
  except AssertionError:pass
  else:raise AssertionError('Bad controls accepted')
 print('YMODEM passive auditor:8 positive/negative synthetic groups passed')

def server_audit(server,values):
 """Official metadata APIs and exact declared-length installed source bytes.
 Does not connect a BBS session or modify server metadata/configuration.
 """
 import json,subprocess,tempfile,os
 from pathlib import Path
 from test_ymodem_dos import parse_files,ROOT
 expected={name:path.read_bytes() for name,path in parse_files(values).items()};checks={};records={}
 if server=='enigma':
  import enigma
  js="""const c=require('./core/oputil/oputil_common');c.initConfigAndDatabases(e=>{if(e)throw e;const F=require('./core/file_entry');F.findByFileNameWildcard(process.argv[1],(e,rows)=>{if(e)throw e;console.log(JSON.stringify(rows.map(f=>({fileId:f.fileId,fileName:f.fileName,areaTag:f.areaTag,storageTag:f.storageTag,filePath:f.filePath,fileSha256:f.fileSha256,meta:f.meta}))));process.exit(0);});});"""
  for name,data in expected.items():
   rows=json.loads(subprocess.check_output(['node','-e',js,name],cwd=enigma.SOURCE,text=True));assert len(rows)==1,('Expected one official entry',name)
   m=rows[0];path=Path(m['filePath']);records[name]=m
   checks[name+'_owned_area']=m['areaTag']=='pcplus_transfer' and m['storageTag']=='pcplus_transfer' and path.resolve().parent==(enigma.SOURCE/'file_base/pcplus_transfer').resolve()
   checks[name+'_physical_exact']=path.is_file() and path.read_bytes()==data
   checks[name+'_metadata_exact']=m['fileName'].upper()==name and m['meta']['byte_size']==len(data) and m['fileSha256']==hashlib.sha256(data).hexdigest()
  commit=enigma.COMMIT
 else:
  import synchronet
  parent=ROOT/'build/bbs-lab/ymodem-audits';parent.mkdir(parents=True,exist_ok=True)
  with tempfile.TemporaryDirectory(dir=parent) as directory:
   program=Path(directory)/'audit.js'
   program.write_text("var f=new FileBase('pcplab');if(!f.open())throw Error(f.last_error);var o={};"+''.join("o["+json.dumps(n)+"]=f.get("+json.dumps(n)+");" for n in expected)+"print('YM_JSON:'+JSON.stringify(o));f.close();")
   raw=subprocess.check_output([str(synchronet.RUNTIME/'exec/jsexec'),'-n',str(program)],env=synchronet.ENV(),text=True,stderr=subprocess.PIPE)
  records=json.loads(raw.split('YM_JSON:',1)[1].splitlines()[0]);area=synchronet.RUNTIME/'data/dirs/pcplab'
  for name,data in expected.items():
   path=area/name;m=records[name];checks[name+'_physical_exact']=path.is_file() and path.read_bytes()==data
   checks[name+'_metadata_exact']=bool(m) and m['name'].upper()==name and m['size']==len(data) and m['crc16']==binascii.crc_hqx(data,0) and m['crc32']==binascii.crc32(data)&0xffffffff and m['sha1']==hashlib.sha1(data).hexdigest() and m['md5']==hashlib.md5(data).hexdigest()
  commit=synchronet.COMMIT
 return dict(passed=all(checks.values()),checks=checks,metadata=records,server_commit=commit,scope='Official FileEntry/FileBase read APIs plus exact owned source bytes and declared lengths; no padded-prefix acceptance, direct SQL or BBS connection.')

if __name__=='__main__':
 import argparse,json,sys
 if len(sys.argv)==1 or '--self-check' in sys.argv:self_check()
 else:
  parser=argparse.ArgumentParser();parser.add_argument('--server',choices=['synchronet','enigma'],required=True);parser.add_argument('--file',action='append',required=True);args=parser.parse_args()
  try:result=server_audit(args.server,args.file)
  except Exception as error:result=dict(passed=False,error=type(error).__name__+': '+str(error))
  print(json.dumps(result,indent=2));raise SystemExit(0 if result['passed'] else 1)
