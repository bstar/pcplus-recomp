#ifndef PCPLUS_NOTICE_SPEAKER_H
#define PCPLUS_NOTICE_SPEAKER_H
#include "notice.h"
/* Optional maintained build. Default quiet; explicit enable changes only the
 * built-in sound route when options.sound is NULL. Legacy callbacks take precedence.
 * Configuration rejects while any notice/window/speaker owner is live. */
unsigned NOTICE_CODE __cdecl notice_speaker_configure(unsigned enabled);
#endif
