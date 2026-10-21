# EOF response timing and optional flow bytes

The [timing correction](../../docs/validation/zmodem-response-end.json) retains
a real stock-helper/native-host pipe counterexample. The receiver checks the
complete hex EOF header, including its required LF, then sends ZRINIT before
reading the optional trailing XON. The old auditor rejected that valid ordering
because its lower bound included the optional flow byte.

The parser now records both full `end` and mandatory `response_end`. Header CRC,
required LF, every source byte and the full stream remain checked. EOF completion
uses the mandatory end for its response lower bound. Binary headers have the same
two endpoints. Historical serialized protocols without the new field retain
their conservative old bound.

The unchanged real bytes pass the corrected full protocol/control audit. A copied
completion reply moved before the mandatory EOF bytes is rejected.94 passive
checks cover XON/XOFF ordering, missing/invalid CRC/ACK/finish, earlier serialized
protocols and ambiguous overlapping timing rows. Two empty-file ACK controls and
all15 checks on the retained normal audio download also pass. The failed larger
audio transfer still has no EOF and remains a failure.

Timing lookups now index unambiguous byte-offset ranges rather than scan the
entire trace for every query. This preserves observed times and explicitly
rejects overlaps; complete stream/manifests remain separate acceptance gates.

```sh
./tools/dev --command python3 lab/bbs/check_zmodem_audit.py \
  --output build/bbs-lab/response-end-checks-new.json
```

This corrects verifier semantics. It does not fix the larger-file audio failure,
change the DOS program or grant broader protocol/hardware acceptance.
