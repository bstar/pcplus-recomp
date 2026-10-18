#ifndef PCPLUS_PRM_DOS_H
#define PCPLUS_PRM_DOS_H
/* Maintained DOS I/O for the proved 2.01 opaque memory-image format.
 * No original/default data or automatic repair/rewrite is included. */
#define PRM_DOS_IMAGE_SIZE 1264U

typedef struct prm_dos_image { unsigned char bytes[PRM_DOS_IMAGE_SIZE]; } prm_dos_image;
typedef enum prm_dos_status {
 PRM_DOS_OK=0, PRM_DOS_ARGUMENT, PRM_DOS_OPEN, PRM_DOS_READ,
 PRM_DOS_SIZE, PRM_DOS_WRITE, PRM_DOS_CLOSE
} prm_dos_status;
typedef struct prm_dos_result {
 prm_dos_status status;
 unsigned dos_error;
 unsigned close_error;
 unsigned bytes_processed;
} prm_dos_result;

/* Small-model C near pointers/cdecl. Result may be NULL.
 * Load updates destination only after exact-size read AND successful close.
 * Save creates/truncates path; write failure may leave a partial file. Callers
 * needing replacement transactions must stage/backup before invoking save. */
prm_dos_status __cdecl prm_dos_load(const char *path,prm_dos_image *destination,prm_dos_result *result);
prm_dos_status __cdecl prm_dos_save(const char *path,const prm_dos_image *source,prm_dos_result *result);
#endif
