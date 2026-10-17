/* REA/Ghidra pseudocode; not original source. Address 0x1adeb; Evidence ev_0fa5b1b8892409d20453568c31e251e41ee1cde81f2c6e8845289782f54ca019. */

undefined4 __cdecl16near FUN_1000_adeb(void)

{
  undefined1 uVar1;
  undefined2 in_AX;
  uint uVar2;
  undefined2 unaff_DS;

  out(*(undefined2 *)0x8ff4,0xb);
  in(*(undefined2 *)0x8ffe);
  in(*(undefined2 *)0x900a);
  in(*(undefined2 *)0x9012);
  uVar1 = in(*(undefined2 *)0x8fee);
  uVar2 = CONCAT11((char)((uint)in_AX >> 8),uVar1) & 0xff7f;
  out(*(undefined2 *)0x8fee,(char)uVar2);
  out(*(undefined2 *)0x901a,1);
  uVar1 = in(0x21);
  uVar2 = CONCAT11((char)(uVar2 >> 8),uVar1) &
          *(uint *)(*(int *)(*(int *)0x1b84 * 2 + 0x1d08) * 2 + 0x3358);
  out(0x21,(char)uVar2);
  return CONCAT22(*(undefined2 *)0x901a,uVar2);
}
