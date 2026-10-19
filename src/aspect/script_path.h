#ifndef PCPLUS_ASPECT_SCRIPT_PATH_H
#define PCPLUS_ASPECT_SCRIPT_PATH_H
/* Native D4D0 accepts an 80-character operand and uses an 82-byte local.
 * The maintained resolver rejects extension append overflow before writing.
 * Output is transactional and may alias input. ASCII uppercasing only.
 * SOURCE means compilation is required; it never permits reading ASP as ASX. */
#define ASPECT_SCRIPT_PATH_CAPACITY 82U
enum { ASPECT_SCRIPT_PATH_COMPILED=0, ASPECT_SCRIPT_PATH_SOURCE,
       ASPECT_SCRIPT_PATH_EMPTY, ASPECT_SCRIPT_PATH_INVALID,
       ASPECT_SCRIPT_PATH_SIZE };
unsigned aspect_script_path(const char *input,char *output);
#endif
