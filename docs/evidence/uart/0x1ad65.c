/* REA/Ghidra pseudocode; not original source. Address 0x1ad65; Evidence ev_4aaa2dd5ea616abc5036154b07afba10131a2f6e6467ae4117500e44ac13481c. */

void __cdecl16near FUN_1000_ad65(void)

{
  code *pcVar1;
  undefined2 in_BX;
  undefined2 unaff_ES;
  undefined2 unaff_DS;

  pcVar1 = (code *)swi(0x21);
  DAT_1000_acb2 = unaff_DS;
  (*pcVar1)();
  pcVar1 = (code *)swi(0x21);
  DAT_1000_acb4 = in_BX;
  DAT_1000_acb6 = unaff_ES;
  (*pcVar1)();
  return;
}
