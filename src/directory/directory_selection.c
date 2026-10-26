#include "directory_selection.h"
#include <dos.h>
#include <string.h>
typedef char selection_word_abi[sizeof(unsigned)==2?1:-1];
typedef char selection_proposal_abi[sizeof(directory_selection_proposal)==1190?1:-1];
static unsigned long linear(const void __far *p)
{return ((unsigned long)FP_SEG(p)<<4)+FP_OFF(p);}
static unsigned far_extent(const void __far *p,unsigned n)
{return p && (unsigned long)FP_OFF(p)+n<=65536UL && linear(p)+n<=0x100000UL;}
static unsigned near_extent(const void *p,unsigned n)
{return p && (unsigned long)(unsigned)p+n<=65536UL && far_extent((const void __far *)p,n);}
static unsigned separate(const void __far *a,unsigned an,const void __far *b,unsigned bn)
{unsigned long x=linear(a),y=linear(b);return x+an<=y || y+bn<=x;}
/* Zero means invalid. A nonempty path of63 bytes occupies64 with its NUL. */
static unsigned path_size(const char *p)
{
 unsigned n;
 for(n=0;n<64;++n){
  if(!near_extent(p,n+1))return 0;
  if(!p[n])return n?n+1:0;
 }
 return 0;
}
unsigned __cdecl directory_selection_stage(const prm_dos_image *image,
 const directory_dos_page_data __far *page,unsigned entry,unsigned codes,
 unsigned category_mask,const live_configuration_plan *active,
 const char *prm_path,const char *directory_path,
 directory_selection_proposal __far *proposal,directory_selection_result *result)
{
 directory_selection_proposal stage;
 live_configuration_result decoded;
 const void __far *regions[7];unsigned sizes[7],pn,dn,i,j,count,status;
 unsigned char __far *to=(unsigned char __far *)proposal;
 if(!near_extent(image,sizeof(*image)) || !near_extent(active,sizeof(*active)) ||
  !near_extent(result,sizeof(*result)) || !far_extent(page,sizeof(*page)) ||
  !far_extent(proposal,sizeof(*proposal)))return DIRECTORY_SELECTION_ARGUMENT;
 pn=path_size(prm_path);dn=path_size(directory_path);
 /* Invalid path extents cannot safely establish an alias contract. */
 if(!pn || !dn)return DIRECTORY_SELECTION_ARGUMENT;
 regions[0]=(const void __far *)image;sizes[0]=sizeof(*image);
 regions[1]=page;sizes[1]=sizeof(*page);
 regions[2]=(const void __far *)active;sizes[2]=sizeof(*active);
 regions[3]=(const void __far *)prm_path;sizes[3]=pn;
 regions[4]=(const void __far *)directory_path;sizes[4]=dn;
 regions[5]=proposal;sizes[5]=sizeof(*proposal);
 regions[6]=(const void __far *)result;sizes[6]=sizeof(*result);
 for(i=0;i<7;++i)for(j=0;j<i;++j)
  if(!separate(regions[i],sizes[i],regions[j],sizes[j]))return DIRECTORY_SELECTION_ARGUMENT;
 memset(result,0,sizeof(*result));
 if(codes>1 || category_mask>15){result->status=DIRECTORY_SELECTION_ARGUMENT;return result->status;}
 count=page->first_entry<=200 && page->first_entry?201-page->first_entry:0;
 if(count>10)count=10;
 if(!count || page->count!=count || entry<page->first_entry ||
  entry-page->first_entry>=count){result->status=DIRECTORY_SELECTION_PAGE;return result->status;}
 memset(&stage,0,sizeof(stage));
 stage.context.selection.entry_number=entry;stage.context.codes=codes;
 for(i=0;i<250;++i)stage.context.selection.header[i]=page->header[i];
 for(i=0;i<114;++i)stage.context.selection.record[i]=page->records[entry-page->first_entry][i];
 memcpy(stage.context.prm_path,prm_path,pn);
 memcpy(stage.context.directory_path,directory_path,dn);
 status=live_configuration_decode(image,&stage.context.selection,codes,category_mask,
  active,&stage.configuration,&decoded);
 if(status){result->status=DIRECTORY_SELECTION_CONFIGURATION;
  result->source_status=status;result->detail=decoded.source_status;return result->status;}
 status=transfer_import_decode(image,&stage.transfer);
 if(status){result->status=DIRECTORY_SELECTION_TRANSFER;result->source_status=status;return result->status;}
 /* No failure point remains. No partial output is visible on a rejected call. */
 for(i=0;i<sizeof(stage);++i)to[i]=((const unsigned char *)&stage)[i];
 return DIRECTORY_SELECTION_OK;
}
