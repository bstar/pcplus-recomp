#!/usr/bin/env python3
"""Pinned stock Synchronet XMODEM-CRC cancellation reference and unique synthetic payloads."""
import argparse,binascii,hashlib,json,time,subprocess
from pathlib import Path
from audio_synchronet import ROOT,RUNTIME,snapshot,message_bodies,statistics,sha
from synchronet_transfer import BinaryPeer,AREA
from synchronet import ENV
NAME="SXCAN002.BIN"
REFNAME="SXCRF002.BIN"
DESCRIPTION="Synthetic PCPlus audio cancel"

def name_for(slot,reference=False):
 assert type(slot) is int and 1<=slot<=999
 return f'{"SXCRF" if reference else "SXCAN"}{slot:03d}.BIN'

def owned_name(name):
 return name in {name_for(slot,ref) for slot in range(1,1000) for ref in (False,True)}

def payload(name):
 assert owned_name(name)
 return hashlib.sha256(name.encode()).digest()+bytes(((i*73+(i>>8)*19)&255)^0x5a for i in range(11521-32))

def stored_files():
 return {p.name:sha(p) for p in sorted(AREA.iterdir()) if p.is_file()}

def metadata(out,name,label):
 assert owned_name(name) and label in ('before','after')
 path=out/('metadata-'+label+'.js');assert not path.exists()
 path.write_text("var f=new FileBase('pcplab');if(!f.open())throw Error(f.last_error);print('PCPLAB_JSON:'+JSON.stringify(f.get('"+name+"')));f.close();\n")
 r=subprocess.run([str(RUNTIME/'exec/jsexec'),'-n',str(path)],env=ENV(),capture_output=True,text=True,check=True)
 (out/('metadata-'+label+'.stdout')).write_text(r.stdout);(out/('metadata-'+label+'.stderr')).write_text(r.stderr)
 value=json.loads(r.stdout.split('PCPLAB_JSON:',1)[1].splitlines()[0]);(out/('metadata-'+label+'.json')).write_text(json.dumps(value,indent=2)+'\n');return value

