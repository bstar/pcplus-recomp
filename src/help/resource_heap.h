#ifndef PCPLUS_HELP_RESOURCE_HEAP_H
#define PCPLUS_HELP_RESOURCE_HEAP_H
/* Far calls into resident CODE; returned storage is near DS=SS backing. */
void * __far __cdecl help_resource_storage_allocate(unsigned);
void __far __cdecl help_resource_storage_release(void *);
#endif
