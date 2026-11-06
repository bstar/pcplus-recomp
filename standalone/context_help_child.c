/* Controlled ABI consumer, not a production PCHELP replacement. Bounds check
 * the declared conventional-memory spans; the diagnostic parent is trusted.
 * No parent ownership/identity inference, original helper code or help text. */
#include <dos.h>
#include <stdio.h>
#include <string.h>
#include "../src/help/format.h"
#ifdef HELP_PARENT_ADMISSION
#include "../src/help/parent.h"
#endif
static unsigned copy_string(unsigned segment,unsigned offset,char *to,unsigned capacity)
{
 unsigned i;const unsigned char __far *from;
 if(offset>65535U-capacity || (unsigned long)segment*16+offset+capacity>0xa0000UL)return 1;
 from=MK_FP(segment,offset);
 for(i=0;i<capacity;++i){to[i]=from[i];if(!to[i])return 0;}
 return 1;
}
int main(int argc,char **argv)
{
 unsigned long pointer,size;unsigned seg,off,i,selected;
 unsigned char raw[18],header[3],record[38];char path[64]={0},title[40]={0},line[80],expected[40];
 const unsigned char __far *source;help_context ctx;help_header h;help_record topic;FILE *f;
#ifdef HELP_PARENT_ADMISSION
 help_parent_context admitted;
#endif
 if(argc!=3)return 2;if(strcmp(argv[1],"PCHELP"))return 3;
 if(help_pointer_parse(argv[2],&pointer))return 4;
#ifdef HELP_PARENT_ADMISSION
 if(help_parent_read_dos(argv[2],&admitted))return 5;
#endif
 seg=(unsigned)(pointer>>16);off=(unsigned)pointer;
 if(seg<0x50 || (unsigned long)seg*16+off+18>0xa0000UL)return 5;
 source=MK_FP(seg,off);for(i=0;i<18;++i)raw[i]=source[i];
 if(help_context_decode(raw,18,&ctx))return 6;
 if(copy_string(seg,ctx.path_offset,path,sizeof(path))||copy_string(seg,ctx.title_offset,title,sizeof(title)))return 7;
#ifdef HELP_PARENT_ADMISSION
 if(admitted.parent_ds!=seg||admitted.descriptor_offset!=off||
    memcmp(&admitted.context,&ctx,sizeof(ctx))||strcmp(admitted.path,path)||strcmp(admitted.title,title))return 6;
#endif
 f=fopen(path,"rb");if(!f)return 8;
 if(fseek(f,0,SEEK_END)){fclose(f);return 9;}size=(unsigned long)ftell(f);rewind(f);
 if(fread(header,1,3,f)!=3||help_header_decode(header,3,size,&h)){fclose(f);return 9;}
 selected=help_topic_select(ctx.topic,h.topics);
 if(fseek(f,3+(long)selected*38,SEEK_SET)||fread(record,1,38,f)!=38||help_record_decode(record,38,&h,size,&topic)){fclose(f);return 10;}
 if(fseek(f,(long)topic.offset,SEEK_SET)||!fgets(line,sizeof(line),f)){fclose(f);return 10;}
 sprintf(expected,"AUTHORED %02u\r\n",selected);if(strcmp(line,expected)){fclose(f);return 10;}
 if(fclose(f))return 10;
 f=fopen("HLPREC.BIN","wb");if(!f)return 11;
 if(fwrite(&pointer,4,1,f)!=1||fwrite(raw,1,18,f)!=18||fwrite(&selected,2,1,f)!=1||fwrite(path,1,64,f)!=64||fwrite(title,1,40,f)!=40){fclose(f);return 11;}
 return fclose(f)?11:0;
}
