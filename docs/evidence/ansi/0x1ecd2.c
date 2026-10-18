/* REA pseudocode, not original source. Evidence ev_11f20bd04542aced412c36c7eb3b31ad664d7138536c41bde318852fbeb544c3. */

void __cdecl16near FUN_1ecd_0002(void)

{
  char cVar1;
  uint uVar2;
  int iVar3;
  undefined2 unaff_DS;
  bool bVar4;

  do {
    while( true ) {
      uVar2 = FUN_1000_5ca0();
      if (uVar2 == 0x48) goto LAB_1ee0_0004;
      cVar1 = (char)uVar2;
      if (0x48 < (int)uVar2) break;
      if (uVar2 == 0x45) goto LAB_1ecd_012e;
      if (0x45 < uVar2) {
        return;
      }
      if (cVar1 == '(') {
        do {
          uVar2 = FUN_1000_5ca0();
        } while (uVar2 == 0);
        *(undefined2 *)0xcde0 = 0;
        *(undefined2 *)0xcdec = 0;
        if (uVar2 == 0x41) {
          *(undefined2 *)0xcde0 = 1;
          return;
        }
        if (0x41 < uVar2) {
          return;
        }
        if (((char)uVar2 != '0') && ((char)uVar2 != '2')) {
          return;
        }
        *(undefined2 *)0xcdec = 1;
        return;
      }
      if ('(' < cVar1) {
        if (cVar1 == '7') {
          FUN_1d97_0404(0);
          return;
        }
        if ('7' < cVar1) {
          if (cVar1 == '8') {
            FUN_1d97_044c(0);
            return;
          }
          if (cVar1 != 'D') {
            return;
          }
          goto LAB_1ecd_0128;
        }
        if (cVar1 == ')') {
          do {
            uVar2 = FUN_1000_5ca0();
          } while (uVar2 == 0);
          *(undefined2 *)0xcde8 = 0;
          *(undefined2 *)0xcdf0 = 0;
          if (uVar2 == 0x41) {
            *(undefined2 *)0xcde8 = 1;
            return;
          }
          if (0x41 < uVar2) {
            return;
          }
          if (((char)uVar2 != '0') && ((char)uVar2 != '2')) {
            return;
          }
          *(undefined2 *)0xcdf0 = 1;
          return;
        }
        if ((char)(cVar1 + -0x29) < '\x01') {
          return;
        }
        if ('\x01' < (char)(cVar1 + -0x2a)) {
          return;
        }
        FUN_1000_5ca0();
        goto LAB_1ecd_00e9;
      }
      if ((cVar1 != '\0') && (cVar1 != '\x1b')) {
        if (cVar1 != ' ') {
          if (cVar1 != '#') {
            return;
          }
          FUN_1d97_0788();
          return;
        }
        iVar3 = FUN_1000_5ca0();
        if ((0x45 < iVar3) && (iVar3 + -0x46 < 2)) {
          return;
        }
        FUN_1000_abde();
        return;
      }
    }
  } while (uVar2 == 0x7f);
  if ((int)uVar2 < 0x80) {
    if (uVar2 == 99) {
      FUN_1000_20a4(1);
      return;
    }
    if (99 < uVar2) {
      return;
    }
    if (cVar1 != 'M') {
      if (cVar1 != 'P') {
        if (cVar1 == 'Z') {
          FUN_1d97_03e8();
          return;
        }
        bVar4 = cVar1 == '[';
LAB_1ecd_00a1:
        if (!bVar4) {
          return;
        }
LAB_1ecd_00e9:
        *(undefined2 *)0xcb5c = 0;
        *(undefined2 *)0xcb3c = 0;
        *(undefined2 *)0xceac = 0;
        *(undefined2 *)0xcee2 = 0;
        uVar2 = 0x44;
        while( true ) {
          while (uVar2 == 0x53) {
            uVar2 = FUN_1e45_0052();
          }
          if (0x53 < uVar2) break;
          if ((char)uVar2 == 'D') {
            uVar2 = FUN_1e3b_0042();
          }
          else {
            if ((char)uVar2 != 'L') {
              return;
            }
            uVar2 = FUN_1e45_0062();
          }
        }
        return;
      }
LAB_1ee0_0010:
      FUN_1eb2_0174();
      return;
    }
  }
  else {
    if (uVar2 == 0x88) {
LAB_1ee0_0004:
      FUN_1d97_0156();
      return;
    }
    if ((int)uVar2 < 0x89) {
      if (uVar2 != 0x84) {
        if (uVar2 != 0x85) {
          return;
        }
LAB_1ecd_012e:
        FUN_1000_12c8();
        return;
      }
LAB_1ecd_0128:
      FUN_1d97_00d6();
      return;
    }
    if (uVar2 != 0x8d) {
      if (uVar2 != 0x90) {
        bVar4 = uVar2 == 0x9b;
        goto LAB_1ecd_00a1;
      }
      goto LAB_1ee0_0010;
    }
  }
  FUN_1d97_0114();
  return;
}
