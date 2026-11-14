`timescale 1ns/1ps
module probe_apply(input logic[255:0] old_labels,line_input,input logic[63:0] operand,input logic[67:0] oldpv,input logic[2:0] op,input logic[1:0] sector,input logic[27:0] argument,output logic changed,output logic reference_changed);
 wire[2:0] apply_slot=0;wire[2:0] ops[1];wire[1:0] sectors[1];wire[255:0] apply_labels=old_labels;
 assign ops[0]=op;assign sectors[0]=sector;
 wire[63:0] single_label;wire[16:0] single_pv;wire[3:0] single_status;
 wire[63:0] all_new_label[4];wire[16:0] all_new_pv[4];wire[3:0] all_status[4];wire[255:0] all_labels;
 pending17_transform single(old_labels[sector*64+:64],operand,oldpv[sector*17+:17],op,argument,single_label,single_pv,single_status);
 for(genvar g=0;g<4;g=g+1)begin
  pending17_transform row(old_labels[g*64+:64],line_input[g*64+:64],oldpv[g*17+:17],3'd3,28'b0,all_new_label[g],all_new_pv[g],all_status[g]);
  assign all_labels[g*64+:64]=all_new_label[g];
 end
 logic computed_changed;
 always_comb begin
  computed_changed=0;
  case(ops[apply_slot])
   3:computed_changed=single_status!=4'd8;
   5:computed_changed=apply_labels[sectors[apply_slot]*64+:64]!=64'b0;
   7:begin
    for(integer s=0;s<4;s=s+1)if(all_status[s]!=4'd8)computed_changed=1;
   end
   default:computed_changed=0;
  endcase
 end

 logic[255:0] expected;
 always_comb begin expected=old_labels;if(op==7)expected=all_labels;else expected[sector*64+:64]=single_label;end
 assign changed=computed_changed;assign reference_changed=expected!=old_labels;
endmodule
