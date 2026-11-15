# cp_pop_dispatch port contract (production fixed64 banks,16 groups)

All vectors pack element i at `[i*WIDTH +: WIDTH]`, bit i for booleans.
Synchronous active-high `reset`; no implicit memory or software callback.

- `clk,reset`; `wave_start` input pulse/valid accepted on `wave_ready` output.
  `bucket[11:0]` input is captured at start. `wave_ready` is high only idle
  with no pending member/reservation/POP. Caller starts only after previous
  backend publication drain and its own MIN selection. `pops_done` output is
  sticky high after complete TAKE/member/POP drain until next start/reset;
  it does **not** imply frontend expansion/candidate/backend finalization done.
  `error` sticky rejects malformed pointer/owner/cookie/protocol responses.
- Directory output64: `ctrl_valid,ctrl_op[64*2],ctrl_bucket[64*12],
  ctrl_ptr[64*14]`; input `ctrl_ready`. Output ops1 TAKE and2 RELEASE only.
  Input `ctrl_rsp_valid,ctrl_rsp_op[64*2],ctrl_rsp_status[64*2],
  ctrl_rsp_bucket[64*12],ctrl_rsp_node[64*32],ctrl_rsp_arg[64*32],
  ctrl_rsp_ptr[64*14],ctrl_rsp_next[64*14]`; output `ctrl_rsp_ready`.
  Parent muxes directory control with its own MIN controller by phase.
  TAKE is issued once per bank and all64 replies form a barrier before
  member RELEASE fetch. NIL=8192; non-NIL pointers must be<8192.
- Frontend output16 `av`, input16 `ar`; input16 `tv`, output16 `tr`;
  input `[16*16-1:0] at` is opaque returned token(gen8,slot8). This directly
  matches lf_front_context reservation ports. Only slots0..7 are legal.
  Output16 `pv`, input16 `pr`; outputs `pt[16*16],stale[16],pn[16*32],
  pp[16*64]`. Parent supplies the current wave epoch to frontend separately.
- POP command output64 `op_valid,op_node[64*32],op_code[64*3],
  op_pair[64*64],op_line[64*256],op_arg[64*28],op_cookie[64*20]`;
  input64 `op_ready`. code=2, pair/line=0; arg is directory version/bucket,
  cookie=`{group[3:0],token[15:0]}`. Parent muxes with SEED by phase.
  At most8 command holding positions are valid globally, so at most8 true
  op_valid&&op_ready handshakes occur at an edge. Hold under backpressure.
- Completion input64 `result_valid,result_node[64*32],result_opcode[64*3],
  result_status[64*4],old_label[64*64],result_cookie[64*20]`;
  output64 `result_ready`. Dispatcher accepts **only opcode2 POP**. Parent
  independently drains SEED/commit results, e.g. final ready=mux on opcode.
  Cookie is validated against actual admitted slot/group/generation/bank/node;
  result arbitration is per-group round-robin across64 banks. One held POP
  output per group retains `{token,stale,node,pair}` until real frontend pr.
- Counters32 outputs: `take_count,release_count,pop_admitted,pop_returned,
  pop_delivered,stale_delivered`; counters reset only by reset, not wave_start.
  `outstanding[7:0]` counts admitted-but-not-frontend-delivered POPs (<=128).

Per bank one pending directory command, one detached pointer and one immutable
member hold. Per group one launch reservation and one token capture; launch
can queue while earlier token awaits POP admission. Assignment scans banks
from a free-running rotating bank cursor and groups from dynamic group RR,
max8 assignments/cycle. The source model's staged reserve_launch/capture is
retained, but real frontend av/ar and tv/tr handshakes replace fixed callback
latency. There is no same-edge release/reuse of holds or tracking slots.

`pops_done` waits until every TAKE response, detached list pointer, RELEASE
response, member hold, reservation, POP command hold, admitted operation and
frontend delivery has drained. It does not clear independently owned frontend
T/D/E records or bypass backend delayed core retirement; parent must also
check backend expansion_idle and frontend/candidate path idle before flush.
