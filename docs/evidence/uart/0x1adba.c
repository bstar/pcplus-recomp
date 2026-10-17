/* REA/Ghidra pseudocode; not original source. Address 0x1adba; Evidence ev_d1a850b16c271f26282d556176df1224daebbfd15953f698f68680d34c52611c. */

undefined1 __cdecl16near FUN_1000_adba(void)

{
  byte bVar1;
  undefined2 unaff_DS;

  FUN_1000_add6();
  bVar1 = in(*(undefined2 *)0x8fee);
  out(*(undefined2 *)0x8fee,bVar1 & 0x7f);
  out(*(undefined2 *)0x901a,0);
  out(*(undefined2 *)0x8ff4,0);
  return 0;
}
