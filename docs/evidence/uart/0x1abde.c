/* REA/Ghidra pseudocode; not original source. Address 0x1abde; Evidence ev_a952239d7ff40a4906076df3d8baf074aa9215a1ef2630a2f412823955359005. */

void __cdecl16near FUN_1000_abde(void)

{
  undefined2 unaff_DS;

  if (*(int *)0x7e1b == 0x7e20) {
    *(undefined2 *)0x7e1b = *(undefined2 *)0x7e1d;
  }
  else {
    *(int *)0x7e1b = *(int *)0x7e1b + -1;
  }
  *(int *)0x8e20 = *(int *)0x8e20 + 1;
  return;
}
