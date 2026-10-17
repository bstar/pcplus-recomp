/* REA/Ghidra pseudocode; not original source. Address 0x1ad93; Evidence ev_5cdcd9ae0eaf088e7d276fb5d0b8fc5bd7de1e4534e5988fcca0ba028a6ec798. */

void __cdecl16near FUN_1000_ad93(void)

{
  byte bVar1;
  undefined1 in_CL;
  undefined2 unaff_DS;

  do {
    bVar1 = in(*(undefined2 *)0x900a);
  } while ((bVar1 & 0x20) == 0);
  out(*(undefined2 *)0x9012,in_CL);
  return;
}
