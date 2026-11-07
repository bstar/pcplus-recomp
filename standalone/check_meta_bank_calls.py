#!/usr/bin/env python3
"""Reject direct near calls/jumps whose linked target belongs to another CS."""
import hashlib,re,subprocess
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def audit(out,objects):
 listing=(out/'METAEDIT.map').read_text()
 symbols={n:(int(s,16),int(o,16)) for s,o,n in re.findall(r'^([0-9a-f]+):([0-9a-f]+)\*?\s+(\w+)\s*$',listing,re.M|re.I)}
 segments={n:int(s,16) for n,s in re.findall(r'^(\w+)\s+\w+\s+\w+\s+([0-9a-f]+):0000\s+[0-9a-f]+',listing,re.M|re.I)}
 reports={};edges=[]
 def check(edge,targets):
  source,target,context=edge
  assert target in targets and targets[target][0]==segments[source],context
 for obj in objects:
  dis=out/(obj.stem+'-calls.dis');subprocess.run(['wdis','-e','-l='+str(dis),str(obj)],check=True,stdout=subprocess.DEVNULL)
  near=far=indirect=0
  for chunk in dis.read_text().split('\nSegment: ')[1:]:
   name=chunk.split()[0]
   labels=set(re.findall(r'^[0-9a-f]{4}\s+([\w$]+):\s*$',chunk,re.M|re.I))
   for m in re.finditer(r'^([0-9a-f]{4})\s+((?:[0-9a-f]{2}\s+)+)(call|jmp)\s+(\S+)',chunk,re.M|re.I):
    address,encoded,operation,target=m.groups();opcode=encoded.split()[0].upper()
    if opcode in ('E8','E9','EB'):
     near+=1
     if target not in labels:
      edge=(name,target,(obj.name,address,operation,target,'near transfer crosses/unresolved CS'))
      check(edge,symbols);edges.append(edge)
    elif opcode in ('9A','EA'):
     far+=1;assert target in labels or target in symbols,(obj.name,target,'unresolved far transfer')
    else:indirect+=1
  reports[obj.name]=dict(near=near,far=far,indirect=indirect,object_sha256=sha(obj),listing_sha256=sha(dis))
 # Alter only linked target placement; feed the same actual near-call edges
 # through the baseline verifier. No corrupted executable is constructed/run.
 challenges=[]
 for target in ('_meta_bank_paths','meta_bank_fmemcpy_','_capture_fs_canonical','_dos_open_'):
  edge=next(e for e in edges if e[1]==target)
  bad=dict(symbols);bad[target]=(symbols[target][0]^0x1000,symbols[target][1])
  try:check(edge,bad)
  except AssertionError:challenges.append(target)
  else:raise AssertionError(('invalid near target admitted',target))
 assert len(challenges)==4

 return dict(passed=True,objects=reports,cross_CS_challenges_rejected=challenges,scope=__doc__+' Indirect calls are counted, not a target-lifetime proof; DOS runtime gates remain necessary.')
