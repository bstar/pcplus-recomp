#include "file_info_runtime.h"
#include "runtime.h"
#include <stdio.h>
#include <dos.h>
static FILE *temporary;
unsigned runtime_file_info_live,runtime_file_info_segment;
unsigned runtime_file_info_reset(void)
{
 struct SREGS segments;
 if(temporary || runtime_file_info_live)return ASPECT_RUN_STATE;
 segread(&segments);runtime_file_info_segment=segments.ds;return 0;
}
void runtime_file_info_finish(void)
{
 FILE *stream=temporary;
 temporary=0;runtime_file_info_live=0;
 if(stream)fclose(stream);
}
FILE *runtime_file_info_open(const char *path,const char *mode)
{
 if(temporary){runtime_set_error(ASPECT_RUN_STATE);return 0;}
 temporary=fopen(path,mode);runtime_file_info_live=temporary!=0;return temporary;
}
int runtime_file_info_close(FILE *stream)
{
 if(!stream || stream!=temporary){runtime_set_error(ASPECT_RUN_STATE);return EOF;}
 /* Retire before close: an error must never close a recycled handle again. */
 temporary=0;runtime_file_info_live=0;return fclose(stream);
}
int runtime_file_info_seek(FILE *stream,long offset,int origin)
{
 if(!stream || stream!=temporary){runtime_set_error(ASPECT_RUN_STATE);return -1;}
 return fseek(stream,offset,origin);
}
long runtime_file_info_tell(FILE *stream)
{
 if(!stream || stream!=temporary){runtime_set_error(ASPECT_RUN_STATE);return -1L;}
 return ftell(stream);
}
