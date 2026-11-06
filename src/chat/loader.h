#ifndef PCPLUS_CHAT_LOADER_H
#define PCPLUS_CHAT_LOADER_H
#include "module.h"
#define CHAT_LOAD_BUSY 1
#define CHAT_LOAD_ACTIVE 2
#define CHAT_LOAD_BOUNDS 3
#define CHAT_LOAD_OPEN 4
#define CHAT_LOAD_READ 5
#define CHAT_LOAD_IDENTITY 6
#define CHAT_LOAD_DOS 7
#define CHAT_LOAD_IMAGE 8
#define CHAT_LOAD_API 9
typedef struct chat_module_handle {
    chat_module_entry entry;
    chat_session CHAT_FAR *state;
    chat_word loaded,busy,active,segment,dos_error;
} chat_module_handle;
/* Initialize handle to zero. Caller exclusively owns supplied conventional
 * storage and separate state. No ownership/allocator inference is made here. */
unsigned CHAT_FAR __cdecl chat_module_load(chat_module_handle *,chat_session CHAT_FAR *,const char *,void CHAT_FAR *,unsigned capacity);
unsigned CHAT_FAR __cdecl chat_module_call(chat_module_handle *,chat_module_request CHAT_FAR *);
unsigned CHAT_FAR __cdecl chat_module_unload(chat_module_handle *);
unsigned CHAT_FAR __cdecl chat_module_image_valid(unsigned segment);
#endif
