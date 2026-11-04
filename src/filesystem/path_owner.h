#ifndef PCPLUS_PATH_OWNER_H
#define PCPLUS_PATH_OWNER_H
enum {PATH_OK=0,PATH_ARGUMENT,PATH_DRIVE,PATH_CHANGE,PATH_VERIFY,PATH_ROLLBACK};
typedef struct path_result {
 unsigned status,dos_error,drive_before,drive_after,rollback_failed;
 char current_path[68];
} path_result;
/* Guarded synchronous owner, not yet a foreground/menu entry. One path1..63
 * bytes, optional ASCII drive, no wildcard/control/UNC. Result must be
 * disjoint. Invalid arguments leave result unchanged. Does not rewrite PRM,
 * defaults or open files. Failed post-change verification attempts rollback;
 * PATH_ROLLBACK must block dependent operations until repaired by the caller.
 * Uses the original58-byte helper after preflight; DS must equal SS.
 */
unsigned __cdecl path_change(const char *path,path_result *result);
unsigned __cdecl path_native_change(const char *path);
unsigned __cdecl path_current_drive(void);
unsigned __cdecl path_select_drive(unsigned drive);
unsigned __cdecl path_getcwd(unsigned drive,char *relative_path);
#endif
