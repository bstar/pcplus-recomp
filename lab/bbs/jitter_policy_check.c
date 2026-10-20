/* Real PJSIP jitter-buffer API: constant prefetch with/without frame discard. */
#include <pjlib.h>
#include <pjmedia/jbuf.h>
#include <assert.h>
#include <stdio.h>
#include <stdint.h>

static unsigned run(pj_pool_t *pool, int no_discard) {
    pjmedia_jbuf *jb;
    pj_str_t name = pj_str(no_discard ? "no-discard" : "progressive");
    pjmedia_jb_state state;
    unsigned missing = 0, normal = 0;
    assert(pjmedia_jbuf_create(pool, &name, sizeof(uint32_t), 20, 25, &jb) == PJ_SUCCESS);
    assert(pjmedia_jbuf_set_adaptive(jb, 2, 2, 2) == PJ_SUCCESS);
    assert(pjmedia_jbuf_set_discard(jb, no_discard ? PJMEDIA_JB_DISCARD_NONE : PJMEDIA_JB_DISCARD_PROGRESSIVE) == PJ_SUCCESS);
    /* A bounded initial burst, followed by balanced sequential arrivals/reads.
       Capacity is never exhausted and no input frame is lost or reordered. */
    for (uint32_t n = 0; n < 12; ++n) pjmedia_jbuf_put_frame(jb, &n, sizeof(n), (int)n);
    uint32_t expected = 0;
    for (uint32_t n = 12; n < 3012; ++n) {
        uint32_t value = UINT32_MAX;
        char type;
        pj_bool_t discarded = PJ_FALSE;
        pjmedia_jbuf_put_frame2(jb, &n, sizeof(n), 0, (int)n, &discarded);
        assert(!discarded);
        pjmedia_jbuf_get_frame(jb, &value, &type);
        if (type == PJMEDIA_JB_NORMAL_FRAME) {
            assert(value >= expected);
            missing += value - expected;
            expected = value + 1;
            ++normal;
        }
    }
    assert(pjmedia_jbuf_get_state(jb, &state) == PJ_SUCCESS);
    assert(normal > 2900 && state.size < 25);
    printf("%s normal=%u skipped_sequence_numbers=%u discard=%u lost=%u size=%u prefetch=%u\n",
           no_discard ? "candidate" : "baseline", normal, missing, state.discard,
           state.lost, state.size, state.prefetch);
    pjmedia_jbuf_destroy(jb);
    return missing;
}

int main(void) {
    pj_caching_pool cache;
    assert(pj_init() == PJ_SUCCESS);
    pj_log_set_level(0);
    pj_caching_pool_init(&cache, NULL, 0);
    pj_pool_t *pool = pj_pool_create(&cache.factory, "jitter-check", 4096, 4096, NULL);
    assert(pool);
    unsigned baseline = run(pool, 0), candidate = run(pool, 1);
    assert(baseline > 0 && candidate == 0);
    pj_pool_release(pool);
    pj_caching_pool_destroy(&cache);
    pj_shutdown();
    puts("PASS: equal prefetch bounds retain progressive discard; NONE preserves sequence.");
    return 0;
}
