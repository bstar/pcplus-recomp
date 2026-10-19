"""Prompt-driven source login for the isolated synthetic loclab account only."""
def source(file_info=False,enumeration=False,file_attributes=False,file_times=False):
 file_attributes=file_attributes or file_times
 enumeration=enumeration or file_attributes
 file_info=file_info or enumeration
 probe=('fopen 4 \"FILECHK.TMP\" \"wb\"\nfputs 4 \"proof\"\nfclose 4\n'
  'getfsize \"FILECHK.TMP\" probe_size\nif failure\nexit\nendif\n'
  'if probe_size != 5L\nexit\nendif\nrename \"FILECHK.TMP\" \"FILECHK.BIN\"\n'
  'if failure\nexit\nendif\nisfile \"FILECHK.BIN\"\nif failure\nexit\nendif\n') if file_info else ''
 enum_probe=('findfirst "FILECHK.BIN"\nif found\nfopen 4 "FIND.LOG" "wb"\n'
  'fputs 4 $FILENAME\nfputs 4 "|"\nfputs 4 $FNAME\nfputs 4 "|"\n'
  'fputs 4 $FEXT\nfputs 4 "|"\nltoa $FSIZE probe_number\nfputs 4 probe_number\nfclose 4\n'
  'else\nexit\nendif\nfindnext\nif found\nexit\nendif\n') if enumeration else ''
 attr_probe=('setfattr "FILECHK.BIN" "RHS"\nif failure\nexit\nendif\n'
  'getfattr "FILECHK.BIN" probe_attrs\nif failure\nexit\nendif\nstrcmp probe_attrs "RHS"\n'
  'if failure\nexit\nendif\nfopen 4 "ATTR.LOG" "wb"\nfputs 4 probe_attrs\nfputs 4 "|"\n'
  'setfattr "FILECHK.BIN" ""\nif failure\nexit\nendif\ngetfattr "FILECHK.BIN" probe_attrs\n'
  'if failure\nexit\nendif\nstrcmp probe_attrs $NULL\nif failure\nexit\nendif\n'
  'fputs 4 probe_attrs\nfclose 4\n') if file_attributes else ''
 time_probe=('setfdate "FILECHK.BIN" "03-07-93"\nsetftime "FILECHK.BIN" "13:45"\n'
  'getfdate "FILECHK.BIN" probe_date\nif failure\nexit\nendif\ngetftime "FILECHK.BIN" probe_time\n'
  'if failure\nexit\nendif\nstrcmp probe_date " 3-07-93"\nif failure\nexit\nendif\n'
  'strcmp probe_time "13:45"\nif failure\nexit\nendif\nfopen 4 "TIME.LOG" "wb"\n'
  'fputs 4 probe_date\nfputs 4 "|"\nfputs 4 probe_time\nfclose 4\n') if file_times else ''
 return ('integer cancel_done,scan_done\n'+('long probe_size\n' if file_info else '')+('string probe_number\n' if enumeration else '')+('string probe_attrs\n' if file_attributes else '')+('string probe_date,probe_time\n' if file_times else '')+'proc main\ninteger attempts\n'+probe+enum_probe+attr_probe+time_probe+
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
