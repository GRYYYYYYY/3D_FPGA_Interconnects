from pathlib import Path
r=Path(__file__).resolve().parents[1]/'rtl';s=(r/'owner_pipeline.sv').read_text()
a=s.index('module sparse_owner_pipe');b=s.index(' localparam',a)
s=s[:a]+'''// External backing contains two 128-bit node records per 32B line:
// {flags32 (bit0 changed), pending32, lexical_label64}. No full-node RTL arrays.
// Ops: READ=0, MARK_CHANGED=1, VALID_POP=2, COMMIT=3, CLEAR_CHANGED=4, SEED=5.
module r2_node_state #(parameter OWNER_BITS=3)(input wire clk,rst,iv,output wire ir,input wire [31:0] node,
 input wire [2:0] opcode,input wire [63:0] operand,input wire [31:0] argument,input wire [5:0] tag,
 input wire [31:0] state_base,node_count,input wire fence,output reg fence_done,
 output wire ov,input wire ordy,output wire [31:0] onode,output wire [5:0] otag,output wire [3:0] status,output wire [127:0] old_record,
 output reg mem_valid,input wire mem_ready,output reg mem_write,output reg [31:0] mem_line,
 output reg [5:0] mem_id,output reg [255:0] mem_data,
 input wire rsp_valid,output wire rsp_ready,input wire [5:0] rsp_id,input wire [255:0] rsp_data,
 output wire idle,output reg error,output reg [31:0] accepted,retired,merges,hits,misses,raw_stall,
 output reg [5:0] mshr_peak,output reg [4:0] dirty_peak);
''' + s[b:]
s=s.replace('wire [95:0] qd;', 'wire [136:0] qd;wire [31:0] qnode=qd[136:105];')
s=s.replace('sparse_fifo #(.WIDTH(96)) request_fifo(clk,rst,iv&&!fence,fifo_ir,{node,pair}', 'sparse_fifo #(.WIDTH(137)) request_fifo(clk,rst,iv&&!fence,fifo_ir,{node,opcode,operand,argument,tag}')
s=s.replace('wire [35:0] event_data,event_out;', 'wire [169:0] event_data,event_out;')
s=s.replace('.WIDTH(36)', '.WIDTH(170)').replace('update_valid,update_ready,event_out', 'ov,ordy,event_out')
s=s.replace('assign {update_line,update_mask}=event_out;', 'assign {onode,otag,status,old_record}=event_out;')
s=s.replace('reg [31:0] ml[0:31],mcount[0:31];', 'reg [31:0] ml[0:31];reg [136:0] miss_request[0:31];')
s=s.replace('reg [255:0] mc[0:31];', '')
s=s.replace('reg [63:0] spair;', 'reg [136:0] srequest;')
s=s.replace("wire [31:0] qline={2'b0,qd[95:66]};", "wire [31:0] qline=state_base+((((qnode>>(OWNER_BITS+2))<<1)|((qnode>>1)&1))<<OWNER_BITS)+((qnode>>2)&((1<<OWNER_BITS)-1));")
s=s.replace('qline[7:3]', 'qline[OWNER_BITS+:5]')
a=s.index(' reg [255:0] hit_data,fill_data;');b=s.index(' wire advance=',a)
s=s[:a]+''' // The operation returns the immutable old record and atomically computes a
 // replacement. Status bit0 is op-specific success/append/first-mark; bit3 error.
 function automatic [131:0] apply_record(input [136:0] req,input [127:0] old);
  reg [127:0] value;reg [3:0] result;reg [31:0] pend;reg [15:0] version;
  begin value=old;result=0;pend=old[95:64];version=pend[27:12]+1;
   case(req[104:102])
   0:result[0]=1;
   1:begin value[96]=1;result[0]=!old[96];end
   2:if(pend[28]&&pend[27:0]==req[33:6])begin value[95:64]=0;result[0]=1;end
   3:if(req[101:38]>=old[63:0])result[3]=1;else begin
    value[63:0]=req[101:38];
    if(!pend[28]||pend[11:0]!=req[101:90])begin value[95:64]={3'b0,1'b1,version,req[101:90]};result[0]=1;end
   end
   4:begin result[0]=old[96];value[96]=0;end
   5:begin value[63:0]=0;value[95:64]=32'h10001000;result[0]=1;end
   default:result[3]=1;
   endcase
   apply_record={result,value};
  end
 endfunction
 wire [127:0] hit_old=base_data[srequest[105]*128+:128];
 wire [136:0] fill_request=miss_request[rd[260:256]];
 wire [127:0] fill_old=rd[fill_request[105]*128+:128];
 wire [131:0] hit_result=apply_record(srequest,hit_old),fill_result=apply_record(fill_request,fill_old);
 reg [255:0] hit_data,fill_data;
 wire hit_changed=hit_result[127:0]!=hit_old,fill_changed=fill_result[127:0]!=fill_old;
 always @*begin hit_data=base_data;hit_data[srequest[105]*128+:128]=hit_result[127:0];fill_data=rd[255:0];fill_data[fill_request[105]*128+:128]=fill_result[127:0];end
''' + s[b:]
s=s.replace("wire advance=!sv||(skind?1'b1:(hit_mask==0||event_r));", 'wire advance=!sv||skind||event_r;')
s=s.replace('fill_wait&&!sv&&(fill_mask==0||event_r)', 'fill_wait&&!sv&&event_r')
s=s.replace('rd[261]||(!sv&&(fill_mask==0||event_r))', 'rd[261]||(!sv&&event_r)')
s=s.replace('(matching>=0||hit>=0||(fm>=0&&victim>=0&&(!dirty[victim]||fw>=0)))', '(matching<0&&(hit>=0||(fm>=0&&victim>=0&&(!dirty[victim]||fw>=0))))')
s=s.replace('sv&&!skind&&advance&&hit_mask!=0', 'sv&&!skind&&advance&&hit_changed')
s=s.replace('assign event_v=hit_write||(fill_take&&fill_mask!=0);', 'assign event_v=(sv&&!skind&&advance)||fill_take;')
s=s.replace('assign event_data=fill_take?{ml[rd[260:256]],fill_mask}:{sline,hit_mask};', 'assign event_data=fill_take?{fill_request[136:105],fill_request[5:0],fill_result[131:128],fill_old}:{srequest[136:105],srequest[5:0],hit_result[131:128],hit_old};')
s=s.replace('!update_valid', '!ov')
s=s.replace('if(iv&&ir)accepted<=accepted+1;', 'if(iv&&ir)begin accepted<=accepted+1;if(node>=node_count)error<=1;end')
s=s.replace('<=fill_mask!=0;', '<=fill_changed;').replace('retired<=retired+mcount[rd[260:256]];', 'retired<=retired+1;if(fill_result[131])error<=1;')
s=s.replace('if(hit_mask!=0)dirty[sslot]<=1;', 'if(hit_changed)dirty[sslot]<=1;if(hit_result[131])error<=1;')
s=s.replace('snode<=qd[95:64];sline<=qline;spair<=qd[63:0];', 'snode<=qnode;sline<=qline;srequest<=qd;')
s=s.replace('mcount[fm]<=1;mc[fm]<={4{INF}};mc[fm][qd[65:64]*64+:64]<=qd[63:0];', 'miss_request[fm]<=qd;')
a=s.index('   if(dispatch&&matching>=0)');b=s.index('   if(!fence)',a);s=s[:a]+s[b:]
(r/'node_state.sv').write_text(s)
