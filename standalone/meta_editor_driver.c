/* Real DOS8086 calls into recovered routines; independent finite expectations. */
#include <stdio.h>
#include <string.h>
extern unsigned char records[540],records_before[16],records_after[16];
extern unsigned attribute,wait_active,wait_default,field_previous,field_next,edit_previous,edit_next;
extern unsigned keys[16],key_count,key_position,selected_row,field_return;
extern unsigned inverse_calls,cursor_calls,draw_calls,last_label,field_calls,service_errors;
extern void __cdecl editor_defaults(void);
#pragma aux editor_defaults "meta_editor_defaults";
extern unsigned __cdecl editor_field_key(unsigned *);
#pragma aux editor_field_key "meta_editor_field_key";
extern unsigned __cdecl editor_row(unsigned);
#pragma aux editor_row "meta_editor_row";
static unsigned data_segment(void);
#pragma aux data_segment = "mov ax,ds" value [ax] modify [];
static unsigned stack_segment(void);
#pragma aux stack_segment = "mov ax,ss" value [ax] modify [];
static unsigned char expected[540];

static int guards(void)
{unsigned i;for(i=0;i<16;++i)if(records_before[i]!=0x5a || records_after[i]!=0xa5)return 0;return 1;}

int main(void)
{
 unsigned key=0,cell,result,want,want_cell,i,j,seed,row,kind,scenario,count=0,next_kind,changed_text;
 unsigned labels[4]={0x1010,0x2020,0x3030,0x4040};
 if(data_segment()!=stack_segment())return 1;
 do {
  cell=key;result=editor_field_key(&cell);
  want=key==9 || key==0x0f00?key:key==255?0xff9d:0;
  want_cell=key==9 || key==0x0f00?13:key;
  if(result!=want || cell!=want_cell){printf("FAIL key %u\r\n",key);return 1;}
  ++key;
 }while(key);
 memset(records_before,0x5a,16);memset(records_after,0xa5,16);
 for(seed=0;seed<3;++seed){
  for(i=0;i<540;++i)records[i]=(unsigned char)(i*17+seed*41);
  memcpy(expected,records,540);
  for(i=0;i<10;++i){expected[i*54]=3;expected[i*54+1]=expected[i*54+2]=0;}
  editor_defaults();
  if(memcmp(records,expected,540)||!guards())return 2;
 }
 for(row=0;row<10;++row)for(kind=0;kind<4;++kind)for(scenario=0;scenario<8;++scenario){
  for(i=0;i<540;++i)records[i]=(unsigned char)(0x81+i*13);
  records[row*54]=(unsigned char)kind;records[row*54+1]=0;records[row*54+2]='a';records[row*54+3]=0;
  memcpy(expected,records,540);selected_row=row;key_position=service_errors=0;
  inverse_calls=cursor_calls=draw_calls=field_calls=last_label=0;
  attribute=0x1f00;field_previous=0x1212;field_next=0x2323;edit_previous=0x3434;edit_next=0x4545;
  wait_active=0x5678;wait_default=0x6789;next_kind=kind;changed_text=0;
  key_count=1;keys[0]=27;field_return=13;want=27;
  if(scenario==1){key_count=2;keys[0]='A';keys[1]=27;}
  if(scenario==2){key_count=2;keys[0]=0x4800;keys[1]=0x0f00;want=0x0f00;next_kind=(kind+1)%4;}
  if(scenario==3){keys[0]=9;changed_text=1;want=13;}
  if(scenario==4){key_count=2;keys[0]=' ';keys[1]=9;field_return=0xffff;changed_text=1;want=0xffff;}
  if(scenario==5){key_count=2;keys[0]=9;keys[1]=0x0f00;field_return=0x0f00;changed_text=1;want=0x0f00;}
  if(scenario==6){key_count=6;for(j=0;j<5;++j)keys[j]=j+1;keys[5]=0x0f00;want=0x0f00;next_kind=(kind+1)%4;}
  if(scenario==7){keys[0]=13;field_return=9;changed_text=1;want=9;}
  expected[row*54]=(unsigned char)next_kind;
  if(changed_text){expected[row*54+2]='x';expected[row*54+3]=0;}
  result=editor_row(row);
  if(result!=want || memcmp(records,expected,540) || !guards() || service_errors || key_position!=key_count || inverse_calls!=1 || cursor_calls!=key_count || field_calls!=changed_text ||
     field_previous!=0x1212 || field_next!=0x2323 || edit_previous!=0x3434 || edit_next!=0x4545 || attribute!=0x1f00 || wait_active!=wait_default || data_segment()!=stack_segment()){
   printf("FAIL row %u kind %u case %u result %u want %u service %u\r\n",row,kind,scenario,result,want,service_errors);return 3;
  }
  if(draw_calls!=(scenario==6?5:(scenario==1||scenario==2||scenario==4)?1:0))return 4;
  if(draw_calls && last_label!=labels[(kind+(scenario==6?5:1))%4])return 5;
  ++count;
 }
 printf("PASS 65536 field keys; 3 opaque-tail defaults; %u row scenarios\r\n",count);
 return 0;
}
