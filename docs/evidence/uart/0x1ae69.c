/* REA/Ghidra pseudocode; not original source. Address 0x1ae69; Evidence ev_83ec103e35e2599b1652cb2f2f6d65a07689bf1f6626a472ff0e882710d2309a. */

undefined4 __cdecl16near FUN_1000_ae69(void)

{
  byte bVar1;
  undefined1 uVar2;
  undefined2 in_AX;
  uint uVar3;
  undefined2 unaff_DS;

  out(0x21,*(undefined1 *)0x9024);
  bVar1 = in(*(undefined2 *)0x8fee);
  out(*(undefined2 *)0x8fee,bVar1 | 0x80);
  out(*(int *)0x9012,*(undefined1 *)0x9044);
  out(*(int *)0x9012 + 1,*(undefined1 *)0x904b);
  uVar2 = in(*(undefined2 *)0x8fee);
  uVar3 = CONCAT11((char)((uint)in_AX >> 8),uVar2) & 0xff7f;
  out(*(undefined2 *)0x8fee,(char)uVar3);
  out(*(undefined2 *)0x8ff4,*(undefined1 *)0x9034);
  out(*(undefined2 *)0x901a,*(undefined1 *)0x9040);
  out(*(undefined2 *)0x8fee,*(undefined1 *)0x902c);
  return CONCAT22(*(undefined2 *)0x8fee,CONCAT11((char)(uVar3 >> 8),*(undefined1 *)0x902c));
}
