#!/usr/bin/env python3
"""Record stock editor successes and the immediate ENiGMA failure separately."""
import argparse,contextlib,io,json,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'standalone'))
from build_aspect_process import sha
from check_editor_dos import audit

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--synchronet',required=True);p.add_argument('--enigma-buffered',required=True)
    p.add_argument('--enigma-immediate',required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();binary=ROOT/'build/terminal-traps/TERMINAL.EXE';runs=[]
    source=ROOT/'build/bbs-lab/enigma/source'
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=source,text=True).strip()
    stock={}
    for n in ['core/client.js','core/multi_line_edit_text_view.js']:
        assert (source/n).read_bytes()==subprocess.check_output(['git','show','HEAD:'+n],cwd=source)
        stock[n]=sha(source/n)
    for name,label,delay in [('synchronet',a.synchronet,0),('enigma',a.enigma_buffered,30),('enigma',a.enigma_immediate,0)]:
        assert re.fullmatch(r'[A-Za-z0-9_-]+',label)
        folder=ROOT/'build/bbs-lab/results'/name/label
        run=json.loads((folder/'result.json').read_text())
        assert run['passed'] and all(run['checks'].values())
        assert run['binary_sha256']==sha(binary) and run['modem_packet_delay_ms']==delay
        assert {k:run['serial'][k] for k in ['com','baud','line','flow']}==dict(com=2,baud=19200,line='8N1',flow='HARD')
        # Re-evaluate captured wire/display and session-bounded stock server
        # records through the existing strict semantic auditor.
        with contextlib.redirect_stdout(io.StringIO()):
            passed=audit(name,label,disconnect=name=='enigma')
        semantic=json.loads((folder/'semantic-audit.json').read_text())
        assert semantic['passed']==passed and semantic['checks']['stock_editor_entered']
        assert semantic['checks']['all_exercised_keys_emitted']
        assert semantic['checks']['no_post_saved' if name=='enigma' else 'draft_aborted']
        if name=='synchronet' or delay:assert passed
        if name=='enigma':assert semantic['authority']['stock_server']
        files=['result.json','semantic-audit.json','dosbox.conf','serial-received.bin','display.bin','SCREEN.BIN','BEFORE.BIN','AFTER.BIN']
        if name=='enigma':files+=['server-log-start.json','server-session.jsonl']
        runs.append(dict(server=name,label=label,modem_packet_delay_ms=delay,editor_passed=passed,
            checks=semantic['checks'],observed_key_wire=semantic['observed_key_wire'],
            evidence={str((folder/n).relative_to(ROOT)):sha(folder/n) for n in files}))
    files=['lab/bbs/test_dos.py','lab/bbs/editor_dos_probe.py','lab/bbs/check_editor_dos.py','lab/bbs/modem.py',
        'lab/bbs/editor-recipes.json','lab/bbs/synchronet-editor-recipe.json']
    receipt=dict(recorded=True,binary_sha256=sha(binary),runs=runs,
        immediate_ENiGMA_passed=runs[2]['editor_passed'],stock_ENiGMA_commit=commit,stock_source_sha256=stock,
        auditor_sha256=sha(Path(__file__)),audit_sources={n:sha(ROOT/n) for n in files},
        scope='Keyboard trap-enabled client, stock local editors, unsaved synthetic drafts. Synchronet immediate and ENiGMA buffered passes remain distinct from immediate ENiGMA outcome. No mouse-BBS, physical modem, multiline editing, transfer or door acceptance claim.')
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(receipt,indent=2)+'\n')
    print('Editor evidence recorded; immediate ENiGMA passed:',receipt['immediate_ENiGMA_passed'])

if __name__=='__main__':main()
