/* REA/Ghidra pseudocode; not original source. Address 0x1add6; Evidence ev_80e285c927abbcf06834fc0ff829af349b362cb1b1b27e68b54da60674c44d02. */

uint __cdecl16near FUN_1000_add6(void)

{
  undefined1 uVar1;
  undefined2 in_AX;
  uint uVar2;
  undefined2 unaff_DS;

  uVar1 = in(0x21);
  uVar2 = CONCAT11((char)((uint)in_AX >> 8),uVar1) |
          *(uint *)(*(int *)(*(int *)0x1b84 * 2 + 0x1d08) * 2 + 0x3368);
  out(0x21,(char)uVar2);
  return uVar2;
}
