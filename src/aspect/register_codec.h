#ifndef PCPLUS_REGISTER_CODEC_H
#define PCPLUS_REGISTER_CODEC_H
/* Accidental-damage seal only; not authentication or a DOS sandbox. */
static unsigned register_seal(const unsigned char __far *p,unsigned token)
{
 unsigned i,h=token;
 for(i=0;i<830;++i){h=(h<<1)|(h>>15);h^=p[i];}
 return h;
}
static unsigned register_strings(const unsigned char __far *p)
{
 unsigned i,j;
 for(i=0;i<10;++i){for(j=0;j<81 && p[20+i*81+j];++j);if(j==81)return 0;}
 return 1;
}
#endif
