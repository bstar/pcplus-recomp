/* Independently checks all text cells, cursor, shape and active BIOS page. */
#include <dos.h>
#include <stdio.h>
#include <stdlib.h>
int xlt_application_main(int argc,char **argv);
static unsigned cells[2000];
int main(int argc,char **argv)
{
 union REGS r;unsigned i,result,page,offset;unsigned __far *video;
 if(argc>=3){r.h.ah=0;r.h.al=(unsigned char)atoi(argv[2]);int86(0x10,&r,&r);}
 if(argc>=4){r.h.ah=5;r.h.al=(unsigned char)atoi(argv[3]);int86(0x10,&r,&r);}
 r.h.ah=15;int86(0x10,&r,&r);page=r.h.bh;
 if(argc>=3 && r.h.al!=(unsigned char)atoi(argv[2]))return 14;
 if(argc>=4 && page!=(unsigned)atoi(argv[3]))return 15;
 offset=*(unsigned __far *)MK_FP(0x40,0x4e);video=(unsigned __far *)MK_FP(r.h.al==7?0xb000:0xb800,offset);
 for(i=0;i<2000;++i)video[i]=cells[i]=(unsigned)(0x1700|(33+i%90));
 r.h.ah=1;r.x.cx=0x0305;int86(0x10,&r,&r);
 r.h.ah=2;r.h.bh=(unsigned char)page;r.x.dx=0x070b;int86(0x10,&r,&r);
 result=(unsigned)xlt_application_main(2,argv);
 for(i=0;i<2000;++i)if(video[i]!=cells[i])return 10;
 r.h.ah=3;r.h.bh=(unsigned char)page;int86(0x10,&r,&r);
 if(r.x.cx!=0x0305 || r.x.dx!=0x070b)return 11;
 r.h.ah=15;int86(0x10,&r,&r);if(r.h.bh!=page)return 12;
 if(result)return 13;
 puts("XLT UI RESTORED");return 0;
}
