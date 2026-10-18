#ifndef PCPLUS_DIRECTORY_DOS_H
#define PCPLUS_DIRECTORY_DOS_H
/* Read-only maintained IO for the proved PCPlus2.01 PCPLUS.DIR storage.
 * Size is not a format/version signature. Caller explicitly selects the file.
 * No defaults, repair, directory UI, semantic interpretation or file writes. */
#define DIRECTORY_DOS_FILE_SIZE 23050U
#define DIRECTORY_DOS_HEADER_SIZE 250U
#define DIRECTORY_DOS_RECORD_SIZE 114U
#define DIRECTORY_DOS_ENTRY_COUNT 200U
#define DIRECTORY_DOS_SELECTION_SIZE 366U
#define DIRECTORY_DOS_PATH_MAX 127U
#define DIRECTORY_DOS_PAGE_COUNT 10U
#define DIRECTORY_DOS_PAGE_SIZE 1394U

typedef unsigned directory_dos_status;
enum {
 DIRECTORY_DOS_OK=0, DIRECTORY_DOS_ARGUMENT, DIRECTORY_DOS_OPEN,
 DIRECTORY_DOS_READ, DIRECTORY_DOS_SIZE, DIRECTORY_DOS_CLOSE
};
typedef struct directory_dos_selection {
 unsigned entry_number;
 unsigned char header[DIRECTORY_DOS_HEADER_SIZE];
 unsigned char record[DIRECTORY_DOS_RECORD_SIZE];
} directory_dos_selection;
typedef struct directory_dos_page_data {
 unsigned first_entry;
 unsigned count;
 unsigned char header[DIRECTORY_DOS_HEADER_SIZE];
 unsigned char records[DIRECTORY_DOS_PAGE_COUNT][DIRECTORY_DOS_RECORD_SIZE];
} directory_dos_page_data;
typedef struct directory_dos_result {
 directory_dos_status status;
 unsigned dos_error;
 unsigned close_error;
 unsigned bytes_processed;
} directory_dos_result;
/* DOS8086 small model, near pointers/cdecl, DS=SS, unsigned16-bit status in AX.
 * Entry uses original numbering1..200. Reads all23050 bytes using bounded
 * streaming storage, probes one extra byte, closes, THEN commits selection.
 * Destination unchanged on every error. No string/padding/enum normalization.
 * Result may be NULL; otherwise must not overlap destination or path. Path
 * must be nonempty and NUL-terminated within127 content bytes. Near extents
 * must not wrap and path/destination must not overlap. Invalid arguments leave
 * result untouched; for valid arguments it records primary/secondary errors.
 * bytes_processed counts bytes from successful reads, including suffix probe.
 * Stack is bounded independently of file size (well below1KiB plus DOS libs). */
directory_dos_status __cdecl directory_dos_read(const char *path,unsigned entry,
 directory_dos_selection *destination,directory_dos_result *result);
/* Same validation/error guarantees. Captures min(10,201-first) consecutive
 * raw records in one full-file stream. Unused final-page slots are zero.
 * The page API returns raw storage; UI must render bounded name/number fields,
 * never raw whole records or password/script fields. Bounded stack below2KiB. */
directory_dos_status __cdecl directory_dos_page(const char *path,unsigned first,
 directory_dos_page_data *destination,directory_dos_result *result);
#endif
