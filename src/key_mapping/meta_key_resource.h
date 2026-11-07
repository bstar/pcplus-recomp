#ifndef PCPLUS_META_KEY_RESOURCE_H
#define PCPLUS_META_KEY_RESOURCE_H
enum {META_RESOURCE_OK=0,META_RESOURCE_ARGUMENT,META_RESOURCE_CANONICAL,META_RESOURCE_PATH,META_RESOURCE_ENVIRONMENT,META_RESOURCE_INSPECT,META_RESOURCE_MISSING};
enum {META_RESOURCE_CURRENT=0,META_RESOURCE_PCPLUS,META_RESOURCE_EXPLICIT};
typedef struct meta_key_resource_result {
 unsigned status,dos_error,environment_error,source,exists;
 char path[64];
} meta_key_resource_result;
/* Near-cdecl, DS=SS. Required near result74/path64 extents, disjoint inputs.
 * Bad arguments leave result unchanged/no DOS. Valid calls populate result.
 * Named lookup: canonical current name first; ONLY absent2/3 bare names try
 * PCPLUS. Operational errors and existing bad file contents cannot be hidden
 * by fallback. Qualified requests have no environment fallback. Existing
 * regular readonly files may load. No KEY reads, creation, claims or adoption.
 * MISSING retains the canonical absent target selected by lookup. Its presence
 * is NOT authorization to create: caller must claim/recheck/use checked IO.
 * Retain successful selected identity for later IO; do not repeat lookup on
 * Save. ASCII DOS83/recovery-parent53 policy matches checked KEY files.
 */
unsigned __cdecl meta_key_resource_lookup(unsigned,const char *,meta_key_resource_result *);
/* Pattern planning is deliberately split: current first, fallback only after
 * an empty current scan. This keeps a usable current list independent of a
 * malformed environment. fallback0/1; no file probe or enumeration here.
 * PCPLUS absent returns MISSING without a pattern. */
unsigned __cdecl meta_key_resource_pattern(unsigned,unsigned,meta_key_resource_result *);
/* Pure composition using an already frozen absolute *.KEY pattern and an
 * accepted stem9. No lookup/DOS; output unchanged on invalid/overlapping spans.
 * Keeps a fallback selection in its selected directory even if CWD changes.
 */
unsigned __cdecl meta_key_resource_selected(const char *,const char *,char *);
#endif
