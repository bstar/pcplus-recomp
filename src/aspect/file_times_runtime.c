#include "file_times_runtime.h"
#include "script_file_runtime.h"
#include "runtime.h"
#include <stdio.h>
#include <stddef.h>
#include <string.h>
#include <io.h>
static FILE *temporary;
static aspect_script_file_prefix prefix;
static char input_copy[81];
unsigned runtime_file_times_live;
typedef char timestamp_prefix_size[sizeof(prefix)==8?1:-1];
typedef char timestamp_descriptor_offset[offsetof(aspect_script_file_prefix,descriptor)==7?1:-1];
unsigned runtime_file_times_reset(void)
{
 if(temporary||runtime_file_times_live)return ASPECT_RUN_STATE;
 memset(&prefix,0,sizeof(prefix));memset(input_copy,0,sizeof(input_copy));return 0;
}
void runtime_file_times_finish(void)
{
 FILE *stream=temporary;temporary=0;runtime_file_times_live=0;
 if(stream)fclose(stream);
}
aspect_script_file_prefix *runtime_file_times_open(const char *path,const char *mode)
{
 int descriptor;
 if(temporary){runtime_set_error(ASPECT_RUN_STATE);return 0;}
 temporary=fopen(path,mode);if(!temporary)return 0;
 descriptor=fileno(temporary);
 if(descriptor<0||descriptor>255){fclose(temporary);temporary=0;return 0;}
 memset(&prefix,0,sizeof(prefix));prefix.descriptor=(unsigned char)descriptor;
 runtime_file_times_live=1;return &prefix;
}
int runtime_file_times_close(aspect_script_file_prefix *value)
{
 FILE *stream;
 if(value!=&prefix||!temporary){runtime_set_error(ASPECT_RUN_STATE);return EOF;}
 stream=temporary;temporary=0;runtime_file_times_live=0;
 return fclose(stream);
}
char *runtime_file_times_copy(const char *source)
{
 unsigned i;memset(input_copy,0,sizeof(input_copy));
 for(i=0;i<80&&source[i];++i)input_copy[i]=source[i];
 return input_copy;
}
