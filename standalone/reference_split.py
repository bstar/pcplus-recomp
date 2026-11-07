"""Derive the resident key classifier and transient reference from one C source.

Only the normal reference event is renamed. The classifier retains the exact
source item ordering, defaults, normalization and feature-selected action code.
No original program or separately maintained action mapping is an input.
"""
import re

def split(source,output):
 text=source.read_text();prefix=text[:text.index('#ifdef CHAT_NEAR_TEXT')]
 table=text[text.index('static const reference_item CONST items[]={'):text.index('#define COUNT')]
 rows=re.findall(r'ITEM\((\w+),(0x[0-9a-f]+),\d+,\d+,(\d+)\)',table)
 assert len(rows)==39 and len({k for n,k,a in rows})==39
 start=text.index('#if defined(',text.index('static word selected'))
 end=text.index('static word length(',start)
 methods=text[start:end]
 unavailable=methods.index('unsigned __far __cdecl command_reference_unavailable(')
 pure=methods[:unavailable]+methods[unavailable:]
 resident=prefix+'\n#define CONST __based(__segname("_CODE"))\n#define UNAVAILABLE 255\ntypedef struct {word key;byte action;} reference_item;\nstatic const reference_item CONST items[]={\n'+',\n'.join('{'+k+','+a+'}'for n,k,a in rows)+'\n};\n#define COUNT (sizeof(items)/sizeof(items[0]))\n'+pure
 bank=text[:start]+methods[:unavailable]+text[end:]
 assert bank.count('unsigned __far __cdecl command_reference_event(')==1
 bank=bank.replace('unsigned __far __cdecl command_reference_event(', 'unsigned __far __cdecl meta_reference_event_far(',1)
 bank=bank.replace('word i;view=frame;', 'word i;view=frame;\n if(event==5 || event==6){if(event==6)refusal=2;draw();return 0;}',1)
 native_help='if(key==0x2c00){refusal=terminal_help_queue(41)?2:0;draw();return 0;}'
 assert bank.count(native_help)==1
 bank=bank.replace(native_help,'if(key==0x2c00)return 0x500;',1)
 path=output/'reference_dispatch.c' ;path.write_text(resident)
 other=output/'reference_bank.c';other.write_text(bank)
 return path,other
