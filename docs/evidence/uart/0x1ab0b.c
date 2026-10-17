/* REA/Ghidra pseudocode; not original source. Address 0x1ab0b; Evidence ev_b2afd6a07745d7fd16c60bc0c442ec842e8745b9dfd9b6de8c02b0bc8b94afad. */

undefined4 FUN_1000_ab0b(undefined1 param_1)

{
  byte bVar1;
  uint in_AX;
  int iVar2;
  int iVar3;
  int iVar4;
  undefined2 unaff_DS;

  if (*(int *)0x39a6 == 1) {
    iVar4 = 0x14;
    iVar2 = FUN_1000_3323();
    FUN_1000_ac0e();
    FUN_1000_3778();
    FUN_1000_31bb(0x7deb,0);
    while (((*(int *)0x39a6 != 0 && (iVar4 != 0)) && (iVar3 = FUN_1000_3f4b(), iVar3 == 0))) {
      iVar3 = FUN_1000_3323();
      if (iVar3 != iVar2) {
        iVar4 = iVar4 + -1;
        iVar2 = iVar3;
      }
    }
    *(undefined2 *)0x39a6 = 0;
    in_AX = FUN_1000_ac0e();
  }
  if (*(int *)0x3356 == 1) {
    do {
      in_AX = FUN_1000_abc1();
      if (in_AX != 0) break;
      in_AX = FUN_1000_3f4b();
    } while (in_AX == 0);
  }
  do {
    bVar1 = in(*(undefined2 *)0x900a);
    in_AX = CONCAT11((char)(in_AX >> 8),bVar1) & 0xff20;
  } while ((bVar1 & 0x20) == 0);
  out(*(undefined2 *)0x9012,param_1);
  return CONCAT22(*(undefined2 *)0x9012,CONCAT11((char)(in_AX >> 8),param_1));
}
