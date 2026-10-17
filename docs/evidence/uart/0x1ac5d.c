/* REA/Ghidra pseudocode; not original source. Address 0x1ac5d; Evidence ev_304930d2e3d275f1bd7d590db158e914458e1caf79eeceb108a33a2746f9e0eb. */

byte __cdecl16near FUN_1000_ac5d(int param_1,int param_2,int param_3)

{
  byte bVar1;
  undefined2 unaff_DS;

  if (param_1 == 0) {
    bVar1 = 0;
  }
  else if (param_1 == 1) {
    bVar1 = 8;
  }
  else if (param_1 == 2) {
    bVar1 = 0x18;
  }
  else {
    bVar1 = 0x28;
    if (param_1 != 3) {
      bVar1 = 0x38;
    }
  }
  if (param_2 == 7) {
    bVar1 = bVar1 | 2;
  }
  else {
    bVar1 = bVar1 | 3;
  }
  if (param_3 != 1) {
    bVar1 = bVar1 | 4;
  }
  out(*(undefined2 *)0x8fee,bVar1);
  return bVar1;
}
