#include "compiler_decimal.h"
#include <string.h>
#include <limits.h>
/*253 decimal digits plus at most577 denominator decimal places and1074
 * binary scaling bits fit within2048 bits. Magnitude classification happens
 * before exponent expansion, so arbitrarily long exponents cannot overrun it. */
#define LIMBS 128
typedef char short_is_word[(USHRT_MAX==65535U)?1:-1];
typedef struct big {unsigned used;unsigned short limb[LIMBS];} big;
static void one(big *b){memset(b,0,sizeof(*b));b->used=1;b->limb[0]=1;}
static unsigned multiply(big *b,unsigned value,unsigned add)
{
 unsigned i;unsigned long carry=add,word;
 for(i=0;i<b->used;++i){word=(unsigned long)b->limb[i]*value+carry;b->limb[i]=(unsigned short)word;carry=word>>16;}
 if(carry){if(b->used==LIMBS)return 1;b->limb[b->used++]=(unsigned short)carry;}
 return 0;
}
static unsigned bits(const big *b)
{unsigned n=b->used*16,top=b->limb[b->used-1];while(top && !(top&32768U)){--n;top<<=1;}return top?n:0;}
static int compare(const big *a,const big *b)
{unsigned i;if(a->used!=b->used)return a->used>b->used?1:-1;i=a->used;while(i--){if(a->limb[i]!=b->limb[i])return a->limb[i]>b->limb[i]?1:-1;}return 0;}
static unsigned shift(big *b,unsigned n)
{
 unsigned words=n/16,part=n%16,i,old=b->used;unsigned long word,carry=0;
 if(!bits(b))return 0;
 if(words+old+(part!=0)>LIMBS)return 1;
 if(words){for(i=old;i--;)b->limb[i+words]=b->limb[i];memset(b->limb,0,words*sizeof(b->limb[0]));b->used+=words;}
 if(part){for(i=words;i<b->used;++i){word=((unsigned long)b->limb[i]<<part)|carry;b->limb[i]=(unsigned short)word;carry=word>>16;}if(carry)b->limb[b->used++]=(unsigned short)carry;}
 return 0;
}
static void subtract(big *a,const big *b)
{
 unsigned i,borrow=0;unsigned long left,right;
 for(i=0;i<a->used;++i){left=a->limb[i];right=(i<b->used?(unsigned long)b->limb[i]:0)+borrow;a->limb[i]=(unsigned short)(left-right);borrow=left<right;}
 while(a->used>1&&!a->limb[a->used-1])--a->used;
}
static void pack(unsigned char out[8],unsigned long low,unsigned long high)
{unsigned i;for(i=0;i<4;++i){out[i]=(unsigned char)low;low>>=8;out[i+4]=(unsigned char)high;high>>=8;}}
unsigned aspect_compiler_decimal(const unsigned char *text,unsigned length,unsigned char out[8])
{
 big numerator,denominator,work;unsigned i,digit,fraction=0,digits=0,after_dot=0,negative_exp=0;
 int exponent=0,scale,order,binary,bit,comparison;unsigned long low=0,high=0;
 if(!text||!out||!length||length>253)return 1;
 memset(out,0,8);memset(&numerator,0,sizeof(numerator));numerator.used=1;one(&denominator);
 for(i=0;i<length && text[i]!='e' && text[i]!='E';++i){
  if(text[i]=='.'){if(after_dot)return 1;after_dot=1;continue;}
  if(text[i]<'0'||text[i]>'9')return 1;digit=text[i]-'0';
  if(digit||digits)++digits;if(after_dot)++fraction;
  if(multiply(&numerator,10,digit))return 1;
 }
 if(i<length){
  ++i;if(i<length&&(text[i]=='-'||text[i]=='+'))negative_exp=text[i++]=='-';
  if(i==length)return 1;
  for(;i<length;++i){if(text[i]<'0'||text[i]>'9')return 1;if(exponent<1000)exponent=exponent*10+text[i]-'0';}
 }
 if(!digits)return 0;
 if(negative_exp)exponent=-exponent;exponent-=(int)fraction;order=(int)digits+exponent-1;
 if(order>308){pack(out,0,0x7ff00000UL);return 0;}if(order< -324)return 0;
 if(exponent>=0){for(i=0;i<(unsigned)exponent;++i)if(multiply(&numerator,10,0))return 1;}
 else for(i=0;i<(unsigned)-exponent;++i)if(multiply(&denominator,10,0))return 1;
 binary=(int)bits(&numerator)-(int)bits(&denominator);
 if(binary>=0){work=denominator;if(shift(&work,(unsigned)binary))return 1;if(compare(&numerator,&work)<0)--binary;}
 else{work=numerator;if(shift(&work,(unsigned)-binary))return 1;if(compare(&work,&denominator)<0)--binary;}
 scale=binary< -1022?1074:52-binary;
 if(scale>=0){if(shift(&numerator,(unsigned)scale))return 1;}
 else if(shift(&denominator,(unsigned)-scale))return 1;
 /* Quotient has at most53 bits. The remaining numerator is the exact
  * remainder; twice that remainder decides nearest/even rounding. */
 for(bit=52;bit>=0;--bit){
  work=denominator;if(shift(&work,(unsigned)bit))continue;
  if(compare(&numerator,&work)>=0){subtract(&numerator,&work);if(bit<32)low|=1UL<<bit;else high|=1UL<<(bit-32);}
 }
 if(shift(&numerator,1))return 1;comparison=compare(&numerator,&denominator);
 if(comparison>0||(comparison==0&&(low&1))){if(++low==0)++high;}
 if(binary< -1022){pack(out,low,high);return 0;}
 if(high&0x200000UL){low=(low>>1)|(high<<31);high>>=1;++binary;}
 if(binary>1023){pack(out,0,0x7ff00000UL);return 0;}
 pack(out,low,(high&0xfffffUL)|((unsigned long)(binary+1023)<<20));return 0;
}
