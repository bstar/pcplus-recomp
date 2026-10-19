/* Maintained IRQ-live, bounded batch calibration. No host timing constant.
 * One 512-iteration native6B72 unit per measurement chunk; no PIC writes.
 * Measurement overhead/quantization are intentional deviations from7956. */
#include "txpace.h"
unsigned aspect_txpace_count,aspect_txpace_step_error;
static unsigned prepared;
void aspect_txpace_reset(void)
{prepared=aspect_txpace_count=aspect_txpace_step_error=0;}
unsigned aspect_txpace_ready(void)
{return prepared;}
static unsigned step(aspect_txpace_step_fn fn,unsigned phase)
{
 aspect_txpace_step_error=fn(phase);
 if(aspect_txpace_step_error)return ASPECT_TXPACE_STEP;
 return (aspect_txpace_flags()&512U)?0:ASPECT_TXPACE_IF;
}
unsigned aspect_txpace_prepare(aspect_txpace_step_fn fn)
{return aspect_txpace_prepare_bounded(fn,ASPECT_TXPACE_MAX_CHUNKS);}
unsigned aspect_txpace_prepare_bounded(aspect_txpace_step_fn fn,unsigned limit)
{
 unsigned saved=aspect_txpace_flags(),error=0,chunks=0,tries;
 unsigned long start,now,elapsed,total;
 if(!(saved&512U)){error=ASPECT_TXPACE_IF;goto out;}
 if(!fn||!limit||limit>ASPECT_TXPACE_MAX_CHUNKS){error=ASPECT_TXPACE_ARGUMENT;goto out;}
 if(prepared)goto out;
 aspect_txpace_count=aspect_txpace_step_error=0;
 start=aspect_txpace_ticks();if(start>=ASPECT_TXPACE_DAY){error=ASPECT_TXPACE_CLOCK;goto fail;}
 error=step(fn,ASPECT_TXPACE_BEFORE_MEASURE);if(error)goto fail;
 start=aspect_txpace_ticks();if(start>=ASPECT_TXPACE_DAY){error=ASPECT_TXPACE_CLOCK;goto fail;}
 for(tries=0;tries<ASPECT_TXPACE_ALIGN_POLLS;++tries){
  error=step(fn,ASPECT_TXPACE_ALIGN);if(error)goto fail;
  now=aspect_txpace_ticks();if(now>=ASPECT_TXPACE_DAY){error=ASPECT_TXPACE_CLOCK;goto fail;}
  if(now!=start)break;
 }
 if(tries==ASPECT_TXPACE_ALIGN_POLLS){error=ASPECT_TXPACE_LIMIT;goto fail;}
 /* The edge is observed after admission and cooperative alignment. */
 start=now;
 aspect_txpace_count=ASPECT_TXPACE_CHUNK;
 do{
  aspect_txpace_native_one();++chunks;
  now=aspect_txpace_ticks();if(now>=ASPECT_TXPACE_DAY){error=ASPECT_TXPACE_CLOCK;goto fail;}
  if(now!=start)break;
 }while(chunks<limit);
 if(now==start){error=ASPECT_TXPACE_LIMIT;goto fail;}
 elapsed=now>=start?now-start:now+ASPECT_TXPACE_DAY-start;
 if(elapsed!=1){error=ASPECT_TXPACE_CLOCK;goto fail;}
 if(chunks<4){error=ASPECT_TXPACE_RESOLUTION;goto fail;}
 total=(unsigned long)chunks*ASPECT_TXPACE_CHUNK;
 total/=55UL;
 if(!total||total>65535UL){error=ASPECT_TXPACE_LIMIT;goto fail;}
 aspect_txpace_count=0;
 error=step(fn,ASPECT_TXPACE_AFTER_MEASURE);if(error)goto fail;
 aspect_txpace_count=(unsigned)total;prepared=1;goto out;
fail:
 prepared=aspect_txpace_count=0;
out:
 aspect_txpace_restore_if(saved);return error;
}
unsigned aspect_txpace_delay(unsigned units,aspect_txpace_step_fn fn)
{
 unsigned saved=aspect_txpace_flags(),error=0,i;
 if(!units)goto out;
 if(units>999U||!fn){error=ASPECT_TXPACE_ARGUMENT;goto out;}
 if(!prepared||!aspect_txpace_count){error=ASPECT_TXPACE_STATE;goto out;}
 if(!(saved&512U)){error=ASPECT_TXPACE_IF;goto out;}
 for(i=0;i<units;++i){
  error=step(fn,ASPECT_TXPACE_DELAY);if(error)goto out;
  aspect_txpace_native_one();
 }
 /* Final poll observes cancellation/overflow accrued during the final unit. */
 error=step(fn,ASPECT_TXPACE_DELAY);
out:
 aspect_txpace_restore_if(saved);return error;
}
