/* REA/Ghidra pseudocode; not original source. Address 0x1ac27; Evidence ev_62315334cf3bcba9fd89f10cd5e7cb2e9e4c61eb289b690877054b2472e81e3a. */

undefined4 __cdecl16near FUN_1000_ac27(uint param_1,int param_2)

{
  byte bVar1;
  undefined1 uVar2;
  undefined2 uVar3;
  undefined2 unaff_DS;

  uVar3 = 1;
  if (param_2 != 1) {
    uVar3 = (undefined2)(0x1c200 / (ulong)param_1);
  }
  bVar1 = in(*(undefined2 *)0x8fee);
  out(*(undefined2 *)0x8fee,bVar1 | 0x80);
  out(*(int *)0x9012,(char)uVar3);
  uVar2 = (undefined1)((uint)uVar3 >> 8);
  out(*(int *)0x9012 + 1,uVar2);
  out(*(undefined2 *)0x8fee,bVar1);
  return CONCAT22(*(undefined2 *)0x8fee,CONCAT11(uVar2,bVar1));
}
