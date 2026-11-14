`timescale 1ns/1ps
// Finite eight-grant selection: one E write per eight-lane group each clock.
// FIRST_FREE and LANE_RR share the same bounded selection/grant resources.
module allocator_grouped #(parameter L=64,C=4,D=8,GROUP_LANES=8)(
 input logic clk,reset,input logic lane_rr,input logic [L*C-1:0] free_context,
 input logic [D-1:0] valid,nonempty,
 output logic [D-1:0] accepted,allocated,output logic [D*8-1:0] context_id
);
 localparam G=(L+GROUP_LANES-1)/GROUP_LANES;
 logic [$clog2(L)-1:0] pointer,next_pointer;
 logic [L*C-1:0] available;logic [G-1:0] used_group;integer chosen;logic blocked;
 always_comb begin
  accepted=0;allocated=0;context_id=0;available=free_context;used_group=0;next_pointer=pointer;blocked=0;
  for(integer n=0;n<D;n=n+1)begin
   chosen=-1;
   if(!blocked&&valid[n])begin
    if(lane_rr)begin
     for(integer k=0;k<L;k=k+1)for(integer j=0;j<C;j=j+1)
      if(chosen<0&&!used_group[((next_pointer+k)%L)/GROUP_LANES]&&available[((next_pointer+k)%L)*C+j])chosen=((next_pointer+k)%L)*C+j;
    end else for(integer i=0;i<L*C;i=i+1)if(chosen<0&&!used_group[(i/C)/GROUP_LANES]&&available[i])chosen=i;
    if(chosen>=0)begin
     accepted[n]=1;context_id[n*8+:8]=chosen;
     if(nonempty[n])begin allocated[n]=1;available[chosen]=0;used_group[(chosen/C)/GROUP_LANES]=1;if(lane_rr)next_pointer=(chosen/C+1)%L;end
    end else blocked=1;
   end else blocked=1;
  end
 end
 always_ff @(posedge clk)if(reset)pointer<=0;else pointer<=next_pointer;
endmodule
