#ifndef PCPLUS_ASPECT_DIRECTORY_RUNTIME_H
#define PCPLUS_ASPECT_DIRECTORY_RUNTIME_H
void runtime_directory_reset(void);
#if defined(ASPECT_RUNTIME_DIAGNOSTIC)
void runtime_directory_fixture(unsigned entry,const unsigned char *record);
#endif
#endif
