`timescale 1ns/1ps
// Source-specific wire ABI: kind[3:0], generation[31:0], local_id[31:0].
// Nothing is truncated: scratch generation is an actual line identity, not gen8.
// Return destination is structural: local sources use codes 48..52 at ONE port;
// dynamic front sources use 0..47. External tag RAM preserves these 74 bits.
module lf_adapter #(parameter SOURCE=0)(
 input wire [3:0] kind,input wire [31:0] local_id,generation,line,
 output wire legal,write,output wire [73:0] packed_id,
 input wire [73:0] returned_id,input wire [255:0] returned_data,
 output wire [3:0] returned_kind,output wire [31:0] returned_local,returned_gen,
 output wire [255:0] read_data,output wire returned_legal);
 localparam CODE=SOURCE<48?SOURCE:SOURCE<112?48+((SOURCE-48)%2):SOURCE<176?50+((SOURCE-112)%2):52;
 localparam PORT=SOURCE<112?(SOURCE-48)/2:SOURCE<176?(SOURCE-112)/2:SOURCE-176;
 wire kind_ok;
 if(SOURCE<16)assign kind_ok=kind==2;
 else if(SOURCE<32)assign kind_ok=kind==1||kind==11;
 else if(SOURCE<48)assign kind_ok=kind==3;
 else if(SOURCE<112)assign kind_ok=kind==4||kind==5||kind==6;
 else if(SOURCE<176)assign kind_ok=kind==7||kind==8;
 else assign kind_ok=kind==0||kind==9||kind==10;
 assign legal=kind_ok&&(SOURCE<48||line[4:0]==PORT);
 assign write=kind==0||kind==6||kind==8||kind==9;
 assign packed_id={6'(CODE),kind,generation,local_id};
 assign {returned_kind,returned_gen,returned_local}=returned_id[67:0];
 assign returned_legal=returned_id[73:68]==CODE;
 assign read_data=(returned_kind==0||returned_kind==6||returned_kind==8||returned_kind==9)?256'b0:returned_data;
endmodule
