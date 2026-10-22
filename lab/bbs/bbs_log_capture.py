"""Checked Bunyan numeric rename-rotation journal ranges.

No copy-truncate, compressed/deleted intermediate history or power-loss claim.
Missing/ambiguous identity, changed prefix and malformed records reject.
"""
import hashlib,json,os
from pathlib import Path


class CaptureError(ValueError):pass


def digest(data):return hashlib.sha256(data).hexdigest()


def begin(log,marker):
 log=Path(log).resolve();marker=Path(marker)
 with log.open('rb') as f:
  stat=os.fstat(f.fileno());prefix=f.read()
 # A writer may be between writes of one record. Include its eventual whole
 # record in our range rather than starting midway through its JSON bytes.
 offset=prefix.rfind(b'\n')+1;prefix=prefix[:offset]
 info=dict(path=str(log),device=stat.st_dev,inode=stat.st_ino,offset=offset,prefix_sha256=digest(prefix))
 with marker.open('x') as f:f.write(json.dumps(info,indent=2)+'\n')
 return info


def catalog(log):
 paths={-1:log}
 for path in log.parent.glob(log.name+'.*'):
  suffix=path.name[len(log.name)+1:]
  if not suffix.isdecimal():continue
  rank=int(suffix)
  if rank in paths:raise CaptureError('Ambiguous rotation rank')
  paths[rank]=path
 result={}
 for rank,path in paths.items():
  if path.is_symlink() or not path.is_file():raise CaptureError('Journal path is not a regular independent file')
  s=path.stat();result[rank]=(path,s.st_dev,s.st_ino)
 return result


def collect(marker,output):
 marker=Path(marker);output=Path(output);info=json.loads(marker.read_text());log=Path(info['path'])
 initial=catalog(log);matching=[rank for rank,(_,dev,ino) in initial.items() if (dev,ino)==(info['device'],info['inode'])]
 if len(matching)!=1:raise CaptureError('Initial journal identity missing or ambiguous')
 first=matching[0];ranks=[-1] if first==-1 else list(range(first,-1,-1))+[-1]
 if any(rank not in initial for rank in ranks):raise CaptureError('Missing intermediate rotated journal')
 segments=[];rows=[]
 for index,rank in enumerate(ranks):
  path,dev,ino=initial[rank]
  with path.open('rb') as f:
   s=os.fstat(f.fileno())
   if (s.st_dev,s.st_ino)!=(dev,ino):raise CaptureError('Journal changed during open')
   data=f.read(s.st_size)
  start=info['offset'] if index==0 else 0
  if len(data)!=s.st_size or start>len(data):raise CaptureError('Truncated journal range')
  if index==0 and digest(data[:start])!=info['prefix_sha256']:raise CaptureError('Initial journal prefix changed')
  body=data[start:]
  if body and not body.endswith(b'\n'):raise CaptureError('Incomplete journal record')
  try:decoded=[json.loads(line) for line in body.splitlines() if line.strip()]
  except (ValueError,UnicodeError) as exc:raise CaptureError('Malformed journal record') from exc
  if any(not isinstance(row,dict) for row in decoded):raise CaptureError('Journal record is not an object')
  rows.extend(decoded);segments.append(dict(path=str(path),device=dev,inode=ino,start=start,end=len(data),sha256=digest(body),body=body))
 if catalog(log)!=initial:raise CaptureError('Journal rotation changed during collection; retry from the same marker')
 output.mkdir(exist_ok=False)
 for i,segment in enumerate(segments):
  name=f'segment-{i:04}.jsonl';(output/name).write_bytes(segment.pop('body'));segment['capture']=name
 report=dict(passed=True,boundary=info,boundary_sha256=digest(marker.read_bytes()),segments=segments,records=len(rows),
  scope=__doc__)
 (output/'result.json').write_text(json.dumps(report,indent=2)+'\n')
 return rows
