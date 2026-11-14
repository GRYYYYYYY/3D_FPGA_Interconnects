// Whole pending-word RMW. A bank-wide reservation is conservative but complete:
// all label/PV readers must use this service; the lock is released only when
// the write ACK, whole68bit PV write and directory/event publication have retired.
module pending17_transform(input logic [63:0] old_label,value,input logic [16:0] old_pv,
 input logic [2:0] opcode,input logic [27:0] argument,
 output logic [63:0] new_label,output logic [16:0] new_pv,output logic [3:0] status);
 always_comb begin
  new_label=old_label;new_pv=old_pv;status=0;
  case(opcode)
   2:if(old_pv[16]&&{old_pv[15:0],old_label[63:52]}==argument)begin new_pv=0;status=1;end
   3:if(value>=old_label)status=8;else begin
    new_label=value;
    if(!old_pv[16]||old_label[63:52]!=value[63:52])begin new_pv={1'b1,16'(old_pv[15:0]+1)};status=1;end
   end
   5:begin new_label=0;new_pv=17'h10001;status=1;end
   default:status=8;
  endcase
 end
endmodule
