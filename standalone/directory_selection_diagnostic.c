#include "directory_selection.h"
#include <dos.h>
#include <malloc.h>
#include <stdio.h>
#include <string.h>
/* Golden vectors are generated independently by the host test. The product
 * cannot see expected bytes until its call has returned. */
typedef struct selection_vector {
 prm_dos_image image;
 directory_dos_page_data page;
 live_configuration_plan active;
 char prm_path[64],directory_path[64];
 unsigned entry,codes,mask,returned;
 directory_selection_result result;
 directory_selection_proposal expected;
} selection_vector;
typedef char vector_abi[sizeof(selection_vector)==4618?1:-1];
selection_vector selection_input,selection_before;
directory_selection_result selection_result;
static unsigned checks;
static unsigned verify(unsigned yes)
{++checks;return yes;}
int main(void)
{
 FILE *input,*output;
 unsigned count=0,status,i;size_t n;
 unsigned char __far *page_memory;
 unsigned char __far *output_memory;
 directory_dos_page_data __far *page;
 directory_selection_proposal __far *proposal;
 page_memory=(unsigned char __far *)_fmalloc(sizeof(*page)+32);
 output_memory=(unsigned char __far *)_fmalloc(sizeof(*proposal)+32);
 if(!page_memory || !output_memory)return 1;
 page=(directory_dos_page_data __far *)(page_memory+16);
 proposal=(directory_selection_proposal __far *)(output_memory+16);
 input=fopen("CASES.BIN","rb");if(!input)return 2;
 while((n=fread(&selection_input,1,sizeof(selection_input),input))!=0){
  if(n!=sizeof(selection_input))return 3;
  memcpy(&selection_before,&selection_input,sizeof(selection_before));
  _fmemset(page_memory,0xa5,sizeof(*page)+32);
  _fmemcpy(page,&selection_input.page,sizeof(*page));
  _fmemset(output_memory,0xcc,sizeof(*proposal)+32);
  memset(&selection_result,0xdd,sizeof(selection_result));
  status=directory_selection_stage(&selection_input.image,page,selection_input.entry,
   selection_input.codes,selection_input.mask,&selection_input.active,
   selection_input.prm_path,selection_input.directory_path,proposal,&selection_result);
  if(!verify(status==selection_input.returned) ||
   !verify(!memcmp(&selection_result,&selection_input.result,sizeof(selection_result))) ||
   !verify(!_fmemcmp(proposal,&selection_input.expected,sizeof(*proposal))) ||
   !verify(!memcmp(&selection_input,&selection_before,sizeof(selection_input))) ||
   !verify(!_fmemcmp(page,&selection_input.page,sizeof(*page)))){
   printf("FAILED VECTOR %u STATUS %u RESULT %u/%u/%u\n",count,status,
    selection_result.status,selection_result.source_status,selection_result.detail);
   return 4;
  }
  for(i=0;i<16;++i)if(!verify(page_memory[i]==0xa5 &&
   page_memory[16+sizeof(*page)+i]==0xa5 && output_memory[i]==0xcc &&
   output_memory[16+sizeof(*proposal)+i]==0xcc))return 5;
  ++count;
 }
 if(ferror(input) || fclose(input) || !count)return 6;
 _ffree(page_memory);_ffree(output_memory);
 output=fopen("RESULT.BIN","wb");if(!output)return 7;
 if(fwrite(&count,2,1,output)!=1 || fwrite(&checks,2,1,output)!=1 || fclose(output))return 8;
 printf("SELECTION PASS %u VECTORS %u CHECKS\n",count,checks);return 0;
}
