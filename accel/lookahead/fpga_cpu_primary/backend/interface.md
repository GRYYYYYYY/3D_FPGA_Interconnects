# cp_backend_bank integration contract (L1)

Module `cp_backend_bank #(BANK_ID=0, SET_BITS=10, WORD_BITS=14)`; production
BANK_ID0..63, OWNER=BANK_ID/2, SUBBANK=BANK_ID%2. Ports below are final names.
All ready/valid payloads remain stable while blocked. Logical memory outputs
connect directly to sources48+BANK_ID (CAN),112+BANK_ID (SCR) of shared radix.
No local tagged physical port and no duplicate memory credits.

- `clk, reset`: synchronous whole-core reset.
- `sample_clear`: pulse ONLY at quiescent sample boundary; reinitializes PV,
  directory, enum state and scratch state. `initialized` stays low until real
  PV/directory/scratch init completes. No external canonical initialization is
  hidden here: global controller writes INF backing through admin sources.
- `node_count[31:0], label_base[63:0], scratch_base[63:0]`: runtime64-bit32B line bases,
  held stable through sample; bases32-line aligned, complete range must fit32bit.
- `wave_restart`: pulse after `done` to deassert internal flush and reopen
  enum+scratch for next wave; preserves pending/PV, directory and generation.
- `flush`: pulse/level requests end of candidate input; internally latched until
  wave_restart/sample_clear. Queued FIFO2 candidates drain before enum sees it.
- candidate: `in_valid,in_ready,in_node[31:0],in_pair[63:0]`.
- POP/SEED: `op_valid,op_ready,op_node[31:0],op_code[2:0],op_pair[63:0],
  op_line[255:0],op_arg[27:0],op_cookie[19:0]`. Codes2 POP,5 SEED; code3 relaxation/code7 line
  commit accepted by canonical contract. Internal finalize commits take priority.
- completion: `result_valid,result_ready,result_node[31:0],result_opcode[2:0],
  result_status[3:0],old_label[63:0],append_mask[3:0],event_arguments[111:0],
  result_pv[67:0],result_cookie[19:0]`. Includes both commits(code7) and external operations;
  controller must consume all, but only POP produces frontend work. Real ACK
  slice: consume output then next edge core retirement, nextedge slot reuse.
- directory control: `ctrl_valid,ctrl_ready,ctrl_op[1:0],ctrl_bucket[11:0],
  ctrl_ptr[13:0]`; ops1 TAKE,2 RELEASE,3 MIN (0 APPEND reserved internally).
  Response `ctrl_rsp_valid,ctrl_rsp_ready,ctrl_rsp_op[1:0],ctrl_rsp_status[1:0],
  ctrl_rsp_bucket[11:0],ctrl_rsp_node[31:0],ctrl_rsp_arg[31:0],
  ctrl_rsp_ptr[13:0],ctrl_rsp_next[13:0]`. NIL=8192. Controls must follow true
  backend publication drain; command and response FIFO2s are real.
- For each prefix `can`, `scr`: request `*_valid,*_ready,*_kind[3:0],
  *_line[31:0],*_id[31:0],*_gen[31:0],*_data[255:0]`; response
  `*_rsp_valid,*_rsp_ready,*_rsp_kind[3:0],*_rsp_id[31:0],*_rsp_gen[31:0],
  *_rsp_status[1:0],*_rsp_data[255:0]`. CAN kinds4 POP read/5 read/6 write;
  SCR7 read/8 write. CAN localID slot0..7 with full32bit generation, explicit
  range reject on return; SCR localID=BANK_ID, generation=full relative line.
- status: `initialized,done,idle,expansion_idle,error,overflow`; `done` requires latched flush,
  enum/scratch completion, empty input/operation/context queues, actual pending
  retirement, publication/directory drain and no logical memory in flight.
  `idle` means canonical/publication/control/input/memory quiescent (not that
  accumulated candidates are flushed); safe for phase control only with done.
- counters32: `accepted,retired,spill_count,enumerated,commits,op_accepted,
  op_retired,event_count`; `dir_used[13:0],dir_peak[13:0],spill_peak[11:0],
  peak_live[3:0]`. Enum/scratch counts cumulative within sample, pending counters
  likewise. `error` is sticky; illegal request is rejected rather than truncated.

Serialized publication captures event, submits it, waits for actual directory
RAM response, then deferred event ACK before capture of next event. Expected
uncontended directory command interval8; tests will bind actual observed value.
No L2 journal. Wave restart is explicitly distinct from sample reset.

`op_cookie[19:0]` is opaque(group4+T token16), stored at actual K8 free slot
and returned at actual publication out_slot, never FIFO-mapped. Commit cookie
is zero. `expansion_idle` additionally checks enum pipeline/fragment FIFO and
scratch expand activity but permits resident occupied entries; it is for
end-of-expand detection before flush. Both bases are64bit and checked for
alignment/range before admitting any request; narrowing only follows the check.
