#include "owner.h"
#include "dos_exec.h"
typedef void (__interrupt __far *vector_type)(void);
extern unsigned mouse_scale_x,mouse_scale_y,mouse_present,mouse_count,mouse_code,mouse_button_pending;
extern unsigned char mouse_enabled[6];
extern unsigned __cdecl mouse_test_emit(unsigned,unsigned,unsigned);
extern void __far mouse_test_prior_callback(void);
extern unsigned __cdecl test_size(void),test_seed_key(void),test_bios_peek(void);
extern unsigned __cdecl test_owned_blocks(void),test_keep(void);
extern void __far * __cdecl test_allocate(unsigned);
extern unsigned __cdecl test_release(void __far *);
extern vector_type __cdecl test_vector(void);
extern void __cdecl test_save(void __far *),test_set_vector(vector_type);
extern void __cdecl test_exchange(void (__far *)(void),unsigned),test_character(unsigned);
static unsigned checks,failures;
static unsigned char image[0x4f0],native[28];
static void text(const char *s){while(*s)test_character((unsigned char)*s++);}
static void number(unsigned n)
{char digits[6];unsigned count=0;do{digits[count++]=(char)('0'+n%10);n/=10;}while(n);while(count)test_character(digits[--count]);}
static void check(unsigned pass,unsigned line)
{++checks;if(!pass){++failures;text("FAIL ");number(line);text("\r\n");}}
#define CHECK(x) check((x)!=0,__LINE__)
static void copy(unsigned char *d,const unsigned char *s,unsigned n)
{unsigned i;for(i=0;i<n;++i)d[i]=s[i];}
static unsigned same(const unsigned char __far *a,const unsigned char __far *b,unsigned n)
{unsigned i;for(i=0;i<n;++i)if(a[i]!=b[i])return 0;return 1;}
unsigned __cdecl bank_main(void)
{
 mouse_settings settings;unsigned key,i,bytes,blocks,keep;
 process_result result;
 unsigned char __far *before;
 unsigned char __far *after;
 vector_type vector;
 for(i=0;i<sizeof(image);++i)image[i]=0xa5;
 image[0x4e4]=8;image[0x4e5]=0;image[0x4e6]=4;image[0x4e7]=0;
 CHECK(mouse_settings_decode(image,sizeof(image),&settings)==MOUSE_OK);
 CHECK(settings.scale_x==8&&settings.scale_y==4);
 for(i=0;i<6;++i)CHECK(settings.enabled[i]==1);
 bytes=test_size();CHECK(bytes>0&&bytes<65504U);
 before=test_allocate(bytes);after=test_allocate(bytes);
 if(!before||!after)return 90;
 vector=test_vector();keep=test_keep();CHECK(keep>0);
 test_exchange(mouse_test_prior_callback,0x0b);test_save(before);
 mouse_scale_x=6;mouse_scale_y=7;mouse_present=0;mouse_count=2;mouse_code=3;mouse_button_pending=1;
 copy(native,(const unsigned char *)&mouse_scale_x,22);copy(native+22,mouse_enabled,6);
 blocks=test_owned_blocks();CHECK(blocks!=0xffff);
 CHECK(mouse_owner_open(&settings)==MOUSE_OK);
 CHECK(test_owned_blocks()==blocks+1);
 CHECK(mouse_owner_phase()==MOUSE_READY&&mouse_owner_bytes()==bytes);
 CHECK(test_seed_key()==0);CHECK(mouse_test_emit(1,16,8)==1);
 CHECK(mouse_owner_key(&key)==MOUSE_OK&&key==0x4d00&&mouse_count==1);
 CHECK(test_bios_peek()==0x256b);
 CHECK(mouse_owner_key(&key)==MOUSE_OK&&key==0x4d00&&mouse_count==0);
 CHECK(mouse_owner_key(&key)==MOUSE_OK&&key=='k');
 key=0xaaaa;CHECK(mouse_owner_key(&key)==MOUSE_PENDING&&key==0xaaaa);
 CHECK(mouse_test_emit(0x0a,16,8)==1);
 CHECK(mouse_owner_key(&key)==MOUSE_OK&&key==13&&mouse_button_pending==0);
 CHECK(mouse_test_emit(8,16,8)==1);CHECK(mouse_owner_key(&key)==MOUSE_OK&&key==27);
 CHECK(mouse_owner_suspend()==MOUSE_OK&&mouse_owner_phase()==MOUSE_SUSPENDED);
 CHECK(mouse_owner_key(&key)==MOUSE_STATE);
 CHECK(process_run("MUTATE.COM",0,&result)==PROCESS_OK&&result.child_status==37);
 CHECK(result.retained_paragraphs==keep&&test_keep()==keep&&test_owned_blocks()==blocks+1);
 CHECK(mouse_owner_resume()==MOUSE_OK&&mouse_owner_phase()==MOUSE_READY);
 CHECK(mouse_scale_x==8&&mouse_scale_y==4&&mouse_count==0);
 CHECK(mouse_test_emit(1,16,8)==1);CHECK(mouse_owner_key(&key)==MOUSE_OK&&key==0x4d00);
 CHECK(mouse_owner_suspend()==MOUSE_OK);
 CHECK(process_run("VECTOR.COM",0,&result)==PROCESS_OK&&result.child_status==37);
 CHECK(test_keep()==keep&&test_owned_blocks()==blocks+1);
 CHECK(mouse_owner_resume()==MOUSE_STATE&&mouse_owner_phase()==MOUSE_QUARANTINED);
 CHECK(mouse_owner_close()==MOUSE_STATE&&mouse_owner_bytes()==bytes);
 test_set_vector(vector);
 CHECK(mouse_owner_close()==MOUSE_OK&&mouse_owner_phase()==MOUSE_CLOSED&&mouse_owner_bytes()==0);
 CHECK(test_owned_blocks()==blocks);
 CHECK(same(native,(const unsigned char *)&mouse_scale_x,22)&&same(native+22,mouse_enabled,6));
 test_save(after);CHECK(same(before,after,bytes));
 CHECK(mouse_owner_close()==MOUSE_OK);
 test_exchange(0,0);CHECK(test_release(before)==0);CHECK(test_release(after)==0);
 CHECK(test_owned_blocks()==blocks-2&&test_keep()==keep);
 text("MOUSEBNK checks=");number(checks);text(" failures=");number(failures);
 text(" driver_bytes=");number(bytes);text("\r\n");
 return failures?1:0;
}
