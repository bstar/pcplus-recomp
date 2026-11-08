/* Real DOS video/BIOS and recovered native cursor state; controlled admission. */
#include <dos.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
extern unsigned field_request(unsigned,unsigned),field_adopt_request(unsigned,unsigned);
extern void field_set_owners(unsigned,unsigned,unsigned);
extern unsigned field_flags,field_abi_bad;
extern unsigned field_break_owner;
#ifdef ASPECT_GET_POLICY
extern unsigned field_status_hidden,field_status_base;
#endif
extern unsigned field_screen_columns,field_screen_video_row_bytes,field_text_video_segment;
extern unsigned field_text_cga_status_port,field_text_bios_output,field_screen_viewport_offset;
extern unsigned field_screen_cursor_row,field_screen_visible_column,field_attributes_current;
extern unsigned field_screen_viewport_enabled,field_screen_viewport_left,field_screen_viewport_active,field_screen_viewport_right;
extern unsigned field_screen_video_offset,field_screen_previous_column,field_screen_attribute_offset,field_screen_cursor_column,field_screen_previous_row,field_screen_attribute_row_bytes,field_screen_use_bios_cursor,field_csi_last_row;
static unsigned admission_error,admission_calls,cases;
static unsigned long checks;
unsigned field_adoptions;
static unsigned initial[2000],expected[2000];
static unsigned char seen[256];
static unsigned __far *video;
static void ck(unsigned yes)
{++checks;if(!yes){printf("FIELD FAIL case%u check%lu ABI%u\r\n",cases,checks,field_abi_bad);exit(1);}}
unsigned field_admit(void){++admission_calls;return admission_error;}
void field_unexpected(void){ck(0);}
static void mode(unsigned value){union REGS in,out;in.x.ax=value;int86(0x10,&in,&out);}
static void cursor(unsigned position,unsigned shape)
{union REGS in,out;in.h.ah=2;in.h.bh=0;in.x.dx=position;int86(0x10,&in,&out);in.h.ah=1;in.x.cx=shape;int86(0x10,&in,&out);}
static unsigned read_cursor(unsigned *shape)
{union REGS in,out;in.h.ah=3;in.h.bh=0;int86(0x10,&in,&out);*shape=out.x.cx;return out.x.dx;}
static void setup(unsigned mono,unsigned origin,unsigned position,unsigned hidden,unsigned fallback)
{
 unsigned i,row=position>>8,col=position&255;mode(mono?7:3);
 field_screen_columns=80;field_screen_video_row_bytes=160;field_text_video_segment=mono?0xb000:0xb800;
 field_text_cga_status_port=fallback==2?0x3da:0;field_text_bios_output=fallback==1;
 field_screen_viewport_offset=origin;field_screen_viewport_enabled=origin!=0;field_screen_viewport_active=0;field_screen_viewport_left=origin;field_screen_viewport_right=79;
 field_screen_attribute_row_bytes=origin?132:80;field_csi_last_row=24;field_attributes_current=7;
#ifdef ASPECT_GET_POLICY
 field_status_hidden=1;field_status_base=24*256;
#endif
 field_screen_cursor_row=field_screen_previous_row=row;field_screen_cursor_column=field_screen_previous_column=col+origin;field_screen_visible_column=col;
 field_screen_attribute_offset=row*field_screen_attribute_row_bytes+col+origin;field_screen_video_offset=row*160+col*2;field_screen_use_bios_cursor=cases%2;
 video=(unsigned __far *)MK_FP(field_text_video_segment,0);for(i=0;i<2000;++i)initial[i]=expected[i]=video[i]=0x0700|(33+i%90);
 admission_error=field_adoptions=field_flags=0;cursor(position,hidden?0x2607:0x0607);
}
static void frame(void){unsigned i;for(i=0;i<2000;++i)ck(video[i]==expected[i]);ck(!field_abi_bad);}
static unsigned info(unsigned index){unsigned value=field_request(4,index);ck((value&0xff00)==0xf000);return value&255;}
static unsigned cell(unsigned i){return 1+(i*37+cases*17)%255;}
static void stage(unsigned width,unsigned attr)
{unsigned i;ck(field_request(1,(attr<<8)|width)==0);for(i=0;i<width;++i)ck(field_request(2,(i<<8)|cell(i))==0);}
static void normal(unsigned mono,unsigned width,unsigned origin,unsigned start,unsigned hidden,unsigned fallback)
{
 unsigned i,shape,original_shape,position,linear=(start>>8)*80+(start&255),last=linear+width-1,attr=cases%2?0x8e:0x1f;
 ++cases;setup(mono,origin,start,hidden,fallback);position=read_cursor(&original_shape);ck(position==start);
 ck(field_request(0,0xffff)==0);ck(info(0)==(start&255)&&info(1)==(start>>8)&&info(2)==7&&info(3)==(original_shape&255)&&info(4)==(original_shape>>8)&&info(5)==80&&info(6)==25&&info(7)==origin&&info(8)==0);
 frame();ck(field_request(3,0)==10&&field_request(0,start)==10);
 if(linear+width>2000){ck(field_request(1,(attr<<8)|width)==7);ck(field_request(5,1)==0);frame();return;}
 stage(width,attr);frame();
 /* Staging is invisible; a complete presentation writes exactly this span. */
 field_flags=2;ck(field_request(3,0x100|width-1)==0);field_flags=0;
 for(i=0;i<width;++i){expected[linear+i]=(attr<<8)|cell(i);seen[cell(i)]=1;}frame();
 position=read_cursor(&shape);ck(position==((last/80)<<8|last%80)&&shape==0x0407);
 ck(field_screen_cursor_row==(start>>8)&&field_screen_cursor_column==(start&255)+origin&&field_adoptions==0);
 ck(info(9)==last%80&&info(10)==last/80);
 ck(field_request(5,0)==0&&field_adoptions==1);frame();position=read_cursor(&shape);
 ck(position==((last/80)<<8|last%80)&&shape==original_shape);
 ck(field_screen_cursor_row==last/80&&field_screen_cursor_column==last%80+origin&&field_screen_visible_column==last%80);
 ck(field_screen_video_offset==last*2&&field_screen_attribute_offset==(last/80)*field_screen_attribute_row_bytes+last%80+origin);
 ck(field_request(5,0)==0&&field_request(4,0)==10);
}
static void guards(void)
{
 unsigned shape,position,i,before_calls;
 ++cases;setup(0,0,0x0205,0,0);
 field_break_owner=1;ck(field_request(0,0xffff)==10);field_break_owner=0;
 field_set_owners(1,0,0);ck(field_request(0,0xffff)==10);
 field_set_owners(0,1,0);ck(field_request(0,0xffff)==10);
 field_set_owners(0,0,1);ck(field_request(0,0xffff)==10);field_set_owners(0,0,0);frame();
 ck(field_request(6,0)==7&&field_request(1,10)==10&&field_request(5,2)==7);
 before_calls=admission_calls;field_flags=1;ck(field_request(0,0xffff)==10&&admission_calls==before_calls);field_flags=0;frame();
 admission_error=3;ck(field_request(0,0xffff)==3);admission_error=0;
 ck(field_request(0,0x1900)==7&&field_request(0,0x0050)==7&&field_request(0,0xffff)==0);
 ck(field_request(1,0)==7&&field_request(1,82)==7&&field_request(4,
#ifdef ASPECT_GET_POLICY
 13
#else
 11
#endif
 )==7);
 ck(field_request(1,0x1f0a)==0&&field_request(2,0x0141)==7&&field_request(2,0)==7&&field_request(3,0)==10);frame();
 stage(10,0x1f);ck(field_request(3,10)==7&&field_request(3,0x0200)==7);frame();
 ck(field_request(3,3)==0);for(i=0;i<10;++i)expected[165+i]=0x1f00|cell(i);frame();
 ck(field_adopt_request(25,0)==7&&field_adopt_request(0,80)==7&&field_adoptions==0);
 ck(field_request(5,1)==0);position=read_cursor(&shape);ck(position==0x0205&&shape==0x0607);frame();
 ck(field_request(0,0xffff)==0);field_set_owners(1,0,0);position=read_cursor(&shape);
 ck(field_request(3,0)==10&&field_request(5,0)==10&&field_request(5,1)==10);field_set_owners(0,0,0);
 {unsigned after;ck(read_cursor(&after)==position&&after==shape);}
 ck(field_request(4,0)==10&&field_request(0,0xffff)==0);
 field_screen_video_row_bytes=162;ck(field_request(4,0)==10&&field_request(5,1)==10);field_screen_video_row_bytes=160;
 ck(field_request(0,0xffff)==0);field_screen_viewport_offset=1;
 ck(field_request(4,0)==10&&field_request(5,1)==10);field_screen_viewport_offset=0;
 ck(field_request(0,0xffff)==0);field_csi_last_row=23;
 ck(field_request(4,0)==10&&field_request(5,1)==10);field_csi_last_row=24;
 field_csi_last_row=23;ck(field_request(0,0x174f)==0&&field_request(1,0x1f02)==7);
 stage(1,0x1f);ck(field_request(3,0)==0&&field_request(5,0)==0);expected[1919]=0x1f00|cell(0);frame();field_csi_last_row=24;
 ck(field_request(0,0xffff)==0);mode(7);position=read_cursor(&shape);
 ck(field_request(5,1)==10);{unsigned after;ck(read_cursor(&after)==position&&after==shape);}
 ck(field_request(4,0)==10);mode(3);
}
#ifdef ASPECT_GET_POLICY
static void policy(void)
{
 unsigned hidden;
 for(hidden=0;hidden<2;++hidden){
  setup(0,0,0x1705,0,0);field_status_hidden=hidden;field_csi_last_row=hidden?24:23;
  ck(field_request(0,65535U)==0);
  ck(info(11)==hidden && info(12)==24 && info(6)==(hidden?25:24));
  ck(field_request(4,13)==7);frame();
  field_status_hidden=1-hidden;ck(field_request(4,11)==10);field_status_hidden=hidden;
  field_status_base=23*256;ck(field_request(4,12)==10);field_status_base=24*256;
  ck(info(11)==hidden && info(12)==24);ck(field_request(5,1)==0);
 }
 setup(0,0,0x0205,0,0);field_status_hidden=2;ck(field_request(0,65535U)==10);
 field_status_hidden=1;field_status_base=0;ck(field_request(0,65535U)==10);
 field_status_base=26*256;ck(field_request(0,65535U)==10);field_status_base=24*256;
 ck(field_request(0,65535U)==0 && field_request(5,1)==0);frame();
}
#endif
int main(void)
{
 unsigned mono,w,p,o,h,b,i;unsigned widths[]={1,10,80,81},positions[]={0x0205,0x1602,0x1800};
 ck(field_request(5,0)==0);
 for(w=0;w<4;++w)for(p=0;p<3;++p)for(o=0;o<2;++o)for(h=0;h<2;++h)for(b=0;b<2;++b)normal(0,widths[w],o?52:0,positions[p],h,b);
 for(mono=0;mono<2;++mono)for(b=0;b<3;++b)normal(mono,81,0,0x0405,1,b);
 guards();
#ifdef ASPECT_GET_POLICY
 policy();
#endif
 for(i=1;i<256;++i)ck(seen[i]);mode(3);printf("PASS SCRIPT FIELD %u cases; %lu checks; 255 CP437 bytes, persistent video, native cursor, ABI\r\n",cases,checks);return field_abi_bad?1:0;
}
