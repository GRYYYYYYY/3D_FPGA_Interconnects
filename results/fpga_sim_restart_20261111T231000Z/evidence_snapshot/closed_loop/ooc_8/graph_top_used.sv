`timescale 1ns/1ps
// 64 (or tile 8) arithmetic lanes and owners, finite shared candidate bus.
// 32 registered physical-channel arbiters. No unconstrained free crossbar.
module graph_top #(parameter OWNERS=64, OB=$clog2(OWNERS))(
 input wire clk,rst,start,input wire [31:0] nodes,jobs,cells,
 input wire [31:0] base_row,base_edge,base_node,base_cost,base_cell,base_job,
 input wire [31:0] base_label,base_prop,base_pending,base_closed,base_output,
 output reg [31:0] mem_valid,input wire [31:0] mem_ready,output reg [31:0] mem_write,
 output reg [32*32-1:0] mem_line,output reg [32*256-1:0] mem_data,
 output reg [32*32-1:0] mem_mask,output reg [32*13-1:0] mem_id,
 input wire [31:0] rsp_valid,output reg [31:0] rsp_ready,
 input wire [32*13-1:0] rsp_id,input wire [32*256-1:0] rsp_data,
 output wire done,error,output wire [31:0] qid,waves,output wire [63:0] cycle,
 output wire [7:0] state,output wire [OWNERS*32-1:0] accepted,retired);
 wire cmv,cmw,crv;reg cmr;wire crr;wire [31:0] cma,cmm;wire [255:0] cmd;reg [255:0] crd;
 wire cv,cr,cf;wire [31:0] cd;wire [63:0] cp,cc;reg cfd;wire ce;
 graph_control control(.clk(clk),.rst(rst),.start(start),.nodes(nodes),.jobs(jobs),.cells(cells),
 .base_row(base_row),.base_edge(base_edge),.base_node(base_node),.base_cost(base_cost),.base_cell(base_cell),.base_job(base_job),
 .base_label(base_label),.base_prop(base_prop),.base_pending(base_pending),.base_closed(base_closed),.base_output(base_output),
 .mv(cmv),.mr(cmr),.mw(cmw),.ma(cma),.md(cmd),.mask(cmm),.rv(crv),.rr(crr),.rd(crd),
 .cv(cv),.cr(cr),.cd(cd),.cp(cp),.cc(cc),.fence(cf),.fence_done(cfd),.done(done),.error(ce),.qid(qid),.waves(waves),.cycle(cycle),.state(state));
 wire [OWNERS-1:0] lir,lov,le;reg [OWNERS-1:0] lor;wire [31:0] ld[0:OWNERS-1];wire [63:0] lp[0:OWNERS-1];
 reg [OB-1:0] produce,arbit;reg busv;wire busr;reg [31:0] busdst;reg [63:0] buspair;
 wire [OWNERS-1:0] oready,ofd,oe,omv,omw,orr;reg [OWNERS-1:0] omr,orv;
 wire [23:0] oml[0:OWNERS-1];wire [255:0] omd[0:OWNERS-1];wire [5:0] omid[0:OWNERS-1];
 reg [5:0] orid[0:OWNERS-1];reg [255:0] ord[0:OWNERS-1];
 reg fencing,sent;reg [OWNERS-1:0] fenced;reg ofence;
 assign error=ce|(|le)|(|oe);assign cr=lir[produce]&&!fencing;
 assign busr=oready[busdst[2+:OB]];
 genvar g;
 generate for(g=0;g<OWNERS;g=g+1)begin: owners
 pair_lane lane(.clk(clk),.rst(rst),.iv(cv&&produce==g&&!fencing),.ir(lir[g]),.dst(cd),.parent(cp),.cost(cc),.ov(lov[g]),.or_(lor[g]),.od(ld[g]),.pair(lp[g]),.error(le[g]));
 owner_service #(.OWNER_BITS(OB)) service(.clk(clk),.rst(rst),.req_valid(busv&&busdst[2+:OB]==g),.req_ready(oready[g]),
 .req_line(busdst[25:2]),.req_sector(busdst[1:0]),.req_pair(buspair),.fence(ofence),.fence_done(ofd[g]),.error(oe[g]),
 .mem_valid(omv[g]),.mem_ready(omr[g]),.mem_write(omw[g]),.mem_line(oml[g]),.mem_data(omd[g]),.mem_id(omid[g]),
 .rsp_valid(orv[g]),.rsp_ready(orr[g]),.rsp_id(orid[g]),.rsp_data(ord[g]),.accepted(accepted[g*32+:32]),.retired(retired[g*32+:32]));
 end endgenerate
 integer chosen,k,ix;
 always @*begin chosen=-1;lor=0;
 for(integer j=OWNERS-1;j>=0;j=j-1)begin ix=(arbit+j)%OWNERS;if(lov[ix])chosen=ix;end
 if((!busv||busr)&&chosen>=0)lor[chosen]=1;
 end
 always @(posedge clk)if(rst)begin produce<=0;arbit<=0;busv<=0;fencing<=0;sent<=0;fenced<=0;ofence<=0;cfd<=0;end else begin
 ofence<=0;cfd<=0;
 if(cv&&cr)produce<=produce+1'b1;
 if(busv&&busr)busv<=0;
 if((!busv||busr)&&chosen>=0)begin busv<=1;busdst<=ld[chosen];buspair<=lp[chosen];arbit<=chosen+1;end
 if(cf)begin fencing<=1;sent<=0;fenced<=0;end
 if(fencing&&!sent&&lov==0&&!busv)begin ofence<=1;sent<=1;end
 if(sent)begin fenced<=fenced|ofd;if(&(fenced|ofd))begin cfd<=1;fencing<=0;sent<=0;end end
 end
 // One-entry registered request buffer per physical channel; arbitration rotates
 // across owners plus the graph controller. The response ID preserves ownership.
 integer pick[0:31];reg [6:0] rotation[0:31];integer channel,idowner,candidate;
 reg control_rv;
 assign crv=control_rv;
 always @*begin
 omr=0;cmr=0;orv=0;control_rv=0;crd=0;rsp_ready=0;
 for(integer z=0;z<OWNERS;z=z+1)begin orid[z]=0;ord[z]=0;end
 for(integer c=0;c<32;c=c+1)begin
 pick[c]=-1;
 for(integer j=OWNERS;j>=0;j=j-1)begin
 if(j==OWNERS)begin if(cmv&&cma[4:0]==c)pick[c]=j;end
 else if(omv[j]&&((base_prop+oml[j])%32)==c)pick[c]=j;
 end
 for(integer j=OWNERS;j>=0;j=j-1)if(j>=rotation[c])begin
 if(j==OWNERS)begin if(cmv&&cma[4:0]==c)pick[c]=j;end
 else if(omv[j]&&((base_prop+oml[j])%32)==c)pick[c]=j;
 end
 if(!mem_valid[c]||mem_ready[c])begin
 if(pick[c]==OWNERS)cmr=1;else if(pick[c]>=0)omr[pick[c]]=1;
 end
 idowner=rsp_id[c*13+6+:7];
 if(rsp_valid[c])begin
 if(idowner==OWNERS)begin control_rv=1;crd=rsp_data[c*256+:256];rsp_ready[c]=crr;end
 else if(idowner<OWNERS)begin orv[idowner]=1;orid[idowner]=rsp_id[c*13+:6];ord[idowner]=rsp_data[c*256+:256];rsp_ready[c]=orr[idowner];end
 end
 end
 end
 always @(posedge clk)if(rst)begin mem_valid<=0;for(integer c=0;c<32;c=c+1)rotation[c]<=0;end else begin
 for(integer c=0;c<32;c=c+1)if(!mem_valid[c]||mem_ready[c])begin
 mem_valid[c]<=pick[c]>=0;
 if(pick[c]>=0)begin
 rotation[c]<=pick[c]==OWNERS?0:pick[c]+1;
 if(pick[c]==OWNERS)begin mem_write[c]<=cmw;mem_line[c*32+:32]<=cma;mem_data[c*256+:256]<=cmd;mem_mask[c*32+:32]<=cmm;mem_id[c*13+:13]<={7'(OWNERS),6'd0};end
 else begin mem_write[c]<=omw[pick[c]];mem_line[c*32+:32]<=base_prop+oml[pick[c]];mem_data[c*256+:256]<=omd[pick[c]];mem_mask[c*32+:32]<=32'hffffffff;mem_id[c*13+:13]<={7'(pick[c]),omid[pick[c]]};end
 end end
 end
endmodule
