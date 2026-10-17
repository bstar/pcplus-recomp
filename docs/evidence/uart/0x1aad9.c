/* REA/Ghidra pseudocode; not original source. Address 0x1aad9; Evidence ev_c89cb6c13b64b5e09ff43d89433e7ace0410e5ba9bb1fdb6e96c70080150b45f. */

void FUN_1000_aad9(int param_1)

{
  int iVar1;
  int iVar2;
  undefined2 unaff_DS;

  if (*(int *)0x8e20 == 0) {
    iVar1 = FUN_1000_3323();
    while ((param_1 != 0 && (*(int *)0x8e20 == 0))) {
      iVar2 = FUN_1000_3323();
      if (iVar2 != iVar1) {
        param_1 = param_1 + -1;
        iVar1 = iVar2;
      }
    }
  }
  FUN_1000_aa65();
  return;
}
