/* REA/Ghidra pseudocode; not original source. Address 0x1e3f2; Evidence ev_eee26e941827e00c190eae7fd9e329a0be13e93287e5be2fd0722da4241d6207. */

undefined2 __cdecl16near FUN_1e3b_0042(void)

{
  int iVar1;
  undefined2 uVar2;
  int iVar3;
  undefined2 unaff_SS;
  undefined2 unaff_DS;
  undefined1 local_22 [32];

  iVar3 = 0;
  while( true ) {
    while( true ) {
      iVar1 = FUN_1000_5ca0();
      if ((iVar1 < 0x30) || (0x39 < iVar1)) break;
      local_22[iVar3] = (char)iVar1;
      iVar3 = iVar3 + 1;
    }
    if ((iVar1 == 0x3b) && (iVar3 == 0)) break;
    if ((iVar1 != 0) && (iVar1 != 0x7f)) {
      if (iVar1 == 0x1b) {
        FUN_1000_abde();
        return 0x41;
      }
      if ((iVar1 < 0) || (0x1a < iVar1)) goto LAB_1e3b_009b;
      FUN_1000_0610(iVar1);
    }
  }
  local_22[0] = 0x30;
  iVar3 = 1;
LAB_1e3b_009b:
  if (iVar3 != 0) {
    local_22[iVar3] = 0;
    uVar2 = thunk_FUN_1000_a7ce(local_22);
    *(undefined2 *)(*(int *)0xcb5c * 2 + -0x34c4) = uVar2;
    *(int *)0xcb5c = *(int *)0xcb5c + 1;
LAB_1e45_0044:
    *(int *)0xcd38 = iVar1;
    return 0x53;
  }
  if (iVar1 == 0x3f) {
    *(undefined2 *)0xceac = 1;
  }
  else {
    if (iVar1 != 0x3e) goto LAB_1e45_0044;
    *(undefined2 *)0xcee2 = 1;
  }
  *(int *)0xcd38 = iVar1;
  return 0x44;
}
