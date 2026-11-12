"""Routable synchronous launch/capture context, separate from the functional DUT.

All DUT ports terminate in real registers using one routed BUFG clock. This
models a registered synchronous integration boundary, not a board or memory
controller. LFSRs keep input registers live; they are NOT functional stimulus
or a performance workload. The ordinary RTL tests remain the correctness proof.
No timing exception is emitted. Resources include the context overhead.
"""
from pathlib import Path
import sys

kind = sys.argv[1]
s = Path(__file__).resolve().parents[1]
if kind == 'owner':
    top, dut = 'r2_owner_context', 'sparse_owner_pipe'
    params = '.OWNER_BITS(5),.REQUEST_STAGE(1)'
    inputs = [('rst',1),('iv',1),('node',32),('pair',64),('fence',1),
              ('update_ready',1),('mem_ready',1),('rsp_valid',1),('rsp_id',6),('rsp_data',256)]
    outputs = [('ir',1),('fence_done',1),('update_valid',1),('update_line',32),('update_mask',4),
               ('mem_valid',1),('mem_write',1),('mem_line',32),('mem_id',6),('mem_data',256),
               ('rsp_ready',1),('idle',1),('error',1),('accepted',32),('retired',32),
               ('merges',32),('hits',32),('misses',32),('raw_stall',32),('mshr_peak',6),('dirty_peak',5)]
elif kind == 'many':
    L,P,MC,CC,U,R = map(int,sys.argv[2:8])
    CACHE = int(sys.argv[8]) if len(sys.argv)>8 else 1
    top, dut = f'r2_many{L}_context', 'r2_many_tile'
    params = f'.L({L}),.PHYS({P}),.MEMBER_CAP({MC}),.CHANGED_LIMIT({CC}),.USE_URAM({U}),.REQUEST_STAGE({R}),.CACHE_ENABLE({CACHE})'
    inputs = [('rst',1),('start',1),('row_base',32),('edge_base',32),('cost_base',32),('job_base',32),
              ('node_count',32),('state_base',32),('jobs',7),('cell_count',16),('cost_count',5),
              ('physical_ready',P),('physical_rsp_valid',P),('physical_rsp_id',P*6),('physical_rsp_data',P*256)]
    outputs = [('done',1),('error',1),('physical_valid',P),('physical_write',P),('physical_line',P*32),
               ('physical_id',P*6),('physical_data',P*256),('physical_rsp_ready',P),('issued',L),('accepted',L),
               ('committed',L),('commit_nodes',L*32),('wave',32),('phase',6),('qid',6),('owner_error',L),
               ('active_counts',L*32),('commit_counts',L*32),('mshr_peaks',L*6),('dirty_peaks',L*5)]
else:
    raise ValueError('unknown context kind')
ni, no = sum(w for _,w in inputs), sum(w for _,w in outputs)
wi, wo = (ni+31)//32, (no+31)//32
lines = ['`timescale 1ns/1ps',
         '// Physical context only: no functional/performance claim from its LFSRs.',
         f'module {top}(input wire clk,output reg [31:0] signature);',
         ' wire core_clk;',
         ' (* LOC="BUFGCE_X0Y144" *) BUFGCE clock_buffer(.I(clk),.CE(1\'b1),.O(core_clk));',
         f' wire [{wi*32-1}:0] stimulus;wire [{wo*32-1}:0] observed;',
         f' wire [{wo*32-1}:0] captured;',
         f' for(genvar k=0;k<{wi};k=k+1)begin:launch',
         '  (* DONT_TOUCH="yes" *) reg [31:0] state=32\'h6d2b79f5+k;',
         '  always @(posedge core_clk)state<={state[30:0],state[31]^state[21]^state[1]^state[0]};',
         '  assign stimulus[k*32+:32]=state;', ' end']
port = ['.clk(core_clk)']
for ports, bus in [(inputs,'stimulus'),(outputs,'observed')]:
    at=0
    for name,width in ports:
        port.append(f'.{name}({bus}[{at}+:{width}])')
        at+=width
if no != wo*32:
    lines.append(f' assign observed[{wo*32-1}:{no}]=0;')
lines.extend([f' (* KEEP_HIERARCHY="yes" *) {dut} #({params}) dut('+','.join(port)+');',
              f' for(genvar k=0;k<{wo};k=k+1)begin:capture',
              '  (* DONT_TOUCH="yes" *) reg [31:0] state=0;',
              '  always @(posedge core_clk)state<={state[30:0],state[31]}^observed[k*32+:32];',
              '  assign captured[k*32+:32]=state;', ' end',
              ' reg [31:0] fold;integer i;',
              f' always @*begin fold=0;for(i=0;i<{wo};i=i+1)fold=fold^captured[i*32+:32];end',
              ' always @(posedge core_clk)signature<=fold;', 'endmodule'])
(s/'physical_context').mkdir(exist_ok=True)
(s/'physical_context'/(top+'.sv')).write_text('\n'.join(lines)+'\n')
print(top, 'launch_bits',ni,'capture_bits',no)
