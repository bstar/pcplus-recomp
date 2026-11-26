/* Admitted display profiles (csi_terminal_id). Default: 4 VT220, 6 ANSI.
 * TERMINAL_ANSI_PROFILES admits every id the recovered dispatch table sends
 * to the shared ansi_escape_entry: 2 VT100, 3 VT102, 5 VT320, 7 IBM PC,
 * 8 WYSE 75, 9 ATT 605, 10 ATT 4410 and 11 TVI 922. The recovered reset
 * (reconstruction/terminal_reset/reset.asm) gives all of them VT220's flags
 * except monochrome for 6..7. They differ only by primary DA
 * (src/reports/data.asm), the native secondary-DA branch
 * (reconstruction/ansi/dispatch.asm L_e9ec) and the status label; see
 * docs/ANSI_FAMILY_PROFILES.md for the original-wide terminal-id audit. */
#ifndef TERMINAL_PROFILE_H
#define TERMINAL_PROFILE_H
#ifdef TERMINAL_ANSI_PROFILES
#define TERMINAL_PROFILE_UNSUPPORTED(p) ((p)<2 || (p)>11)
#else
#define TERMINAL_PROFILE_UNSUPPORTED(p) ((p)!=4 && (p)!=6)
#endif
/* Running id (csi_terminal_id). TERMINAL_VT52 also admits 1, which DECANM
 * (ESC[?2l) enters at runtime; VT52 is never a configured profile. */
#ifdef TERMINAL_VT52
#define TERMINAL_ACTIVE_PROFILE_UNSUPPORTED(p) ((p)!=1 && TERMINAL_PROFILE_UNSUPPORTED(p))
#else
#define TERMINAL_ACTIVE_PROFILE_UNSUPPORTED(p) TERMINAL_PROFILE_UNSUPPORTED(p)
#endif
#endif
