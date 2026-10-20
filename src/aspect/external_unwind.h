#ifndef ASPECT_EXTERNAL_UNWIND_H
#define ASPECT_EXTERNAL_UNWIND_H
/* Maintained synchronous foreground recovery on the ASPECT DS=SS allocation.
 * The checkpoint restores a C stack; the native dispatcher owns final register
 * restoration. Foreign DOS child stacks retain neutral termination. Kernel,
 * BIOS, allocator corruption and recursive cleanup faults are separate cases. */
enum { EXTERNAL_SCOPE=1,EXTERNAL_PARENT,EXTERNAL_STREAMS,EXTERNAL_HANDLES,
 EXTERNAL_VIEW,EXTERNAL_PAUSED,EXTERNAL_PROCESS,EXTERNAL_NEAR,
 EXTERNAL_ARENA,EXTERNAL_CHILD_RETURN,EXTERNAL_RESUMED,EXTERNAL_WAIT,
 EXTERNAL_VIEW_RETURN,EXTERNAL_HANDLES_RETURN,EXTERNAL_STREAMS_RETURN,
 EXTERNAL_PARENT_RETURN,EXTERNAL_SNAPSHOT_ALLOC,EXTERNAL_HANDLE_MASK,
 EXTERNAL_HANDLE_UNMASK,EXTERNAL_BACKUP_ALLOC,EXTERNAL_WAIT_KEY,
 EXTERNAL_SNAPSHOT_FREE };
#if defined(ASPECT_EXTERNAL_UNWIND)
unsigned __cdecl runtime_external_checkpoint_active(void);
void __cdecl runtime_external_checkpoint_retire(void);
void __cdecl runtime_external_checkpoint_recovering(void);
void __cdecl runtime_external_recover(unsigned cause);
extern unsigned runtime_external_recoveries,runtime_external_cleanup_error;
unsigned __cdecl runtime_external_scope_active(void);
#if defined(ASPECT_EXTERNAL_DIAGNOSTIC)
void __cdecl runtime_external_phase(unsigned);
extern unsigned runtime_external_fault_at,runtime_external_fault_kind,runtime_external_fault_fired;
extern unsigned runtime_external_arena_valid,runtime_external_arena_ok;
extern unsigned runtime_external_frame_offset,runtime_external_arena_changed;
extern void __far *runtime_external_arena_copy;
#define external_phase(value) runtime_external_phase(value)
#else
#define external_phase(value) ((void)0)
#endif
#else
#define external_phase(value) ((void)0)
#endif
#endif
