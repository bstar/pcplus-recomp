/* REA/Ghidra pseudocode; not original source. Address 0x1aa65; Evidence ev_50e6c33585e94bcec4c6154d1018002c075084ecf51a922423b33f289963f368. */

undefined4 __cdecl16near FUN_1000_aa65(void)

{
  undefined2 uVar1;
  undefined2 in_AX;
  uint uVar2;
  undefined2 in_DX;
  undefined2 extraout_DX;
  undefined1 *puVar3;
  undefined2 unaff_DS;

  if (*(int *)0x8e20 == 0) {
    return CONCAT22(in_DX,0xffff);
  }
  puVar3 = (undefined1 *)*(undefined2 *)0x7e1b;
  uVar2 = CONCAT11((char)((uint)in_AX >> 8),*puVar3) & *(uint *)0x8e22;
  *(int *)0x8e20 = *(int *)0x8e20 + -1;
  if (puVar3 == (undefined1 *)*(undefined2 *)0x7e1d) {
    puVar3 = (undefined1 *)0x7e20;
  }
  else {
    puVar3 = puVar3 + 1;
  }
  *(undefined2 *)0x7e1b = puVar3;
  if (*(int *)0x3354 == 0) {
    if (((*(int *)0x3356 != 0) && (*(char *)0x7e18 != '\0')) && (*(int *)0x8e20 < 0x81)) {
      uVar1 = *(undefined2 *)0x8ff4;
      out(uVar1,0xb);
      *(undefined1 *)0x7e18 = 0;
      return CONCAT22(uVar1,uVar2);
    }
  }
  else if ((*(char *)0x7e17 == '\x01') && (*(int *)0x8e20 < 0x81)) {
    *(undefined1 *)0x7e17 = 0;
    FUN_1000_ad93();
    return CONCAT22(extraout_DX,uVar2);
  }
  return CONCAT22(in_DX,uVar2);
}
