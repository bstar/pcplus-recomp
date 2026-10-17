/* REA/Ghidra pseudocode; not original source. Address 0x1acb8; Evidence ev_0ce93bfdceeb449f379dcaaaf1e5cef7471d936a6b5c8bd90a69faa9d4edb01d. */

/* WARNING: This function may have set the stack pointer */

undefined4 entry(void)

{
  undefined1 uVar1;
  byte bVar2;
  undefined2 in_AX;
  undefined2 in_CX;
  undefined2 in_DX;
  int iVar4;
  int extraout_DX;
  undefined2 in_BX;
  undefined2 unaff_DS;
  int iVar3;

  uVar1 = in(DAT_1fb7_9022);
  iVar3 = CONCAT11(0x1f,uVar1);
  iVar4 = DAT_1fb7_9022;
  DAT_1fb7_f2a6 = in_CX;
  DAT_1fb7_f2a8 = in_BX;
  DAT_1fb7_f2aa = unaff_DS;
  DAT_1fb7_f2ac = in_DX;
  DAT_1fb7_f2ae = in_AX;
  do {
    if (DAT_1fb7_3354 == 0) {
      if (DAT_1fb7_3356 == 0) {
LAB_1000_acd9:
        if (DAT_1fb7_8e20 == 0x1000) goto LAB_1000_acfa;
      }
      else if (0xbff < DAT_1fb7_8e20) {
        out(DAT_1fb7_8ff4,9);
        DAT_1fb7_7e18 = 1;
        DAT_1fb7_f2a4 = iVar4;
      }
    }
    else {
      if ((char)iVar3 == '\x13') {
        DAT_1fb7_39a6 = 1;
LAB_1000_acfa:
        out(0x20,0x20);
        return CONCAT22(DAT_1fb7_f2ac,DAT_1fb7_f2ae);
      }
      if ((char)iVar3 == '\x11') {
        DAT_1fb7_39a6 = 0;
        goto LAB_1000_acfa;
      }
      if ((DAT_1fb7_7e17 & 1) != 0) goto LAB_1000_acd9;
      if (0xbff < DAT_1fb7_8e20) {
        DAT_1fb7_7e17 = 1;
        DAT_1fb7_f2a2 = 0xad2f;
        DAT_1fb7_f2a4 = iVar3;
        FUN_1000_ad93();
        iVar3 = DAT_1fb7_f2a4;
        iVar4 = extraout_DX;
      }
    }
    *DAT_1fb7_7e19 = (char)iVar3;
    DAT_1fb7_8e20 = DAT_1fb7_8e20 + 1;
    if (DAT_1fb7_7e19 == DAT_1fb7_7e1d) {
      DAT_1fb7_7e19 = (undefined1 *)0x7e20;
    }
    else {
      DAT_1fb7_7e19 = DAT_1fb7_7e19 + 1;
    }
    bVar2 = in(iVar4 + 2);
    if ((bVar2 & 4) == 0) goto LAB_1000_acfa;
    uVar1 = in(iVar4);
    iVar3 = CONCAT11((char)((uint)iVar3 >> 8),uVar1);
  } while( true );
}
