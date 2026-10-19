"""Prompt-driven source login for the isolated synthetic loclab account only."""
def source():
 return ('integer cancel_done,scan_done\nproc main\ninteger attempts\n'
 'fopen 5 "LOGIN.LOG" "wb"\nfputs 5 "START"\n'
 'cancel_done=0\nscan_done=0\nattempts=0\n'
 'waitfor "lOGIN" 25\ntransmit "^M"\n'
 'waitfor "PASSW_" 10\nwaitquiet 1 10\ntransmit "loclab^M"\nwaitquiet 1 10\n'
 'when 0 "eyboard" call advance\nwhen 1 "nAH" call cancel\n'
 'when 2 "erform global newscan" call decline\ntransmit "LoC-Lab-2026!^M"\nfputs 5 "AUTH"\n'
 'while attempts < 60\nwaitfor "Main Menu" 1\nif waitfor\nexitwhile\nendif\nattempts+=1\nendwhile\n'
 'if waitfor\nfputs 5 "READY"\nelse\nfputs 5 "TIMEOUT"\nendif\n'
 'cwhen 0\ncwhen 1\ncwhen 2\nendproc\n'
 'proc advance\ncwhen 0\nwaitquiet 1 5\nwhen 0 "eyboard" call advance\ntransmit "^M"\nendproc\n'
 'proc cancel\nif cancel_done==0\ncancel_done=1\ncwhen 1\nwaitquiet 1 5\ntransmit "^["\nendif\nendproc\n'
 'proc decline\nif scan_done==0\nscan_done=1\ncwhen 2\nwaitquiet 1 5\ntransmit "N"\nendif\nendproc\n')
