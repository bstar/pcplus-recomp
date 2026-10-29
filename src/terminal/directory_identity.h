#ifndef PCPLUS_DIRECTORY_IDENTITY_H
#define PCPLUS_DIRECTORY_IDENTITY_H
enum {DI_OK,DI_ARGUMENT,DI_CONTEXT,DI_CANONICAL,DI_PATH};
/* Internal DOS16 CONFIG_CODE near-cdecl, DS=SS/IF1/DF0. Resolve a bounded
 * nonempty path64 into a disjoint destination64. Canonical DOS83 absolute
 * names only; no open, writes, file lock or external-generation guarantee.
 * Failure preserves the output. Caller owns startup or quiesced file IO. */
unsigned __cdecl directory_identity_path(const char *,char *);
/* Return the retained near canonical source path, or0 if context/entry/path
 * is invalid. Read-only, no DOS; accounting must refuse an unbound request. */
unsigned __far __cdecl terminal_directory_account_identity(void);
#endif
