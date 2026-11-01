#ifndef PCPLUS_PHONE_LOG_STARTUP_H
#define PCPLUS_PHONE_LOG_STARTUP_H
enum { PLS_OK=0,PLS_ARGUMENT,PLS_RESOURCE,PLS_PATH,PLS_FILESYSTEM,PLS_BASELINE,
       PLS_QUEUE_BASE=256 };
/* Foreground DOS16 near cdecl, DS=SS. Read the accepted exact1264-byte PRM
 * image; do not reopen a configuration file or publish any new PRM values.
 * Disabled logging ignores PSP/environment/filesystem paths. Enabled logging
 * selects an existing current PCPLUS.FON first; otherwise PCPLUS's directory,
 * or current directory when that variable is absent/empty. A missing leaf may
 * be created later, but missing/inaccessible directories, read-only/nonregular
 * existing files and malformed environment values fail closed. Do not fall
 * back after an error other than file-not-found.
 * Canonicalize and validate the selected absolute DOS83 identity BEFORE the
 * checked queue configuration; subsequent CWD changes cannot redirect it.
 * No file is opened, created or written here. Failures before queue configure
 * preserve that owner. A queue refusal returns PLS_QUEUE_BASE+PLQ_* unchanged;
 * pending/retry/recovery records are never discarded to apply new settings.
 * This service must be explicitly wired by the application startup owner;
 * it does not install hooks or automatically enable connection logging.
 */
unsigned __cdecl phone_log_startup_configure(const unsigned char *,unsigned,unsigned);
#endif
