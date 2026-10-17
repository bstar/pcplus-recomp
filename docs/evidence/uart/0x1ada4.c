/* REA/Ghidra pseudocode; not original source. Address 0x1ada4; Evidence ev_68abaf60364d11311798529f98ca3394639e9e6ff023dfce839a11195d6d4ba5. */

void __cdecl16near FUN_1000_ada4(void)

{
  code *pcVar1;

  pcVar1 = (code *)swi(0x21);
  (*pcVar1)();
  return;
}
