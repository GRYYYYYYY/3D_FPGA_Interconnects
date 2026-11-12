`timescale 1ns/1ps
// Runtime graph, Q=1. Deterministic bounded pending-array directory.
// All persistent graph state is external, with counted acknowledged accesses.
module graph_control(input wire clk,rst,start,
 input wire [31:0] nodes,jobs,cells,
 input wire [31:0] base_row,base_edge,base_node,base_cost,base_cell,base_job,
 input wire [31:0] base_label,base_prop,base_pending,base_closed,base_output,
 output reg mv,input wire mr,output reg mw,output reg [31:0] ma,
 output reg [255:0] md,output reg [31:0] mask,
 input wire rv,output wire rr,input wire [255:0] rd,
 output reg cv,input wire cr,output reg [31:0] cd,
 output reg [63:0] cp,cc,output reg fence,input wire fence_done,
 output reg done,error,output reg [31:0] qid,waves,output reg [63:0] cycle,
 output reg [7:0] state);
 localparam [63:0] INF=64'h7f8000007f800000, NANPAIR=64'h7fc000007fc00000;
 localparam IDLE=0,IO_SEND=1,IO_WAIT=2,JOB=3,INIT_L=4,INIT_P=5,INIT_D=6,INIT_C=7,INIT_O=8,
 SEED_L=9,SEED_P=10,SEED_D=11,MIN=12,MIN_GOT=13,SELECT=14,ACTIVE=15,ACTIVE_GOT=16,
 ACTIVE_CLEAR=17,ACTIVE_CLOSED=18,PARENT_NODE=19,PARENT_LABEL=20,ROW0=21,ROW1=22,
 EDGE=23,EDGE_GOT=24,CHILD=25,COST=26,EMIT=27,NEXT_NODE=28,FENCE_START=29,FENCE_WAIT=30,
 COMMIT=31,COMMIT_P=32,COMMIT_L=33,COMMIT_UPDATE=34,COMMIT_PENDING=35,COMMIT_SET=36,
 CLOSE=37,CLOSE_GOT=38,CLOSE_NODE=39,CLOSE_CELL=40,CLOSE_LABEL=41,CLOSE_OUTPUT=42,
 CLOSE_WRITE=43,CLOSE_CLEAR=44,AFTER_CLOSE=45,FINISH_SAMPLE=46,FINISH_BATCH=47;
 reg [7:0] resume;reg [255:0] data;reg [4:0] offset;
 reg [31:0] i,source,nt,recorded,bucket,nextbucket,old_pending,active_count;
 reg [63:0] edgepos,edgeend;reg [127:0] pnode,cnode;reg [63:0] parent,proposal,label;
 reg [31:0] child,cellid;reg have_bucket;
 function automatic less(input [63:0] a,b);less=a[63:32]<b[63:32]||(a[63:32]==b[63:32]&&a[31:0]<b[31:0]);endfunction
 // byte_address is 35b; ma is a 32B-aligned physical line. All bases are line addresses.
 task automatic read_item(input [31:0] base,input [63:0] byteoff,input [7:0] ret);
 begin ma<=base+(byteoff>>5);offset<=byteoff[4:0];mw<=0;md<=0;mask<=0;mv<=1;resume<=ret;state<=IO_SEND;end endtask
 task automatic write_item(input [31:0] base,input [63:0] byteoff,input [255:0] val,input [31:0] strobes,input [7:0] ret);
 begin ma<=base+(byteoff>>5);mw<=1;md<=val<<(byteoff[4:0]*8);mask<=strobes<<byteoff[4:0];mv<=1;resume<=ret;state<=IO_SEND;end endtask
 assign rr=state==IO_WAIT;
 always @(posedge clk)begin
 if(rst)begin state<=IDLE;mv<=0;cv<=0;fence<=0;done<=0;error<=0;qid<=0;waves<=0;cycle<=0;end else begin
 cycle<=cycle+1;fence<=0;
 case(state)
 IDLE:if(start)begin if(nodes==0||nodes>67108864||jobs==0||cells==0||base_prop[4:0]!=0)error<=1;else begin qid<=0;read_item(base_job,0,JOB);end end
 IO_SEND:if(mr)begin mv<=0;state<=IO_WAIT;end
 IO_WAIT:if(rv)begin data<=rd>>(offset*8);state<=resume;end
 JOB:begin source<=data[31:0];nt<=data[63:32];recorded<=0;active_count<=1;have_bucket<=0;i<=0;state<=INIT_L;end
 INIT_L:if(i<(nodes+3)/4)begin write_item(base_label,i*32,{4{INF}},32'hffffffff,INIT_L);i<=i+1;end else begin i<=0;state<=INIT_P;end
 INIT_P:if(i<(nodes+3)/4)begin write_item(base_prop,i*32,{4{INF}},32'hffffffff,INIT_P);i<=i+1;end else begin i<=0;state<=INIT_D;end
 INIT_D:if(i<(nodes+7)/8)begin write_item(base_pending,i*32,{8{32'hffffffff}},32'hffffffff,INIT_D);i<=i+1;end else begin i<=0;state<=INIT_C;end
 INIT_C:if(i<(nodes+7)/8)begin write_item(base_closed,i*32,0,32'hffffffff,INIT_C);i<=i+1;end else begin i<=0;state<=INIT_O;end
 INIT_O:if(i<cells)begin write_item(base_output,(qid*cells+i)*8,NANPAIR,32'hff,INIT_O);i<=i+1;end else if(nt==0)state<=FINISH_SAMPLE;else state<=SEED_L;
 SEED_L:write_item(base_label,source*8,0,32'hff,SEED_P);
 SEED_P:write_item(base_prop,source*8,0,32'hff,SEED_D);
 SEED_D:begin write_item(base_pending,source*4,0,32'hf,MIN);i<=0;nextbucket<=32'hffffffff;end
 MIN:if(i<nodes)read_item(base_pending,i*4,MIN_GOT);else state<=SELECT;
 MIN_GOT:begin if(data[31:0]<nextbucket)nextbucket<=data[31:0];i<=i+1;state<=MIN;end
 SELECT:begin
 if(have_bucket&&nextbucket!=bucket)begin i<=0;state<=CLOSE;end
 else if(nextbucket==32'hffffffff)state<=FINISH_SAMPLE;
 else if(nextbucket>=4096||waves>=1000000)begin error<=1;state<=IDLE;end
 else begin bucket<=nextbucket;have_bucket<=1;i<=0;waves<=waves+1;state<=ACTIVE;end end
 ACTIVE:if(i<nodes)read_item(base_pending,i*4,ACTIVE_GOT);else state<=FENCE_START;
 ACTIVE_GOT:if(data[31:0]==bucket)begin active_count<=active_count-1;state<=ACTIVE_CLEAR;end else state<=NEXT_NODE;
 ACTIVE_CLEAR:write_item(base_pending,i*4,32'hffffffff,32'hf,ACTIVE_CLOSED);
 ACTIVE_CLOSED:write_item(base_closed,i*4,1,32'hf,PARENT_NODE);
 PARENT_NODE:read_item(base_node,i*16,PARENT_LABEL);
 PARENT_LABEL:begin pnode<=data[127:0];read_item(base_label,i*8,ROW0);end
 ROW0:begin parent<=data[63:0];read_item(base_row,i*8,ROW1);end
 ROW1:begin edgepos<=data[63:0];read_item(base_row,(i+1)*8,EDGE);end
 EDGE:begin edgeend<=data[63:0];state<=EDGE_GOT;end
 EDGE_GOT:if(edgepos<edgeend)read_item(base_edge,edgepos*8,CHILD);else state<=NEXT_NODE;
 CHILD:begin child<=data[31:0];read_item(base_node,data[31:0]*16,COST);end
 COST:begin cnode<=data[127:0];
 if(data[95:64]==0||(!pnode[127]&&!data[127]&&pnode[127:96]!=data[127:96]))begin edgepos<=edgepos+1;state<=EDGE_GOT;end
 else if(data[31:0]==2)state<=NEXT_NODE;
 else read_item(base_cost,data[63:32]*8,EMIT);end
 EMIT:begin cv<=1;cd<=child;cp<=parent;cc<=data[63:0];if(cv&&cr)begin cv<=0;edgepos<=edgepos+1;state<=EDGE_GOT;end end
 NEXT_NODE:begin i<=i+1;state<=ACTIVE;end
 FENCE_START:begin fence<=1;state<=FENCE_WAIT;end
 FENCE_WAIT:if(fence_done)begin i<=0;state<=COMMIT;end
 COMMIT:if(i<nodes)read_item(base_prop,i*8,COMMIT_P);else begin i<=0;nextbucket<=32'hffffffff;state<=MIN;end
 COMMIT_P:begin proposal<=data[63:0];read_item(base_label,i*8,COMMIT_L);end
 COMMIT_L:begin label<=data[63:0];if(less(proposal,data[63:0]))state<=COMMIT_UPDATE;else begin i<=i+1;state<=COMMIT;end end
 COMMIT_UPDATE:if(proposal[63:52]<bucket)begin error<=1;state<=IDLE;end else write_item(base_label,i*8,proposal,32'hff,COMMIT_PENDING);
 COMMIT_PENDING:read_item(base_pending,i*4,COMMIT_SET);
 COMMIT_SET:begin
 if(data[31:0]==32'hffffffff)active_count<=active_count+1;
 if(active_count>=524288&&data[31:0]==32'hffffffff)begin error<=1;state<=IDLE;end
 else begin write_item(base_pending,i*4,{20'd0,proposal[63:52]},32'hf,COMMIT);i<=i+1;end end
 CLOSE:if(i<nodes)read_item(base_closed,i*4,CLOSE_GOT);else state<=AFTER_CLOSE;
 CLOSE_GOT:if(data[31:0])read_item(base_node,i*16,CLOSE_NODE);else begin i<=i+1;state<=CLOSE;end
 CLOSE_NODE:if(data[31:0]==1)read_item(base_cell,(qid*nodes+i)*4,CLOSE_CELL);else state<=CLOSE_CLEAR;
 CLOSE_CELL:if(data[31:0]!=32'hffffffff)begin cellid<=data[31:0];read_item(base_label,i*8,CLOSE_LABEL);end else state<=CLOSE_CLEAR;
 CLOSE_LABEL:begin label<=data[63:0];read_item(base_output,(qid*cells+cellid)*8,CLOSE_OUTPUT);end
 CLOSE_OUTPUT:if(data[62:55]==255&&data[54:32]!=0)begin recorded<=recorded+1;state<=CLOSE_WRITE;end else if(less(label,data[63:0]))state<=CLOSE_WRITE;else state<=CLOSE_CLEAR;
 CLOSE_WRITE:write_item(base_output,(qid*cells+cellid)*8,label,32'hff,CLOSE_CLEAR);
 CLOSE_CLEAR:begin write_item(base_closed,i*4,0,32'hf,CLOSE);i<=i+1;end
 AFTER_CLOSE:begin have_bucket<=0;if(recorded==nt)state<=FINISH_SAMPLE;else state<=SELECT;end
 FINISH_SAMPLE:if(qid+1==jobs)state<=FINISH_BATCH;else begin qid<=qid+1;read_item(base_job,(qid+1)*32,JOB);end
 FINISH_BATCH:begin done<=1;state<=IDLE;end
 default:begin error<=1;state<=IDLE;end
 endcase
 end end
endmodule
