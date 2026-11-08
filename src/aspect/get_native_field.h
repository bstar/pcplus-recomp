#ifndef PCPLUS_ASPECT_GET_NATIVE_FIELD_H
#define PCPLUS_ASPECT_GET_NATIVE_FIELD_H
/* Native79D4-shaped field adapter, ordinary DS=SS near C ABI. Assembly consumes
 * the recovered owner's seven words. The callback must be one of GET's two
 * known filters. Initial/output are native near slots; only accepted text+NUL
 * (at most81 bytes) is copied after successful display/keyboard retirement.
 * Failed service raises the native GET checkpoint, never a fake field result.
 * No source/output pointer is retained after return. */
unsigned __cdecl runtime_get_native_field(unsigned,unsigned,unsigned,unsigned,unsigned,unsigned,unsigned);
#endif
