`timescale 1ns/1ps
module lf_radix_network(
 input wire clk,reset,input wire [207:0] cv,output wire [207:0] cr,
 input wire [208*4-1:0] ck,input wire [208*32-1:0] cl,cid,cgen,
 input wire [160*256-1:0] local_write_data,
 output wire [207:0] rv,input wire [207:0] rr,
 output wire [208*4-1:0] rk,output wire [208*32-1:0] rid,rgen,
 output wire [208*256-1:0] rd,output wire [208*2-1:0] rstatus,
 output wire [31:0] mv,input wire [31:0] mr,output wire [31:0] mw,
 output wire [32*32-1:0] ml,output wire [32*5-1:0] mtag,output wire [32*256-1:0] md,
 input wire [31:0] sv,output wire [31:0] sr,input wire [32*5-1:0] stag,
 input wire [32*256-1:0] sd,input wire [32*2-1:0] sstatus,
 output wire [31:0] port_error,output reg error);
wire[63:0]fqv,fqr,fxv,fxr,bxv,bxr,frv,frr;
 wire[64*106-1:0]fqd,fxd;wire[383:0]fqdest,brdest;
 wire[64*332-1:0]brdata,frdata;
 lf_radix #(.WIDTH(106)) front_requests(.clk,.reset,.iv(fqv),.ir(fqr),.dest(fqdest),.idata(fqd),.ov(fxv),.ordy(fxr),.odata(fxd));
 lf_radix #(.WIDTH(332)) front_returns(.clk,.reset,.iv(bxv),.ir(bxr),.dest(brdest),.idata(brdata),.ov(frv),.ordy(frr),.odata(frdata));
 assign fqv[63:48]=0;assign fqd[64*106-1:48*106]=0;assign fqdest[383:288]=0;assign frr[63:48]=0;
 wire [207:0] qv,qr,legal,write_,rlegal;
 wire [73:0] qi[208],ai[208],ri[208];wire [31:0] ql[208];
 wire [255:0] qd[160],raw_rd[208];wire qw[160];
 wire [127:0] gv,gr,bv,br;wire [362:0] gd[128];
 wire [331:0] bd[128];wire [5:0] dest[128];
 wire [207:0] source_accept;
 always @(posedge clk)if(reset)error<=0;else if(|(cv&~legal)|||(rv&~rlegal)|||port_error)error<=1;

lf_adapter #(.SOURCE(0)) a0(.kind(ck[0+:4]),.local_id(cid[0+:32]),.generation(cgen[0+:32]),.line(cl[0+:32]),.legal(legal[0]),.write(write_[0]),.packed_id(ai[0]),.returned_id(ri[0]),.returned_data(raw_rd[0]),.returned_kind(rk[0+:4]),.returned_local(rid[0+:32]),.returned_gen(rgen[0+:32]),.read_data(rd[0+:256]),.returned_legal(rlegal[0]));
 assign cr[0]=source_accept[0]&&legal[0];
assign fqv[0]=cv[0]&&legal[0];assign source_accept[0]=fqr[0];assign fqd[0*106+:106]={cl[0*32+:32],ai[0]};assign fqdest[0*6+:6]={cl[0*32+:5],1'b0};
lf_adapter #(.SOURCE(1)) a1(.kind(ck[4+:4]),.local_id(cid[32+:32]),.generation(cgen[32+:32]),.line(cl[32+:32]),.legal(legal[1]),.write(write_[1]),.packed_id(ai[1]),.returned_id(ri[1]),.returned_data(raw_rd[1]),.returned_kind(rk[4+:4]),.returned_local(rid[32+:32]),.returned_gen(rgen[32+:32]),.read_data(rd[256+:256]),.returned_legal(rlegal[1]));
 assign cr[1]=source_accept[1]&&legal[1];
assign fqv[1]=cv[1]&&legal[1];assign source_accept[1]=fqr[1];assign fqd[1*106+:106]={cl[1*32+:32],ai[1]};assign fqdest[1*6+:6]={cl[1*32+:5],1'b0};
lf_adapter #(.SOURCE(2)) a2(.kind(ck[8+:4]),.local_id(cid[64+:32]),.generation(cgen[64+:32]),.line(cl[64+:32]),.legal(legal[2]),.write(write_[2]),.packed_id(ai[2]),.returned_id(ri[2]),.returned_data(raw_rd[2]),.returned_kind(rk[8+:4]),.returned_local(rid[64+:32]),.returned_gen(rgen[64+:32]),.read_data(rd[512+:256]),.returned_legal(rlegal[2]));
 assign cr[2]=source_accept[2]&&legal[2];
assign fqv[2]=cv[2]&&legal[2];assign source_accept[2]=fqr[2];assign fqd[2*106+:106]={cl[2*32+:32],ai[2]};assign fqdest[2*6+:6]={cl[2*32+:5],1'b0};
lf_adapter #(.SOURCE(3)) a3(.kind(ck[12+:4]),.local_id(cid[96+:32]),.generation(cgen[96+:32]),.line(cl[96+:32]),.legal(legal[3]),.write(write_[3]),.packed_id(ai[3]),.returned_id(ri[3]),.returned_data(raw_rd[3]),.returned_kind(rk[12+:4]),.returned_local(rid[96+:32]),.returned_gen(rgen[96+:32]),.read_data(rd[768+:256]),.returned_legal(rlegal[3]));
 assign cr[3]=source_accept[3]&&legal[3];
assign fqv[3]=cv[3]&&legal[3];assign source_accept[3]=fqr[3];assign fqd[3*106+:106]={cl[3*32+:32],ai[3]};assign fqdest[3*6+:6]={cl[3*32+:5],1'b0};
lf_adapter #(.SOURCE(4)) a4(.kind(ck[16+:4]),.local_id(cid[128+:32]),.generation(cgen[128+:32]),.line(cl[128+:32]),.legal(legal[4]),.write(write_[4]),.packed_id(ai[4]),.returned_id(ri[4]),.returned_data(raw_rd[4]),.returned_kind(rk[16+:4]),.returned_local(rid[128+:32]),.returned_gen(rgen[128+:32]),.read_data(rd[1024+:256]),.returned_legal(rlegal[4]));
 assign cr[4]=source_accept[4]&&legal[4];
assign fqv[4]=cv[4]&&legal[4];assign source_accept[4]=fqr[4];assign fqd[4*106+:106]={cl[4*32+:32],ai[4]};assign fqdest[4*6+:6]={cl[4*32+:5],1'b0};
lf_adapter #(.SOURCE(5)) a5(.kind(ck[20+:4]),.local_id(cid[160+:32]),.generation(cgen[160+:32]),.line(cl[160+:32]),.legal(legal[5]),.write(write_[5]),.packed_id(ai[5]),.returned_id(ri[5]),.returned_data(raw_rd[5]),.returned_kind(rk[20+:4]),.returned_local(rid[160+:32]),.returned_gen(rgen[160+:32]),.read_data(rd[1280+:256]),.returned_legal(rlegal[5]));
 assign cr[5]=source_accept[5]&&legal[5];
assign fqv[5]=cv[5]&&legal[5];assign source_accept[5]=fqr[5];assign fqd[5*106+:106]={cl[5*32+:32],ai[5]};assign fqdest[5*6+:6]={cl[5*32+:5],1'b0};
lf_adapter #(.SOURCE(6)) a6(.kind(ck[24+:4]),.local_id(cid[192+:32]),.generation(cgen[192+:32]),.line(cl[192+:32]),.legal(legal[6]),.write(write_[6]),.packed_id(ai[6]),.returned_id(ri[6]),.returned_data(raw_rd[6]),.returned_kind(rk[24+:4]),.returned_local(rid[192+:32]),.returned_gen(rgen[192+:32]),.read_data(rd[1536+:256]),.returned_legal(rlegal[6]));
 assign cr[6]=source_accept[6]&&legal[6];
assign fqv[6]=cv[6]&&legal[6];assign source_accept[6]=fqr[6];assign fqd[6*106+:106]={cl[6*32+:32],ai[6]};assign fqdest[6*6+:6]={cl[6*32+:5],1'b0};
lf_adapter #(.SOURCE(7)) a7(.kind(ck[28+:4]),.local_id(cid[224+:32]),.generation(cgen[224+:32]),.line(cl[224+:32]),.legal(legal[7]),.write(write_[7]),.packed_id(ai[7]),.returned_id(ri[7]),.returned_data(raw_rd[7]),.returned_kind(rk[28+:4]),.returned_local(rid[224+:32]),.returned_gen(rgen[224+:32]),.read_data(rd[1792+:256]),.returned_legal(rlegal[7]));
 assign cr[7]=source_accept[7]&&legal[7];
assign fqv[7]=cv[7]&&legal[7];assign source_accept[7]=fqr[7];assign fqd[7*106+:106]={cl[7*32+:32],ai[7]};assign fqdest[7*6+:6]={cl[7*32+:5],1'b0};
lf_adapter #(.SOURCE(8)) a8(.kind(ck[32+:4]),.local_id(cid[256+:32]),.generation(cgen[256+:32]),.line(cl[256+:32]),.legal(legal[8]),.write(write_[8]),.packed_id(ai[8]),.returned_id(ri[8]),.returned_data(raw_rd[8]),.returned_kind(rk[32+:4]),.returned_local(rid[256+:32]),.returned_gen(rgen[256+:32]),.read_data(rd[2048+:256]),.returned_legal(rlegal[8]));
 assign cr[8]=source_accept[8]&&legal[8];
assign fqv[8]=cv[8]&&legal[8];assign source_accept[8]=fqr[8];assign fqd[8*106+:106]={cl[8*32+:32],ai[8]};assign fqdest[8*6+:6]={cl[8*32+:5],1'b0};
lf_adapter #(.SOURCE(9)) a9(.kind(ck[36+:4]),.local_id(cid[288+:32]),.generation(cgen[288+:32]),.line(cl[288+:32]),.legal(legal[9]),.write(write_[9]),.packed_id(ai[9]),.returned_id(ri[9]),.returned_data(raw_rd[9]),.returned_kind(rk[36+:4]),.returned_local(rid[288+:32]),.returned_gen(rgen[288+:32]),.read_data(rd[2304+:256]),.returned_legal(rlegal[9]));
 assign cr[9]=source_accept[9]&&legal[9];
assign fqv[9]=cv[9]&&legal[9];assign source_accept[9]=fqr[9];assign fqd[9*106+:106]={cl[9*32+:32],ai[9]};assign fqdest[9*6+:6]={cl[9*32+:5],1'b0};
lf_adapter #(.SOURCE(10)) a10(.kind(ck[40+:4]),.local_id(cid[320+:32]),.generation(cgen[320+:32]),.line(cl[320+:32]),.legal(legal[10]),.write(write_[10]),.packed_id(ai[10]),.returned_id(ri[10]),.returned_data(raw_rd[10]),.returned_kind(rk[40+:4]),.returned_local(rid[320+:32]),.returned_gen(rgen[320+:32]),.read_data(rd[2560+:256]),.returned_legal(rlegal[10]));
 assign cr[10]=source_accept[10]&&legal[10];
assign fqv[10]=cv[10]&&legal[10];assign source_accept[10]=fqr[10];assign fqd[10*106+:106]={cl[10*32+:32],ai[10]};assign fqdest[10*6+:6]={cl[10*32+:5],1'b0};
lf_adapter #(.SOURCE(11)) a11(.kind(ck[44+:4]),.local_id(cid[352+:32]),.generation(cgen[352+:32]),.line(cl[352+:32]),.legal(legal[11]),.write(write_[11]),.packed_id(ai[11]),.returned_id(ri[11]),.returned_data(raw_rd[11]),.returned_kind(rk[44+:4]),.returned_local(rid[352+:32]),.returned_gen(rgen[352+:32]),.read_data(rd[2816+:256]),.returned_legal(rlegal[11]));
 assign cr[11]=source_accept[11]&&legal[11];
assign fqv[11]=cv[11]&&legal[11];assign source_accept[11]=fqr[11];assign fqd[11*106+:106]={cl[11*32+:32],ai[11]};assign fqdest[11*6+:6]={cl[11*32+:5],1'b0};
lf_adapter #(.SOURCE(12)) a12(.kind(ck[48+:4]),.local_id(cid[384+:32]),.generation(cgen[384+:32]),.line(cl[384+:32]),.legal(legal[12]),.write(write_[12]),.packed_id(ai[12]),.returned_id(ri[12]),.returned_data(raw_rd[12]),.returned_kind(rk[48+:4]),.returned_local(rid[384+:32]),.returned_gen(rgen[384+:32]),.read_data(rd[3072+:256]),.returned_legal(rlegal[12]));
 assign cr[12]=source_accept[12]&&legal[12];
assign fqv[12]=cv[12]&&legal[12];assign source_accept[12]=fqr[12];assign fqd[12*106+:106]={cl[12*32+:32],ai[12]};assign fqdest[12*6+:6]={cl[12*32+:5],1'b0};
lf_adapter #(.SOURCE(13)) a13(.kind(ck[52+:4]),.local_id(cid[416+:32]),.generation(cgen[416+:32]),.line(cl[416+:32]),.legal(legal[13]),.write(write_[13]),.packed_id(ai[13]),.returned_id(ri[13]),.returned_data(raw_rd[13]),.returned_kind(rk[52+:4]),.returned_local(rid[416+:32]),.returned_gen(rgen[416+:32]),.read_data(rd[3328+:256]),.returned_legal(rlegal[13]));
 assign cr[13]=source_accept[13]&&legal[13];
assign fqv[13]=cv[13]&&legal[13];assign source_accept[13]=fqr[13];assign fqd[13*106+:106]={cl[13*32+:32],ai[13]};assign fqdest[13*6+:6]={cl[13*32+:5],1'b0};
lf_adapter #(.SOURCE(14)) a14(.kind(ck[56+:4]),.local_id(cid[448+:32]),.generation(cgen[448+:32]),.line(cl[448+:32]),.legal(legal[14]),.write(write_[14]),.packed_id(ai[14]),.returned_id(ri[14]),.returned_data(raw_rd[14]),.returned_kind(rk[56+:4]),.returned_local(rid[448+:32]),.returned_gen(rgen[448+:32]),.read_data(rd[3584+:256]),.returned_legal(rlegal[14]));
 assign cr[14]=source_accept[14]&&legal[14];
assign fqv[14]=cv[14]&&legal[14];assign source_accept[14]=fqr[14];assign fqd[14*106+:106]={cl[14*32+:32],ai[14]};assign fqdest[14*6+:6]={cl[14*32+:5],1'b0};
lf_adapter #(.SOURCE(15)) a15(.kind(ck[60+:4]),.local_id(cid[480+:32]),.generation(cgen[480+:32]),.line(cl[480+:32]),.legal(legal[15]),.write(write_[15]),.packed_id(ai[15]),.returned_id(ri[15]),.returned_data(raw_rd[15]),.returned_kind(rk[60+:4]),.returned_local(rid[480+:32]),.returned_gen(rgen[480+:32]),.read_data(rd[3840+:256]),.returned_legal(rlegal[15]));
 assign cr[15]=source_accept[15]&&legal[15];
assign fqv[15]=cv[15]&&legal[15];assign source_accept[15]=fqr[15];assign fqd[15*106+:106]={cl[15*32+:32],ai[15]};assign fqdest[15*6+:6]={cl[15*32+:5],1'b0};
lf_adapter #(.SOURCE(16)) a16(.kind(ck[64+:4]),.local_id(cid[512+:32]),.generation(cgen[512+:32]),.line(cl[512+:32]),.legal(legal[16]),.write(write_[16]),.packed_id(ai[16]),.returned_id(ri[16]),.returned_data(raw_rd[16]),.returned_kind(rk[64+:4]),.returned_local(rid[512+:32]),.returned_gen(rgen[512+:32]),.read_data(rd[4096+:256]),.returned_legal(rlegal[16]));
 assign cr[16]=source_accept[16]&&legal[16];
assign fqv[16]=cv[16]&&legal[16];assign source_accept[16]=fqr[16];assign fqd[16*106+:106]={cl[16*32+:32],ai[16]};assign fqdest[16*6+:6]={cl[16*32+:5],1'b1};
lf_adapter #(.SOURCE(17)) a17(.kind(ck[68+:4]),.local_id(cid[544+:32]),.generation(cgen[544+:32]),.line(cl[544+:32]),.legal(legal[17]),.write(write_[17]),.packed_id(ai[17]),.returned_id(ri[17]),.returned_data(raw_rd[17]),.returned_kind(rk[68+:4]),.returned_local(rid[544+:32]),.returned_gen(rgen[544+:32]),.read_data(rd[4352+:256]),.returned_legal(rlegal[17]));
 assign cr[17]=source_accept[17]&&legal[17];
assign fqv[17]=cv[17]&&legal[17];assign source_accept[17]=fqr[17];assign fqd[17*106+:106]={cl[17*32+:32],ai[17]};assign fqdest[17*6+:6]={cl[17*32+:5],1'b1};
lf_adapter #(.SOURCE(18)) a18(.kind(ck[72+:4]),.local_id(cid[576+:32]),.generation(cgen[576+:32]),.line(cl[576+:32]),.legal(legal[18]),.write(write_[18]),.packed_id(ai[18]),.returned_id(ri[18]),.returned_data(raw_rd[18]),.returned_kind(rk[72+:4]),.returned_local(rid[576+:32]),.returned_gen(rgen[576+:32]),.read_data(rd[4608+:256]),.returned_legal(rlegal[18]));
 assign cr[18]=source_accept[18]&&legal[18];
assign fqv[18]=cv[18]&&legal[18];assign source_accept[18]=fqr[18];assign fqd[18*106+:106]={cl[18*32+:32],ai[18]};assign fqdest[18*6+:6]={cl[18*32+:5],1'b1};
lf_adapter #(.SOURCE(19)) a19(.kind(ck[76+:4]),.local_id(cid[608+:32]),.generation(cgen[608+:32]),.line(cl[608+:32]),.legal(legal[19]),.write(write_[19]),.packed_id(ai[19]),.returned_id(ri[19]),.returned_data(raw_rd[19]),.returned_kind(rk[76+:4]),.returned_local(rid[608+:32]),.returned_gen(rgen[608+:32]),.read_data(rd[4864+:256]),.returned_legal(rlegal[19]));
 assign cr[19]=source_accept[19]&&legal[19];
assign fqv[19]=cv[19]&&legal[19];assign source_accept[19]=fqr[19];assign fqd[19*106+:106]={cl[19*32+:32],ai[19]};assign fqdest[19*6+:6]={cl[19*32+:5],1'b1};
lf_adapter #(.SOURCE(20)) a20(.kind(ck[80+:4]),.local_id(cid[640+:32]),.generation(cgen[640+:32]),.line(cl[640+:32]),.legal(legal[20]),.write(write_[20]),.packed_id(ai[20]),.returned_id(ri[20]),.returned_data(raw_rd[20]),.returned_kind(rk[80+:4]),.returned_local(rid[640+:32]),.returned_gen(rgen[640+:32]),.read_data(rd[5120+:256]),.returned_legal(rlegal[20]));
 assign cr[20]=source_accept[20]&&legal[20];
assign fqv[20]=cv[20]&&legal[20];assign source_accept[20]=fqr[20];assign fqd[20*106+:106]={cl[20*32+:32],ai[20]};assign fqdest[20*6+:6]={cl[20*32+:5],1'b1};
lf_adapter #(.SOURCE(21)) a21(.kind(ck[84+:4]),.local_id(cid[672+:32]),.generation(cgen[672+:32]),.line(cl[672+:32]),.legal(legal[21]),.write(write_[21]),.packed_id(ai[21]),.returned_id(ri[21]),.returned_data(raw_rd[21]),.returned_kind(rk[84+:4]),.returned_local(rid[672+:32]),.returned_gen(rgen[672+:32]),.read_data(rd[5376+:256]),.returned_legal(rlegal[21]));
 assign cr[21]=source_accept[21]&&legal[21];
assign fqv[21]=cv[21]&&legal[21];assign source_accept[21]=fqr[21];assign fqd[21*106+:106]={cl[21*32+:32],ai[21]};assign fqdest[21*6+:6]={cl[21*32+:5],1'b1};
lf_adapter #(.SOURCE(22)) a22(.kind(ck[88+:4]),.local_id(cid[704+:32]),.generation(cgen[704+:32]),.line(cl[704+:32]),.legal(legal[22]),.write(write_[22]),.packed_id(ai[22]),.returned_id(ri[22]),.returned_data(raw_rd[22]),.returned_kind(rk[88+:4]),.returned_local(rid[704+:32]),.returned_gen(rgen[704+:32]),.read_data(rd[5632+:256]),.returned_legal(rlegal[22]));
 assign cr[22]=source_accept[22]&&legal[22];
assign fqv[22]=cv[22]&&legal[22];assign source_accept[22]=fqr[22];assign fqd[22*106+:106]={cl[22*32+:32],ai[22]};assign fqdest[22*6+:6]={cl[22*32+:5],1'b1};
lf_adapter #(.SOURCE(23)) a23(.kind(ck[92+:4]),.local_id(cid[736+:32]),.generation(cgen[736+:32]),.line(cl[736+:32]),.legal(legal[23]),.write(write_[23]),.packed_id(ai[23]),.returned_id(ri[23]),.returned_data(raw_rd[23]),.returned_kind(rk[92+:4]),.returned_local(rid[736+:32]),.returned_gen(rgen[736+:32]),.read_data(rd[5888+:256]),.returned_legal(rlegal[23]));
 assign cr[23]=source_accept[23]&&legal[23];
assign fqv[23]=cv[23]&&legal[23];assign source_accept[23]=fqr[23];assign fqd[23*106+:106]={cl[23*32+:32],ai[23]};assign fqdest[23*6+:6]={cl[23*32+:5],1'b1};
lf_adapter #(.SOURCE(24)) a24(.kind(ck[96+:4]),.local_id(cid[768+:32]),.generation(cgen[768+:32]),.line(cl[768+:32]),.legal(legal[24]),.write(write_[24]),.packed_id(ai[24]),.returned_id(ri[24]),.returned_data(raw_rd[24]),.returned_kind(rk[96+:4]),.returned_local(rid[768+:32]),.returned_gen(rgen[768+:32]),.read_data(rd[6144+:256]),.returned_legal(rlegal[24]));
 assign cr[24]=source_accept[24]&&legal[24];
assign fqv[24]=cv[24]&&legal[24];assign source_accept[24]=fqr[24];assign fqd[24*106+:106]={cl[24*32+:32],ai[24]};assign fqdest[24*6+:6]={cl[24*32+:5],1'b1};
lf_adapter #(.SOURCE(25)) a25(.kind(ck[100+:4]),.local_id(cid[800+:32]),.generation(cgen[800+:32]),.line(cl[800+:32]),.legal(legal[25]),.write(write_[25]),.packed_id(ai[25]),.returned_id(ri[25]),.returned_data(raw_rd[25]),.returned_kind(rk[100+:4]),.returned_local(rid[800+:32]),.returned_gen(rgen[800+:32]),.read_data(rd[6400+:256]),.returned_legal(rlegal[25]));
 assign cr[25]=source_accept[25]&&legal[25];
assign fqv[25]=cv[25]&&legal[25];assign source_accept[25]=fqr[25];assign fqd[25*106+:106]={cl[25*32+:32],ai[25]};assign fqdest[25*6+:6]={cl[25*32+:5],1'b1};
lf_adapter #(.SOURCE(26)) a26(.kind(ck[104+:4]),.local_id(cid[832+:32]),.generation(cgen[832+:32]),.line(cl[832+:32]),.legal(legal[26]),.write(write_[26]),.packed_id(ai[26]),.returned_id(ri[26]),.returned_data(raw_rd[26]),.returned_kind(rk[104+:4]),.returned_local(rid[832+:32]),.returned_gen(rgen[832+:32]),.read_data(rd[6656+:256]),.returned_legal(rlegal[26]));
 assign cr[26]=source_accept[26]&&legal[26];
assign fqv[26]=cv[26]&&legal[26];assign source_accept[26]=fqr[26];assign fqd[26*106+:106]={cl[26*32+:32],ai[26]};assign fqdest[26*6+:6]={cl[26*32+:5],1'b1};
lf_adapter #(.SOURCE(27)) a27(.kind(ck[108+:4]),.local_id(cid[864+:32]),.generation(cgen[864+:32]),.line(cl[864+:32]),.legal(legal[27]),.write(write_[27]),.packed_id(ai[27]),.returned_id(ri[27]),.returned_data(raw_rd[27]),.returned_kind(rk[108+:4]),.returned_local(rid[864+:32]),.returned_gen(rgen[864+:32]),.read_data(rd[6912+:256]),.returned_legal(rlegal[27]));
 assign cr[27]=source_accept[27]&&legal[27];
assign fqv[27]=cv[27]&&legal[27];assign source_accept[27]=fqr[27];assign fqd[27*106+:106]={cl[27*32+:32],ai[27]};assign fqdest[27*6+:6]={cl[27*32+:5],1'b1};
lf_adapter #(.SOURCE(28)) a28(.kind(ck[112+:4]),.local_id(cid[896+:32]),.generation(cgen[896+:32]),.line(cl[896+:32]),.legal(legal[28]),.write(write_[28]),.packed_id(ai[28]),.returned_id(ri[28]),.returned_data(raw_rd[28]),.returned_kind(rk[112+:4]),.returned_local(rid[896+:32]),.returned_gen(rgen[896+:32]),.read_data(rd[7168+:256]),.returned_legal(rlegal[28]));
 assign cr[28]=source_accept[28]&&legal[28];
assign fqv[28]=cv[28]&&legal[28];assign source_accept[28]=fqr[28];assign fqd[28*106+:106]={cl[28*32+:32],ai[28]};assign fqdest[28*6+:6]={cl[28*32+:5],1'b1};
lf_adapter #(.SOURCE(29)) a29(.kind(ck[116+:4]),.local_id(cid[928+:32]),.generation(cgen[928+:32]),.line(cl[928+:32]),.legal(legal[29]),.write(write_[29]),.packed_id(ai[29]),.returned_id(ri[29]),.returned_data(raw_rd[29]),.returned_kind(rk[116+:4]),.returned_local(rid[928+:32]),.returned_gen(rgen[928+:32]),.read_data(rd[7424+:256]),.returned_legal(rlegal[29]));
 assign cr[29]=source_accept[29]&&legal[29];
assign fqv[29]=cv[29]&&legal[29];assign source_accept[29]=fqr[29];assign fqd[29*106+:106]={cl[29*32+:32],ai[29]};assign fqdest[29*6+:6]={cl[29*32+:5],1'b1};
lf_adapter #(.SOURCE(30)) a30(.kind(ck[120+:4]),.local_id(cid[960+:32]),.generation(cgen[960+:32]),.line(cl[960+:32]),.legal(legal[30]),.write(write_[30]),.packed_id(ai[30]),.returned_id(ri[30]),.returned_data(raw_rd[30]),.returned_kind(rk[120+:4]),.returned_local(rid[960+:32]),.returned_gen(rgen[960+:32]),.read_data(rd[7680+:256]),.returned_legal(rlegal[30]));
 assign cr[30]=source_accept[30]&&legal[30];
assign fqv[30]=cv[30]&&legal[30];assign source_accept[30]=fqr[30];assign fqd[30*106+:106]={cl[30*32+:32],ai[30]};assign fqdest[30*6+:6]={cl[30*32+:5],1'b1};
lf_adapter #(.SOURCE(31)) a31(.kind(ck[124+:4]),.local_id(cid[992+:32]),.generation(cgen[992+:32]),.line(cl[992+:32]),.legal(legal[31]),.write(write_[31]),.packed_id(ai[31]),.returned_id(ri[31]),.returned_data(raw_rd[31]),.returned_kind(rk[124+:4]),.returned_local(rid[992+:32]),.returned_gen(rgen[992+:32]),.read_data(rd[7936+:256]),.returned_legal(rlegal[31]));
 assign cr[31]=source_accept[31]&&legal[31];
assign fqv[31]=cv[31]&&legal[31];assign source_accept[31]=fqr[31];assign fqd[31*106+:106]={cl[31*32+:32],ai[31]};assign fqdest[31*6+:6]={cl[31*32+:5],1'b1};
lf_adapter #(.SOURCE(32)) a32(.kind(ck[128+:4]),.local_id(cid[1024+:32]),.generation(cgen[1024+:32]),.line(cl[1024+:32]),.legal(legal[32]),.write(write_[32]),.packed_id(ai[32]),.returned_id(ri[32]),.returned_data(raw_rd[32]),.returned_kind(rk[128+:4]),.returned_local(rid[1024+:32]),.returned_gen(rgen[1024+:32]),.read_data(rd[8192+:256]),.returned_legal(rlegal[32]));
 assign cr[32]=source_accept[32]&&legal[32];
assign fqv[32]=cv[32]&&legal[32];assign source_accept[32]=fqr[32];assign fqd[32*106+:106]={cl[32*32+:32],ai[32]};assign fqdest[32*6+:6]={cl[32*32+:5],1'b1};
lf_adapter #(.SOURCE(33)) a33(.kind(ck[132+:4]),.local_id(cid[1056+:32]),.generation(cgen[1056+:32]),.line(cl[1056+:32]),.legal(legal[33]),.write(write_[33]),.packed_id(ai[33]),.returned_id(ri[33]),.returned_data(raw_rd[33]),.returned_kind(rk[132+:4]),.returned_local(rid[1056+:32]),.returned_gen(rgen[1056+:32]),.read_data(rd[8448+:256]),.returned_legal(rlegal[33]));
 assign cr[33]=source_accept[33]&&legal[33];
assign fqv[33]=cv[33]&&legal[33];assign source_accept[33]=fqr[33];assign fqd[33*106+:106]={cl[33*32+:32],ai[33]};assign fqdest[33*6+:6]={cl[33*32+:5],1'b1};
lf_adapter #(.SOURCE(34)) a34(.kind(ck[136+:4]),.local_id(cid[1088+:32]),.generation(cgen[1088+:32]),.line(cl[1088+:32]),.legal(legal[34]),.write(write_[34]),.packed_id(ai[34]),.returned_id(ri[34]),.returned_data(raw_rd[34]),.returned_kind(rk[136+:4]),.returned_local(rid[1088+:32]),.returned_gen(rgen[1088+:32]),.read_data(rd[8704+:256]),.returned_legal(rlegal[34]));
 assign cr[34]=source_accept[34]&&legal[34];
assign fqv[34]=cv[34]&&legal[34];assign source_accept[34]=fqr[34];assign fqd[34*106+:106]={cl[34*32+:32],ai[34]};assign fqdest[34*6+:6]={cl[34*32+:5],1'b1};
lf_adapter #(.SOURCE(35)) a35(.kind(ck[140+:4]),.local_id(cid[1120+:32]),.generation(cgen[1120+:32]),.line(cl[1120+:32]),.legal(legal[35]),.write(write_[35]),.packed_id(ai[35]),.returned_id(ri[35]),.returned_data(raw_rd[35]),.returned_kind(rk[140+:4]),.returned_local(rid[1120+:32]),.returned_gen(rgen[1120+:32]),.read_data(rd[8960+:256]),.returned_legal(rlegal[35]));
 assign cr[35]=source_accept[35]&&legal[35];
assign fqv[35]=cv[35]&&legal[35];assign source_accept[35]=fqr[35];assign fqd[35*106+:106]={cl[35*32+:32],ai[35]};assign fqdest[35*6+:6]={cl[35*32+:5],1'b1};
lf_adapter #(.SOURCE(36)) a36(.kind(ck[144+:4]),.local_id(cid[1152+:32]),.generation(cgen[1152+:32]),.line(cl[1152+:32]),.legal(legal[36]),.write(write_[36]),.packed_id(ai[36]),.returned_id(ri[36]),.returned_data(raw_rd[36]),.returned_kind(rk[144+:4]),.returned_local(rid[1152+:32]),.returned_gen(rgen[1152+:32]),.read_data(rd[9216+:256]),.returned_legal(rlegal[36]));
 assign cr[36]=source_accept[36]&&legal[36];
assign fqv[36]=cv[36]&&legal[36];assign source_accept[36]=fqr[36];assign fqd[36*106+:106]={cl[36*32+:32],ai[36]};assign fqdest[36*6+:6]={cl[36*32+:5],1'b1};
lf_adapter #(.SOURCE(37)) a37(.kind(ck[148+:4]),.local_id(cid[1184+:32]),.generation(cgen[1184+:32]),.line(cl[1184+:32]),.legal(legal[37]),.write(write_[37]),.packed_id(ai[37]),.returned_id(ri[37]),.returned_data(raw_rd[37]),.returned_kind(rk[148+:4]),.returned_local(rid[1184+:32]),.returned_gen(rgen[1184+:32]),.read_data(rd[9472+:256]),.returned_legal(rlegal[37]));
 assign cr[37]=source_accept[37]&&legal[37];
assign fqv[37]=cv[37]&&legal[37];assign source_accept[37]=fqr[37];assign fqd[37*106+:106]={cl[37*32+:32],ai[37]};assign fqdest[37*6+:6]={cl[37*32+:5],1'b1};
lf_adapter #(.SOURCE(38)) a38(.kind(ck[152+:4]),.local_id(cid[1216+:32]),.generation(cgen[1216+:32]),.line(cl[1216+:32]),.legal(legal[38]),.write(write_[38]),.packed_id(ai[38]),.returned_id(ri[38]),.returned_data(raw_rd[38]),.returned_kind(rk[152+:4]),.returned_local(rid[1216+:32]),.returned_gen(rgen[1216+:32]),.read_data(rd[9728+:256]),.returned_legal(rlegal[38]));
 assign cr[38]=source_accept[38]&&legal[38];
assign fqv[38]=cv[38]&&legal[38];assign source_accept[38]=fqr[38];assign fqd[38*106+:106]={cl[38*32+:32],ai[38]};assign fqdest[38*6+:6]={cl[38*32+:5],1'b1};
lf_adapter #(.SOURCE(39)) a39(.kind(ck[156+:4]),.local_id(cid[1248+:32]),.generation(cgen[1248+:32]),.line(cl[1248+:32]),.legal(legal[39]),.write(write_[39]),.packed_id(ai[39]),.returned_id(ri[39]),.returned_data(raw_rd[39]),.returned_kind(rk[156+:4]),.returned_local(rid[1248+:32]),.returned_gen(rgen[1248+:32]),.read_data(rd[9984+:256]),.returned_legal(rlegal[39]));
 assign cr[39]=source_accept[39]&&legal[39];
assign fqv[39]=cv[39]&&legal[39];assign source_accept[39]=fqr[39];assign fqd[39*106+:106]={cl[39*32+:32],ai[39]};assign fqdest[39*6+:6]={cl[39*32+:5],1'b1};
lf_adapter #(.SOURCE(40)) a40(.kind(ck[160+:4]),.local_id(cid[1280+:32]),.generation(cgen[1280+:32]),.line(cl[1280+:32]),.legal(legal[40]),.write(write_[40]),.packed_id(ai[40]),.returned_id(ri[40]),.returned_data(raw_rd[40]),.returned_kind(rk[160+:4]),.returned_local(rid[1280+:32]),.returned_gen(rgen[1280+:32]),.read_data(rd[10240+:256]),.returned_legal(rlegal[40]));
 assign cr[40]=source_accept[40]&&legal[40];
assign fqv[40]=cv[40]&&legal[40];assign source_accept[40]=fqr[40];assign fqd[40*106+:106]={cl[40*32+:32],ai[40]};assign fqdest[40*6+:6]={cl[40*32+:5],1'b1};
lf_adapter #(.SOURCE(41)) a41(.kind(ck[164+:4]),.local_id(cid[1312+:32]),.generation(cgen[1312+:32]),.line(cl[1312+:32]),.legal(legal[41]),.write(write_[41]),.packed_id(ai[41]),.returned_id(ri[41]),.returned_data(raw_rd[41]),.returned_kind(rk[164+:4]),.returned_local(rid[1312+:32]),.returned_gen(rgen[1312+:32]),.read_data(rd[10496+:256]),.returned_legal(rlegal[41]));
 assign cr[41]=source_accept[41]&&legal[41];
assign fqv[41]=cv[41]&&legal[41];assign source_accept[41]=fqr[41];assign fqd[41*106+:106]={cl[41*32+:32],ai[41]};assign fqdest[41*6+:6]={cl[41*32+:5],1'b1};
lf_adapter #(.SOURCE(42)) a42(.kind(ck[168+:4]),.local_id(cid[1344+:32]),.generation(cgen[1344+:32]),.line(cl[1344+:32]),.legal(legal[42]),.write(write_[42]),.packed_id(ai[42]),.returned_id(ri[42]),.returned_data(raw_rd[42]),.returned_kind(rk[168+:4]),.returned_local(rid[1344+:32]),.returned_gen(rgen[1344+:32]),.read_data(rd[10752+:256]),.returned_legal(rlegal[42]));
 assign cr[42]=source_accept[42]&&legal[42];
assign fqv[42]=cv[42]&&legal[42];assign source_accept[42]=fqr[42];assign fqd[42*106+:106]={cl[42*32+:32],ai[42]};assign fqdest[42*6+:6]={cl[42*32+:5],1'b1};
lf_adapter #(.SOURCE(43)) a43(.kind(ck[172+:4]),.local_id(cid[1376+:32]),.generation(cgen[1376+:32]),.line(cl[1376+:32]),.legal(legal[43]),.write(write_[43]),.packed_id(ai[43]),.returned_id(ri[43]),.returned_data(raw_rd[43]),.returned_kind(rk[172+:4]),.returned_local(rid[1376+:32]),.returned_gen(rgen[1376+:32]),.read_data(rd[11008+:256]),.returned_legal(rlegal[43]));
 assign cr[43]=source_accept[43]&&legal[43];
assign fqv[43]=cv[43]&&legal[43];assign source_accept[43]=fqr[43];assign fqd[43*106+:106]={cl[43*32+:32],ai[43]};assign fqdest[43*6+:6]={cl[43*32+:5],1'b1};
lf_adapter #(.SOURCE(44)) a44(.kind(ck[176+:4]),.local_id(cid[1408+:32]),.generation(cgen[1408+:32]),.line(cl[1408+:32]),.legal(legal[44]),.write(write_[44]),.packed_id(ai[44]),.returned_id(ri[44]),.returned_data(raw_rd[44]),.returned_kind(rk[176+:4]),.returned_local(rid[1408+:32]),.returned_gen(rgen[1408+:32]),.read_data(rd[11264+:256]),.returned_legal(rlegal[44]));
 assign cr[44]=source_accept[44]&&legal[44];
assign fqv[44]=cv[44]&&legal[44];assign source_accept[44]=fqr[44];assign fqd[44*106+:106]={cl[44*32+:32],ai[44]};assign fqdest[44*6+:6]={cl[44*32+:5],1'b1};
lf_adapter #(.SOURCE(45)) a45(.kind(ck[180+:4]),.local_id(cid[1440+:32]),.generation(cgen[1440+:32]),.line(cl[1440+:32]),.legal(legal[45]),.write(write_[45]),.packed_id(ai[45]),.returned_id(ri[45]),.returned_data(raw_rd[45]),.returned_kind(rk[180+:4]),.returned_local(rid[1440+:32]),.returned_gen(rgen[1440+:32]),.read_data(rd[11520+:256]),.returned_legal(rlegal[45]));
 assign cr[45]=source_accept[45]&&legal[45];
assign fqv[45]=cv[45]&&legal[45];assign source_accept[45]=fqr[45];assign fqd[45*106+:106]={cl[45*32+:32],ai[45]};assign fqdest[45*6+:6]={cl[45*32+:5],1'b1};
lf_adapter #(.SOURCE(46)) a46(.kind(ck[184+:4]),.local_id(cid[1472+:32]),.generation(cgen[1472+:32]),.line(cl[1472+:32]),.legal(legal[46]),.write(write_[46]),.packed_id(ai[46]),.returned_id(ri[46]),.returned_data(raw_rd[46]),.returned_kind(rk[184+:4]),.returned_local(rid[1472+:32]),.returned_gen(rgen[1472+:32]),.read_data(rd[11776+:256]),.returned_legal(rlegal[46]));
 assign cr[46]=source_accept[46]&&legal[46];
assign fqv[46]=cv[46]&&legal[46];assign source_accept[46]=fqr[46];assign fqd[46*106+:106]={cl[46*32+:32],ai[46]};assign fqdest[46*6+:6]={cl[46*32+:5],1'b1};
lf_adapter #(.SOURCE(47)) a47(.kind(ck[188+:4]),.local_id(cid[1504+:32]),.generation(cgen[1504+:32]),.line(cl[1504+:32]),.legal(legal[47]),.write(write_[47]),.packed_id(ai[47]),.returned_id(ri[47]),.returned_data(raw_rd[47]),.returned_kind(rk[188+:4]),.returned_local(rid[1504+:32]),.returned_gen(rgen[1504+:32]),.read_data(rd[12032+:256]),.returned_legal(rlegal[47]));
 assign cr[47]=source_accept[47]&&legal[47];
assign fqv[47]=cv[47]&&legal[47];assign source_accept[47]=fqr[47];assign fqd[47*106+:106]={cl[47*32+:32],ai[47]};assign fqdest[47*6+:6]={cl[47*32+:5],1'b1};
lf_adapter #(.SOURCE(48)) a48(.kind(ck[192+:4]),.local_id(cid[1536+:32]),.generation(cgen[1536+:32]),.line(cl[1536+:32]),.legal(legal[48]),.write(write_[48]),.packed_id(ai[48]),.returned_id(ri[48]),.returned_data(raw_rd[48]),.returned_kind(rk[192+:4]),.returned_local(rid[1536+:32]),.returned_gen(rgen[1536+:32]),.read_data(rd[12288+:256]),.returned_legal(rlegal[48]));
 assign cr[48]=source_accept[48]&&legal[48];
df_fifo #(.WIDTH(363),.DEPTH(4)) q48(.clk,.reset,.iv(cv[48]&&legal[48]),.ir(source_accept[48]),.idata({write_[48],cl[1536+:32],ai[48],local_write_data[0+:256]}),.ov(qv[48]),.ordy(qr[48]),.odata({qw[0],ql[48],qi[48],qd[0]}));
lf_adapter #(.SOURCE(49)) a49(.kind(ck[196+:4]),.local_id(cid[1568+:32]),.generation(cgen[1568+:32]),.line(cl[1568+:32]),.legal(legal[49]),.write(write_[49]),.packed_id(ai[49]),.returned_id(ri[49]),.returned_data(raw_rd[49]),.returned_kind(rk[196+:4]),.returned_local(rid[1568+:32]),.returned_gen(rgen[1568+:32]),.read_data(rd[12544+:256]),.returned_legal(rlegal[49]));
 assign cr[49]=source_accept[49]&&legal[49];
df_fifo #(.WIDTH(363),.DEPTH(4)) q49(.clk,.reset,.iv(cv[49]&&legal[49]),.ir(source_accept[49]),.idata({write_[49],cl[1568+:32],ai[49],local_write_data[256+:256]}),.ov(qv[49]),.ordy(qr[49]),.odata({qw[1],ql[49],qi[49],qd[1]}));
lf_adapter #(.SOURCE(50)) a50(.kind(ck[200+:4]),.local_id(cid[1600+:32]),.generation(cgen[1600+:32]),.line(cl[1600+:32]),.legal(legal[50]),.write(write_[50]),.packed_id(ai[50]),.returned_id(ri[50]),.returned_data(raw_rd[50]),.returned_kind(rk[200+:4]),.returned_local(rid[1600+:32]),.returned_gen(rgen[1600+:32]),.read_data(rd[12800+:256]),.returned_legal(rlegal[50]));
 assign cr[50]=source_accept[50]&&legal[50];
df_fifo #(.WIDTH(363),.DEPTH(4)) q50(.clk,.reset,.iv(cv[50]&&legal[50]),.ir(source_accept[50]),.idata({write_[50],cl[1600+:32],ai[50],local_write_data[512+:256]}),.ov(qv[50]),.ordy(qr[50]),.odata({qw[2],ql[50],qi[50],qd[2]}));
lf_adapter #(.SOURCE(51)) a51(.kind(ck[204+:4]),.local_id(cid[1632+:32]),.generation(cgen[1632+:32]),.line(cl[1632+:32]),.legal(legal[51]),.write(write_[51]),.packed_id(ai[51]),.returned_id(ri[51]),.returned_data(raw_rd[51]),.returned_kind(rk[204+:4]),.returned_local(rid[1632+:32]),.returned_gen(rgen[1632+:32]),.read_data(rd[13056+:256]),.returned_legal(rlegal[51]));
 assign cr[51]=source_accept[51]&&legal[51];
df_fifo #(.WIDTH(363),.DEPTH(4)) q51(.clk,.reset,.iv(cv[51]&&legal[51]),.ir(source_accept[51]),.idata({write_[51],cl[1632+:32],ai[51],local_write_data[768+:256]}),.ov(qv[51]),.ordy(qr[51]),.odata({qw[3],ql[51],qi[51],qd[3]}));
lf_adapter #(.SOURCE(52)) a52(.kind(ck[208+:4]),.local_id(cid[1664+:32]),.generation(cgen[1664+:32]),.line(cl[1664+:32]),.legal(legal[52]),.write(write_[52]),.packed_id(ai[52]),.returned_id(ri[52]),.returned_data(raw_rd[52]),.returned_kind(rk[208+:4]),.returned_local(rid[1664+:32]),.returned_gen(rgen[1664+:32]),.read_data(rd[13312+:256]),.returned_legal(rlegal[52]));
 assign cr[52]=source_accept[52]&&legal[52];
df_fifo #(.WIDTH(363),.DEPTH(4)) q52(.clk,.reset,.iv(cv[52]&&legal[52]),.ir(source_accept[52]),.idata({write_[52],cl[1664+:32],ai[52],local_write_data[1024+:256]}),.ov(qv[52]),.ordy(qr[52]),.odata({qw[4],ql[52],qi[52],qd[4]}));
lf_adapter #(.SOURCE(53)) a53(.kind(ck[212+:4]),.local_id(cid[1696+:32]),.generation(cgen[1696+:32]),.line(cl[1696+:32]),.legal(legal[53]),.write(write_[53]),.packed_id(ai[53]),.returned_id(ri[53]),.returned_data(raw_rd[53]),.returned_kind(rk[212+:4]),.returned_local(rid[1696+:32]),.returned_gen(rgen[1696+:32]),.read_data(rd[13568+:256]),.returned_legal(rlegal[53]));
 assign cr[53]=source_accept[53]&&legal[53];
df_fifo #(.WIDTH(363),.DEPTH(4)) q53(.clk,.reset,.iv(cv[53]&&legal[53]),.ir(source_accept[53]),.idata({write_[53],cl[1696+:32],ai[53],local_write_data[1280+:256]}),.ov(qv[53]),.ordy(qr[53]),.odata({qw[5],ql[53],qi[53],qd[5]}));
lf_adapter #(.SOURCE(54)) a54(.kind(ck[216+:4]),.local_id(cid[1728+:32]),.generation(cgen[1728+:32]),.line(cl[1728+:32]),.legal(legal[54]),.write(write_[54]),.packed_id(ai[54]),.returned_id(ri[54]),.returned_data(raw_rd[54]),.returned_kind(rk[216+:4]),.returned_local(rid[1728+:32]),.returned_gen(rgen[1728+:32]),.read_data(rd[13824+:256]),.returned_legal(rlegal[54]));
 assign cr[54]=source_accept[54]&&legal[54];
df_fifo #(.WIDTH(363),.DEPTH(4)) q54(.clk,.reset,.iv(cv[54]&&legal[54]),.ir(source_accept[54]),.idata({write_[54],cl[1728+:32],ai[54],local_write_data[1536+:256]}),.ov(qv[54]),.ordy(qr[54]),.odata({qw[6],ql[54],qi[54],qd[6]}));
lf_adapter #(.SOURCE(55)) a55(.kind(ck[220+:4]),.local_id(cid[1760+:32]),.generation(cgen[1760+:32]),.line(cl[1760+:32]),.legal(legal[55]),.write(write_[55]),.packed_id(ai[55]),.returned_id(ri[55]),.returned_data(raw_rd[55]),.returned_kind(rk[220+:4]),.returned_local(rid[1760+:32]),.returned_gen(rgen[1760+:32]),.read_data(rd[14080+:256]),.returned_legal(rlegal[55]));
 assign cr[55]=source_accept[55]&&legal[55];
df_fifo #(.WIDTH(363),.DEPTH(4)) q55(.clk,.reset,.iv(cv[55]&&legal[55]),.ir(source_accept[55]),.idata({write_[55],cl[1760+:32],ai[55],local_write_data[1792+:256]}),.ov(qv[55]),.ordy(qr[55]),.odata({qw[7],ql[55],qi[55],qd[7]}));
lf_adapter #(.SOURCE(56)) a56(.kind(ck[224+:4]),.local_id(cid[1792+:32]),.generation(cgen[1792+:32]),.line(cl[1792+:32]),.legal(legal[56]),.write(write_[56]),.packed_id(ai[56]),.returned_id(ri[56]),.returned_data(raw_rd[56]),.returned_kind(rk[224+:4]),.returned_local(rid[1792+:32]),.returned_gen(rgen[1792+:32]),.read_data(rd[14336+:256]),.returned_legal(rlegal[56]));
 assign cr[56]=source_accept[56]&&legal[56];
df_fifo #(.WIDTH(363),.DEPTH(4)) q56(.clk,.reset,.iv(cv[56]&&legal[56]),.ir(source_accept[56]),.idata({write_[56],cl[1792+:32],ai[56],local_write_data[2048+:256]}),.ov(qv[56]),.ordy(qr[56]),.odata({qw[8],ql[56],qi[56],qd[8]}));
lf_adapter #(.SOURCE(57)) a57(.kind(ck[228+:4]),.local_id(cid[1824+:32]),.generation(cgen[1824+:32]),.line(cl[1824+:32]),.legal(legal[57]),.write(write_[57]),.packed_id(ai[57]),.returned_id(ri[57]),.returned_data(raw_rd[57]),.returned_kind(rk[228+:4]),.returned_local(rid[1824+:32]),.returned_gen(rgen[1824+:32]),.read_data(rd[14592+:256]),.returned_legal(rlegal[57]));
 assign cr[57]=source_accept[57]&&legal[57];
df_fifo #(.WIDTH(363),.DEPTH(4)) q57(.clk,.reset,.iv(cv[57]&&legal[57]),.ir(source_accept[57]),.idata({write_[57],cl[1824+:32],ai[57],local_write_data[2304+:256]}),.ov(qv[57]),.ordy(qr[57]),.odata({qw[9],ql[57],qi[57],qd[9]}));
lf_adapter #(.SOURCE(58)) a58(.kind(ck[232+:4]),.local_id(cid[1856+:32]),.generation(cgen[1856+:32]),.line(cl[1856+:32]),.legal(legal[58]),.write(write_[58]),.packed_id(ai[58]),.returned_id(ri[58]),.returned_data(raw_rd[58]),.returned_kind(rk[232+:4]),.returned_local(rid[1856+:32]),.returned_gen(rgen[1856+:32]),.read_data(rd[14848+:256]),.returned_legal(rlegal[58]));
 assign cr[58]=source_accept[58]&&legal[58];
df_fifo #(.WIDTH(363),.DEPTH(4)) q58(.clk,.reset,.iv(cv[58]&&legal[58]),.ir(source_accept[58]),.idata({write_[58],cl[1856+:32],ai[58],local_write_data[2560+:256]}),.ov(qv[58]),.ordy(qr[58]),.odata({qw[10],ql[58],qi[58],qd[10]}));
lf_adapter #(.SOURCE(59)) a59(.kind(ck[236+:4]),.local_id(cid[1888+:32]),.generation(cgen[1888+:32]),.line(cl[1888+:32]),.legal(legal[59]),.write(write_[59]),.packed_id(ai[59]),.returned_id(ri[59]),.returned_data(raw_rd[59]),.returned_kind(rk[236+:4]),.returned_local(rid[1888+:32]),.returned_gen(rgen[1888+:32]),.read_data(rd[15104+:256]),.returned_legal(rlegal[59]));
 assign cr[59]=source_accept[59]&&legal[59];
df_fifo #(.WIDTH(363),.DEPTH(4)) q59(.clk,.reset,.iv(cv[59]&&legal[59]),.ir(source_accept[59]),.idata({write_[59],cl[1888+:32],ai[59],local_write_data[2816+:256]}),.ov(qv[59]),.ordy(qr[59]),.odata({qw[11],ql[59],qi[59],qd[11]}));
lf_adapter #(.SOURCE(60)) a60(.kind(ck[240+:4]),.local_id(cid[1920+:32]),.generation(cgen[1920+:32]),.line(cl[1920+:32]),.legal(legal[60]),.write(write_[60]),.packed_id(ai[60]),.returned_id(ri[60]),.returned_data(raw_rd[60]),.returned_kind(rk[240+:4]),.returned_local(rid[1920+:32]),.returned_gen(rgen[1920+:32]),.read_data(rd[15360+:256]),.returned_legal(rlegal[60]));
 assign cr[60]=source_accept[60]&&legal[60];
df_fifo #(.WIDTH(363),.DEPTH(4)) q60(.clk,.reset,.iv(cv[60]&&legal[60]),.ir(source_accept[60]),.idata({write_[60],cl[1920+:32],ai[60],local_write_data[3072+:256]}),.ov(qv[60]),.ordy(qr[60]),.odata({qw[12],ql[60],qi[60],qd[12]}));
lf_adapter #(.SOURCE(61)) a61(.kind(ck[244+:4]),.local_id(cid[1952+:32]),.generation(cgen[1952+:32]),.line(cl[1952+:32]),.legal(legal[61]),.write(write_[61]),.packed_id(ai[61]),.returned_id(ri[61]),.returned_data(raw_rd[61]),.returned_kind(rk[244+:4]),.returned_local(rid[1952+:32]),.returned_gen(rgen[1952+:32]),.read_data(rd[15616+:256]),.returned_legal(rlegal[61]));
 assign cr[61]=source_accept[61]&&legal[61];
df_fifo #(.WIDTH(363),.DEPTH(4)) q61(.clk,.reset,.iv(cv[61]&&legal[61]),.ir(source_accept[61]),.idata({write_[61],cl[1952+:32],ai[61],local_write_data[3328+:256]}),.ov(qv[61]),.ordy(qr[61]),.odata({qw[13],ql[61],qi[61],qd[13]}));
lf_adapter #(.SOURCE(62)) a62(.kind(ck[248+:4]),.local_id(cid[1984+:32]),.generation(cgen[1984+:32]),.line(cl[1984+:32]),.legal(legal[62]),.write(write_[62]),.packed_id(ai[62]),.returned_id(ri[62]),.returned_data(raw_rd[62]),.returned_kind(rk[248+:4]),.returned_local(rid[1984+:32]),.returned_gen(rgen[1984+:32]),.read_data(rd[15872+:256]),.returned_legal(rlegal[62]));
 assign cr[62]=source_accept[62]&&legal[62];
df_fifo #(.WIDTH(363),.DEPTH(4)) q62(.clk,.reset,.iv(cv[62]&&legal[62]),.ir(source_accept[62]),.idata({write_[62],cl[1984+:32],ai[62],local_write_data[3584+:256]}),.ov(qv[62]),.ordy(qr[62]),.odata({qw[14],ql[62],qi[62],qd[14]}));
lf_adapter #(.SOURCE(63)) a63(.kind(ck[252+:4]),.local_id(cid[2016+:32]),.generation(cgen[2016+:32]),.line(cl[2016+:32]),.legal(legal[63]),.write(write_[63]),.packed_id(ai[63]),.returned_id(ri[63]),.returned_data(raw_rd[63]),.returned_kind(rk[252+:4]),.returned_local(rid[2016+:32]),.returned_gen(rgen[2016+:32]),.read_data(rd[16128+:256]),.returned_legal(rlegal[63]));
 assign cr[63]=source_accept[63]&&legal[63];
df_fifo #(.WIDTH(363),.DEPTH(4)) q63(.clk,.reset,.iv(cv[63]&&legal[63]),.ir(source_accept[63]),.idata({write_[63],cl[2016+:32],ai[63],local_write_data[3840+:256]}),.ov(qv[63]),.ordy(qr[63]),.odata({qw[15],ql[63],qi[63],qd[15]}));
lf_adapter #(.SOURCE(64)) a64(.kind(ck[256+:4]),.local_id(cid[2048+:32]),.generation(cgen[2048+:32]),.line(cl[2048+:32]),.legal(legal[64]),.write(write_[64]),.packed_id(ai[64]),.returned_id(ri[64]),.returned_data(raw_rd[64]),.returned_kind(rk[256+:4]),.returned_local(rid[2048+:32]),.returned_gen(rgen[2048+:32]),.read_data(rd[16384+:256]),.returned_legal(rlegal[64]));
 assign cr[64]=source_accept[64]&&legal[64];
df_fifo #(.WIDTH(363),.DEPTH(4)) q64(.clk,.reset,.iv(cv[64]&&legal[64]),.ir(source_accept[64]),.idata({write_[64],cl[2048+:32],ai[64],local_write_data[4096+:256]}),.ov(qv[64]),.ordy(qr[64]),.odata({qw[16],ql[64],qi[64],qd[16]}));
lf_adapter #(.SOURCE(65)) a65(.kind(ck[260+:4]),.local_id(cid[2080+:32]),.generation(cgen[2080+:32]),.line(cl[2080+:32]),.legal(legal[65]),.write(write_[65]),.packed_id(ai[65]),.returned_id(ri[65]),.returned_data(raw_rd[65]),.returned_kind(rk[260+:4]),.returned_local(rid[2080+:32]),.returned_gen(rgen[2080+:32]),.read_data(rd[16640+:256]),.returned_legal(rlegal[65]));
 assign cr[65]=source_accept[65]&&legal[65];
df_fifo #(.WIDTH(363),.DEPTH(4)) q65(.clk,.reset,.iv(cv[65]&&legal[65]),.ir(source_accept[65]),.idata({write_[65],cl[2080+:32],ai[65],local_write_data[4352+:256]}),.ov(qv[65]),.ordy(qr[65]),.odata({qw[17],ql[65],qi[65],qd[17]}));
lf_adapter #(.SOURCE(66)) a66(.kind(ck[264+:4]),.local_id(cid[2112+:32]),.generation(cgen[2112+:32]),.line(cl[2112+:32]),.legal(legal[66]),.write(write_[66]),.packed_id(ai[66]),.returned_id(ri[66]),.returned_data(raw_rd[66]),.returned_kind(rk[264+:4]),.returned_local(rid[2112+:32]),.returned_gen(rgen[2112+:32]),.read_data(rd[16896+:256]),.returned_legal(rlegal[66]));
 assign cr[66]=source_accept[66]&&legal[66];
df_fifo #(.WIDTH(363),.DEPTH(4)) q66(.clk,.reset,.iv(cv[66]&&legal[66]),.ir(source_accept[66]),.idata({write_[66],cl[2112+:32],ai[66],local_write_data[4608+:256]}),.ov(qv[66]),.ordy(qr[66]),.odata({qw[18],ql[66],qi[66],qd[18]}));
lf_adapter #(.SOURCE(67)) a67(.kind(ck[268+:4]),.local_id(cid[2144+:32]),.generation(cgen[2144+:32]),.line(cl[2144+:32]),.legal(legal[67]),.write(write_[67]),.packed_id(ai[67]),.returned_id(ri[67]),.returned_data(raw_rd[67]),.returned_kind(rk[268+:4]),.returned_local(rid[2144+:32]),.returned_gen(rgen[2144+:32]),.read_data(rd[17152+:256]),.returned_legal(rlegal[67]));
 assign cr[67]=source_accept[67]&&legal[67];
df_fifo #(.WIDTH(363),.DEPTH(4)) q67(.clk,.reset,.iv(cv[67]&&legal[67]),.ir(source_accept[67]),.idata({write_[67],cl[2144+:32],ai[67],local_write_data[4864+:256]}),.ov(qv[67]),.ordy(qr[67]),.odata({qw[19],ql[67],qi[67],qd[19]}));
lf_adapter #(.SOURCE(68)) a68(.kind(ck[272+:4]),.local_id(cid[2176+:32]),.generation(cgen[2176+:32]),.line(cl[2176+:32]),.legal(legal[68]),.write(write_[68]),.packed_id(ai[68]),.returned_id(ri[68]),.returned_data(raw_rd[68]),.returned_kind(rk[272+:4]),.returned_local(rid[2176+:32]),.returned_gen(rgen[2176+:32]),.read_data(rd[17408+:256]),.returned_legal(rlegal[68]));
 assign cr[68]=source_accept[68]&&legal[68];
df_fifo #(.WIDTH(363),.DEPTH(4)) q68(.clk,.reset,.iv(cv[68]&&legal[68]),.ir(source_accept[68]),.idata({write_[68],cl[2176+:32],ai[68],local_write_data[5120+:256]}),.ov(qv[68]),.ordy(qr[68]),.odata({qw[20],ql[68],qi[68],qd[20]}));
lf_adapter #(.SOURCE(69)) a69(.kind(ck[276+:4]),.local_id(cid[2208+:32]),.generation(cgen[2208+:32]),.line(cl[2208+:32]),.legal(legal[69]),.write(write_[69]),.packed_id(ai[69]),.returned_id(ri[69]),.returned_data(raw_rd[69]),.returned_kind(rk[276+:4]),.returned_local(rid[2208+:32]),.returned_gen(rgen[2208+:32]),.read_data(rd[17664+:256]),.returned_legal(rlegal[69]));
 assign cr[69]=source_accept[69]&&legal[69];
df_fifo #(.WIDTH(363),.DEPTH(4)) q69(.clk,.reset,.iv(cv[69]&&legal[69]),.ir(source_accept[69]),.idata({write_[69],cl[2208+:32],ai[69],local_write_data[5376+:256]}),.ov(qv[69]),.ordy(qr[69]),.odata({qw[21],ql[69],qi[69],qd[21]}));
lf_adapter #(.SOURCE(70)) a70(.kind(ck[280+:4]),.local_id(cid[2240+:32]),.generation(cgen[2240+:32]),.line(cl[2240+:32]),.legal(legal[70]),.write(write_[70]),.packed_id(ai[70]),.returned_id(ri[70]),.returned_data(raw_rd[70]),.returned_kind(rk[280+:4]),.returned_local(rid[2240+:32]),.returned_gen(rgen[2240+:32]),.read_data(rd[17920+:256]),.returned_legal(rlegal[70]));
 assign cr[70]=source_accept[70]&&legal[70];
df_fifo #(.WIDTH(363),.DEPTH(4)) q70(.clk,.reset,.iv(cv[70]&&legal[70]),.ir(source_accept[70]),.idata({write_[70],cl[2240+:32],ai[70],local_write_data[5632+:256]}),.ov(qv[70]),.ordy(qr[70]),.odata({qw[22],ql[70],qi[70],qd[22]}));
lf_adapter #(.SOURCE(71)) a71(.kind(ck[284+:4]),.local_id(cid[2272+:32]),.generation(cgen[2272+:32]),.line(cl[2272+:32]),.legal(legal[71]),.write(write_[71]),.packed_id(ai[71]),.returned_id(ri[71]),.returned_data(raw_rd[71]),.returned_kind(rk[284+:4]),.returned_local(rid[2272+:32]),.returned_gen(rgen[2272+:32]),.read_data(rd[18176+:256]),.returned_legal(rlegal[71]));
 assign cr[71]=source_accept[71]&&legal[71];
df_fifo #(.WIDTH(363),.DEPTH(4)) q71(.clk,.reset,.iv(cv[71]&&legal[71]),.ir(source_accept[71]),.idata({write_[71],cl[2272+:32],ai[71],local_write_data[5888+:256]}),.ov(qv[71]),.ordy(qr[71]),.odata({qw[23],ql[71],qi[71],qd[23]}));
lf_adapter #(.SOURCE(72)) a72(.kind(ck[288+:4]),.local_id(cid[2304+:32]),.generation(cgen[2304+:32]),.line(cl[2304+:32]),.legal(legal[72]),.write(write_[72]),.packed_id(ai[72]),.returned_id(ri[72]),.returned_data(raw_rd[72]),.returned_kind(rk[288+:4]),.returned_local(rid[2304+:32]),.returned_gen(rgen[2304+:32]),.read_data(rd[18432+:256]),.returned_legal(rlegal[72]));
 assign cr[72]=source_accept[72]&&legal[72];
df_fifo #(.WIDTH(363),.DEPTH(4)) q72(.clk,.reset,.iv(cv[72]&&legal[72]),.ir(source_accept[72]),.idata({write_[72],cl[2304+:32],ai[72],local_write_data[6144+:256]}),.ov(qv[72]),.ordy(qr[72]),.odata({qw[24],ql[72],qi[72],qd[24]}));
lf_adapter #(.SOURCE(73)) a73(.kind(ck[292+:4]),.local_id(cid[2336+:32]),.generation(cgen[2336+:32]),.line(cl[2336+:32]),.legal(legal[73]),.write(write_[73]),.packed_id(ai[73]),.returned_id(ri[73]),.returned_data(raw_rd[73]),.returned_kind(rk[292+:4]),.returned_local(rid[2336+:32]),.returned_gen(rgen[2336+:32]),.read_data(rd[18688+:256]),.returned_legal(rlegal[73]));
 assign cr[73]=source_accept[73]&&legal[73];
df_fifo #(.WIDTH(363),.DEPTH(4)) q73(.clk,.reset,.iv(cv[73]&&legal[73]),.ir(source_accept[73]),.idata({write_[73],cl[2336+:32],ai[73],local_write_data[6400+:256]}),.ov(qv[73]),.ordy(qr[73]),.odata({qw[25],ql[73],qi[73],qd[25]}));
lf_adapter #(.SOURCE(74)) a74(.kind(ck[296+:4]),.local_id(cid[2368+:32]),.generation(cgen[2368+:32]),.line(cl[2368+:32]),.legal(legal[74]),.write(write_[74]),.packed_id(ai[74]),.returned_id(ri[74]),.returned_data(raw_rd[74]),.returned_kind(rk[296+:4]),.returned_local(rid[2368+:32]),.returned_gen(rgen[2368+:32]),.read_data(rd[18944+:256]),.returned_legal(rlegal[74]));
 assign cr[74]=source_accept[74]&&legal[74];
df_fifo #(.WIDTH(363),.DEPTH(4)) q74(.clk,.reset,.iv(cv[74]&&legal[74]),.ir(source_accept[74]),.idata({write_[74],cl[2368+:32],ai[74],local_write_data[6656+:256]}),.ov(qv[74]),.ordy(qr[74]),.odata({qw[26],ql[74],qi[74],qd[26]}));
lf_adapter #(.SOURCE(75)) a75(.kind(ck[300+:4]),.local_id(cid[2400+:32]),.generation(cgen[2400+:32]),.line(cl[2400+:32]),.legal(legal[75]),.write(write_[75]),.packed_id(ai[75]),.returned_id(ri[75]),.returned_data(raw_rd[75]),.returned_kind(rk[300+:4]),.returned_local(rid[2400+:32]),.returned_gen(rgen[2400+:32]),.read_data(rd[19200+:256]),.returned_legal(rlegal[75]));
 assign cr[75]=source_accept[75]&&legal[75];
df_fifo #(.WIDTH(363),.DEPTH(4)) q75(.clk,.reset,.iv(cv[75]&&legal[75]),.ir(source_accept[75]),.idata({write_[75],cl[2400+:32],ai[75],local_write_data[6912+:256]}),.ov(qv[75]),.ordy(qr[75]),.odata({qw[27],ql[75],qi[75],qd[27]}));
lf_adapter #(.SOURCE(76)) a76(.kind(ck[304+:4]),.local_id(cid[2432+:32]),.generation(cgen[2432+:32]),.line(cl[2432+:32]),.legal(legal[76]),.write(write_[76]),.packed_id(ai[76]),.returned_id(ri[76]),.returned_data(raw_rd[76]),.returned_kind(rk[304+:4]),.returned_local(rid[2432+:32]),.returned_gen(rgen[2432+:32]),.read_data(rd[19456+:256]),.returned_legal(rlegal[76]));
 assign cr[76]=source_accept[76]&&legal[76];
df_fifo #(.WIDTH(363),.DEPTH(4)) q76(.clk,.reset,.iv(cv[76]&&legal[76]),.ir(source_accept[76]),.idata({write_[76],cl[2432+:32],ai[76],local_write_data[7168+:256]}),.ov(qv[76]),.ordy(qr[76]),.odata({qw[28],ql[76],qi[76],qd[28]}));
lf_adapter #(.SOURCE(77)) a77(.kind(ck[308+:4]),.local_id(cid[2464+:32]),.generation(cgen[2464+:32]),.line(cl[2464+:32]),.legal(legal[77]),.write(write_[77]),.packed_id(ai[77]),.returned_id(ri[77]),.returned_data(raw_rd[77]),.returned_kind(rk[308+:4]),.returned_local(rid[2464+:32]),.returned_gen(rgen[2464+:32]),.read_data(rd[19712+:256]),.returned_legal(rlegal[77]));
 assign cr[77]=source_accept[77]&&legal[77];
df_fifo #(.WIDTH(363),.DEPTH(4)) q77(.clk,.reset,.iv(cv[77]&&legal[77]),.ir(source_accept[77]),.idata({write_[77],cl[2464+:32],ai[77],local_write_data[7424+:256]}),.ov(qv[77]),.ordy(qr[77]),.odata({qw[29],ql[77],qi[77],qd[29]}));
lf_adapter #(.SOURCE(78)) a78(.kind(ck[312+:4]),.local_id(cid[2496+:32]),.generation(cgen[2496+:32]),.line(cl[2496+:32]),.legal(legal[78]),.write(write_[78]),.packed_id(ai[78]),.returned_id(ri[78]),.returned_data(raw_rd[78]),.returned_kind(rk[312+:4]),.returned_local(rid[2496+:32]),.returned_gen(rgen[2496+:32]),.read_data(rd[19968+:256]),.returned_legal(rlegal[78]));
 assign cr[78]=source_accept[78]&&legal[78];
df_fifo #(.WIDTH(363),.DEPTH(4)) q78(.clk,.reset,.iv(cv[78]&&legal[78]),.ir(source_accept[78]),.idata({write_[78],cl[2496+:32],ai[78],local_write_data[7680+:256]}),.ov(qv[78]),.ordy(qr[78]),.odata({qw[30],ql[78],qi[78],qd[30]}));
lf_adapter #(.SOURCE(79)) a79(.kind(ck[316+:4]),.local_id(cid[2528+:32]),.generation(cgen[2528+:32]),.line(cl[2528+:32]),.legal(legal[79]),.write(write_[79]),.packed_id(ai[79]),.returned_id(ri[79]),.returned_data(raw_rd[79]),.returned_kind(rk[316+:4]),.returned_local(rid[2528+:32]),.returned_gen(rgen[2528+:32]),.read_data(rd[20224+:256]),.returned_legal(rlegal[79]));
 assign cr[79]=source_accept[79]&&legal[79];
df_fifo #(.WIDTH(363),.DEPTH(4)) q79(.clk,.reset,.iv(cv[79]&&legal[79]),.ir(source_accept[79]),.idata({write_[79],cl[2528+:32],ai[79],local_write_data[7936+:256]}),.ov(qv[79]),.ordy(qr[79]),.odata({qw[31],ql[79],qi[79],qd[31]}));
lf_adapter #(.SOURCE(80)) a80(.kind(ck[320+:4]),.local_id(cid[2560+:32]),.generation(cgen[2560+:32]),.line(cl[2560+:32]),.legal(legal[80]),.write(write_[80]),.packed_id(ai[80]),.returned_id(ri[80]),.returned_data(raw_rd[80]),.returned_kind(rk[320+:4]),.returned_local(rid[2560+:32]),.returned_gen(rgen[2560+:32]),.read_data(rd[20480+:256]),.returned_legal(rlegal[80]));
 assign cr[80]=source_accept[80]&&legal[80];
df_fifo #(.WIDTH(363),.DEPTH(4)) q80(.clk,.reset,.iv(cv[80]&&legal[80]),.ir(source_accept[80]),.idata({write_[80],cl[2560+:32],ai[80],local_write_data[8192+:256]}),.ov(qv[80]),.ordy(qr[80]),.odata({qw[32],ql[80],qi[80],qd[32]}));
lf_adapter #(.SOURCE(81)) a81(.kind(ck[324+:4]),.local_id(cid[2592+:32]),.generation(cgen[2592+:32]),.line(cl[2592+:32]),.legal(legal[81]),.write(write_[81]),.packed_id(ai[81]),.returned_id(ri[81]),.returned_data(raw_rd[81]),.returned_kind(rk[324+:4]),.returned_local(rid[2592+:32]),.returned_gen(rgen[2592+:32]),.read_data(rd[20736+:256]),.returned_legal(rlegal[81]));
 assign cr[81]=source_accept[81]&&legal[81];
df_fifo #(.WIDTH(363),.DEPTH(4)) q81(.clk,.reset,.iv(cv[81]&&legal[81]),.ir(source_accept[81]),.idata({write_[81],cl[2592+:32],ai[81],local_write_data[8448+:256]}),.ov(qv[81]),.ordy(qr[81]),.odata({qw[33],ql[81],qi[81],qd[33]}));
lf_adapter #(.SOURCE(82)) a82(.kind(ck[328+:4]),.local_id(cid[2624+:32]),.generation(cgen[2624+:32]),.line(cl[2624+:32]),.legal(legal[82]),.write(write_[82]),.packed_id(ai[82]),.returned_id(ri[82]),.returned_data(raw_rd[82]),.returned_kind(rk[328+:4]),.returned_local(rid[2624+:32]),.returned_gen(rgen[2624+:32]),.read_data(rd[20992+:256]),.returned_legal(rlegal[82]));
 assign cr[82]=source_accept[82]&&legal[82];
df_fifo #(.WIDTH(363),.DEPTH(4)) q82(.clk,.reset,.iv(cv[82]&&legal[82]),.ir(source_accept[82]),.idata({write_[82],cl[2624+:32],ai[82],local_write_data[8704+:256]}),.ov(qv[82]),.ordy(qr[82]),.odata({qw[34],ql[82],qi[82],qd[34]}));
lf_adapter #(.SOURCE(83)) a83(.kind(ck[332+:4]),.local_id(cid[2656+:32]),.generation(cgen[2656+:32]),.line(cl[2656+:32]),.legal(legal[83]),.write(write_[83]),.packed_id(ai[83]),.returned_id(ri[83]),.returned_data(raw_rd[83]),.returned_kind(rk[332+:4]),.returned_local(rid[2656+:32]),.returned_gen(rgen[2656+:32]),.read_data(rd[21248+:256]),.returned_legal(rlegal[83]));
 assign cr[83]=source_accept[83]&&legal[83];
df_fifo #(.WIDTH(363),.DEPTH(4)) q83(.clk,.reset,.iv(cv[83]&&legal[83]),.ir(source_accept[83]),.idata({write_[83],cl[2656+:32],ai[83],local_write_data[8960+:256]}),.ov(qv[83]),.ordy(qr[83]),.odata({qw[35],ql[83],qi[83],qd[35]}));
lf_adapter #(.SOURCE(84)) a84(.kind(ck[336+:4]),.local_id(cid[2688+:32]),.generation(cgen[2688+:32]),.line(cl[2688+:32]),.legal(legal[84]),.write(write_[84]),.packed_id(ai[84]),.returned_id(ri[84]),.returned_data(raw_rd[84]),.returned_kind(rk[336+:4]),.returned_local(rid[2688+:32]),.returned_gen(rgen[2688+:32]),.read_data(rd[21504+:256]),.returned_legal(rlegal[84]));
 assign cr[84]=source_accept[84]&&legal[84];
df_fifo #(.WIDTH(363),.DEPTH(4)) q84(.clk,.reset,.iv(cv[84]&&legal[84]),.ir(source_accept[84]),.idata({write_[84],cl[2688+:32],ai[84],local_write_data[9216+:256]}),.ov(qv[84]),.ordy(qr[84]),.odata({qw[36],ql[84],qi[84],qd[36]}));
lf_adapter #(.SOURCE(85)) a85(.kind(ck[340+:4]),.local_id(cid[2720+:32]),.generation(cgen[2720+:32]),.line(cl[2720+:32]),.legal(legal[85]),.write(write_[85]),.packed_id(ai[85]),.returned_id(ri[85]),.returned_data(raw_rd[85]),.returned_kind(rk[340+:4]),.returned_local(rid[2720+:32]),.returned_gen(rgen[2720+:32]),.read_data(rd[21760+:256]),.returned_legal(rlegal[85]));
 assign cr[85]=source_accept[85]&&legal[85];
df_fifo #(.WIDTH(363),.DEPTH(4)) q85(.clk,.reset,.iv(cv[85]&&legal[85]),.ir(source_accept[85]),.idata({write_[85],cl[2720+:32],ai[85],local_write_data[9472+:256]}),.ov(qv[85]),.ordy(qr[85]),.odata({qw[37],ql[85],qi[85],qd[37]}));
lf_adapter #(.SOURCE(86)) a86(.kind(ck[344+:4]),.local_id(cid[2752+:32]),.generation(cgen[2752+:32]),.line(cl[2752+:32]),.legal(legal[86]),.write(write_[86]),.packed_id(ai[86]),.returned_id(ri[86]),.returned_data(raw_rd[86]),.returned_kind(rk[344+:4]),.returned_local(rid[2752+:32]),.returned_gen(rgen[2752+:32]),.read_data(rd[22016+:256]),.returned_legal(rlegal[86]));
 assign cr[86]=source_accept[86]&&legal[86];
df_fifo #(.WIDTH(363),.DEPTH(4)) q86(.clk,.reset,.iv(cv[86]&&legal[86]),.ir(source_accept[86]),.idata({write_[86],cl[2752+:32],ai[86],local_write_data[9728+:256]}),.ov(qv[86]),.ordy(qr[86]),.odata({qw[38],ql[86],qi[86],qd[38]}));
lf_adapter #(.SOURCE(87)) a87(.kind(ck[348+:4]),.local_id(cid[2784+:32]),.generation(cgen[2784+:32]),.line(cl[2784+:32]),.legal(legal[87]),.write(write_[87]),.packed_id(ai[87]),.returned_id(ri[87]),.returned_data(raw_rd[87]),.returned_kind(rk[348+:4]),.returned_local(rid[2784+:32]),.returned_gen(rgen[2784+:32]),.read_data(rd[22272+:256]),.returned_legal(rlegal[87]));
 assign cr[87]=source_accept[87]&&legal[87];
df_fifo #(.WIDTH(363),.DEPTH(4)) q87(.clk,.reset,.iv(cv[87]&&legal[87]),.ir(source_accept[87]),.idata({write_[87],cl[2784+:32],ai[87],local_write_data[9984+:256]}),.ov(qv[87]),.ordy(qr[87]),.odata({qw[39],ql[87],qi[87],qd[39]}));
lf_adapter #(.SOURCE(88)) a88(.kind(ck[352+:4]),.local_id(cid[2816+:32]),.generation(cgen[2816+:32]),.line(cl[2816+:32]),.legal(legal[88]),.write(write_[88]),.packed_id(ai[88]),.returned_id(ri[88]),.returned_data(raw_rd[88]),.returned_kind(rk[352+:4]),.returned_local(rid[2816+:32]),.returned_gen(rgen[2816+:32]),.read_data(rd[22528+:256]),.returned_legal(rlegal[88]));
 assign cr[88]=source_accept[88]&&legal[88];
df_fifo #(.WIDTH(363),.DEPTH(4)) q88(.clk,.reset,.iv(cv[88]&&legal[88]),.ir(source_accept[88]),.idata({write_[88],cl[2816+:32],ai[88],local_write_data[10240+:256]}),.ov(qv[88]),.ordy(qr[88]),.odata({qw[40],ql[88],qi[88],qd[40]}));
lf_adapter #(.SOURCE(89)) a89(.kind(ck[356+:4]),.local_id(cid[2848+:32]),.generation(cgen[2848+:32]),.line(cl[2848+:32]),.legal(legal[89]),.write(write_[89]),.packed_id(ai[89]),.returned_id(ri[89]),.returned_data(raw_rd[89]),.returned_kind(rk[356+:4]),.returned_local(rid[2848+:32]),.returned_gen(rgen[2848+:32]),.read_data(rd[22784+:256]),.returned_legal(rlegal[89]));
 assign cr[89]=source_accept[89]&&legal[89];
df_fifo #(.WIDTH(363),.DEPTH(4)) q89(.clk,.reset,.iv(cv[89]&&legal[89]),.ir(source_accept[89]),.idata({write_[89],cl[2848+:32],ai[89],local_write_data[10496+:256]}),.ov(qv[89]),.ordy(qr[89]),.odata({qw[41],ql[89],qi[89],qd[41]}));
lf_adapter #(.SOURCE(90)) a90(.kind(ck[360+:4]),.local_id(cid[2880+:32]),.generation(cgen[2880+:32]),.line(cl[2880+:32]),.legal(legal[90]),.write(write_[90]),.packed_id(ai[90]),.returned_id(ri[90]),.returned_data(raw_rd[90]),.returned_kind(rk[360+:4]),.returned_local(rid[2880+:32]),.returned_gen(rgen[2880+:32]),.read_data(rd[23040+:256]),.returned_legal(rlegal[90]));
 assign cr[90]=source_accept[90]&&legal[90];
df_fifo #(.WIDTH(363),.DEPTH(4)) q90(.clk,.reset,.iv(cv[90]&&legal[90]),.ir(source_accept[90]),.idata({write_[90],cl[2880+:32],ai[90],local_write_data[10752+:256]}),.ov(qv[90]),.ordy(qr[90]),.odata({qw[42],ql[90],qi[90],qd[42]}));
lf_adapter #(.SOURCE(91)) a91(.kind(ck[364+:4]),.local_id(cid[2912+:32]),.generation(cgen[2912+:32]),.line(cl[2912+:32]),.legal(legal[91]),.write(write_[91]),.packed_id(ai[91]),.returned_id(ri[91]),.returned_data(raw_rd[91]),.returned_kind(rk[364+:4]),.returned_local(rid[2912+:32]),.returned_gen(rgen[2912+:32]),.read_data(rd[23296+:256]),.returned_legal(rlegal[91]));
 assign cr[91]=source_accept[91]&&legal[91];
df_fifo #(.WIDTH(363),.DEPTH(4)) q91(.clk,.reset,.iv(cv[91]&&legal[91]),.ir(source_accept[91]),.idata({write_[91],cl[2912+:32],ai[91],local_write_data[11008+:256]}),.ov(qv[91]),.ordy(qr[91]),.odata({qw[43],ql[91],qi[91],qd[43]}));
lf_adapter #(.SOURCE(92)) a92(.kind(ck[368+:4]),.local_id(cid[2944+:32]),.generation(cgen[2944+:32]),.line(cl[2944+:32]),.legal(legal[92]),.write(write_[92]),.packed_id(ai[92]),.returned_id(ri[92]),.returned_data(raw_rd[92]),.returned_kind(rk[368+:4]),.returned_local(rid[2944+:32]),.returned_gen(rgen[2944+:32]),.read_data(rd[23552+:256]),.returned_legal(rlegal[92]));
 assign cr[92]=source_accept[92]&&legal[92];
df_fifo #(.WIDTH(363),.DEPTH(4)) q92(.clk,.reset,.iv(cv[92]&&legal[92]),.ir(source_accept[92]),.idata({write_[92],cl[2944+:32],ai[92],local_write_data[11264+:256]}),.ov(qv[92]),.ordy(qr[92]),.odata({qw[44],ql[92],qi[92],qd[44]}));
lf_adapter #(.SOURCE(93)) a93(.kind(ck[372+:4]),.local_id(cid[2976+:32]),.generation(cgen[2976+:32]),.line(cl[2976+:32]),.legal(legal[93]),.write(write_[93]),.packed_id(ai[93]),.returned_id(ri[93]),.returned_data(raw_rd[93]),.returned_kind(rk[372+:4]),.returned_local(rid[2976+:32]),.returned_gen(rgen[2976+:32]),.read_data(rd[23808+:256]),.returned_legal(rlegal[93]));
 assign cr[93]=source_accept[93]&&legal[93];
df_fifo #(.WIDTH(363),.DEPTH(4)) q93(.clk,.reset,.iv(cv[93]&&legal[93]),.ir(source_accept[93]),.idata({write_[93],cl[2976+:32],ai[93],local_write_data[11520+:256]}),.ov(qv[93]),.ordy(qr[93]),.odata({qw[45],ql[93],qi[93],qd[45]}));
lf_adapter #(.SOURCE(94)) a94(.kind(ck[376+:4]),.local_id(cid[3008+:32]),.generation(cgen[3008+:32]),.line(cl[3008+:32]),.legal(legal[94]),.write(write_[94]),.packed_id(ai[94]),.returned_id(ri[94]),.returned_data(raw_rd[94]),.returned_kind(rk[376+:4]),.returned_local(rid[3008+:32]),.returned_gen(rgen[3008+:32]),.read_data(rd[24064+:256]),.returned_legal(rlegal[94]));
 assign cr[94]=source_accept[94]&&legal[94];
df_fifo #(.WIDTH(363),.DEPTH(4)) q94(.clk,.reset,.iv(cv[94]&&legal[94]),.ir(source_accept[94]),.idata({write_[94],cl[3008+:32],ai[94],local_write_data[11776+:256]}),.ov(qv[94]),.ordy(qr[94]),.odata({qw[46],ql[94],qi[94],qd[46]}));
lf_adapter #(.SOURCE(95)) a95(.kind(ck[380+:4]),.local_id(cid[3040+:32]),.generation(cgen[3040+:32]),.line(cl[3040+:32]),.legal(legal[95]),.write(write_[95]),.packed_id(ai[95]),.returned_id(ri[95]),.returned_data(raw_rd[95]),.returned_kind(rk[380+:4]),.returned_local(rid[3040+:32]),.returned_gen(rgen[3040+:32]),.read_data(rd[24320+:256]),.returned_legal(rlegal[95]));
 assign cr[95]=source_accept[95]&&legal[95];
df_fifo #(.WIDTH(363),.DEPTH(4)) q95(.clk,.reset,.iv(cv[95]&&legal[95]),.ir(source_accept[95]),.idata({write_[95],cl[3040+:32],ai[95],local_write_data[12032+:256]}),.ov(qv[95]),.ordy(qr[95]),.odata({qw[47],ql[95],qi[95],qd[47]}));
lf_adapter #(.SOURCE(96)) a96(.kind(ck[384+:4]),.local_id(cid[3072+:32]),.generation(cgen[3072+:32]),.line(cl[3072+:32]),.legal(legal[96]),.write(write_[96]),.packed_id(ai[96]),.returned_id(ri[96]),.returned_data(raw_rd[96]),.returned_kind(rk[384+:4]),.returned_local(rid[3072+:32]),.returned_gen(rgen[3072+:32]),.read_data(rd[24576+:256]),.returned_legal(rlegal[96]));
 assign cr[96]=source_accept[96]&&legal[96];
df_fifo #(.WIDTH(363),.DEPTH(4)) q96(.clk,.reset,.iv(cv[96]&&legal[96]),.ir(source_accept[96]),.idata({write_[96],cl[3072+:32],ai[96],local_write_data[12288+:256]}),.ov(qv[96]),.ordy(qr[96]),.odata({qw[48],ql[96],qi[96],qd[48]}));
lf_adapter #(.SOURCE(97)) a97(.kind(ck[388+:4]),.local_id(cid[3104+:32]),.generation(cgen[3104+:32]),.line(cl[3104+:32]),.legal(legal[97]),.write(write_[97]),.packed_id(ai[97]),.returned_id(ri[97]),.returned_data(raw_rd[97]),.returned_kind(rk[388+:4]),.returned_local(rid[3104+:32]),.returned_gen(rgen[3104+:32]),.read_data(rd[24832+:256]),.returned_legal(rlegal[97]));
 assign cr[97]=source_accept[97]&&legal[97];
df_fifo #(.WIDTH(363),.DEPTH(4)) q97(.clk,.reset,.iv(cv[97]&&legal[97]),.ir(source_accept[97]),.idata({write_[97],cl[3104+:32],ai[97],local_write_data[12544+:256]}),.ov(qv[97]),.ordy(qr[97]),.odata({qw[49],ql[97],qi[97],qd[49]}));
lf_adapter #(.SOURCE(98)) a98(.kind(ck[392+:4]),.local_id(cid[3136+:32]),.generation(cgen[3136+:32]),.line(cl[3136+:32]),.legal(legal[98]),.write(write_[98]),.packed_id(ai[98]),.returned_id(ri[98]),.returned_data(raw_rd[98]),.returned_kind(rk[392+:4]),.returned_local(rid[3136+:32]),.returned_gen(rgen[3136+:32]),.read_data(rd[25088+:256]),.returned_legal(rlegal[98]));
 assign cr[98]=source_accept[98]&&legal[98];
df_fifo #(.WIDTH(363),.DEPTH(4)) q98(.clk,.reset,.iv(cv[98]&&legal[98]),.ir(source_accept[98]),.idata({write_[98],cl[3136+:32],ai[98],local_write_data[12800+:256]}),.ov(qv[98]),.ordy(qr[98]),.odata({qw[50],ql[98],qi[98],qd[50]}));
lf_adapter #(.SOURCE(99)) a99(.kind(ck[396+:4]),.local_id(cid[3168+:32]),.generation(cgen[3168+:32]),.line(cl[3168+:32]),.legal(legal[99]),.write(write_[99]),.packed_id(ai[99]),.returned_id(ri[99]),.returned_data(raw_rd[99]),.returned_kind(rk[396+:4]),.returned_local(rid[3168+:32]),.returned_gen(rgen[3168+:32]),.read_data(rd[25344+:256]),.returned_legal(rlegal[99]));
 assign cr[99]=source_accept[99]&&legal[99];
df_fifo #(.WIDTH(363),.DEPTH(4)) q99(.clk,.reset,.iv(cv[99]&&legal[99]),.ir(source_accept[99]),.idata({write_[99],cl[3168+:32],ai[99],local_write_data[13056+:256]}),.ov(qv[99]),.ordy(qr[99]),.odata({qw[51],ql[99],qi[99],qd[51]}));
lf_adapter #(.SOURCE(100)) a100(.kind(ck[400+:4]),.local_id(cid[3200+:32]),.generation(cgen[3200+:32]),.line(cl[3200+:32]),.legal(legal[100]),.write(write_[100]),.packed_id(ai[100]),.returned_id(ri[100]),.returned_data(raw_rd[100]),.returned_kind(rk[400+:4]),.returned_local(rid[3200+:32]),.returned_gen(rgen[3200+:32]),.read_data(rd[25600+:256]),.returned_legal(rlegal[100]));
 assign cr[100]=source_accept[100]&&legal[100];
df_fifo #(.WIDTH(363),.DEPTH(4)) q100(.clk,.reset,.iv(cv[100]&&legal[100]),.ir(source_accept[100]),.idata({write_[100],cl[3200+:32],ai[100],local_write_data[13312+:256]}),.ov(qv[100]),.ordy(qr[100]),.odata({qw[52],ql[100],qi[100],qd[52]}));
lf_adapter #(.SOURCE(101)) a101(.kind(ck[404+:4]),.local_id(cid[3232+:32]),.generation(cgen[3232+:32]),.line(cl[3232+:32]),.legal(legal[101]),.write(write_[101]),.packed_id(ai[101]),.returned_id(ri[101]),.returned_data(raw_rd[101]),.returned_kind(rk[404+:4]),.returned_local(rid[3232+:32]),.returned_gen(rgen[3232+:32]),.read_data(rd[25856+:256]),.returned_legal(rlegal[101]));
 assign cr[101]=source_accept[101]&&legal[101];
df_fifo #(.WIDTH(363),.DEPTH(4)) q101(.clk,.reset,.iv(cv[101]&&legal[101]),.ir(source_accept[101]),.idata({write_[101],cl[3232+:32],ai[101],local_write_data[13568+:256]}),.ov(qv[101]),.ordy(qr[101]),.odata({qw[53],ql[101],qi[101],qd[53]}));
lf_adapter #(.SOURCE(102)) a102(.kind(ck[408+:4]),.local_id(cid[3264+:32]),.generation(cgen[3264+:32]),.line(cl[3264+:32]),.legal(legal[102]),.write(write_[102]),.packed_id(ai[102]),.returned_id(ri[102]),.returned_data(raw_rd[102]),.returned_kind(rk[408+:4]),.returned_local(rid[3264+:32]),.returned_gen(rgen[3264+:32]),.read_data(rd[26112+:256]),.returned_legal(rlegal[102]));
 assign cr[102]=source_accept[102]&&legal[102];
df_fifo #(.WIDTH(363),.DEPTH(4)) q102(.clk,.reset,.iv(cv[102]&&legal[102]),.ir(source_accept[102]),.idata({write_[102],cl[3264+:32],ai[102],local_write_data[13824+:256]}),.ov(qv[102]),.ordy(qr[102]),.odata({qw[54],ql[102],qi[102],qd[54]}));
lf_adapter #(.SOURCE(103)) a103(.kind(ck[412+:4]),.local_id(cid[3296+:32]),.generation(cgen[3296+:32]),.line(cl[3296+:32]),.legal(legal[103]),.write(write_[103]),.packed_id(ai[103]),.returned_id(ri[103]),.returned_data(raw_rd[103]),.returned_kind(rk[412+:4]),.returned_local(rid[3296+:32]),.returned_gen(rgen[3296+:32]),.read_data(rd[26368+:256]),.returned_legal(rlegal[103]));
 assign cr[103]=source_accept[103]&&legal[103];
df_fifo #(.WIDTH(363),.DEPTH(4)) q103(.clk,.reset,.iv(cv[103]&&legal[103]),.ir(source_accept[103]),.idata({write_[103],cl[3296+:32],ai[103],local_write_data[14080+:256]}),.ov(qv[103]),.ordy(qr[103]),.odata({qw[55],ql[103],qi[103],qd[55]}));
lf_adapter #(.SOURCE(104)) a104(.kind(ck[416+:4]),.local_id(cid[3328+:32]),.generation(cgen[3328+:32]),.line(cl[3328+:32]),.legal(legal[104]),.write(write_[104]),.packed_id(ai[104]),.returned_id(ri[104]),.returned_data(raw_rd[104]),.returned_kind(rk[416+:4]),.returned_local(rid[3328+:32]),.returned_gen(rgen[3328+:32]),.read_data(rd[26624+:256]),.returned_legal(rlegal[104]));
 assign cr[104]=source_accept[104]&&legal[104];
df_fifo #(.WIDTH(363),.DEPTH(4)) q104(.clk,.reset,.iv(cv[104]&&legal[104]),.ir(source_accept[104]),.idata({write_[104],cl[3328+:32],ai[104],local_write_data[14336+:256]}),.ov(qv[104]),.ordy(qr[104]),.odata({qw[56],ql[104],qi[104],qd[56]}));
lf_adapter #(.SOURCE(105)) a105(.kind(ck[420+:4]),.local_id(cid[3360+:32]),.generation(cgen[3360+:32]),.line(cl[3360+:32]),.legal(legal[105]),.write(write_[105]),.packed_id(ai[105]),.returned_id(ri[105]),.returned_data(raw_rd[105]),.returned_kind(rk[420+:4]),.returned_local(rid[3360+:32]),.returned_gen(rgen[3360+:32]),.read_data(rd[26880+:256]),.returned_legal(rlegal[105]));
 assign cr[105]=source_accept[105]&&legal[105];
df_fifo #(.WIDTH(363),.DEPTH(4)) q105(.clk,.reset,.iv(cv[105]&&legal[105]),.ir(source_accept[105]),.idata({write_[105],cl[3360+:32],ai[105],local_write_data[14592+:256]}),.ov(qv[105]),.ordy(qr[105]),.odata({qw[57],ql[105],qi[105],qd[57]}));
lf_adapter #(.SOURCE(106)) a106(.kind(ck[424+:4]),.local_id(cid[3392+:32]),.generation(cgen[3392+:32]),.line(cl[3392+:32]),.legal(legal[106]),.write(write_[106]),.packed_id(ai[106]),.returned_id(ri[106]),.returned_data(raw_rd[106]),.returned_kind(rk[424+:4]),.returned_local(rid[3392+:32]),.returned_gen(rgen[3392+:32]),.read_data(rd[27136+:256]),.returned_legal(rlegal[106]));
 assign cr[106]=source_accept[106]&&legal[106];
df_fifo #(.WIDTH(363),.DEPTH(4)) q106(.clk,.reset,.iv(cv[106]&&legal[106]),.ir(source_accept[106]),.idata({write_[106],cl[3392+:32],ai[106],local_write_data[14848+:256]}),.ov(qv[106]),.ordy(qr[106]),.odata({qw[58],ql[106],qi[106],qd[58]}));
lf_adapter #(.SOURCE(107)) a107(.kind(ck[428+:4]),.local_id(cid[3424+:32]),.generation(cgen[3424+:32]),.line(cl[3424+:32]),.legal(legal[107]),.write(write_[107]),.packed_id(ai[107]),.returned_id(ri[107]),.returned_data(raw_rd[107]),.returned_kind(rk[428+:4]),.returned_local(rid[3424+:32]),.returned_gen(rgen[3424+:32]),.read_data(rd[27392+:256]),.returned_legal(rlegal[107]));
 assign cr[107]=source_accept[107]&&legal[107];
df_fifo #(.WIDTH(363),.DEPTH(4)) q107(.clk,.reset,.iv(cv[107]&&legal[107]),.ir(source_accept[107]),.idata({write_[107],cl[3424+:32],ai[107],local_write_data[15104+:256]}),.ov(qv[107]),.ordy(qr[107]),.odata({qw[59],ql[107],qi[107],qd[59]}));
lf_adapter #(.SOURCE(108)) a108(.kind(ck[432+:4]),.local_id(cid[3456+:32]),.generation(cgen[3456+:32]),.line(cl[3456+:32]),.legal(legal[108]),.write(write_[108]),.packed_id(ai[108]),.returned_id(ri[108]),.returned_data(raw_rd[108]),.returned_kind(rk[432+:4]),.returned_local(rid[3456+:32]),.returned_gen(rgen[3456+:32]),.read_data(rd[27648+:256]),.returned_legal(rlegal[108]));
 assign cr[108]=source_accept[108]&&legal[108];
df_fifo #(.WIDTH(363),.DEPTH(4)) q108(.clk,.reset,.iv(cv[108]&&legal[108]),.ir(source_accept[108]),.idata({write_[108],cl[3456+:32],ai[108],local_write_data[15360+:256]}),.ov(qv[108]),.ordy(qr[108]),.odata({qw[60],ql[108],qi[108],qd[60]}));
lf_adapter #(.SOURCE(109)) a109(.kind(ck[436+:4]),.local_id(cid[3488+:32]),.generation(cgen[3488+:32]),.line(cl[3488+:32]),.legal(legal[109]),.write(write_[109]),.packed_id(ai[109]),.returned_id(ri[109]),.returned_data(raw_rd[109]),.returned_kind(rk[436+:4]),.returned_local(rid[3488+:32]),.returned_gen(rgen[3488+:32]),.read_data(rd[27904+:256]),.returned_legal(rlegal[109]));
 assign cr[109]=source_accept[109]&&legal[109];
df_fifo #(.WIDTH(363),.DEPTH(4)) q109(.clk,.reset,.iv(cv[109]&&legal[109]),.ir(source_accept[109]),.idata({write_[109],cl[3488+:32],ai[109],local_write_data[15616+:256]}),.ov(qv[109]),.ordy(qr[109]),.odata({qw[61],ql[109],qi[109],qd[61]}));
lf_adapter #(.SOURCE(110)) a110(.kind(ck[440+:4]),.local_id(cid[3520+:32]),.generation(cgen[3520+:32]),.line(cl[3520+:32]),.legal(legal[110]),.write(write_[110]),.packed_id(ai[110]),.returned_id(ri[110]),.returned_data(raw_rd[110]),.returned_kind(rk[440+:4]),.returned_local(rid[3520+:32]),.returned_gen(rgen[3520+:32]),.read_data(rd[28160+:256]),.returned_legal(rlegal[110]));
 assign cr[110]=source_accept[110]&&legal[110];
df_fifo #(.WIDTH(363),.DEPTH(4)) q110(.clk,.reset,.iv(cv[110]&&legal[110]),.ir(source_accept[110]),.idata({write_[110],cl[3520+:32],ai[110],local_write_data[15872+:256]}),.ov(qv[110]),.ordy(qr[110]),.odata({qw[62],ql[110],qi[110],qd[62]}));
lf_adapter #(.SOURCE(111)) a111(.kind(ck[444+:4]),.local_id(cid[3552+:32]),.generation(cgen[3552+:32]),.line(cl[3552+:32]),.legal(legal[111]),.write(write_[111]),.packed_id(ai[111]),.returned_id(ri[111]),.returned_data(raw_rd[111]),.returned_kind(rk[444+:4]),.returned_local(rid[3552+:32]),.returned_gen(rgen[3552+:32]),.read_data(rd[28416+:256]),.returned_legal(rlegal[111]));
 assign cr[111]=source_accept[111]&&legal[111];
df_fifo #(.WIDTH(363),.DEPTH(4)) q111(.clk,.reset,.iv(cv[111]&&legal[111]),.ir(source_accept[111]),.idata({write_[111],cl[3552+:32],ai[111],local_write_data[16128+:256]}),.ov(qv[111]),.ordy(qr[111]),.odata({qw[63],ql[111],qi[111],qd[63]}));
lf_adapter #(.SOURCE(112)) a112(.kind(ck[448+:4]),.local_id(cid[3584+:32]),.generation(cgen[3584+:32]),.line(cl[3584+:32]),.legal(legal[112]),.write(write_[112]),.packed_id(ai[112]),.returned_id(ri[112]),.returned_data(raw_rd[112]),.returned_kind(rk[448+:4]),.returned_local(rid[3584+:32]),.returned_gen(rgen[3584+:32]),.read_data(rd[28672+:256]),.returned_legal(rlegal[112]));
 assign cr[112]=source_accept[112]&&legal[112];
df_fifo #(.WIDTH(363),.DEPTH(4)) q112(.clk,.reset,.iv(cv[112]&&legal[112]),.ir(source_accept[112]),.idata({write_[112],cl[3584+:32],ai[112],local_write_data[16384+:256]}),.ov(qv[112]),.ordy(qr[112]),.odata({qw[64],ql[112],qi[112],qd[64]}));
lf_adapter #(.SOURCE(113)) a113(.kind(ck[452+:4]),.local_id(cid[3616+:32]),.generation(cgen[3616+:32]),.line(cl[3616+:32]),.legal(legal[113]),.write(write_[113]),.packed_id(ai[113]),.returned_id(ri[113]),.returned_data(raw_rd[113]),.returned_kind(rk[452+:4]),.returned_local(rid[3616+:32]),.returned_gen(rgen[3616+:32]),.read_data(rd[28928+:256]),.returned_legal(rlegal[113]));
 assign cr[113]=source_accept[113]&&legal[113];
df_fifo #(.WIDTH(363),.DEPTH(4)) q113(.clk,.reset,.iv(cv[113]&&legal[113]),.ir(source_accept[113]),.idata({write_[113],cl[3616+:32],ai[113],local_write_data[16640+:256]}),.ov(qv[113]),.ordy(qr[113]),.odata({qw[65],ql[113],qi[113],qd[65]}));
lf_adapter #(.SOURCE(114)) a114(.kind(ck[456+:4]),.local_id(cid[3648+:32]),.generation(cgen[3648+:32]),.line(cl[3648+:32]),.legal(legal[114]),.write(write_[114]),.packed_id(ai[114]),.returned_id(ri[114]),.returned_data(raw_rd[114]),.returned_kind(rk[456+:4]),.returned_local(rid[3648+:32]),.returned_gen(rgen[3648+:32]),.read_data(rd[29184+:256]),.returned_legal(rlegal[114]));
 assign cr[114]=source_accept[114]&&legal[114];
df_fifo #(.WIDTH(363),.DEPTH(4)) q114(.clk,.reset,.iv(cv[114]&&legal[114]),.ir(source_accept[114]),.idata({write_[114],cl[3648+:32],ai[114],local_write_data[16896+:256]}),.ov(qv[114]),.ordy(qr[114]),.odata({qw[66],ql[114],qi[114],qd[66]}));
lf_adapter #(.SOURCE(115)) a115(.kind(ck[460+:4]),.local_id(cid[3680+:32]),.generation(cgen[3680+:32]),.line(cl[3680+:32]),.legal(legal[115]),.write(write_[115]),.packed_id(ai[115]),.returned_id(ri[115]),.returned_data(raw_rd[115]),.returned_kind(rk[460+:4]),.returned_local(rid[3680+:32]),.returned_gen(rgen[3680+:32]),.read_data(rd[29440+:256]),.returned_legal(rlegal[115]));
 assign cr[115]=source_accept[115]&&legal[115];
df_fifo #(.WIDTH(363),.DEPTH(4)) q115(.clk,.reset,.iv(cv[115]&&legal[115]),.ir(source_accept[115]),.idata({write_[115],cl[3680+:32],ai[115],local_write_data[17152+:256]}),.ov(qv[115]),.ordy(qr[115]),.odata({qw[67],ql[115],qi[115],qd[67]}));
lf_adapter #(.SOURCE(116)) a116(.kind(ck[464+:4]),.local_id(cid[3712+:32]),.generation(cgen[3712+:32]),.line(cl[3712+:32]),.legal(legal[116]),.write(write_[116]),.packed_id(ai[116]),.returned_id(ri[116]),.returned_data(raw_rd[116]),.returned_kind(rk[464+:4]),.returned_local(rid[3712+:32]),.returned_gen(rgen[3712+:32]),.read_data(rd[29696+:256]),.returned_legal(rlegal[116]));
 assign cr[116]=source_accept[116]&&legal[116];
df_fifo #(.WIDTH(363),.DEPTH(4)) q116(.clk,.reset,.iv(cv[116]&&legal[116]),.ir(source_accept[116]),.idata({write_[116],cl[3712+:32],ai[116],local_write_data[17408+:256]}),.ov(qv[116]),.ordy(qr[116]),.odata({qw[68],ql[116],qi[116],qd[68]}));
lf_adapter #(.SOURCE(117)) a117(.kind(ck[468+:4]),.local_id(cid[3744+:32]),.generation(cgen[3744+:32]),.line(cl[3744+:32]),.legal(legal[117]),.write(write_[117]),.packed_id(ai[117]),.returned_id(ri[117]),.returned_data(raw_rd[117]),.returned_kind(rk[468+:4]),.returned_local(rid[3744+:32]),.returned_gen(rgen[3744+:32]),.read_data(rd[29952+:256]),.returned_legal(rlegal[117]));
 assign cr[117]=source_accept[117]&&legal[117];
df_fifo #(.WIDTH(363),.DEPTH(4)) q117(.clk,.reset,.iv(cv[117]&&legal[117]),.ir(source_accept[117]),.idata({write_[117],cl[3744+:32],ai[117],local_write_data[17664+:256]}),.ov(qv[117]),.ordy(qr[117]),.odata({qw[69],ql[117],qi[117],qd[69]}));
lf_adapter #(.SOURCE(118)) a118(.kind(ck[472+:4]),.local_id(cid[3776+:32]),.generation(cgen[3776+:32]),.line(cl[3776+:32]),.legal(legal[118]),.write(write_[118]),.packed_id(ai[118]),.returned_id(ri[118]),.returned_data(raw_rd[118]),.returned_kind(rk[472+:4]),.returned_local(rid[3776+:32]),.returned_gen(rgen[3776+:32]),.read_data(rd[30208+:256]),.returned_legal(rlegal[118]));
 assign cr[118]=source_accept[118]&&legal[118];
df_fifo #(.WIDTH(363),.DEPTH(4)) q118(.clk,.reset,.iv(cv[118]&&legal[118]),.ir(source_accept[118]),.idata({write_[118],cl[3776+:32],ai[118],local_write_data[17920+:256]}),.ov(qv[118]),.ordy(qr[118]),.odata({qw[70],ql[118],qi[118],qd[70]}));
lf_adapter #(.SOURCE(119)) a119(.kind(ck[476+:4]),.local_id(cid[3808+:32]),.generation(cgen[3808+:32]),.line(cl[3808+:32]),.legal(legal[119]),.write(write_[119]),.packed_id(ai[119]),.returned_id(ri[119]),.returned_data(raw_rd[119]),.returned_kind(rk[476+:4]),.returned_local(rid[3808+:32]),.returned_gen(rgen[3808+:32]),.read_data(rd[30464+:256]),.returned_legal(rlegal[119]));
 assign cr[119]=source_accept[119]&&legal[119];
df_fifo #(.WIDTH(363),.DEPTH(4)) q119(.clk,.reset,.iv(cv[119]&&legal[119]),.ir(source_accept[119]),.idata({write_[119],cl[3808+:32],ai[119],local_write_data[18176+:256]}),.ov(qv[119]),.ordy(qr[119]),.odata({qw[71],ql[119],qi[119],qd[71]}));
lf_adapter #(.SOURCE(120)) a120(.kind(ck[480+:4]),.local_id(cid[3840+:32]),.generation(cgen[3840+:32]),.line(cl[3840+:32]),.legal(legal[120]),.write(write_[120]),.packed_id(ai[120]),.returned_id(ri[120]),.returned_data(raw_rd[120]),.returned_kind(rk[480+:4]),.returned_local(rid[3840+:32]),.returned_gen(rgen[3840+:32]),.read_data(rd[30720+:256]),.returned_legal(rlegal[120]));
 assign cr[120]=source_accept[120]&&legal[120];
df_fifo #(.WIDTH(363),.DEPTH(4)) q120(.clk,.reset,.iv(cv[120]&&legal[120]),.ir(source_accept[120]),.idata({write_[120],cl[3840+:32],ai[120],local_write_data[18432+:256]}),.ov(qv[120]),.ordy(qr[120]),.odata({qw[72],ql[120],qi[120],qd[72]}));
lf_adapter #(.SOURCE(121)) a121(.kind(ck[484+:4]),.local_id(cid[3872+:32]),.generation(cgen[3872+:32]),.line(cl[3872+:32]),.legal(legal[121]),.write(write_[121]),.packed_id(ai[121]),.returned_id(ri[121]),.returned_data(raw_rd[121]),.returned_kind(rk[484+:4]),.returned_local(rid[3872+:32]),.returned_gen(rgen[3872+:32]),.read_data(rd[30976+:256]),.returned_legal(rlegal[121]));
 assign cr[121]=source_accept[121]&&legal[121];
df_fifo #(.WIDTH(363),.DEPTH(4)) q121(.clk,.reset,.iv(cv[121]&&legal[121]),.ir(source_accept[121]),.idata({write_[121],cl[3872+:32],ai[121],local_write_data[18688+:256]}),.ov(qv[121]),.ordy(qr[121]),.odata({qw[73],ql[121],qi[121],qd[73]}));
lf_adapter #(.SOURCE(122)) a122(.kind(ck[488+:4]),.local_id(cid[3904+:32]),.generation(cgen[3904+:32]),.line(cl[3904+:32]),.legal(legal[122]),.write(write_[122]),.packed_id(ai[122]),.returned_id(ri[122]),.returned_data(raw_rd[122]),.returned_kind(rk[488+:4]),.returned_local(rid[3904+:32]),.returned_gen(rgen[3904+:32]),.read_data(rd[31232+:256]),.returned_legal(rlegal[122]));
 assign cr[122]=source_accept[122]&&legal[122];
df_fifo #(.WIDTH(363),.DEPTH(4)) q122(.clk,.reset,.iv(cv[122]&&legal[122]),.ir(source_accept[122]),.idata({write_[122],cl[3904+:32],ai[122],local_write_data[18944+:256]}),.ov(qv[122]),.ordy(qr[122]),.odata({qw[74],ql[122],qi[122],qd[74]}));
lf_adapter #(.SOURCE(123)) a123(.kind(ck[492+:4]),.local_id(cid[3936+:32]),.generation(cgen[3936+:32]),.line(cl[3936+:32]),.legal(legal[123]),.write(write_[123]),.packed_id(ai[123]),.returned_id(ri[123]),.returned_data(raw_rd[123]),.returned_kind(rk[492+:4]),.returned_local(rid[3936+:32]),.returned_gen(rgen[3936+:32]),.read_data(rd[31488+:256]),.returned_legal(rlegal[123]));
 assign cr[123]=source_accept[123]&&legal[123];
df_fifo #(.WIDTH(363),.DEPTH(4)) q123(.clk,.reset,.iv(cv[123]&&legal[123]),.ir(source_accept[123]),.idata({write_[123],cl[3936+:32],ai[123],local_write_data[19200+:256]}),.ov(qv[123]),.ordy(qr[123]),.odata({qw[75],ql[123],qi[123],qd[75]}));
lf_adapter #(.SOURCE(124)) a124(.kind(ck[496+:4]),.local_id(cid[3968+:32]),.generation(cgen[3968+:32]),.line(cl[3968+:32]),.legal(legal[124]),.write(write_[124]),.packed_id(ai[124]),.returned_id(ri[124]),.returned_data(raw_rd[124]),.returned_kind(rk[496+:4]),.returned_local(rid[3968+:32]),.returned_gen(rgen[3968+:32]),.read_data(rd[31744+:256]),.returned_legal(rlegal[124]));
 assign cr[124]=source_accept[124]&&legal[124];
df_fifo #(.WIDTH(363),.DEPTH(4)) q124(.clk,.reset,.iv(cv[124]&&legal[124]),.ir(source_accept[124]),.idata({write_[124],cl[3968+:32],ai[124],local_write_data[19456+:256]}),.ov(qv[124]),.ordy(qr[124]),.odata({qw[76],ql[124],qi[124],qd[76]}));
lf_adapter #(.SOURCE(125)) a125(.kind(ck[500+:4]),.local_id(cid[4000+:32]),.generation(cgen[4000+:32]),.line(cl[4000+:32]),.legal(legal[125]),.write(write_[125]),.packed_id(ai[125]),.returned_id(ri[125]),.returned_data(raw_rd[125]),.returned_kind(rk[500+:4]),.returned_local(rid[4000+:32]),.returned_gen(rgen[4000+:32]),.read_data(rd[32000+:256]),.returned_legal(rlegal[125]));
 assign cr[125]=source_accept[125]&&legal[125];
df_fifo #(.WIDTH(363),.DEPTH(4)) q125(.clk,.reset,.iv(cv[125]&&legal[125]),.ir(source_accept[125]),.idata({write_[125],cl[4000+:32],ai[125],local_write_data[19712+:256]}),.ov(qv[125]),.ordy(qr[125]),.odata({qw[77],ql[125],qi[125],qd[77]}));
lf_adapter #(.SOURCE(126)) a126(.kind(ck[504+:4]),.local_id(cid[4032+:32]),.generation(cgen[4032+:32]),.line(cl[4032+:32]),.legal(legal[126]),.write(write_[126]),.packed_id(ai[126]),.returned_id(ri[126]),.returned_data(raw_rd[126]),.returned_kind(rk[504+:4]),.returned_local(rid[4032+:32]),.returned_gen(rgen[4032+:32]),.read_data(rd[32256+:256]),.returned_legal(rlegal[126]));
 assign cr[126]=source_accept[126]&&legal[126];
df_fifo #(.WIDTH(363),.DEPTH(4)) q126(.clk,.reset,.iv(cv[126]&&legal[126]),.ir(source_accept[126]),.idata({write_[126],cl[4032+:32],ai[126],local_write_data[19968+:256]}),.ov(qv[126]),.ordy(qr[126]),.odata({qw[78],ql[126],qi[126],qd[78]}));
lf_adapter #(.SOURCE(127)) a127(.kind(ck[508+:4]),.local_id(cid[4064+:32]),.generation(cgen[4064+:32]),.line(cl[4064+:32]),.legal(legal[127]),.write(write_[127]),.packed_id(ai[127]),.returned_id(ri[127]),.returned_data(raw_rd[127]),.returned_kind(rk[508+:4]),.returned_local(rid[4064+:32]),.returned_gen(rgen[4064+:32]),.read_data(rd[32512+:256]),.returned_legal(rlegal[127]));
 assign cr[127]=source_accept[127]&&legal[127];
df_fifo #(.WIDTH(363),.DEPTH(4)) q127(.clk,.reset,.iv(cv[127]&&legal[127]),.ir(source_accept[127]),.idata({write_[127],cl[4064+:32],ai[127],local_write_data[20224+:256]}),.ov(qv[127]),.ordy(qr[127]),.odata({qw[79],ql[127],qi[127],qd[79]}));
lf_adapter #(.SOURCE(128)) a128(.kind(ck[512+:4]),.local_id(cid[4096+:32]),.generation(cgen[4096+:32]),.line(cl[4096+:32]),.legal(legal[128]),.write(write_[128]),.packed_id(ai[128]),.returned_id(ri[128]),.returned_data(raw_rd[128]),.returned_kind(rk[512+:4]),.returned_local(rid[4096+:32]),.returned_gen(rgen[4096+:32]),.read_data(rd[32768+:256]),.returned_legal(rlegal[128]));
 assign cr[128]=source_accept[128]&&legal[128];
df_fifo #(.WIDTH(363),.DEPTH(4)) q128(.clk,.reset,.iv(cv[128]&&legal[128]),.ir(source_accept[128]),.idata({write_[128],cl[4096+:32],ai[128],local_write_data[20480+:256]}),.ov(qv[128]),.ordy(qr[128]),.odata({qw[80],ql[128],qi[128],qd[80]}));
lf_adapter #(.SOURCE(129)) a129(.kind(ck[516+:4]),.local_id(cid[4128+:32]),.generation(cgen[4128+:32]),.line(cl[4128+:32]),.legal(legal[129]),.write(write_[129]),.packed_id(ai[129]),.returned_id(ri[129]),.returned_data(raw_rd[129]),.returned_kind(rk[516+:4]),.returned_local(rid[4128+:32]),.returned_gen(rgen[4128+:32]),.read_data(rd[33024+:256]),.returned_legal(rlegal[129]));
 assign cr[129]=source_accept[129]&&legal[129];
df_fifo #(.WIDTH(363),.DEPTH(4)) q129(.clk,.reset,.iv(cv[129]&&legal[129]),.ir(source_accept[129]),.idata({write_[129],cl[4128+:32],ai[129],local_write_data[20736+:256]}),.ov(qv[129]),.ordy(qr[129]),.odata({qw[81],ql[129],qi[129],qd[81]}));
lf_adapter #(.SOURCE(130)) a130(.kind(ck[520+:4]),.local_id(cid[4160+:32]),.generation(cgen[4160+:32]),.line(cl[4160+:32]),.legal(legal[130]),.write(write_[130]),.packed_id(ai[130]),.returned_id(ri[130]),.returned_data(raw_rd[130]),.returned_kind(rk[520+:4]),.returned_local(rid[4160+:32]),.returned_gen(rgen[4160+:32]),.read_data(rd[33280+:256]),.returned_legal(rlegal[130]));
 assign cr[130]=source_accept[130]&&legal[130];
df_fifo #(.WIDTH(363),.DEPTH(4)) q130(.clk,.reset,.iv(cv[130]&&legal[130]),.ir(source_accept[130]),.idata({write_[130],cl[4160+:32],ai[130],local_write_data[20992+:256]}),.ov(qv[130]),.ordy(qr[130]),.odata({qw[82],ql[130],qi[130],qd[82]}));
lf_adapter #(.SOURCE(131)) a131(.kind(ck[524+:4]),.local_id(cid[4192+:32]),.generation(cgen[4192+:32]),.line(cl[4192+:32]),.legal(legal[131]),.write(write_[131]),.packed_id(ai[131]),.returned_id(ri[131]),.returned_data(raw_rd[131]),.returned_kind(rk[524+:4]),.returned_local(rid[4192+:32]),.returned_gen(rgen[4192+:32]),.read_data(rd[33536+:256]),.returned_legal(rlegal[131]));
 assign cr[131]=source_accept[131]&&legal[131];
df_fifo #(.WIDTH(363),.DEPTH(4)) q131(.clk,.reset,.iv(cv[131]&&legal[131]),.ir(source_accept[131]),.idata({write_[131],cl[4192+:32],ai[131],local_write_data[21248+:256]}),.ov(qv[131]),.ordy(qr[131]),.odata({qw[83],ql[131],qi[131],qd[83]}));
lf_adapter #(.SOURCE(132)) a132(.kind(ck[528+:4]),.local_id(cid[4224+:32]),.generation(cgen[4224+:32]),.line(cl[4224+:32]),.legal(legal[132]),.write(write_[132]),.packed_id(ai[132]),.returned_id(ri[132]),.returned_data(raw_rd[132]),.returned_kind(rk[528+:4]),.returned_local(rid[4224+:32]),.returned_gen(rgen[4224+:32]),.read_data(rd[33792+:256]),.returned_legal(rlegal[132]));
 assign cr[132]=source_accept[132]&&legal[132];
df_fifo #(.WIDTH(363),.DEPTH(4)) q132(.clk,.reset,.iv(cv[132]&&legal[132]),.ir(source_accept[132]),.idata({write_[132],cl[4224+:32],ai[132],local_write_data[21504+:256]}),.ov(qv[132]),.ordy(qr[132]),.odata({qw[84],ql[132],qi[132],qd[84]}));
lf_adapter #(.SOURCE(133)) a133(.kind(ck[532+:4]),.local_id(cid[4256+:32]),.generation(cgen[4256+:32]),.line(cl[4256+:32]),.legal(legal[133]),.write(write_[133]),.packed_id(ai[133]),.returned_id(ri[133]),.returned_data(raw_rd[133]),.returned_kind(rk[532+:4]),.returned_local(rid[4256+:32]),.returned_gen(rgen[4256+:32]),.read_data(rd[34048+:256]),.returned_legal(rlegal[133]));
 assign cr[133]=source_accept[133]&&legal[133];
df_fifo #(.WIDTH(363),.DEPTH(4)) q133(.clk,.reset,.iv(cv[133]&&legal[133]),.ir(source_accept[133]),.idata({write_[133],cl[4256+:32],ai[133],local_write_data[21760+:256]}),.ov(qv[133]),.ordy(qr[133]),.odata({qw[85],ql[133],qi[133],qd[85]}));
lf_adapter #(.SOURCE(134)) a134(.kind(ck[536+:4]),.local_id(cid[4288+:32]),.generation(cgen[4288+:32]),.line(cl[4288+:32]),.legal(legal[134]),.write(write_[134]),.packed_id(ai[134]),.returned_id(ri[134]),.returned_data(raw_rd[134]),.returned_kind(rk[536+:4]),.returned_local(rid[4288+:32]),.returned_gen(rgen[4288+:32]),.read_data(rd[34304+:256]),.returned_legal(rlegal[134]));
 assign cr[134]=source_accept[134]&&legal[134];
df_fifo #(.WIDTH(363),.DEPTH(4)) q134(.clk,.reset,.iv(cv[134]&&legal[134]),.ir(source_accept[134]),.idata({write_[134],cl[4288+:32],ai[134],local_write_data[22016+:256]}),.ov(qv[134]),.ordy(qr[134]),.odata({qw[86],ql[134],qi[134],qd[86]}));
lf_adapter #(.SOURCE(135)) a135(.kind(ck[540+:4]),.local_id(cid[4320+:32]),.generation(cgen[4320+:32]),.line(cl[4320+:32]),.legal(legal[135]),.write(write_[135]),.packed_id(ai[135]),.returned_id(ri[135]),.returned_data(raw_rd[135]),.returned_kind(rk[540+:4]),.returned_local(rid[4320+:32]),.returned_gen(rgen[4320+:32]),.read_data(rd[34560+:256]),.returned_legal(rlegal[135]));
 assign cr[135]=source_accept[135]&&legal[135];
df_fifo #(.WIDTH(363),.DEPTH(4)) q135(.clk,.reset,.iv(cv[135]&&legal[135]),.ir(source_accept[135]),.idata({write_[135],cl[4320+:32],ai[135],local_write_data[22272+:256]}),.ov(qv[135]),.ordy(qr[135]),.odata({qw[87],ql[135],qi[135],qd[87]}));
lf_adapter #(.SOURCE(136)) a136(.kind(ck[544+:4]),.local_id(cid[4352+:32]),.generation(cgen[4352+:32]),.line(cl[4352+:32]),.legal(legal[136]),.write(write_[136]),.packed_id(ai[136]),.returned_id(ri[136]),.returned_data(raw_rd[136]),.returned_kind(rk[544+:4]),.returned_local(rid[4352+:32]),.returned_gen(rgen[4352+:32]),.read_data(rd[34816+:256]),.returned_legal(rlegal[136]));
 assign cr[136]=source_accept[136]&&legal[136];
df_fifo #(.WIDTH(363),.DEPTH(4)) q136(.clk,.reset,.iv(cv[136]&&legal[136]),.ir(source_accept[136]),.idata({write_[136],cl[4352+:32],ai[136],local_write_data[22528+:256]}),.ov(qv[136]),.ordy(qr[136]),.odata({qw[88],ql[136],qi[136],qd[88]}));
lf_adapter #(.SOURCE(137)) a137(.kind(ck[548+:4]),.local_id(cid[4384+:32]),.generation(cgen[4384+:32]),.line(cl[4384+:32]),.legal(legal[137]),.write(write_[137]),.packed_id(ai[137]),.returned_id(ri[137]),.returned_data(raw_rd[137]),.returned_kind(rk[548+:4]),.returned_local(rid[4384+:32]),.returned_gen(rgen[4384+:32]),.read_data(rd[35072+:256]),.returned_legal(rlegal[137]));
 assign cr[137]=source_accept[137]&&legal[137];
df_fifo #(.WIDTH(363),.DEPTH(4)) q137(.clk,.reset,.iv(cv[137]&&legal[137]),.ir(source_accept[137]),.idata({write_[137],cl[4384+:32],ai[137],local_write_data[22784+:256]}),.ov(qv[137]),.ordy(qr[137]),.odata({qw[89],ql[137],qi[137],qd[89]}));
lf_adapter #(.SOURCE(138)) a138(.kind(ck[552+:4]),.local_id(cid[4416+:32]),.generation(cgen[4416+:32]),.line(cl[4416+:32]),.legal(legal[138]),.write(write_[138]),.packed_id(ai[138]),.returned_id(ri[138]),.returned_data(raw_rd[138]),.returned_kind(rk[552+:4]),.returned_local(rid[4416+:32]),.returned_gen(rgen[4416+:32]),.read_data(rd[35328+:256]),.returned_legal(rlegal[138]));
 assign cr[138]=source_accept[138]&&legal[138];
df_fifo #(.WIDTH(363),.DEPTH(4)) q138(.clk,.reset,.iv(cv[138]&&legal[138]),.ir(source_accept[138]),.idata({write_[138],cl[4416+:32],ai[138],local_write_data[23040+:256]}),.ov(qv[138]),.ordy(qr[138]),.odata({qw[90],ql[138],qi[138],qd[90]}));
lf_adapter #(.SOURCE(139)) a139(.kind(ck[556+:4]),.local_id(cid[4448+:32]),.generation(cgen[4448+:32]),.line(cl[4448+:32]),.legal(legal[139]),.write(write_[139]),.packed_id(ai[139]),.returned_id(ri[139]),.returned_data(raw_rd[139]),.returned_kind(rk[556+:4]),.returned_local(rid[4448+:32]),.returned_gen(rgen[4448+:32]),.read_data(rd[35584+:256]),.returned_legal(rlegal[139]));
 assign cr[139]=source_accept[139]&&legal[139];
df_fifo #(.WIDTH(363),.DEPTH(4)) q139(.clk,.reset,.iv(cv[139]&&legal[139]),.ir(source_accept[139]),.idata({write_[139],cl[4448+:32],ai[139],local_write_data[23296+:256]}),.ov(qv[139]),.ordy(qr[139]),.odata({qw[91],ql[139],qi[139],qd[91]}));
lf_adapter #(.SOURCE(140)) a140(.kind(ck[560+:4]),.local_id(cid[4480+:32]),.generation(cgen[4480+:32]),.line(cl[4480+:32]),.legal(legal[140]),.write(write_[140]),.packed_id(ai[140]),.returned_id(ri[140]),.returned_data(raw_rd[140]),.returned_kind(rk[560+:4]),.returned_local(rid[4480+:32]),.returned_gen(rgen[4480+:32]),.read_data(rd[35840+:256]),.returned_legal(rlegal[140]));
 assign cr[140]=source_accept[140]&&legal[140];
df_fifo #(.WIDTH(363),.DEPTH(4)) q140(.clk,.reset,.iv(cv[140]&&legal[140]),.ir(source_accept[140]),.idata({write_[140],cl[4480+:32],ai[140],local_write_data[23552+:256]}),.ov(qv[140]),.ordy(qr[140]),.odata({qw[92],ql[140],qi[140],qd[92]}));
lf_adapter #(.SOURCE(141)) a141(.kind(ck[564+:4]),.local_id(cid[4512+:32]),.generation(cgen[4512+:32]),.line(cl[4512+:32]),.legal(legal[141]),.write(write_[141]),.packed_id(ai[141]),.returned_id(ri[141]),.returned_data(raw_rd[141]),.returned_kind(rk[564+:4]),.returned_local(rid[4512+:32]),.returned_gen(rgen[4512+:32]),.read_data(rd[36096+:256]),.returned_legal(rlegal[141]));
 assign cr[141]=source_accept[141]&&legal[141];
df_fifo #(.WIDTH(363),.DEPTH(4)) q141(.clk,.reset,.iv(cv[141]&&legal[141]),.ir(source_accept[141]),.idata({write_[141],cl[4512+:32],ai[141],local_write_data[23808+:256]}),.ov(qv[141]),.ordy(qr[141]),.odata({qw[93],ql[141],qi[141],qd[93]}));
lf_adapter #(.SOURCE(142)) a142(.kind(ck[568+:4]),.local_id(cid[4544+:32]),.generation(cgen[4544+:32]),.line(cl[4544+:32]),.legal(legal[142]),.write(write_[142]),.packed_id(ai[142]),.returned_id(ri[142]),.returned_data(raw_rd[142]),.returned_kind(rk[568+:4]),.returned_local(rid[4544+:32]),.returned_gen(rgen[4544+:32]),.read_data(rd[36352+:256]),.returned_legal(rlegal[142]));
 assign cr[142]=source_accept[142]&&legal[142];
df_fifo #(.WIDTH(363),.DEPTH(4)) q142(.clk,.reset,.iv(cv[142]&&legal[142]),.ir(source_accept[142]),.idata({write_[142],cl[4544+:32],ai[142],local_write_data[24064+:256]}),.ov(qv[142]),.ordy(qr[142]),.odata({qw[94],ql[142],qi[142],qd[94]}));
lf_adapter #(.SOURCE(143)) a143(.kind(ck[572+:4]),.local_id(cid[4576+:32]),.generation(cgen[4576+:32]),.line(cl[4576+:32]),.legal(legal[143]),.write(write_[143]),.packed_id(ai[143]),.returned_id(ri[143]),.returned_data(raw_rd[143]),.returned_kind(rk[572+:4]),.returned_local(rid[4576+:32]),.returned_gen(rgen[4576+:32]),.read_data(rd[36608+:256]),.returned_legal(rlegal[143]));
 assign cr[143]=source_accept[143]&&legal[143];
df_fifo #(.WIDTH(363),.DEPTH(4)) q143(.clk,.reset,.iv(cv[143]&&legal[143]),.ir(source_accept[143]),.idata({write_[143],cl[4576+:32],ai[143],local_write_data[24320+:256]}),.ov(qv[143]),.ordy(qr[143]),.odata({qw[95],ql[143],qi[143],qd[95]}));
lf_adapter #(.SOURCE(144)) a144(.kind(ck[576+:4]),.local_id(cid[4608+:32]),.generation(cgen[4608+:32]),.line(cl[4608+:32]),.legal(legal[144]),.write(write_[144]),.packed_id(ai[144]),.returned_id(ri[144]),.returned_data(raw_rd[144]),.returned_kind(rk[576+:4]),.returned_local(rid[4608+:32]),.returned_gen(rgen[4608+:32]),.read_data(rd[36864+:256]),.returned_legal(rlegal[144]));
 assign cr[144]=source_accept[144]&&legal[144];
df_fifo #(.WIDTH(363),.DEPTH(4)) q144(.clk,.reset,.iv(cv[144]&&legal[144]),.ir(source_accept[144]),.idata({write_[144],cl[4608+:32],ai[144],local_write_data[24576+:256]}),.ov(qv[144]),.ordy(qr[144]),.odata({qw[96],ql[144],qi[144],qd[96]}));
lf_adapter #(.SOURCE(145)) a145(.kind(ck[580+:4]),.local_id(cid[4640+:32]),.generation(cgen[4640+:32]),.line(cl[4640+:32]),.legal(legal[145]),.write(write_[145]),.packed_id(ai[145]),.returned_id(ri[145]),.returned_data(raw_rd[145]),.returned_kind(rk[580+:4]),.returned_local(rid[4640+:32]),.returned_gen(rgen[4640+:32]),.read_data(rd[37120+:256]),.returned_legal(rlegal[145]));
 assign cr[145]=source_accept[145]&&legal[145];
df_fifo #(.WIDTH(363),.DEPTH(4)) q145(.clk,.reset,.iv(cv[145]&&legal[145]),.ir(source_accept[145]),.idata({write_[145],cl[4640+:32],ai[145],local_write_data[24832+:256]}),.ov(qv[145]),.ordy(qr[145]),.odata({qw[97],ql[145],qi[145],qd[97]}));
lf_adapter #(.SOURCE(146)) a146(.kind(ck[584+:4]),.local_id(cid[4672+:32]),.generation(cgen[4672+:32]),.line(cl[4672+:32]),.legal(legal[146]),.write(write_[146]),.packed_id(ai[146]),.returned_id(ri[146]),.returned_data(raw_rd[146]),.returned_kind(rk[584+:4]),.returned_local(rid[4672+:32]),.returned_gen(rgen[4672+:32]),.read_data(rd[37376+:256]),.returned_legal(rlegal[146]));
 assign cr[146]=source_accept[146]&&legal[146];
df_fifo #(.WIDTH(363),.DEPTH(4)) q146(.clk,.reset,.iv(cv[146]&&legal[146]),.ir(source_accept[146]),.idata({write_[146],cl[4672+:32],ai[146],local_write_data[25088+:256]}),.ov(qv[146]),.ordy(qr[146]),.odata({qw[98],ql[146],qi[146],qd[98]}));
lf_adapter #(.SOURCE(147)) a147(.kind(ck[588+:4]),.local_id(cid[4704+:32]),.generation(cgen[4704+:32]),.line(cl[4704+:32]),.legal(legal[147]),.write(write_[147]),.packed_id(ai[147]),.returned_id(ri[147]),.returned_data(raw_rd[147]),.returned_kind(rk[588+:4]),.returned_local(rid[4704+:32]),.returned_gen(rgen[4704+:32]),.read_data(rd[37632+:256]),.returned_legal(rlegal[147]));
 assign cr[147]=source_accept[147]&&legal[147];
df_fifo #(.WIDTH(363),.DEPTH(4)) q147(.clk,.reset,.iv(cv[147]&&legal[147]),.ir(source_accept[147]),.idata({write_[147],cl[4704+:32],ai[147],local_write_data[25344+:256]}),.ov(qv[147]),.ordy(qr[147]),.odata({qw[99],ql[147],qi[147],qd[99]}));
lf_adapter #(.SOURCE(148)) a148(.kind(ck[592+:4]),.local_id(cid[4736+:32]),.generation(cgen[4736+:32]),.line(cl[4736+:32]),.legal(legal[148]),.write(write_[148]),.packed_id(ai[148]),.returned_id(ri[148]),.returned_data(raw_rd[148]),.returned_kind(rk[592+:4]),.returned_local(rid[4736+:32]),.returned_gen(rgen[4736+:32]),.read_data(rd[37888+:256]),.returned_legal(rlegal[148]));
 assign cr[148]=source_accept[148]&&legal[148];
df_fifo #(.WIDTH(363),.DEPTH(4)) q148(.clk,.reset,.iv(cv[148]&&legal[148]),.ir(source_accept[148]),.idata({write_[148],cl[4736+:32],ai[148],local_write_data[25600+:256]}),.ov(qv[148]),.ordy(qr[148]),.odata({qw[100],ql[148],qi[148],qd[100]}));
lf_adapter #(.SOURCE(149)) a149(.kind(ck[596+:4]),.local_id(cid[4768+:32]),.generation(cgen[4768+:32]),.line(cl[4768+:32]),.legal(legal[149]),.write(write_[149]),.packed_id(ai[149]),.returned_id(ri[149]),.returned_data(raw_rd[149]),.returned_kind(rk[596+:4]),.returned_local(rid[4768+:32]),.returned_gen(rgen[4768+:32]),.read_data(rd[38144+:256]),.returned_legal(rlegal[149]));
 assign cr[149]=source_accept[149]&&legal[149];
df_fifo #(.WIDTH(363),.DEPTH(4)) q149(.clk,.reset,.iv(cv[149]&&legal[149]),.ir(source_accept[149]),.idata({write_[149],cl[4768+:32],ai[149],local_write_data[25856+:256]}),.ov(qv[149]),.ordy(qr[149]),.odata({qw[101],ql[149],qi[149],qd[101]}));
lf_adapter #(.SOURCE(150)) a150(.kind(ck[600+:4]),.local_id(cid[4800+:32]),.generation(cgen[4800+:32]),.line(cl[4800+:32]),.legal(legal[150]),.write(write_[150]),.packed_id(ai[150]),.returned_id(ri[150]),.returned_data(raw_rd[150]),.returned_kind(rk[600+:4]),.returned_local(rid[4800+:32]),.returned_gen(rgen[4800+:32]),.read_data(rd[38400+:256]),.returned_legal(rlegal[150]));
 assign cr[150]=source_accept[150]&&legal[150];
df_fifo #(.WIDTH(363),.DEPTH(4)) q150(.clk,.reset,.iv(cv[150]&&legal[150]),.ir(source_accept[150]),.idata({write_[150],cl[4800+:32],ai[150],local_write_data[26112+:256]}),.ov(qv[150]),.ordy(qr[150]),.odata({qw[102],ql[150],qi[150],qd[102]}));
lf_adapter #(.SOURCE(151)) a151(.kind(ck[604+:4]),.local_id(cid[4832+:32]),.generation(cgen[4832+:32]),.line(cl[4832+:32]),.legal(legal[151]),.write(write_[151]),.packed_id(ai[151]),.returned_id(ri[151]),.returned_data(raw_rd[151]),.returned_kind(rk[604+:4]),.returned_local(rid[4832+:32]),.returned_gen(rgen[4832+:32]),.read_data(rd[38656+:256]),.returned_legal(rlegal[151]));
 assign cr[151]=source_accept[151]&&legal[151];
df_fifo #(.WIDTH(363),.DEPTH(4)) q151(.clk,.reset,.iv(cv[151]&&legal[151]),.ir(source_accept[151]),.idata({write_[151],cl[4832+:32],ai[151],local_write_data[26368+:256]}),.ov(qv[151]),.ordy(qr[151]),.odata({qw[103],ql[151],qi[151],qd[103]}));
lf_adapter #(.SOURCE(152)) a152(.kind(ck[608+:4]),.local_id(cid[4864+:32]),.generation(cgen[4864+:32]),.line(cl[4864+:32]),.legal(legal[152]),.write(write_[152]),.packed_id(ai[152]),.returned_id(ri[152]),.returned_data(raw_rd[152]),.returned_kind(rk[608+:4]),.returned_local(rid[4864+:32]),.returned_gen(rgen[4864+:32]),.read_data(rd[38912+:256]),.returned_legal(rlegal[152]));
 assign cr[152]=source_accept[152]&&legal[152];
df_fifo #(.WIDTH(363),.DEPTH(4)) q152(.clk,.reset,.iv(cv[152]&&legal[152]),.ir(source_accept[152]),.idata({write_[152],cl[4864+:32],ai[152],local_write_data[26624+:256]}),.ov(qv[152]),.ordy(qr[152]),.odata({qw[104],ql[152],qi[152],qd[104]}));
lf_adapter #(.SOURCE(153)) a153(.kind(ck[612+:4]),.local_id(cid[4896+:32]),.generation(cgen[4896+:32]),.line(cl[4896+:32]),.legal(legal[153]),.write(write_[153]),.packed_id(ai[153]),.returned_id(ri[153]),.returned_data(raw_rd[153]),.returned_kind(rk[612+:4]),.returned_local(rid[4896+:32]),.returned_gen(rgen[4896+:32]),.read_data(rd[39168+:256]),.returned_legal(rlegal[153]));
 assign cr[153]=source_accept[153]&&legal[153];
df_fifo #(.WIDTH(363),.DEPTH(4)) q153(.clk,.reset,.iv(cv[153]&&legal[153]),.ir(source_accept[153]),.idata({write_[153],cl[4896+:32],ai[153],local_write_data[26880+:256]}),.ov(qv[153]),.ordy(qr[153]),.odata({qw[105],ql[153],qi[153],qd[105]}));
lf_adapter #(.SOURCE(154)) a154(.kind(ck[616+:4]),.local_id(cid[4928+:32]),.generation(cgen[4928+:32]),.line(cl[4928+:32]),.legal(legal[154]),.write(write_[154]),.packed_id(ai[154]),.returned_id(ri[154]),.returned_data(raw_rd[154]),.returned_kind(rk[616+:4]),.returned_local(rid[4928+:32]),.returned_gen(rgen[4928+:32]),.read_data(rd[39424+:256]),.returned_legal(rlegal[154]));
 assign cr[154]=source_accept[154]&&legal[154];
df_fifo #(.WIDTH(363),.DEPTH(4)) q154(.clk,.reset,.iv(cv[154]&&legal[154]),.ir(source_accept[154]),.idata({write_[154],cl[4928+:32],ai[154],local_write_data[27136+:256]}),.ov(qv[154]),.ordy(qr[154]),.odata({qw[106],ql[154],qi[154],qd[106]}));
lf_adapter #(.SOURCE(155)) a155(.kind(ck[620+:4]),.local_id(cid[4960+:32]),.generation(cgen[4960+:32]),.line(cl[4960+:32]),.legal(legal[155]),.write(write_[155]),.packed_id(ai[155]),.returned_id(ri[155]),.returned_data(raw_rd[155]),.returned_kind(rk[620+:4]),.returned_local(rid[4960+:32]),.returned_gen(rgen[4960+:32]),.read_data(rd[39680+:256]),.returned_legal(rlegal[155]));
 assign cr[155]=source_accept[155]&&legal[155];
df_fifo #(.WIDTH(363),.DEPTH(4)) q155(.clk,.reset,.iv(cv[155]&&legal[155]),.ir(source_accept[155]),.idata({write_[155],cl[4960+:32],ai[155],local_write_data[27392+:256]}),.ov(qv[155]),.ordy(qr[155]),.odata({qw[107],ql[155],qi[155],qd[107]}));
lf_adapter #(.SOURCE(156)) a156(.kind(ck[624+:4]),.local_id(cid[4992+:32]),.generation(cgen[4992+:32]),.line(cl[4992+:32]),.legal(legal[156]),.write(write_[156]),.packed_id(ai[156]),.returned_id(ri[156]),.returned_data(raw_rd[156]),.returned_kind(rk[624+:4]),.returned_local(rid[4992+:32]),.returned_gen(rgen[4992+:32]),.read_data(rd[39936+:256]),.returned_legal(rlegal[156]));
 assign cr[156]=source_accept[156]&&legal[156];
df_fifo #(.WIDTH(363),.DEPTH(4)) q156(.clk,.reset,.iv(cv[156]&&legal[156]),.ir(source_accept[156]),.idata({write_[156],cl[4992+:32],ai[156],local_write_data[27648+:256]}),.ov(qv[156]),.ordy(qr[156]),.odata({qw[108],ql[156],qi[156],qd[108]}));
lf_adapter #(.SOURCE(157)) a157(.kind(ck[628+:4]),.local_id(cid[5024+:32]),.generation(cgen[5024+:32]),.line(cl[5024+:32]),.legal(legal[157]),.write(write_[157]),.packed_id(ai[157]),.returned_id(ri[157]),.returned_data(raw_rd[157]),.returned_kind(rk[628+:4]),.returned_local(rid[5024+:32]),.returned_gen(rgen[5024+:32]),.read_data(rd[40192+:256]),.returned_legal(rlegal[157]));
 assign cr[157]=source_accept[157]&&legal[157];
df_fifo #(.WIDTH(363),.DEPTH(4)) q157(.clk,.reset,.iv(cv[157]&&legal[157]),.ir(source_accept[157]),.idata({write_[157],cl[5024+:32],ai[157],local_write_data[27904+:256]}),.ov(qv[157]),.ordy(qr[157]),.odata({qw[109],ql[157],qi[157],qd[109]}));
lf_adapter #(.SOURCE(158)) a158(.kind(ck[632+:4]),.local_id(cid[5056+:32]),.generation(cgen[5056+:32]),.line(cl[5056+:32]),.legal(legal[158]),.write(write_[158]),.packed_id(ai[158]),.returned_id(ri[158]),.returned_data(raw_rd[158]),.returned_kind(rk[632+:4]),.returned_local(rid[5056+:32]),.returned_gen(rgen[5056+:32]),.read_data(rd[40448+:256]),.returned_legal(rlegal[158]));
 assign cr[158]=source_accept[158]&&legal[158];
df_fifo #(.WIDTH(363),.DEPTH(4)) q158(.clk,.reset,.iv(cv[158]&&legal[158]),.ir(source_accept[158]),.idata({write_[158],cl[5056+:32],ai[158],local_write_data[28160+:256]}),.ov(qv[158]),.ordy(qr[158]),.odata({qw[110],ql[158],qi[158],qd[110]}));
lf_adapter #(.SOURCE(159)) a159(.kind(ck[636+:4]),.local_id(cid[5088+:32]),.generation(cgen[5088+:32]),.line(cl[5088+:32]),.legal(legal[159]),.write(write_[159]),.packed_id(ai[159]),.returned_id(ri[159]),.returned_data(raw_rd[159]),.returned_kind(rk[636+:4]),.returned_local(rid[5088+:32]),.returned_gen(rgen[5088+:32]),.read_data(rd[40704+:256]),.returned_legal(rlegal[159]));
 assign cr[159]=source_accept[159]&&legal[159];
df_fifo #(.WIDTH(363),.DEPTH(4)) q159(.clk,.reset,.iv(cv[159]&&legal[159]),.ir(source_accept[159]),.idata({write_[159],cl[5088+:32],ai[159],local_write_data[28416+:256]}),.ov(qv[159]),.ordy(qr[159]),.odata({qw[111],ql[159],qi[159],qd[111]}));
lf_adapter #(.SOURCE(160)) a160(.kind(ck[640+:4]),.local_id(cid[5120+:32]),.generation(cgen[5120+:32]),.line(cl[5120+:32]),.legal(legal[160]),.write(write_[160]),.packed_id(ai[160]),.returned_id(ri[160]),.returned_data(raw_rd[160]),.returned_kind(rk[640+:4]),.returned_local(rid[5120+:32]),.returned_gen(rgen[5120+:32]),.read_data(rd[40960+:256]),.returned_legal(rlegal[160]));
 assign cr[160]=source_accept[160]&&legal[160];
df_fifo #(.WIDTH(363),.DEPTH(4)) q160(.clk,.reset,.iv(cv[160]&&legal[160]),.ir(source_accept[160]),.idata({write_[160],cl[5120+:32],ai[160],local_write_data[28672+:256]}),.ov(qv[160]),.ordy(qr[160]),.odata({qw[112],ql[160],qi[160],qd[112]}));
lf_adapter #(.SOURCE(161)) a161(.kind(ck[644+:4]),.local_id(cid[5152+:32]),.generation(cgen[5152+:32]),.line(cl[5152+:32]),.legal(legal[161]),.write(write_[161]),.packed_id(ai[161]),.returned_id(ri[161]),.returned_data(raw_rd[161]),.returned_kind(rk[644+:4]),.returned_local(rid[5152+:32]),.returned_gen(rgen[5152+:32]),.read_data(rd[41216+:256]),.returned_legal(rlegal[161]));
 assign cr[161]=source_accept[161]&&legal[161];
df_fifo #(.WIDTH(363),.DEPTH(4)) q161(.clk,.reset,.iv(cv[161]&&legal[161]),.ir(source_accept[161]),.idata({write_[161],cl[5152+:32],ai[161],local_write_data[28928+:256]}),.ov(qv[161]),.ordy(qr[161]),.odata({qw[113],ql[161],qi[161],qd[113]}));
lf_adapter #(.SOURCE(162)) a162(.kind(ck[648+:4]),.local_id(cid[5184+:32]),.generation(cgen[5184+:32]),.line(cl[5184+:32]),.legal(legal[162]),.write(write_[162]),.packed_id(ai[162]),.returned_id(ri[162]),.returned_data(raw_rd[162]),.returned_kind(rk[648+:4]),.returned_local(rid[5184+:32]),.returned_gen(rgen[5184+:32]),.read_data(rd[41472+:256]),.returned_legal(rlegal[162]));
 assign cr[162]=source_accept[162]&&legal[162];
df_fifo #(.WIDTH(363),.DEPTH(4)) q162(.clk,.reset,.iv(cv[162]&&legal[162]),.ir(source_accept[162]),.idata({write_[162],cl[5184+:32],ai[162],local_write_data[29184+:256]}),.ov(qv[162]),.ordy(qr[162]),.odata({qw[114],ql[162],qi[162],qd[114]}));
lf_adapter #(.SOURCE(163)) a163(.kind(ck[652+:4]),.local_id(cid[5216+:32]),.generation(cgen[5216+:32]),.line(cl[5216+:32]),.legal(legal[163]),.write(write_[163]),.packed_id(ai[163]),.returned_id(ri[163]),.returned_data(raw_rd[163]),.returned_kind(rk[652+:4]),.returned_local(rid[5216+:32]),.returned_gen(rgen[5216+:32]),.read_data(rd[41728+:256]),.returned_legal(rlegal[163]));
 assign cr[163]=source_accept[163]&&legal[163];
df_fifo #(.WIDTH(363),.DEPTH(4)) q163(.clk,.reset,.iv(cv[163]&&legal[163]),.ir(source_accept[163]),.idata({write_[163],cl[5216+:32],ai[163],local_write_data[29440+:256]}),.ov(qv[163]),.ordy(qr[163]),.odata({qw[115],ql[163],qi[163],qd[115]}));
lf_adapter #(.SOURCE(164)) a164(.kind(ck[656+:4]),.local_id(cid[5248+:32]),.generation(cgen[5248+:32]),.line(cl[5248+:32]),.legal(legal[164]),.write(write_[164]),.packed_id(ai[164]),.returned_id(ri[164]),.returned_data(raw_rd[164]),.returned_kind(rk[656+:4]),.returned_local(rid[5248+:32]),.returned_gen(rgen[5248+:32]),.read_data(rd[41984+:256]),.returned_legal(rlegal[164]));
 assign cr[164]=source_accept[164]&&legal[164];
df_fifo #(.WIDTH(363),.DEPTH(4)) q164(.clk,.reset,.iv(cv[164]&&legal[164]),.ir(source_accept[164]),.idata({write_[164],cl[5248+:32],ai[164],local_write_data[29696+:256]}),.ov(qv[164]),.ordy(qr[164]),.odata({qw[116],ql[164],qi[164],qd[116]}));
lf_adapter #(.SOURCE(165)) a165(.kind(ck[660+:4]),.local_id(cid[5280+:32]),.generation(cgen[5280+:32]),.line(cl[5280+:32]),.legal(legal[165]),.write(write_[165]),.packed_id(ai[165]),.returned_id(ri[165]),.returned_data(raw_rd[165]),.returned_kind(rk[660+:4]),.returned_local(rid[5280+:32]),.returned_gen(rgen[5280+:32]),.read_data(rd[42240+:256]),.returned_legal(rlegal[165]));
 assign cr[165]=source_accept[165]&&legal[165];
df_fifo #(.WIDTH(363),.DEPTH(4)) q165(.clk,.reset,.iv(cv[165]&&legal[165]),.ir(source_accept[165]),.idata({write_[165],cl[5280+:32],ai[165],local_write_data[29952+:256]}),.ov(qv[165]),.ordy(qr[165]),.odata({qw[117],ql[165],qi[165],qd[117]}));
lf_adapter #(.SOURCE(166)) a166(.kind(ck[664+:4]),.local_id(cid[5312+:32]),.generation(cgen[5312+:32]),.line(cl[5312+:32]),.legal(legal[166]),.write(write_[166]),.packed_id(ai[166]),.returned_id(ri[166]),.returned_data(raw_rd[166]),.returned_kind(rk[664+:4]),.returned_local(rid[5312+:32]),.returned_gen(rgen[5312+:32]),.read_data(rd[42496+:256]),.returned_legal(rlegal[166]));
 assign cr[166]=source_accept[166]&&legal[166];
df_fifo #(.WIDTH(363),.DEPTH(4)) q166(.clk,.reset,.iv(cv[166]&&legal[166]),.ir(source_accept[166]),.idata({write_[166],cl[5312+:32],ai[166],local_write_data[30208+:256]}),.ov(qv[166]),.ordy(qr[166]),.odata({qw[118],ql[166],qi[166],qd[118]}));
lf_adapter #(.SOURCE(167)) a167(.kind(ck[668+:4]),.local_id(cid[5344+:32]),.generation(cgen[5344+:32]),.line(cl[5344+:32]),.legal(legal[167]),.write(write_[167]),.packed_id(ai[167]),.returned_id(ri[167]),.returned_data(raw_rd[167]),.returned_kind(rk[668+:4]),.returned_local(rid[5344+:32]),.returned_gen(rgen[5344+:32]),.read_data(rd[42752+:256]),.returned_legal(rlegal[167]));
 assign cr[167]=source_accept[167]&&legal[167];
df_fifo #(.WIDTH(363),.DEPTH(4)) q167(.clk,.reset,.iv(cv[167]&&legal[167]),.ir(source_accept[167]),.idata({write_[167],cl[5344+:32],ai[167],local_write_data[30464+:256]}),.ov(qv[167]),.ordy(qr[167]),.odata({qw[119],ql[167],qi[167],qd[119]}));
lf_adapter #(.SOURCE(168)) a168(.kind(ck[672+:4]),.local_id(cid[5376+:32]),.generation(cgen[5376+:32]),.line(cl[5376+:32]),.legal(legal[168]),.write(write_[168]),.packed_id(ai[168]),.returned_id(ri[168]),.returned_data(raw_rd[168]),.returned_kind(rk[672+:4]),.returned_local(rid[5376+:32]),.returned_gen(rgen[5376+:32]),.read_data(rd[43008+:256]),.returned_legal(rlegal[168]));
 assign cr[168]=source_accept[168]&&legal[168];
df_fifo #(.WIDTH(363),.DEPTH(4)) q168(.clk,.reset,.iv(cv[168]&&legal[168]),.ir(source_accept[168]),.idata({write_[168],cl[5376+:32],ai[168],local_write_data[30720+:256]}),.ov(qv[168]),.ordy(qr[168]),.odata({qw[120],ql[168],qi[168],qd[120]}));
lf_adapter #(.SOURCE(169)) a169(.kind(ck[676+:4]),.local_id(cid[5408+:32]),.generation(cgen[5408+:32]),.line(cl[5408+:32]),.legal(legal[169]),.write(write_[169]),.packed_id(ai[169]),.returned_id(ri[169]),.returned_data(raw_rd[169]),.returned_kind(rk[676+:4]),.returned_local(rid[5408+:32]),.returned_gen(rgen[5408+:32]),.read_data(rd[43264+:256]),.returned_legal(rlegal[169]));
 assign cr[169]=source_accept[169]&&legal[169];
df_fifo #(.WIDTH(363),.DEPTH(4)) q169(.clk,.reset,.iv(cv[169]&&legal[169]),.ir(source_accept[169]),.idata({write_[169],cl[5408+:32],ai[169],local_write_data[30976+:256]}),.ov(qv[169]),.ordy(qr[169]),.odata({qw[121],ql[169],qi[169],qd[121]}));
lf_adapter #(.SOURCE(170)) a170(.kind(ck[680+:4]),.local_id(cid[5440+:32]),.generation(cgen[5440+:32]),.line(cl[5440+:32]),.legal(legal[170]),.write(write_[170]),.packed_id(ai[170]),.returned_id(ri[170]),.returned_data(raw_rd[170]),.returned_kind(rk[680+:4]),.returned_local(rid[5440+:32]),.returned_gen(rgen[5440+:32]),.read_data(rd[43520+:256]),.returned_legal(rlegal[170]));
 assign cr[170]=source_accept[170]&&legal[170];
df_fifo #(.WIDTH(363),.DEPTH(4)) q170(.clk,.reset,.iv(cv[170]&&legal[170]),.ir(source_accept[170]),.idata({write_[170],cl[5440+:32],ai[170],local_write_data[31232+:256]}),.ov(qv[170]),.ordy(qr[170]),.odata({qw[122],ql[170],qi[170],qd[122]}));
lf_adapter #(.SOURCE(171)) a171(.kind(ck[684+:4]),.local_id(cid[5472+:32]),.generation(cgen[5472+:32]),.line(cl[5472+:32]),.legal(legal[171]),.write(write_[171]),.packed_id(ai[171]),.returned_id(ri[171]),.returned_data(raw_rd[171]),.returned_kind(rk[684+:4]),.returned_local(rid[5472+:32]),.returned_gen(rgen[5472+:32]),.read_data(rd[43776+:256]),.returned_legal(rlegal[171]));
 assign cr[171]=source_accept[171]&&legal[171];
df_fifo #(.WIDTH(363),.DEPTH(4)) q171(.clk,.reset,.iv(cv[171]&&legal[171]),.ir(source_accept[171]),.idata({write_[171],cl[5472+:32],ai[171],local_write_data[31488+:256]}),.ov(qv[171]),.ordy(qr[171]),.odata({qw[123],ql[171],qi[171],qd[123]}));
lf_adapter #(.SOURCE(172)) a172(.kind(ck[688+:4]),.local_id(cid[5504+:32]),.generation(cgen[5504+:32]),.line(cl[5504+:32]),.legal(legal[172]),.write(write_[172]),.packed_id(ai[172]),.returned_id(ri[172]),.returned_data(raw_rd[172]),.returned_kind(rk[688+:4]),.returned_local(rid[5504+:32]),.returned_gen(rgen[5504+:32]),.read_data(rd[44032+:256]),.returned_legal(rlegal[172]));
 assign cr[172]=source_accept[172]&&legal[172];
df_fifo #(.WIDTH(363),.DEPTH(4)) q172(.clk,.reset,.iv(cv[172]&&legal[172]),.ir(source_accept[172]),.idata({write_[172],cl[5504+:32],ai[172],local_write_data[31744+:256]}),.ov(qv[172]),.ordy(qr[172]),.odata({qw[124],ql[172],qi[172],qd[124]}));
lf_adapter #(.SOURCE(173)) a173(.kind(ck[692+:4]),.local_id(cid[5536+:32]),.generation(cgen[5536+:32]),.line(cl[5536+:32]),.legal(legal[173]),.write(write_[173]),.packed_id(ai[173]),.returned_id(ri[173]),.returned_data(raw_rd[173]),.returned_kind(rk[692+:4]),.returned_local(rid[5536+:32]),.returned_gen(rgen[5536+:32]),.read_data(rd[44288+:256]),.returned_legal(rlegal[173]));
 assign cr[173]=source_accept[173]&&legal[173];
df_fifo #(.WIDTH(363),.DEPTH(4)) q173(.clk,.reset,.iv(cv[173]&&legal[173]),.ir(source_accept[173]),.idata({write_[173],cl[5536+:32],ai[173],local_write_data[32000+:256]}),.ov(qv[173]),.ordy(qr[173]),.odata({qw[125],ql[173],qi[173],qd[125]}));
lf_adapter #(.SOURCE(174)) a174(.kind(ck[696+:4]),.local_id(cid[5568+:32]),.generation(cgen[5568+:32]),.line(cl[5568+:32]),.legal(legal[174]),.write(write_[174]),.packed_id(ai[174]),.returned_id(ri[174]),.returned_data(raw_rd[174]),.returned_kind(rk[696+:4]),.returned_local(rid[5568+:32]),.returned_gen(rgen[5568+:32]),.read_data(rd[44544+:256]),.returned_legal(rlegal[174]));
 assign cr[174]=source_accept[174]&&legal[174];
df_fifo #(.WIDTH(363),.DEPTH(4)) q174(.clk,.reset,.iv(cv[174]&&legal[174]),.ir(source_accept[174]),.idata({write_[174],cl[5568+:32],ai[174],local_write_data[32256+:256]}),.ov(qv[174]),.ordy(qr[174]),.odata({qw[126],ql[174],qi[174],qd[126]}));
lf_adapter #(.SOURCE(175)) a175(.kind(ck[700+:4]),.local_id(cid[5600+:32]),.generation(cgen[5600+:32]),.line(cl[5600+:32]),.legal(legal[175]),.write(write_[175]),.packed_id(ai[175]),.returned_id(ri[175]),.returned_data(raw_rd[175]),.returned_kind(rk[700+:4]),.returned_local(rid[5600+:32]),.returned_gen(rgen[5600+:32]),.read_data(rd[44800+:256]),.returned_legal(rlegal[175]));
 assign cr[175]=source_accept[175]&&legal[175];
df_fifo #(.WIDTH(363),.DEPTH(4)) q175(.clk,.reset,.iv(cv[175]&&legal[175]),.ir(source_accept[175]),.idata({write_[175],cl[5600+:32],ai[175],local_write_data[32512+:256]}),.ov(qv[175]),.ordy(qr[175]),.odata({qw[127],ql[175],qi[175],qd[127]}));
lf_adapter #(.SOURCE(176)) a176(.kind(ck[704+:4]),.local_id(cid[5632+:32]),.generation(cgen[5632+:32]),.line(cl[5632+:32]),.legal(legal[176]),.write(write_[176]),.packed_id(ai[176]),.returned_id(ri[176]),.returned_data(raw_rd[176]),.returned_kind(rk[704+:4]),.returned_local(rid[5632+:32]),.returned_gen(rgen[5632+:32]),.read_data(rd[45056+:256]),.returned_legal(rlegal[176]));
 assign cr[176]=source_accept[176]&&legal[176];
df_fifo #(.WIDTH(363),.DEPTH(4)) q176(.clk,.reset,.iv(cv[176]&&legal[176]),.ir(source_accept[176]),.idata({write_[176],cl[5632+:32],ai[176],local_write_data[32768+:256]}),.ov(qv[176]),.ordy(qr[176]),.odata({qw[128],ql[176],qi[176],qd[128]}));
lf_adapter #(.SOURCE(177)) a177(.kind(ck[708+:4]),.local_id(cid[5664+:32]),.generation(cgen[5664+:32]),.line(cl[5664+:32]),.legal(legal[177]),.write(write_[177]),.packed_id(ai[177]),.returned_id(ri[177]),.returned_data(raw_rd[177]),.returned_kind(rk[708+:4]),.returned_local(rid[5664+:32]),.returned_gen(rgen[5664+:32]),.read_data(rd[45312+:256]),.returned_legal(rlegal[177]));
 assign cr[177]=source_accept[177]&&legal[177];
df_fifo #(.WIDTH(363),.DEPTH(4)) q177(.clk,.reset,.iv(cv[177]&&legal[177]),.ir(source_accept[177]),.idata({write_[177],cl[5664+:32],ai[177],local_write_data[33024+:256]}),.ov(qv[177]),.ordy(qr[177]),.odata({qw[129],ql[177],qi[177],qd[129]}));
lf_adapter #(.SOURCE(178)) a178(.kind(ck[712+:4]),.local_id(cid[5696+:32]),.generation(cgen[5696+:32]),.line(cl[5696+:32]),.legal(legal[178]),.write(write_[178]),.packed_id(ai[178]),.returned_id(ri[178]),.returned_data(raw_rd[178]),.returned_kind(rk[712+:4]),.returned_local(rid[5696+:32]),.returned_gen(rgen[5696+:32]),.read_data(rd[45568+:256]),.returned_legal(rlegal[178]));
 assign cr[178]=source_accept[178]&&legal[178];
df_fifo #(.WIDTH(363),.DEPTH(4)) q178(.clk,.reset,.iv(cv[178]&&legal[178]),.ir(source_accept[178]),.idata({write_[178],cl[5696+:32],ai[178],local_write_data[33280+:256]}),.ov(qv[178]),.ordy(qr[178]),.odata({qw[130],ql[178],qi[178],qd[130]}));
lf_adapter #(.SOURCE(179)) a179(.kind(ck[716+:4]),.local_id(cid[5728+:32]),.generation(cgen[5728+:32]),.line(cl[5728+:32]),.legal(legal[179]),.write(write_[179]),.packed_id(ai[179]),.returned_id(ri[179]),.returned_data(raw_rd[179]),.returned_kind(rk[716+:4]),.returned_local(rid[5728+:32]),.returned_gen(rgen[5728+:32]),.read_data(rd[45824+:256]),.returned_legal(rlegal[179]));
 assign cr[179]=source_accept[179]&&legal[179];
df_fifo #(.WIDTH(363),.DEPTH(4)) q179(.clk,.reset,.iv(cv[179]&&legal[179]),.ir(source_accept[179]),.idata({write_[179],cl[5728+:32],ai[179],local_write_data[33536+:256]}),.ov(qv[179]),.ordy(qr[179]),.odata({qw[131],ql[179],qi[179],qd[131]}));
lf_adapter #(.SOURCE(180)) a180(.kind(ck[720+:4]),.local_id(cid[5760+:32]),.generation(cgen[5760+:32]),.line(cl[5760+:32]),.legal(legal[180]),.write(write_[180]),.packed_id(ai[180]),.returned_id(ri[180]),.returned_data(raw_rd[180]),.returned_kind(rk[720+:4]),.returned_local(rid[5760+:32]),.returned_gen(rgen[5760+:32]),.read_data(rd[46080+:256]),.returned_legal(rlegal[180]));
 assign cr[180]=source_accept[180]&&legal[180];
df_fifo #(.WIDTH(363),.DEPTH(4)) q180(.clk,.reset,.iv(cv[180]&&legal[180]),.ir(source_accept[180]),.idata({write_[180],cl[5760+:32],ai[180],local_write_data[33792+:256]}),.ov(qv[180]),.ordy(qr[180]),.odata({qw[132],ql[180],qi[180],qd[132]}));
lf_adapter #(.SOURCE(181)) a181(.kind(ck[724+:4]),.local_id(cid[5792+:32]),.generation(cgen[5792+:32]),.line(cl[5792+:32]),.legal(legal[181]),.write(write_[181]),.packed_id(ai[181]),.returned_id(ri[181]),.returned_data(raw_rd[181]),.returned_kind(rk[724+:4]),.returned_local(rid[5792+:32]),.returned_gen(rgen[5792+:32]),.read_data(rd[46336+:256]),.returned_legal(rlegal[181]));
 assign cr[181]=source_accept[181]&&legal[181];
df_fifo #(.WIDTH(363),.DEPTH(4)) q181(.clk,.reset,.iv(cv[181]&&legal[181]),.ir(source_accept[181]),.idata({write_[181],cl[5792+:32],ai[181],local_write_data[34048+:256]}),.ov(qv[181]),.ordy(qr[181]),.odata({qw[133],ql[181],qi[181],qd[133]}));
lf_adapter #(.SOURCE(182)) a182(.kind(ck[728+:4]),.local_id(cid[5824+:32]),.generation(cgen[5824+:32]),.line(cl[5824+:32]),.legal(legal[182]),.write(write_[182]),.packed_id(ai[182]),.returned_id(ri[182]),.returned_data(raw_rd[182]),.returned_kind(rk[728+:4]),.returned_local(rid[5824+:32]),.returned_gen(rgen[5824+:32]),.read_data(rd[46592+:256]),.returned_legal(rlegal[182]));
 assign cr[182]=source_accept[182]&&legal[182];
df_fifo #(.WIDTH(363),.DEPTH(4)) q182(.clk,.reset,.iv(cv[182]&&legal[182]),.ir(source_accept[182]),.idata({write_[182],cl[5824+:32],ai[182],local_write_data[34304+:256]}),.ov(qv[182]),.ordy(qr[182]),.odata({qw[134],ql[182],qi[182],qd[134]}));
lf_adapter #(.SOURCE(183)) a183(.kind(ck[732+:4]),.local_id(cid[5856+:32]),.generation(cgen[5856+:32]),.line(cl[5856+:32]),.legal(legal[183]),.write(write_[183]),.packed_id(ai[183]),.returned_id(ri[183]),.returned_data(raw_rd[183]),.returned_kind(rk[732+:4]),.returned_local(rid[5856+:32]),.returned_gen(rgen[5856+:32]),.read_data(rd[46848+:256]),.returned_legal(rlegal[183]));
 assign cr[183]=source_accept[183]&&legal[183];
df_fifo #(.WIDTH(363),.DEPTH(4)) q183(.clk,.reset,.iv(cv[183]&&legal[183]),.ir(source_accept[183]),.idata({write_[183],cl[5856+:32],ai[183],local_write_data[34560+:256]}),.ov(qv[183]),.ordy(qr[183]),.odata({qw[135],ql[183],qi[183],qd[135]}));
lf_adapter #(.SOURCE(184)) a184(.kind(ck[736+:4]),.local_id(cid[5888+:32]),.generation(cgen[5888+:32]),.line(cl[5888+:32]),.legal(legal[184]),.write(write_[184]),.packed_id(ai[184]),.returned_id(ri[184]),.returned_data(raw_rd[184]),.returned_kind(rk[736+:4]),.returned_local(rid[5888+:32]),.returned_gen(rgen[5888+:32]),.read_data(rd[47104+:256]),.returned_legal(rlegal[184]));
 assign cr[184]=source_accept[184]&&legal[184];
df_fifo #(.WIDTH(363),.DEPTH(4)) q184(.clk,.reset,.iv(cv[184]&&legal[184]),.ir(source_accept[184]),.idata({write_[184],cl[5888+:32],ai[184],local_write_data[34816+:256]}),.ov(qv[184]),.ordy(qr[184]),.odata({qw[136],ql[184],qi[184],qd[136]}));
lf_adapter #(.SOURCE(185)) a185(.kind(ck[740+:4]),.local_id(cid[5920+:32]),.generation(cgen[5920+:32]),.line(cl[5920+:32]),.legal(legal[185]),.write(write_[185]),.packed_id(ai[185]),.returned_id(ri[185]),.returned_data(raw_rd[185]),.returned_kind(rk[740+:4]),.returned_local(rid[5920+:32]),.returned_gen(rgen[5920+:32]),.read_data(rd[47360+:256]),.returned_legal(rlegal[185]));
 assign cr[185]=source_accept[185]&&legal[185];
df_fifo #(.WIDTH(363),.DEPTH(4)) q185(.clk,.reset,.iv(cv[185]&&legal[185]),.ir(source_accept[185]),.idata({write_[185],cl[5920+:32],ai[185],local_write_data[35072+:256]}),.ov(qv[185]),.ordy(qr[185]),.odata({qw[137],ql[185],qi[185],qd[137]}));
lf_adapter #(.SOURCE(186)) a186(.kind(ck[744+:4]),.local_id(cid[5952+:32]),.generation(cgen[5952+:32]),.line(cl[5952+:32]),.legal(legal[186]),.write(write_[186]),.packed_id(ai[186]),.returned_id(ri[186]),.returned_data(raw_rd[186]),.returned_kind(rk[744+:4]),.returned_local(rid[5952+:32]),.returned_gen(rgen[5952+:32]),.read_data(rd[47616+:256]),.returned_legal(rlegal[186]));
 assign cr[186]=source_accept[186]&&legal[186];
df_fifo #(.WIDTH(363),.DEPTH(4)) q186(.clk,.reset,.iv(cv[186]&&legal[186]),.ir(source_accept[186]),.idata({write_[186],cl[5952+:32],ai[186],local_write_data[35328+:256]}),.ov(qv[186]),.ordy(qr[186]),.odata({qw[138],ql[186],qi[186],qd[138]}));
lf_adapter #(.SOURCE(187)) a187(.kind(ck[748+:4]),.local_id(cid[5984+:32]),.generation(cgen[5984+:32]),.line(cl[5984+:32]),.legal(legal[187]),.write(write_[187]),.packed_id(ai[187]),.returned_id(ri[187]),.returned_data(raw_rd[187]),.returned_kind(rk[748+:4]),.returned_local(rid[5984+:32]),.returned_gen(rgen[5984+:32]),.read_data(rd[47872+:256]),.returned_legal(rlegal[187]));
 assign cr[187]=source_accept[187]&&legal[187];
df_fifo #(.WIDTH(363),.DEPTH(4)) q187(.clk,.reset,.iv(cv[187]&&legal[187]),.ir(source_accept[187]),.idata({write_[187],cl[5984+:32],ai[187],local_write_data[35584+:256]}),.ov(qv[187]),.ordy(qr[187]),.odata({qw[139],ql[187],qi[187],qd[139]}));
lf_adapter #(.SOURCE(188)) a188(.kind(ck[752+:4]),.local_id(cid[6016+:32]),.generation(cgen[6016+:32]),.line(cl[6016+:32]),.legal(legal[188]),.write(write_[188]),.packed_id(ai[188]),.returned_id(ri[188]),.returned_data(raw_rd[188]),.returned_kind(rk[752+:4]),.returned_local(rid[6016+:32]),.returned_gen(rgen[6016+:32]),.read_data(rd[48128+:256]),.returned_legal(rlegal[188]));
 assign cr[188]=source_accept[188]&&legal[188];
df_fifo #(.WIDTH(363),.DEPTH(4)) q188(.clk,.reset,.iv(cv[188]&&legal[188]),.ir(source_accept[188]),.idata({write_[188],cl[6016+:32],ai[188],local_write_data[35840+:256]}),.ov(qv[188]),.ordy(qr[188]),.odata({qw[140],ql[188],qi[188],qd[140]}));
lf_adapter #(.SOURCE(189)) a189(.kind(ck[756+:4]),.local_id(cid[6048+:32]),.generation(cgen[6048+:32]),.line(cl[6048+:32]),.legal(legal[189]),.write(write_[189]),.packed_id(ai[189]),.returned_id(ri[189]),.returned_data(raw_rd[189]),.returned_kind(rk[756+:4]),.returned_local(rid[6048+:32]),.returned_gen(rgen[6048+:32]),.read_data(rd[48384+:256]),.returned_legal(rlegal[189]));
 assign cr[189]=source_accept[189]&&legal[189];
df_fifo #(.WIDTH(363),.DEPTH(4)) q189(.clk,.reset,.iv(cv[189]&&legal[189]),.ir(source_accept[189]),.idata({write_[189],cl[6048+:32],ai[189],local_write_data[36096+:256]}),.ov(qv[189]),.ordy(qr[189]),.odata({qw[141],ql[189],qi[189],qd[141]}));
lf_adapter #(.SOURCE(190)) a190(.kind(ck[760+:4]),.local_id(cid[6080+:32]),.generation(cgen[6080+:32]),.line(cl[6080+:32]),.legal(legal[190]),.write(write_[190]),.packed_id(ai[190]),.returned_id(ri[190]),.returned_data(raw_rd[190]),.returned_kind(rk[760+:4]),.returned_local(rid[6080+:32]),.returned_gen(rgen[6080+:32]),.read_data(rd[48640+:256]),.returned_legal(rlegal[190]));
 assign cr[190]=source_accept[190]&&legal[190];
df_fifo #(.WIDTH(363),.DEPTH(4)) q190(.clk,.reset,.iv(cv[190]&&legal[190]),.ir(source_accept[190]),.idata({write_[190],cl[6080+:32],ai[190],local_write_data[36352+:256]}),.ov(qv[190]),.ordy(qr[190]),.odata({qw[142],ql[190],qi[190],qd[142]}));
lf_adapter #(.SOURCE(191)) a191(.kind(ck[764+:4]),.local_id(cid[6112+:32]),.generation(cgen[6112+:32]),.line(cl[6112+:32]),.legal(legal[191]),.write(write_[191]),.packed_id(ai[191]),.returned_id(ri[191]),.returned_data(raw_rd[191]),.returned_kind(rk[764+:4]),.returned_local(rid[6112+:32]),.returned_gen(rgen[6112+:32]),.read_data(rd[48896+:256]),.returned_legal(rlegal[191]));
 assign cr[191]=source_accept[191]&&legal[191];
df_fifo #(.WIDTH(363),.DEPTH(4)) q191(.clk,.reset,.iv(cv[191]&&legal[191]),.ir(source_accept[191]),.idata({write_[191],cl[6112+:32],ai[191],local_write_data[36608+:256]}),.ov(qv[191]),.ordy(qr[191]),.odata({qw[143],ql[191],qi[191],qd[143]}));
lf_adapter #(.SOURCE(192)) a192(.kind(ck[768+:4]),.local_id(cid[6144+:32]),.generation(cgen[6144+:32]),.line(cl[6144+:32]),.legal(legal[192]),.write(write_[192]),.packed_id(ai[192]),.returned_id(ri[192]),.returned_data(raw_rd[192]),.returned_kind(rk[768+:4]),.returned_local(rid[6144+:32]),.returned_gen(rgen[6144+:32]),.read_data(rd[49152+:256]),.returned_legal(rlegal[192]));
 assign cr[192]=source_accept[192]&&legal[192];
df_fifo #(.WIDTH(363),.DEPTH(4)) q192(.clk,.reset,.iv(cv[192]&&legal[192]),.ir(source_accept[192]),.idata({write_[192],cl[6144+:32],ai[192],local_write_data[36864+:256]}),.ov(qv[192]),.ordy(qr[192]),.odata({qw[144],ql[192],qi[192],qd[144]}));
lf_adapter #(.SOURCE(193)) a193(.kind(ck[772+:4]),.local_id(cid[6176+:32]),.generation(cgen[6176+:32]),.line(cl[6176+:32]),.legal(legal[193]),.write(write_[193]),.packed_id(ai[193]),.returned_id(ri[193]),.returned_data(raw_rd[193]),.returned_kind(rk[772+:4]),.returned_local(rid[6176+:32]),.returned_gen(rgen[6176+:32]),.read_data(rd[49408+:256]),.returned_legal(rlegal[193]));
 assign cr[193]=source_accept[193]&&legal[193];
df_fifo #(.WIDTH(363),.DEPTH(4)) q193(.clk,.reset,.iv(cv[193]&&legal[193]),.ir(source_accept[193]),.idata({write_[193],cl[6176+:32],ai[193],local_write_data[37120+:256]}),.ov(qv[193]),.ordy(qr[193]),.odata({qw[145],ql[193],qi[193],qd[145]}));
lf_adapter #(.SOURCE(194)) a194(.kind(ck[776+:4]),.local_id(cid[6208+:32]),.generation(cgen[6208+:32]),.line(cl[6208+:32]),.legal(legal[194]),.write(write_[194]),.packed_id(ai[194]),.returned_id(ri[194]),.returned_data(raw_rd[194]),.returned_kind(rk[776+:4]),.returned_local(rid[6208+:32]),.returned_gen(rgen[6208+:32]),.read_data(rd[49664+:256]),.returned_legal(rlegal[194]));
 assign cr[194]=source_accept[194]&&legal[194];
df_fifo #(.WIDTH(363),.DEPTH(4)) q194(.clk,.reset,.iv(cv[194]&&legal[194]),.ir(source_accept[194]),.idata({write_[194],cl[6208+:32],ai[194],local_write_data[37376+:256]}),.ov(qv[194]),.ordy(qr[194]),.odata({qw[146],ql[194],qi[194],qd[146]}));
lf_adapter #(.SOURCE(195)) a195(.kind(ck[780+:4]),.local_id(cid[6240+:32]),.generation(cgen[6240+:32]),.line(cl[6240+:32]),.legal(legal[195]),.write(write_[195]),.packed_id(ai[195]),.returned_id(ri[195]),.returned_data(raw_rd[195]),.returned_kind(rk[780+:4]),.returned_local(rid[6240+:32]),.returned_gen(rgen[6240+:32]),.read_data(rd[49920+:256]),.returned_legal(rlegal[195]));
 assign cr[195]=source_accept[195]&&legal[195];
df_fifo #(.WIDTH(363),.DEPTH(4)) q195(.clk,.reset,.iv(cv[195]&&legal[195]),.ir(source_accept[195]),.idata({write_[195],cl[6240+:32],ai[195],local_write_data[37632+:256]}),.ov(qv[195]),.ordy(qr[195]),.odata({qw[147],ql[195],qi[195],qd[147]}));
lf_adapter #(.SOURCE(196)) a196(.kind(ck[784+:4]),.local_id(cid[6272+:32]),.generation(cgen[6272+:32]),.line(cl[6272+:32]),.legal(legal[196]),.write(write_[196]),.packed_id(ai[196]),.returned_id(ri[196]),.returned_data(raw_rd[196]),.returned_kind(rk[784+:4]),.returned_local(rid[6272+:32]),.returned_gen(rgen[6272+:32]),.read_data(rd[50176+:256]),.returned_legal(rlegal[196]));
 assign cr[196]=source_accept[196]&&legal[196];
df_fifo #(.WIDTH(363),.DEPTH(4)) q196(.clk,.reset,.iv(cv[196]&&legal[196]),.ir(source_accept[196]),.idata({write_[196],cl[6272+:32],ai[196],local_write_data[37888+:256]}),.ov(qv[196]),.ordy(qr[196]),.odata({qw[148],ql[196],qi[196],qd[148]}));
lf_adapter #(.SOURCE(197)) a197(.kind(ck[788+:4]),.local_id(cid[6304+:32]),.generation(cgen[6304+:32]),.line(cl[6304+:32]),.legal(legal[197]),.write(write_[197]),.packed_id(ai[197]),.returned_id(ri[197]),.returned_data(raw_rd[197]),.returned_kind(rk[788+:4]),.returned_local(rid[6304+:32]),.returned_gen(rgen[6304+:32]),.read_data(rd[50432+:256]),.returned_legal(rlegal[197]));
 assign cr[197]=source_accept[197]&&legal[197];
df_fifo #(.WIDTH(363),.DEPTH(4)) q197(.clk,.reset,.iv(cv[197]&&legal[197]),.ir(source_accept[197]),.idata({write_[197],cl[6304+:32],ai[197],local_write_data[38144+:256]}),.ov(qv[197]),.ordy(qr[197]),.odata({qw[149],ql[197],qi[197],qd[149]}));
lf_adapter #(.SOURCE(198)) a198(.kind(ck[792+:4]),.local_id(cid[6336+:32]),.generation(cgen[6336+:32]),.line(cl[6336+:32]),.legal(legal[198]),.write(write_[198]),.packed_id(ai[198]),.returned_id(ri[198]),.returned_data(raw_rd[198]),.returned_kind(rk[792+:4]),.returned_local(rid[6336+:32]),.returned_gen(rgen[6336+:32]),.read_data(rd[50688+:256]),.returned_legal(rlegal[198]));
 assign cr[198]=source_accept[198]&&legal[198];
df_fifo #(.WIDTH(363),.DEPTH(4)) q198(.clk,.reset,.iv(cv[198]&&legal[198]),.ir(source_accept[198]),.idata({write_[198],cl[6336+:32],ai[198],local_write_data[38400+:256]}),.ov(qv[198]),.ordy(qr[198]),.odata({qw[150],ql[198],qi[198],qd[150]}));
lf_adapter #(.SOURCE(199)) a199(.kind(ck[796+:4]),.local_id(cid[6368+:32]),.generation(cgen[6368+:32]),.line(cl[6368+:32]),.legal(legal[199]),.write(write_[199]),.packed_id(ai[199]),.returned_id(ri[199]),.returned_data(raw_rd[199]),.returned_kind(rk[796+:4]),.returned_local(rid[6368+:32]),.returned_gen(rgen[6368+:32]),.read_data(rd[50944+:256]),.returned_legal(rlegal[199]));
 assign cr[199]=source_accept[199]&&legal[199];
df_fifo #(.WIDTH(363),.DEPTH(4)) q199(.clk,.reset,.iv(cv[199]&&legal[199]),.ir(source_accept[199]),.idata({write_[199],cl[6368+:32],ai[199],local_write_data[38656+:256]}),.ov(qv[199]),.ordy(qr[199]),.odata({qw[151],ql[199],qi[199],qd[151]}));
lf_adapter #(.SOURCE(200)) a200(.kind(ck[800+:4]),.local_id(cid[6400+:32]),.generation(cgen[6400+:32]),.line(cl[6400+:32]),.legal(legal[200]),.write(write_[200]),.packed_id(ai[200]),.returned_id(ri[200]),.returned_data(raw_rd[200]),.returned_kind(rk[800+:4]),.returned_local(rid[6400+:32]),.returned_gen(rgen[6400+:32]),.read_data(rd[51200+:256]),.returned_legal(rlegal[200]));
 assign cr[200]=source_accept[200]&&legal[200];
df_fifo #(.WIDTH(363),.DEPTH(4)) q200(.clk,.reset,.iv(cv[200]&&legal[200]),.ir(source_accept[200]),.idata({write_[200],cl[6400+:32],ai[200],local_write_data[38912+:256]}),.ov(qv[200]),.ordy(qr[200]),.odata({qw[152],ql[200],qi[200],qd[152]}));
lf_adapter #(.SOURCE(201)) a201(.kind(ck[804+:4]),.local_id(cid[6432+:32]),.generation(cgen[6432+:32]),.line(cl[6432+:32]),.legal(legal[201]),.write(write_[201]),.packed_id(ai[201]),.returned_id(ri[201]),.returned_data(raw_rd[201]),.returned_kind(rk[804+:4]),.returned_local(rid[6432+:32]),.returned_gen(rgen[6432+:32]),.read_data(rd[51456+:256]),.returned_legal(rlegal[201]));
 assign cr[201]=source_accept[201]&&legal[201];
df_fifo #(.WIDTH(363),.DEPTH(4)) q201(.clk,.reset,.iv(cv[201]&&legal[201]),.ir(source_accept[201]),.idata({write_[201],cl[6432+:32],ai[201],local_write_data[39168+:256]}),.ov(qv[201]),.ordy(qr[201]),.odata({qw[153],ql[201],qi[201],qd[153]}));
lf_adapter #(.SOURCE(202)) a202(.kind(ck[808+:4]),.local_id(cid[6464+:32]),.generation(cgen[6464+:32]),.line(cl[6464+:32]),.legal(legal[202]),.write(write_[202]),.packed_id(ai[202]),.returned_id(ri[202]),.returned_data(raw_rd[202]),.returned_kind(rk[808+:4]),.returned_local(rid[6464+:32]),.returned_gen(rgen[6464+:32]),.read_data(rd[51712+:256]),.returned_legal(rlegal[202]));
 assign cr[202]=source_accept[202]&&legal[202];
df_fifo #(.WIDTH(363),.DEPTH(4)) q202(.clk,.reset,.iv(cv[202]&&legal[202]),.ir(source_accept[202]),.idata({write_[202],cl[6464+:32],ai[202],local_write_data[39424+:256]}),.ov(qv[202]),.ordy(qr[202]),.odata({qw[154],ql[202],qi[202],qd[154]}));
lf_adapter #(.SOURCE(203)) a203(.kind(ck[812+:4]),.local_id(cid[6496+:32]),.generation(cgen[6496+:32]),.line(cl[6496+:32]),.legal(legal[203]),.write(write_[203]),.packed_id(ai[203]),.returned_id(ri[203]),.returned_data(raw_rd[203]),.returned_kind(rk[812+:4]),.returned_local(rid[6496+:32]),.returned_gen(rgen[6496+:32]),.read_data(rd[51968+:256]),.returned_legal(rlegal[203]));
 assign cr[203]=source_accept[203]&&legal[203];
df_fifo #(.WIDTH(363),.DEPTH(4)) q203(.clk,.reset,.iv(cv[203]&&legal[203]),.ir(source_accept[203]),.idata({write_[203],cl[6496+:32],ai[203],local_write_data[39680+:256]}),.ov(qv[203]),.ordy(qr[203]),.odata({qw[155],ql[203],qi[203],qd[155]}));
lf_adapter #(.SOURCE(204)) a204(.kind(ck[816+:4]),.local_id(cid[6528+:32]),.generation(cgen[6528+:32]),.line(cl[6528+:32]),.legal(legal[204]),.write(write_[204]),.packed_id(ai[204]),.returned_id(ri[204]),.returned_data(raw_rd[204]),.returned_kind(rk[816+:4]),.returned_local(rid[6528+:32]),.returned_gen(rgen[6528+:32]),.read_data(rd[52224+:256]),.returned_legal(rlegal[204]));
 assign cr[204]=source_accept[204]&&legal[204];
df_fifo #(.WIDTH(363),.DEPTH(4)) q204(.clk,.reset,.iv(cv[204]&&legal[204]),.ir(source_accept[204]),.idata({write_[204],cl[6528+:32],ai[204],local_write_data[39936+:256]}),.ov(qv[204]),.ordy(qr[204]),.odata({qw[156],ql[204],qi[204],qd[156]}));
lf_adapter #(.SOURCE(205)) a205(.kind(ck[820+:4]),.local_id(cid[6560+:32]),.generation(cgen[6560+:32]),.line(cl[6560+:32]),.legal(legal[205]),.write(write_[205]),.packed_id(ai[205]),.returned_id(ri[205]),.returned_data(raw_rd[205]),.returned_kind(rk[820+:4]),.returned_local(rid[6560+:32]),.returned_gen(rgen[6560+:32]),.read_data(rd[52480+:256]),.returned_legal(rlegal[205]));
 assign cr[205]=source_accept[205]&&legal[205];
df_fifo #(.WIDTH(363),.DEPTH(4)) q205(.clk,.reset,.iv(cv[205]&&legal[205]),.ir(source_accept[205]),.idata({write_[205],cl[6560+:32],ai[205],local_write_data[40192+:256]}),.ov(qv[205]),.ordy(qr[205]),.odata({qw[157],ql[205],qi[205],qd[157]}));
lf_adapter #(.SOURCE(206)) a206(.kind(ck[824+:4]),.local_id(cid[6592+:32]),.generation(cgen[6592+:32]),.line(cl[6592+:32]),.legal(legal[206]),.write(write_[206]),.packed_id(ai[206]),.returned_id(ri[206]),.returned_data(raw_rd[206]),.returned_kind(rk[824+:4]),.returned_local(rid[6592+:32]),.returned_gen(rgen[6592+:32]),.read_data(rd[52736+:256]),.returned_legal(rlegal[206]));
 assign cr[206]=source_accept[206]&&legal[206];
df_fifo #(.WIDTH(363),.DEPTH(4)) q206(.clk,.reset,.iv(cv[206]&&legal[206]),.ir(source_accept[206]),.idata({write_[206],cl[6592+:32],ai[206],local_write_data[40448+:256]}),.ov(qv[206]),.ordy(qr[206]),.odata({qw[158],ql[206],qi[206],qd[158]}));
lf_adapter #(.SOURCE(207)) a207(.kind(ck[828+:4]),.local_id(cid[6624+:32]),.generation(cgen[6624+:32]),.line(cl[6624+:32]),.legal(legal[207]),.write(write_[207]),.packed_id(ai[207]),.returned_id(ri[207]),.returned_data(raw_rd[207]),.returned_kind(rk[828+:4]),.returned_local(rid[6624+:32]),.returned_gen(rgen[6624+:32]),.read_data(rd[52992+:256]),.returned_legal(rlegal[207]));
 assign cr[207]=source_accept[207]&&legal[207];
df_fifo #(.WIDTH(363),.DEPTH(4)) q207(.clk,.reset,.iv(cv[207]&&legal[207]),.ir(source_accept[207]),.idata({write_[207],cl[6624+:32],ai[207],local_write_data[40704+:256]}),.ov(qv[207]),.ordy(qr[207]),.odata({qw[159],ql[207],qi[207],qd[159]}));
assign gv[0]=fxv[0];assign fxr[0]=gr[0];assign gd[0]={1'b0,fxd[0*106+:106],256'b0};
begin:req1
 wire[1:0]eligible={qv[176],fxv[1]};wire[1:0]grant;wire any;wire accept=!gv[1]||gr[1];reg valid;reg[362:0]hold;
 lf_select #(.N(2)) select_(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 wire[105:0]selected_narrow=(fxd[1*106+:106]&{106{grant[0]}})|({ql[176],qi[176]}&{106{grant[1]}});
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={grant[1]&&qw[128],selected_narrow,qd[128]&{256{grant[1]}}};end
 assign gv[1]=valid;assign gd[1]=hold;assign fxr[1]=accept&&grant[0];end
begin:req2
wire [1:0] eligible,grant;wire any;wire accept=!gv[2]||gr[2]; reg [362:0] hold;reg valid;wire [105:0] narrow[2];wire [105:0] selected_narrow;
assign eligible[0]=qv[48];
assign narrow[0]={106{grant[0]}}&{ql[48],qi[48]};
assign eligible[1]=qv[49];
assign narrow[1]={106{grant[1]}}&{ql[49],qi[49]};
assign selected_narrow=narrow[0]|narrow[1];
lf_select #(.N(2)) sel(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={(grant[0]&&qw[0])|(grant[1]&&qw[1]),selected_narrow,({256{grant[0]}}&qd[0])|({256{grant[1]}}&qd[1])};end
 assign gv[2]=valid;assign gd[2]=hold;end
begin:req3
wire [1:0] eligible,grant;wire any;wire accept=!gv[3]||gr[3]; reg [362:0] hold;reg valid;wire [105:0] narrow[2];wire [105:0] selected_narrow;
assign eligible[0]=qv[112];
assign narrow[0]={106{grant[0]}}&{ql[112],qi[112]};
assign eligible[1]=qv[113];
assign narrow[1]={106{grant[1]}}&{ql[113],qi[113]};
assign selected_narrow=narrow[0]|narrow[1];
lf_select #(.N(2)) sel(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={(grant[0]&&qw[64])|(grant[1]&&qw[65]),selected_narrow,({256{grant[0]}}&qd[64])|({256{grant[1]}}&qd[65])};end
 assign gv[3]=valid;assign gd[3]=hold;end
assign gv[4]=fxv[2];assign fxr[2]=gr[4];assign gd[4]={1'b0,fxd[2*106+:106],256'b0};
begin:req5
 wire[1:0]eligible={qv[177],fxv[3]};wire[1:0]grant;wire any;wire accept=!gv[5]||gr[5];reg valid;reg[362:0]hold;
 lf_select #(.N(2)) select_(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 wire[105:0]selected_narrow=(fxd[3*106+:106]&{106{grant[0]}})|({ql[177],qi[177]}&{106{grant[1]}});
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={grant[1]&&qw[129],selected_narrow,qd[129]&{256{grant[1]}}};end
 assign gv[5]=valid;assign gd[5]=hold;assign fxr[3]=accept&&grant[0];end
begin:req6
wire [1:0] eligible,grant;wire any;wire accept=!gv[6]||gr[6]; reg [362:0] hold;reg valid;wire [105:0] narrow[2];wire [105:0] selected_narrow;
assign eligible[0]=qv[50];
assign narrow[0]={106{grant[0]}}&{ql[50],qi[50]};
assign eligible[1]=qv[51];
assign narrow[1]={106{grant[1]}}&{ql[51],qi[51]};
assign selected_narrow=narrow[0]|narrow[1];
lf_select #(.N(2)) sel(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={(grant[0]&&qw[2])|(grant[1]&&qw[3]),selected_narrow,({256{grant[0]}}&qd[2])|({256{grant[1]}}&qd[3])};end
 assign gv[6]=valid;assign gd[6]=hold;end
begin:req7
wire [1:0] eligible,grant;wire any;wire accept=!gv[7]||gr[7]; reg [362:0] hold;reg valid;wire [105:0] narrow[2];wire [105:0] selected_narrow;
assign eligible[0]=qv[114];
assign narrow[0]={106{grant[0]}}&{ql[114],qi[114]};
assign eligible[1]=qv[115];
assign narrow[1]={106{grant[1]}}&{ql[115],qi[115]};
assign selected_narrow=narrow[0]|narrow[1];
lf_select #(.N(2)) sel(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={(grant[0]&&qw[66])|(grant[1]&&qw[67]),selected_narrow,({256{grant[0]}}&qd[66])|({256{grant[1]}}&qd[67])};end
 assign gv[7]=valid;assign gd[7]=hold;end
assign gv[8]=fxv[4];assign fxr[4]=gr[8];assign gd[8]={1'b0,fxd[4*106+:106],256'b0};
begin:req9
 wire[1:0]eligible={qv[178],fxv[5]};wire[1:0]grant;wire any;wire accept=!gv[9]||gr[9];reg valid;reg[362:0]hold;
 lf_select #(.N(2)) select_(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 wire[105:0]selected_narrow=(fxd[5*106+:106]&{106{grant[0]}})|({ql[178],qi[178]}&{106{grant[1]}});
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={grant[1]&&qw[130],selected_narrow,qd[130]&{256{grant[1]}}};end
 assign gv[9]=valid;assign gd[9]=hold;assign fxr[5]=accept&&grant[0];end
begin:req10
wire [1:0] eligible,grant;wire any;wire accept=!gv[10]||gr[10]; reg [362:0] hold;reg valid;wire [105:0] narrow[2];wire [105:0] selected_narrow;
assign eligible[0]=qv[52];
assign narrow[0]={106{grant[0]}}&{ql[52],qi[52]};
assign eligible[1]=qv[53];
assign narrow[1]={106{grant[1]}}&{ql[53],qi[53]};
assign selected_narrow=narrow[0]|narrow[1];
lf_select #(.N(2)) sel(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={(grant[0]&&qw[4])|(grant[1]&&qw[5]),selected_narrow,({256{grant[0]}}&qd[4])|({256{grant[1]}}&qd[5])};end
 assign gv[10]=valid;assign gd[10]=hold;end
begin:req11
wire [1:0] eligible,grant;wire any;wire accept=!gv[11]||gr[11]; reg [362:0] hold;reg valid;wire [105:0] narrow[2];wire [105:0] selected_narrow;
assign eligible[0]=qv[116];
assign narrow[0]={106{grant[0]}}&{ql[116],qi[116]};
assign eligible[1]=qv[117];
assign narrow[1]={106{grant[1]}}&{ql[117],qi[117]};
assign selected_narrow=narrow[0]|narrow[1];
lf_select #(.N(2)) sel(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={(grant[0]&&qw[68])|(grant[1]&&qw[69]),selected_narrow,({256{grant[0]}}&qd[68])|({256{grant[1]}}&qd[69])};end
 assign gv[11]=valid;assign gd[11]=hold;end
assign gv[12]=fxv[6];assign fxr[6]=gr[12];assign gd[12]={1'b0,fxd[6*106+:106],256'b0};
begin:req13
 wire[1:0]eligible={qv[179],fxv[7]};wire[1:0]grant;wire any;wire accept=!gv[13]||gr[13];reg valid;reg[362:0]hold;
 lf_select #(.N(2)) select_(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 wire[105:0]selected_narrow=(fxd[7*106+:106]&{106{grant[0]}})|({ql[179],qi[179]}&{106{grant[1]}});
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={grant[1]&&qw[131],selected_narrow,qd[131]&{256{grant[1]}}};end
 assign gv[13]=valid;assign gd[13]=hold;assign fxr[7]=accept&&grant[0];end
begin:req14
wire [1:0] eligible,grant;wire any;wire accept=!gv[14]||gr[14]; reg [362:0] hold;reg valid;wire [105:0] narrow[2];wire [105:0] selected_narrow;
assign eligible[0]=qv[54];
assign narrow[0]={106{grant[0]}}&{ql[54],qi[54]};
assign eligible[1]=qv[55];
assign narrow[1]={106{grant[1]}}&{ql[55],qi[55]};
assign selected_narrow=narrow[0]|narrow[1];
lf_select #(.N(2)) sel(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={(grant[0]&&qw[6])|(grant[1]&&qw[7]),selected_narrow,({256{grant[0]}}&qd[6])|({256{grant[1]}}&qd[7])};end
 assign gv[14]=valid;assign gd[14]=hold;end
begin:req15
wire [1:0] eligible,grant;wire any;wire accept=!gv[15]||gr[15]; reg [362:0] hold;reg valid;wire [105:0] narrow[2];wire [105:0] selected_narrow;
assign eligible[0]=qv[118];
assign narrow[0]={106{grant[0]}}&{ql[118],qi[118]};
assign eligible[1]=qv[119];
assign narrow[1]={106{grant[1]}}&{ql[119],qi[119]};
assign selected_narrow=narrow[0]|narrow[1];
lf_select #(.N(2)) sel(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={(grant[0]&&qw[70])|(grant[1]&&qw[71]),selected_narrow,({256{grant[0]}}&qd[70])|({256{grant[1]}}&qd[71])};end
 assign gv[15]=valid;assign gd[15]=hold;end
assign gv[16]=fxv[8];assign fxr[8]=gr[16];assign gd[16]={1'b0,fxd[8*106+:106],256'b0};
begin:req17
 wire[1:0]eligible={qv[180],fxv[9]};wire[1:0]grant;wire any;wire accept=!gv[17]||gr[17];reg valid;reg[362:0]hold;
 lf_select #(.N(2)) select_(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 wire[105:0]selected_narrow=(fxd[9*106+:106]&{106{grant[0]}})|({ql[180],qi[180]}&{106{grant[1]}});
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={grant[1]&&qw[132],selected_narrow,qd[132]&{256{grant[1]}}};end
 assign gv[17]=valid;assign gd[17]=hold;assign fxr[9]=accept&&grant[0];end
begin:req18
wire [1:0] eligible,grant;wire any;wire accept=!gv[18]||gr[18]; reg [362:0] hold;reg valid;wire [105:0] narrow[2];wire [105:0] selected_narrow;
assign eligible[0]=qv[56];
assign narrow[0]={106{grant[0]}}&{ql[56],qi[56]};
assign eligible[1]=qv[57];
assign narrow[1]={106{grant[1]}}&{ql[57],qi[57]};
assign selected_narrow=narrow[0]|narrow[1];
lf_select #(.N(2)) sel(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={(grant[0]&&qw[8])|(grant[1]&&qw[9]),selected_narrow,({256{grant[0]}}&qd[8])|({256{grant[1]}}&qd[9])};end
 assign gv[18]=valid;assign gd[18]=hold;end
begin:req19
wire [1:0] eligible,grant;wire any;wire accept=!gv[19]||gr[19]; reg [362:0] hold;reg valid;wire [105:0] narrow[2];wire [105:0] selected_narrow;
assign eligible[0]=qv[120];
assign narrow[0]={106{grant[0]}}&{ql[120],qi[120]};
assign eligible[1]=qv[121];
assign narrow[1]={106{grant[1]}}&{ql[121],qi[121]};
assign selected_narrow=narrow[0]|narrow[1];
lf_select #(.N(2)) sel(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={(grant[0]&&qw[72])|(grant[1]&&qw[73]),selected_narrow,({256{grant[0]}}&qd[72])|({256{grant[1]}}&qd[73])};end
 assign gv[19]=valid;assign gd[19]=hold;end
assign gv[20]=fxv[10];assign fxr[10]=gr[20];assign gd[20]={1'b0,fxd[10*106+:106],256'b0};
begin:req21
 wire[1:0]eligible={qv[181],fxv[11]};wire[1:0]grant;wire any;wire accept=!gv[21]||gr[21];reg valid;reg[362:0]hold;
 lf_select #(.N(2)) select_(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 wire[105:0]selected_narrow=(fxd[11*106+:106]&{106{grant[0]}})|({ql[181],qi[181]}&{106{grant[1]}});
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={grant[1]&&qw[133],selected_narrow,qd[133]&{256{grant[1]}}};end
 assign gv[21]=valid;assign gd[21]=hold;assign fxr[11]=accept&&grant[0];end
begin:req22
wire [1:0] eligible,grant;wire any;wire accept=!gv[22]||gr[22]; reg [362:0] hold;reg valid;wire [105:0] narrow[2];wire [105:0] selected_narrow;
assign eligible[0]=qv[58];
assign narrow[0]={106{grant[0]}}&{ql[58],qi[58]};
assign eligible[1]=qv[59];
assign narrow[1]={106{grant[1]}}&{ql[59],qi[59]};
assign selected_narrow=narrow[0]|narrow[1];
lf_select #(.N(2)) sel(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={(grant[0]&&qw[10])|(grant[1]&&qw[11]),selected_narrow,({256{grant[0]}}&qd[10])|({256{grant[1]}}&qd[11])};end
 assign gv[22]=valid;assign gd[22]=hold;end
begin:req23
wire [1:0] eligible,grant;wire any;wire accept=!gv[23]||gr[23]; reg [362:0] hold;reg valid;wire [105:0] narrow[2];wire [105:0] selected_narrow;
assign eligible[0]=qv[122];
assign narrow[0]={106{grant[0]}}&{ql[122],qi[122]};
assign eligible[1]=qv[123];
assign narrow[1]={106{grant[1]}}&{ql[123],qi[123]};
assign selected_narrow=narrow[0]|narrow[1];
lf_select #(.N(2)) sel(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={(grant[0]&&qw[74])|(grant[1]&&qw[75]),selected_narrow,({256{grant[0]}}&qd[74])|({256{grant[1]}}&qd[75])};end
 assign gv[23]=valid;assign gd[23]=hold;end
assign gv[24]=fxv[12];assign fxr[12]=gr[24];assign gd[24]={1'b0,fxd[12*106+:106],256'b0};
begin:req25
 wire[1:0]eligible={qv[182],fxv[13]};wire[1:0]grant;wire any;wire accept=!gv[25]||gr[25];reg valid;reg[362:0]hold;
 lf_select #(.N(2)) select_(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 wire[105:0]selected_narrow=(fxd[13*106+:106]&{106{grant[0]}})|({ql[182],qi[182]}&{106{grant[1]}});
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={grant[1]&&qw[134],selected_narrow,qd[134]&{256{grant[1]}}};end
 assign gv[25]=valid;assign gd[25]=hold;assign fxr[13]=accept&&grant[0];end
begin:req26
wire [1:0] eligible,grant;wire any;wire accept=!gv[26]||gr[26]; reg [362:0] hold;reg valid;wire [105:0] narrow[2];wire [105:0] selected_narrow;
assign eligible[0]=qv[60];
assign narrow[0]={106{grant[0]}}&{ql[60],qi[60]};
assign eligible[1]=qv[61];
assign narrow[1]={106{grant[1]}}&{ql[61],qi[61]};
assign selected_narrow=narrow[0]|narrow[1];
lf_select #(.N(2)) sel(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={(grant[0]&&qw[12])|(grant[1]&&qw[13]),selected_narrow,({256{grant[0]}}&qd[12])|({256{grant[1]}}&qd[13])};end
 assign gv[26]=valid;assign gd[26]=hold;end
begin:req27
wire [1:0] eligible,grant;wire any;wire accept=!gv[27]||gr[27]; reg [362:0] hold;reg valid;wire [105:0] narrow[2];wire [105:0] selected_narrow;
assign eligible[0]=qv[124];
assign narrow[0]={106{grant[0]}}&{ql[124],qi[124]};
assign eligible[1]=qv[125];
assign narrow[1]={106{grant[1]}}&{ql[125],qi[125]};
assign selected_narrow=narrow[0]|narrow[1];
lf_select #(.N(2)) sel(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={(grant[0]&&qw[76])|(grant[1]&&qw[77]),selected_narrow,({256{grant[0]}}&qd[76])|({256{grant[1]}}&qd[77])};end
 assign gv[27]=valid;assign gd[27]=hold;end
assign gv[28]=fxv[14];assign fxr[14]=gr[28];assign gd[28]={1'b0,fxd[14*106+:106],256'b0};
begin:req29
 wire[1:0]eligible={qv[183],fxv[15]};wire[1:0]grant;wire any;wire accept=!gv[29]||gr[29];reg valid;reg[362:0]hold;
 lf_select #(.N(2)) select_(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 wire[105:0]selected_narrow=(fxd[15*106+:106]&{106{grant[0]}})|({ql[183],qi[183]}&{106{grant[1]}});
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={grant[1]&&qw[135],selected_narrow,qd[135]&{256{grant[1]}}};end
 assign gv[29]=valid;assign gd[29]=hold;assign fxr[15]=accept&&grant[0];end
begin:req30
wire [1:0] eligible,grant;wire any;wire accept=!gv[30]||gr[30]; reg [362:0] hold;reg valid;wire [105:0] narrow[2];wire [105:0] selected_narrow;
assign eligible[0]=qv[62];
assign narrow[0]={106{grant[0]}}&{ql[62],qi[62]};
assign eligible[1]=qv[63];
assign narrow[1]={106{grant[1]}}&{ql[63],qi[63]};
assign selected_narrow=narrow[0]|narrow[1];
lf_select #(.N(2)) sel(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={(grant[0]&&qw[14])|(grant[1]&&qw[15]),selected_narrow,({256{grant[0]}}&qd[14])|({256{grant[1]}}&qd[15])};end
 assign gv[30]=valid;assign gd[30]=hold;end
begin:req31
wire [1:0] eligible,grant;wire any;wire accept=!gv[31]||gr[31]; reg [362:0] hold;reg valid;wire [105:0] narrow[2];wire [105:0] selected_narrow;
assign eligible[0]=qv[126];
assign narrow[0]={106{grant[0]}}&{ql[126],qi[126]};
assign eligible[1]=qv[127];
assign narrow[1]={106{grant[1]}}&{ql[127],qi[127]};
assign selected_narrow=narrow[0]|narrow[1];
lf_select #(.N(2)) sel(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={(grant[0]&&qw[78])|(grant[1]&&qw[79]),selected_narrow,({256{grant[0]}}&qd[78])|({256{grant[1]}}&qd[79])};end
 assign gv[31]=valid;assign gd[31]=hold;end
assign gv[32]=fxv[16];assign fxr[16]=gr[32];assign gd[32]={1'b0,fxd[16*106+:106],256'b0};
begin:req33
 wire[1:0]eligible={qv[184],fxv[17]};wire[1:0]grant;wire any;wire accept=!gv[33]||gr[33];reg valid;reg[362:0]hold;
 lf_select #(.N(2)) select_(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 wire[105:0]selected_narrow=(fxd[17*106+:106]&{106{grant[0]}})|({ql[184],qi[184]}&{106{grant[1]}});
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={grant[1]&&qw[136],selected_narrow,qd[136]&{256{grant[1]}}};end
 assign gv[33]=valid;assign gd[33]=hold;assign fxr[17]=accept&&grant[0];end
begin:req34
wire [1:0] eligible,grant;wire any;wire accept=!gv[34]||gr[34]; reg [362:0] hold;reg valid;wire [105:0] narrow[2];wire [105:0] selected_narrow;
assign eligible[0]=qv[64];
assign narrow[0]={106{grant[0]}}&{ql[64],qi[64]};
assign eligible[1]=qv[65];
assign narrow[1]={106{grant[1]}}&{ql[65],qi[65]};
assign selected_narrow=narrow[0]|narrow[1];
lf_select #(.N(2)) sel(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={(grant[0]&&qw[16])|(grant[1]&&qw[17]),selected_narrow,({256{grant[0]}}&qd[16])|({256{grant[1]}}&qd[17])};end
 assign gv[34]=valid;assign gd[34]=hold;end
begin:req35
wire [1:0] eligible,grant;wire any;wire accept=!gv[35]||gr[35]; reg [362:0] hold;reg valid;wire [105:0] narrow[2];wire [105:0] selected_narrow;
assign eligible[0]=qv[128];
assign narrow[0]={106{grant[0]}}&{ql[128],qi[128]};
assign eligible[1]=qv[129];
assign narrow[1]={106{grant[1]}}&{ql[129],qi[129]};
assign selected_narrow=narrow[0]|narrow[1];
lf_select #(.N(2)) sel(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={(grant[0]&&qw[80])|(grant[1]&&qw[81]),selected_narrow,({256{grant[0]}}&qd[80])|({256{grant[1]}}&qd[81])};end
 assign gv[35]=valid;assign gd[35]=hold;end
assign gv[36]=fxv[18];assign fxr[18]=gr[36];assign gd[36]={1'b0,fxd[18*106+:106],256'b0};
begin:req37
 wire[1:0]eligible={qv[185],fxv[19]};wire[1:0]grant;wire any;wire accept=!gv[37]||gr[37];reg valid;reg[362:0]hold;
 lf_select #(.N(2)) select_(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 wire[105:0]selected_narrow=(fxd[19*106+:106]&{106{grant[0]}})|({ql[185],qi[185]}&{106{grant[1]}});
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={grant[1]&&qw[137],selected_narrow,qd[137]&{256{grant[1]}}};end
 assign gv[37]=valid;assign gd[37]=hold;assign fxr[19]=accept&&grant[0];end
begin:req38
wire [1:0] eligible,grant;wire any;wire accept=!gv[38]||gr[38]; reg [362:0] hold;reg valid;wire [105:0] narrow[2];wire [105:0] selected_narrow;
assign eligible[0]=qv[66];
assign narrow[0]={106{grant[0]}}&{ql[66],qi[66]};
assign eligible[1]=qv[67];
assign narrow[1]={106{grant[1]}}&{ql[67],qi[67]};
assign selected_narrow=narrow[0]|narrow[1];
lf_select #(.N(2)) sel(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={(grant[0]&&qw[18])|(grant[1]&&qw[19]),selected_narrow,({256{grant[0]}}&qd[18])|({256{grant[1]}}&qd[19])};end
 assign gv[38]=valid;assign gd[38]=hold;end
begin:req39
wire [1:0] eligible,grant;wire any;wire accept=!gv[39]||gr[39]; reg [362:0] hold;reg valid;wire [105:0] narrow[2];wire [105:0] selected_narrow;
assign eligible[0]=qv[130];
assign narrow[0]={106{grant[0]}}&{ql[130],qi[130]};
assign eligible[1]=qv[131];
assign narrow[1]={106{grant[1]}}&{ql[131],qi[131]};
assign selected_narrow=narrow[0]|narrow[1];
lf_select #(.N(2)) sel(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={(grant[0]&&qw[82])|(grant[1]&&qw[83]),selected_narrow,({256{grant[0]}}&qd[82])|({256{grant[1]}}&qd[83])};end
 assign gv[39]=valid;assign gd[39]=hold;end
assign gv[40]=fxv[20];assign fxr[20]=gr[40];assign gd[40]={1'b0,fxd[20*106+:106],256'b0};
begin:req41
 wire[1:0]eligible={qv[186],fxv[21]};wire[1:0]grant;wire any;wire accept=!gv[41]||gr[41];reg valid;reg[362:0]hold;
 lf_select #(.N(2)) select_(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 wire[105:0]selected_narrow=(fxd[21*106+:106]&{106{grant[0]}})|({ql[186],qi[186]}&{106{grant[1]}});
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={grant[1]&&qw[138],selected_narrow,qd[138]&{256{grant[1]}}};end
 assign gv[41]=valid;assign gd[41]=hold;assign fxr[21]=accept&&grant[0];end
begin:req42
wire [1:0] eligible,grant;wire any;wire accept=!gv[42]||gr[42]; reg [362:0] hold;reg valid;wire [105:0] narrow[2];wire [105:0] selected_narrow;
assign eligible[0]=qv[68];
assign narrow[0]={106{grant[0]}}&{ql[68],qi[68]};
assign eligible[1]=qv[69];
assign narrow[1]={106{grant[1]}}&{ql[69],qi[69]};
assign selected_narrow=narrow[0]|narrow[1];
lf_select #(.N(2)) sel(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={(grant[0]&&qw[20])|(grant[1]&&qw[21]),selected_narrow,({256{grant[0]}}&qd[20])|({256{grant[1]}}&qd[21])};end
 assign gv[42]=valid;assign gd[42]=hold;end
begin:req43
wire [1:0] eligible,grant;wire any;wire accept=!gv[43]||gr[43]; reg [362:0] hold;reg valid;wire [105:0] narrow[2];wire [105:0] selected_narrow;
assign eligible[0]=qv[132];
assign narrow[0]={106{grant[0]}}&{ql[132],qi[132]};
assign eligible[1]=qv[133];
assign narrow[1]={106{grant[1]}}&{ql[133],qi[133]};
assign selected_narrow=narrow[0]|narrow[1];
lf_select #(.N(2)) sel(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={(grant[0]&&qw[84])|(grant[1]&&qw[85]),selected_narrow,({256{grant[0]}}&qd[84])|({256{grant[1]}}&qd[85])};end
 assign gv[43]=valid;assign gd[43]=hold;end
assign gv[44]=fxv[22];assign fxr[22]=gr[44];assign gd[44]={1'b0,fxd[22*106+:106],256'b0};
begin:req45
 wire[1:0]eligible={qv[187],fxv[23]};wire[1:0]grant;wire any;wire accept=!gv[45]||gr[45];reg valid;reg[362:0]hold;
 lf_select #(.N(2)) select_(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 wire[105:0]selected_narrow=(fxd[23*106+:106]&{106{grant[0]}})|({ql[187],qi[187]}&{106{grant[1]}});
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={grant[1]&&qw[139],selected_narrow,qd[139]&{256{grant[1]}}};end
 assign gv[45]=valid;assign gd[45]=hold;assign fxr[23]=accept&&grant[0];end
begin:req46
wire [1:0] eligible,grant;wire any;wire accept=!gv[46]||gr[46]; reg [362:0] hold;reg valid;wire [105:0] narrow[2];wire [105:0] selected_narrow;
assign eligible[0]=qv[70];
assign narrow[0]={106{grant[0]}}&{ql[70],qi[70]};
assign eligible[1]=qv[71];
assign narrow[1]={106{grant[1]}}&{ql[71],qi[71]};
assign selected_narrow=narrow[0]|narrow[1];
lf_select #(.N(2)) sel(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={(grant[0]&&qw[22])|(grant[1]&&qw[23]),selected_narrow,({256{grant[0]}}&qd[22])|({256{grant[1]}}&qd[23])};end
 assign gv[46]=valid;assign gd[46]=hold;end
begin:req47
wire [1:0] eligible,grant;wire any;wire accept=!gv[47]||gr[47]; reg [362:0] hold;reg valid;wire [105:0] narrow[2];wire [105:0] selected_narrow;
assign eligible[0]=qv[134];
assign narrow[0]={106{grant[0]}}&{ql[134],qi[134]};
assign eligible[1]=qv[135];
assign narrow[1]={106{grant[1]}}&{ql[135],qi[135]};
assign selected_narrow=narrow[0]|narrow[1];
lf_select #(.N(2)) sel(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={(grant[0]&&qw[86])|(grant[1]&&qw[87]),selected_narrow,({256{grant[0]}}&qd[86])|({256{grant[1]}}&qd[87])};end
 assign gv[47]=valid;assign gd[47]=hold;end
assign gv[48]=fxv[24];assign fxr[24]=gr[48];assign gd[48]={1'b0,fxd[24*106+:106],256'b0};
begin:req49
 wire[1:0]eligible={qv[188],fxv[25]};wire[1:0]grant;wire any;wire accept=!gv[49]||gr[49];reg valid;reg[362:0]hold;
 lf_select #(.N(2)) select_(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 wire[105:0]selected_narrow=(fxd[25*106+:106]&{106{grant[0]}})|({ql[188],qi[188]}&{106{grant[1]}});
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={grant[1]&&qw[140],selected_narrow,qd[140]&{256{grant[1]}}};end
 assign gv[49]=valid;assign gd[49]=hold;assign fxr[25]=accept&&grant[0];end
begin:req50
wire [1:0] eligible,grant;wire any;wire accept=!gv[50]||gr[50]; reg [362:0] hold;reg valid;wire [105:0] narrow[2];wire [105:0] selected_narrow;
assign eligible[0]=qv[72];
assign narrow[0]={106{grant[0]}}&{ql[72],qi[72]};
assign eligible[1]=qv[73];
assign narrow[1]={106{grant[1]}}&{ql[73],qi[73]};
assign selected_narrow=narrow[0]|narrow[1];
lf_select #(.N(2)) sel(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={(grant[0]&&qw[24])|(grant[1]&&qw[25]),selected_narrow,({256{grant[0]}}&qd[24])|({256{grant[1]}}&qd[25])};end
 assign gv[50]=valid;assign gd[50]=hold;end
begin:req51
wire [1:0] eligible,grant;wire any;wire accept=!gv[51]||gr[51]; reg [362:0] hold;reg valid;wire [105:0] narrow[2];wire [105:0] selected_narrow;
assign eligible[0]=qv[136];
assign narrow[0]={106{grant[0]}}&{ql[136],qi[136]};
assign eligible[1]=qv[137];
assign narrow[1]={106{grant[1]}}&{ql[137],qi[137]};
assign selected_narrow=narrow[0]|narrow[1];
lf_select #(.N(2)) sel(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={(grant[0]&&qw[88])|(grant[1]&&qw[89]),selected_narrow,({256{grant[0]}}&qd[88])|({256{grant[1]}}&qd[89])};end
 assign gv[51]=valid;assign gd[51]=hold;end
assign gv[52]=fxv[26];assign fxr[26]=gr[52];assign gd[52]={1'b0,fxd[26*106+:106],256'b0};
begin:req53
 wire[1:0]eligible={qv[189],fxv[27]};wire[1:0]grant;wire any;wire accept=!gv[53]||gr[53];reg valid;reg[362:0]hold;
 lf_select #(.N(2)) select_(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 wire[105:0]selected_narrow=(fxd[27*106+:106]&{106{grant[0]}})|({ql[189],qi[189]}&{106{grant[1]}});
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={grant[1]&&qw[141],selected_narrow,qd[141]&{256{grant[1]}}};end
 assign gv[53]=valid;assign gd[53]=hold;assign fxr[27]=accept&&grant[0];end
begin:req54
wire [1:0] eligible,grant;wire any;wire accept=!gv[54]||gr[54]; reg [362:0] hold;reg valid;wire [105:0] narrow[2];wire [105:0] selected_narrow;
assign eligible[0]=qv[74];
assign narrow[0]={106{grant[0]}}&{ql[74],qi[74]};
assign eligible[1]=qv[75];
assign narrow[1]={106{grant[1]}}&{ql[75],qi[75]};
assign selected_narrow=narrow[0]|narrow[1];
lf_select #(.N(2)) sel(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={(grant[0]&&qw[26])|(grant[1]&&qw[27]),selected_narrow,({256{grant[0]}}&qd[26])|({256{grant[1]}}&qd[27])};end
 assign gv[54]=valid;assign gd[54]=hold;end
begin:req55
wire [1:0] eligible,grant;wire any;wire accept=!gv[55]||gr[55]; reg [362:0] hold;reg valid;wire [105:0] narrow[2];wire [105:0] selected_narrow;
assign eligible[0]=qv[138];
assign narrow[0]={106{grant[0]}}&{ql[138],qi[138]};
assign eligible[1]=qv[139];
assign narrow[1]={106{grant[1]}}&{ql[139],qi[139]};
assign selected_narrow=narrow[0]|narrow[1];
lf_select #(.N(2)) sel(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={(grant[0]&&qw[90])|(grant[1]&&qw[91]),selected_narrow,({256{grant[0]}}&qd[90])|({256{grant[1]}}&qd[91])};end
 assign gv[55]=valid;assign gd[55]=hold;end
assign gv[56]=fxv[28];assign fxr[28]=gr[56];assign gd[56]={1'b0,fxd[28*106+:106],256'b0};
begin:req57
 wire[1:0]eligible={qv[190],fxv[29]};wire[1:0]grant;wire any;wire accept=!gv[57]||gr[57];reg valid;reg[362:0]hold;
 lf_select #(.N(2)) select_(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 wire[105:0]selected_narrow=(fxd[29*106+:106]&{106{grant[0]}})|({ql[190],qi[190]}&{106{grant[1]}});
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={grant[1]&&qw[142],selected_narrow,qd[142]&{256{grant[1]}}};end
 assign gv[57]=valid;assign gd[57]=hold;assign fxr[29]=accept&&grant[0];end
begin:req58
wire [1:0] eligible,grant;wire any;wire accept=!gv[58]||gr[58]; reg [362:0] hold;reg valid;wire [105:0] narrow[2];wire [105:0] selected_narrow;
assign eligible[0]=qv[76];
assign narrow[0]={106{grant[0]}}&{ql[76],qi[76]};
assign eligible[1]=qv[77];
assign narrow[1]={106{grant[1]}}&{ql[77],qi[77]};
assign selected_narrow=narrow[0]|narrow[1];
lf_select #(.N(2)) sel(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={(grant[0]&&qw[28])|(grant[1]&&qw[29]),selected_narrow,({256{grant[0]}}&qd[28])|({256{grant[1]}}&qd[29])};end
 assign gv[58]=valid;assign gd[58]=hold;end
begin:req59
wire [1:0] eligible,grant;wire any;wire accept=!gv[59]||gr[59]; reg [362:0] hold;reg valid;wire [105:0] narrow[2];wire [105:0] selected_narrow;
assign eligible[0]=qv[140];
assign narrow[0]={106{grant[0]}}&{ql[140],qi[140]};
assign eligible[1]=qv[141];
assign narrow[1]={106{grant[1]}}&{ql[141],qi[141]};
assign selected_narrow=narrow[0]|narrow[1];
lf_select #(.N(2)) sel(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={(grant[0]&&qw[92])|(grant[1]&&qw[93]),selected_narrow,({256{grant[0]}}&qd[92])|({256{grant[1]}}&qd[93])};end
 assign gv[59]=valid;assign gd[59]=hold;end
assign gv[60]=fxv[30];assign fxr[30]=gr[60];assign gd[60]={1'b0,fxd[30*106+:106],256'b0};
begin:req61
 wire[1:0]eligible={qv[191],fxv[31]};wire[1:0]grant;wire any;wire accept=!gv[61]||gr[61];reg valid;reg[362:0]hold;
 lf_select #(.N(2)) select_(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 wire[105:0]selected_narrow=(fxd[31*106+:106]&{106{grant[0]}})|({ql[191],qi[191]}&{106{grant[1]}});
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={grant[1]&&qw[143],selected_narrow,qd[143]&{256{grant[1]}}};end
 assign gv[61]=valid;assign gd[61]=hold;assign fxr[31]=accept&&grant[0];end
begin:req62
wire [1:0] eligible,grant;wire any;wire accept=!gv[62]||gr[62]; reg [362:0] hold;reg valid;wire [105:0] narrow[2];wire [105:0] selected_narrow;
assign eligible[0]=qv[78];
assign narrow[0]={106{grant[0]}}&{ql[78],qi[78]};
assign eligible[1]=qv[79];
assign narrow[1]={106{grant[1]}}&{ql[79],qi[79]};
assign selected_narrow=narrow[0]|narrow[1];
lf_select #(.N(2)) sel(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={(grant[0]&&qw[30])|(grant[1]&&qw[31]),selected_narrow,({256{grant[0]}}&qd[30])|({256{grant[1]}}&qd[31])};end
 assign gv[62]=valid;assign gd[62]=hold;end
begin:req63
wire [1:0] eligible,grant;wire any;wire accept=!gv[63]||gr[63]; reg [362:0] hold;reg valid;wire [105:0] narrow[2];wire [105:0] selected_narrow;
assign eligible[0]=qv[142];
assign narrow[0]={106{grant[0]}}&{ql[142],qi[142]};
assign eligible[1]=qv[143];
assign narrow[1]={106{grant[1]}}&{ql[143],qi[143]};
assign selected_narrow=narrow[0]|narrow[1];
lf_select #(.N(2)) sel(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={(grant[0]&&qw[94])|(grant[1]&&qw[95]),selected_narrow,({256{grant[0]}}&qd[94])|({256{grant[1]}}&qd[95])};end
 assign gv[63]=valid;assign gd[63]=hold;end
assign gv[64]=fxv[32];assign fxr[32]=gr[64];assign gd[64]={1'b0,fxd[32*106+:106],256'b0};
begin:req65
 wire[1:0]eligible={qv[192],fxv[33]};wire[1:0]grant;wire any;wire accept=!gv[65]||gr[65];reg valid;reg[362:0]hold;
 lf_select #(.N(2)) select_(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 wire[105:0]selected_narrow=(fxd[33*106+:106]&{106{grant[0]}})|({ql[192],qi[192]}&{106{grant[1]}});
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={grant[1]&&qw[144],selected_narrow,qd[144]&{256{grant[1]}}};end
 assign gv[65]=valid;assign gd[65]=hold;assign fxr[33]=accept&&grant[0];end
begin:req66
wire [1:0] eligible,grant;wire any;wire accept=!gv[66]||gr[66]; reg [362:0] hold;reg valid;wire [105:0] narrow[2];wire [105:0] selected_narrow;
assign eligible[0]=qv[80];
assign narrow[0]={106{grant[0]}}&{ql[80],qi[80]};
assign eligible[1]=qv[81];
assign narrow[1]={106{grant[1]}}&{ql[81],qi[81]};
assign selected_narrow=narrow[0]|narrow[1];
lf_select #(.N(2)) sel(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={(grant[0]&&qw[32])|(grant[1]&&qw[33]),selected_narrow,({256{grant[0]}}&qd[32])|({256{grant[1]}}&qd[33])};end
 assign gv[66]=valid;assign gd[66]=hold;end
begin:req67
wire [1:0] eligible,grant;wire any;wire accept=!gv[67]||gr[67]; reg [362:0] hold;reg valid;wire [105:0] narrow[2];wire [105:0] selected_narrow;
assign eligible[0]=qv[144];
assign narrow[0]={106{grant[0]}}&{ql[144],qi[144]};
assign eligible[1]=qv[145];
assign narrow[1]={106{grant[1]}}&{ql[145],qi[145]};
assign selected_narrow=narrow[0]|narrow[1];
lf_select #(.N(2)) sel(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={(grant[0]&&qw[96])|(grant[1]&&qw[97]),selected_narrow,({256{grant[0]}}&qd[96])|({256{grant[1]}}&qd[97])};end
 assign gv[67]=valid;assign gd[67]=hold;end
assign gv[68]=fxv[34];assign fxr[34]=gr[68];assign gd[68]={1'b0,fxd[34*106+:106],256'b0};
begin:req69
 wire[1:0]eligible={qv[193],fxv[35]};wire[1:0]grant;wire any;wire accept=!gv[69]||gr[69];reg valid;reg[362:0]hold;
 lf_select #(.N(2)) select_(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 wire[105:0]selected_narrow=(fxd[35*106+:106]&{106{grant[0]}})|({ql[193],qi[193]}&{106{grant[1]}});
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={grant[1]&&qw[145],selected_narrow,qd[145]&{256{grant[1]}}};end
 assign gv[69]=valid;assign gd[69]=hold;assign fxr[35]=accept&&grant[0];end
begin:req70
wire [1:0] eligible,grant;wire any;wire accept=!gv[70]||gr[70]; reg [362:0] hold;reg valid;wire [105:0] narrow[2];wire [105:0] selected_narrow;
assign eligible[0]=qv[82];
assign narrow[0]={106{grant[0]}}&{ql[82],qi[82]};
assign eligible[1]=qv[83];
assign narrow[1]={106{grant[1]}}&{ql[83],qi[83]};
assign selected_narrow=narrow[0]|narrow[1];
lf_select #(.N(2)) sel(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={(grant[0]&&qw[34])|(grant[1]&&qw[35]),selected_narrow,({256{grant[0]}}&qd[34])|({256{grant[1]}}&qd[35])};end
 assign gv[70]=valid;assign gd[70]=hold;end
begin:req71
wire [1:0] eligible,grant;wire any;wire accept=!gv[71]||gr[71]; reg [362:0] hold;reg valid;wire [105:0] narrow[2];wire [105:0] selected_narrow;
assign eligible[0]=qv[146];
assign narrow[0]={106{grant[0]}}&{ql[146],qi[146]};
assign eligible[1]=qv[147];
assign narrow[1]={106{grant[1]}}&{ql[147],qi[147]};
assign selected_narrow=narrow[0]|narrow[1];
lf_select #(.N(2)) sel(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={(grant[0]&&qw[98])|(grant[1]&&qw[99]),selected_narrow,({256{grant[0]}}&qd[98])|({256{grant[1]}}&qd[99])};end
 assign gv[71]=valid;assign gd[71]=hold;end
assign gv[72]=fxv[36];assign fxr[36]=gr[72];assign gd[72]={1'b0,fxd[36*106+:106],256'b0};
begin:req73
 wire[1:0]eligible={qv[194],fxv[37]};wire[1:0]grant;wire any;wire accept=!gv[73]||gr[73];reg valid;reg[362:0]hold;
 lf_select #(.N(2)) select_(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 wire[105:0]selected_narrow=(fxd[37*106+:106]&{106{grant[0]}})|({ql[194],qi[194]}&{106{grant[1]}});
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={grant[1]&&qw[146],selected_narrow,qd[146]&{256{grant[1]}}};end
 assign gv[73]=valid;assign gd[73]=hold;assign fxr[37]=accept&&grant[0];end
begin:req74
wire [1:0] eligible,grant;wire any;wire accept=!gv[74]||gr[74]; reg [362:0] hold;reg valid;wire [105:0] narrow[2];wire [105:0] selected_narrow;
assign eligible[0]=qv[84];
assign narrow[0]={106{grant[0]}}&{ql[84],qi[84]};
assign eligible[1]=qv[85];
assign narrow[1]={106{grant[1]}}&{ql[85],qi[85]};
assign selected_narrow=narrow[0]|narrow[1];
lf_select #(.N(2)) sel(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={(grant[0]&&qw[36])|(grant[1]&&qw[37]),selected_narrow,({256{grant[0]}}&qd[36])|({256{grant[1]}}&qd[37])};end
 assign gv[74]=valid;assign gd[74]=hold;end
begin:req75
wire [1:0] eligible,grant;wire any;wire accept=!gv[75]||gr[75]; reg [362:0] hold;reg valid;wire [105:0] narrow[2];wire [105:0] selected_narrow;
assign eligible[0]=qv[148];
assign narrow[0]={106{grant[0]}}&{ql[148],qi[148]};
assign eligible[1]=qv[149];
assign narrow[1]={106{grant[1]}}&{ql[149],qi[149]};
assign selected_narrow=narrow[0]|narrow[1];
lf_select #(.N(2)) sel(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={(grant[0]&&qw[100])|(grant[1]&&qw[101]),selected_narrow,({256{grant[0]}}&qd[100])|({256{grant[1]}}&qd[101])};end
 assign gv[75]=valid;assign gd[75]=hold;end
assign gv[76]=fxv[38];assign fxr[38]=gr[76];assign gd[76]={1'b0,fxd[38*106+:106],256'b0};
begin:req77
 wire[1:0]eligible={qv[195],fxv[39]};wire[1:0]grant;wire any;wire accept=!gv[77]||gr[77];reg valid;reg[362:0]hold;
 lf_select #(.N(2)) select_(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 wire[105:0]selected_narrow=(fxd[39*106+:106]&{106{grant[0]}})|({ql[195],qi[195]}&{106{grant[1]}});
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={grant[1]&&qw[147],selected_narrow,qd[147]&{256{grant[1]}}};end
 assign gv[77]=valid;assign gd[77]=hold;assign fxr[39]=accept&&grant[0];end
begin:req78
wire [1:0] eligible,grant;wire any;wire accept=!gv[78]||gr[78]; reg [362:0] hold;reg valid;wire [105:0] narrow[2];wire [105:0] selected_narrow;
assign eligible[0]=qv[86];
assign narrow[0]={106{grant[0]}}&{ql[86],qi[86]};
assign eligible[1]=qv[87];
assign narrow[1]={106{grant[1]}}&{ql[87],qi[87]};
assign selected_narrow=narrow[0]|narrow[1];
lf_select #(.N(2)) sel(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={(grant[0]&&qw[38])|(grant[1]&&qw[39]),selected_narrow,({256{grant[0]}}&qd[38])|({256{grant[1]}}&qd[39])};end
 assign gv[78]=valid;assign gd[78]=hold;end
begin:req79
wire [1:0] eligible,grant;wire any;wire accept=!gv[79]||gr[79]; reg [362:0] hold;reg valid;wire [105:0] narrow[2];wire [105:0] selected_narrow;
assign eligible[0]=qv[150];
assign narrow[0]={106{grant[0]}}&{ql[150],qi[150]};
assign eligible[1]=qv[151];
assign narrow[1]={106{grant[1]}}&{ql[151],qi[151]};
assign selected_narrow=narrow[0]|narrow[1];
lf_select #(.N(2)) sel(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={(grant[0]&&qw[102])|(grant[1]&&qw[103]),selected_narrow,({256{grant[0]}}&qd[102])|({256{grant[1]}}&qd[103])};end
 assign gv[79]=valid;assign gd[79]=hold;end
assign gv[80]=fxv[40];assign fxr[40]=gr[80];assign gd[80]={1'b0,fxd[40*106+:106],256'b0};
begin:req81
 wire[1:0]eligible={qv[196],fxv[41]};wire[1:0]grant;wire any;wire accept=!gv[81]||gr[81];reg valid;reg[362:0]hold;
 lf_select #(.N(2)) select_(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 wire[105:0]selected_narrow=(fxd[41*106+:106]&{106{grant[0]}})|({ql[196],qi[196]}&{106{grant[1]}});
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={grant[1]&&qw[148],selected_narrow,qd[148]&{256{grant[1]}}};end
 assign gv[81]=valid;assign gd[81]=hold;assign fxr[41]=accept&&grant[0];end
begin:req82
wire [1:0] eligible,grant;wire any;wire accept=!gv[82]||gr[82]; reg [362:0] hold;reg valid;wire [105:0] narrow[2];wire [105:0] selected_narrow;
assign eligible[0]=qv[88];
assign narrow[0]={106{grant[0]}}&{ql[88],qi[88]};
assign eligible[1]=qv[89];
assign narrow[1]={106{grant[1]}}&{ql[89],qi[89]};
assign selected_narrow=narrow[0]|narrow[1];
lf_select #(.N(2)) sel(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={(grant[0]&&qw[40])|(grant[1]&&qw[41]),selected_narrow,({256{grant[0]}}&qd[40])|({256{grant[1]}}&qd[41])};end
 assign gv[82]=valid;assign gd[82]=hold;end
begin:req83
wire [1:0] eligible,grant;wire any;wire accept=!gv[83]||gr[83]; reg [362:0] hold;reg valid;wire [105:0] narrow[2];wire [105:0] selected_narrow;
assign eligible[0]=qv[152];
assign narrow[0]={106{grant[0]}}&{ql[152],qi[152]};
assign eligible[1]=qv[153];
assign narrow[1]={106{grant[1]}}&{ql[153],qi[153]};
assign selected_narrow=narrow[0]|narrow[1];
lf_select #(.N(2)) sel(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={(grant[0]&&qw[104])|(grant[1]&&qw[105]),selected_narrow,({256{grant[0]}}&qd[104])|({256{grant[1]}}&qd[105])};end
 assign gv[83]=valid;assign gd[83]=hold;end
assign gv[84]=fxv[42];assign fxr[42]=gr[84];assign gd[84]={1'b0,fxd[42*106+:106],256'b0};
begin:req85
 wire[1:0]eligible={qv[197],fxv[43]};wire[1:0]grant;wire any;wire accept=!gv[85]||gr[85];reg valid;reg[362:0]hold;
 lf_select #(.N(2)) select_(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 wire[105:0]selected_narrow=(fxd[43*106+:106]&{106{grant[0]}})|({ql[197],qi[197]}&{106{grant[1]}});
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={grant[1]&&qw[149],selected_narrow,qd[149]&{256{grant[1]}}};end
 assign gv[85]=valid;assign gd[85]=hold;assign fxr[43]=accept&&grant[0];end
begin:req86
wire [1:0] eligible,grant;wire any;wire accept=!gv[86]||gr[86]; reg [362:0] hold;reg valid;wire [105:0] narrow[2];wire [105:0] selected_narrow;
assign eligible[0]=qv[90];
assign narrow[0]={106{grant[0]}}&{ql[90],qi[90]};
assign eligible[1]=qv[91];
assign narrow[1]={106{grant[1]}}&{ql[91],qi[91]};
assign selected_narrow=narrow[0]|narrow[1];
lf_select #(.N(2)) sel(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={(grant[0]&&qw[42])|(grant[1]&&qw[43]),selected_narrow,({256{grant[0]}}&qd[42])|({256{grant[1]}}&qd[43])};end
 assign gv[86]=valid;assign gd[86]=hold;end
begin:req87
wire [1:0] eligible,grant;wire any;wire accept=!gv[87]||gr[87]; reg [362:0] hold;reg valid;wire [105:0] narrow[2];wire [105:0] selected_narrow;
assign eligible[0]=qv[154];
assign narrow[0]={106{grant[0]}}&{ql[154],qi[154]};
assign eligible[1]=qv[155];
assign narrow[1]={106{grant[1]}}&{ql[155],qi[155]};
assign selected_narrow=narrow[0]|narrow[1];
lf_select #(.N(2)) sel(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={(grant[0]&&qw[106])|(grant[1]&&qw[107]),selected_narrow,({256{grant[0]}}&qd[106])|({256{grant[1]}}&qd[107])};end
 assign gv[87]=valid;assign gd[87]=hold;end
assign gv[88]=fxv[44];assign fxr[44]=gr[88];assign gd[88]={1'b0,fxd[44*106+:106],256'b0};
begin:req89
 wire[1:0]eligible={qv[198],fxv[45]};wire[1:0]grant;wire any;wire accept=!gv[89]||gr[89];reg valid;reg[362:0]hold;
 lf_select #(.N(2)) select_(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 wire[105:0]selected_narrow=(fxd[45*106+:106]&{106{grant[0]}})|({ql[198],qi[198]}&{106{grant[1]}});
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={grant[1]&&qw[150],selected_narrow,qd[150]&{256{grant[1]}}};end
 assign gv[89]=valid;assign gd[89]=hold;assign fxr[45]=accept&&grant[0];end
begin:req90
wire [1:0] eligible,grant;wire any;wire accept=!gv[90]||gr[90]; reg [362:0] hold;reg valid;wire [105:0] narrow[2];wire [105:0] selected_narrow;
assign eligible[0]=qv[92];
assign narrow[0]={106{grant[0]}}&{ql[92],qi[92]};
assign eligible[1]=qv[93];
assign narrow[1]={106{grant[1]}}&{ql[93],qi[93]};
assign selected_narrow=narrow[0]|narrow[1];
lf_select #(.N(2)) sel(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={(grant[0]&&qw[44])|(grant[1]&&qw[45]),selected_narrow,({256{grant[0]}}&qd[44])|({256{grant[1]}}&qd[45])};end
 assign gv[90]=valid;assign gd[90]=hold;end
begin:req91
wire [1:0] eligible,grant;wire any;wire accept=!gv[91]||gr[91]; reg [362:0] hold;reg valid;wire [105:0] narrow[2];wire [105:0] selected_narrow;
assign eligible[0]=qv[156];
assign narrow[0]={106{grant[0]}}&{ql[156],qi[156]};
assign eligible[1]=qv[157];
assign narrow[1]={106{grant[1]}}&{ql[157],qi[157]};
assign selected_narrow=narrow[0]|narrow[1];
lf_select #(.N(2)) sel(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={(grant[0]&&qw[108])|(grant[1]&&qw[109]),selected_narrow,({256{grant[0]}}&qd[108])|({256{grant[1]}}&qd[109])};end
 assign gv[91]=valid;assign gd[91]=hold;end
assign gv[92]=fxv[46];assign fxr[46]=gr[92];assign gd[92]={1'b0,fxd[46*106+:106],256'b0};
begin:req93
 wire[1:0]eligible={qv[199],fxv[47]};wire[1:0]grant;wire any;wire accept=!gv[93]||gr[93];reg valid;reg[362:0]hold;
 lf_select #(.N(2)) select_(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 wire[105:0]selected_narrow=(fxd[47*106+:106]&{106{grant[0]}})|({ql[199],qi[199]}&{106{grant[1]}});
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={grant[1]&&qw[151],selected_narrow,qd[151]&{256{grant[1]}}};end
 assign gv[93]=valid;assign gd[93]=hold;assign fxr[47]=accept&&grant[0];end
begin:req94
wire [1:0] eligible,grant;wire any;wire accept=!gv[94]||gr[94]; reg [362:0] hold;reg valid;wire [105:0] narrow[2];wire [105:0] selected_narrow;
assign eligible[0]=qv[94];
assign narrow[0]={106{grant[0]}}&{ql[94],qi[94]};
assign eligible[1]=qv[95];
assign narrow[1]={106{grant[1]}}&{ql[95],qi[95]};
assign selected_narrow=narrow[0]|narrow[1];
lf_select #(.N(2)) sel(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={(grant[0]&&qw[46])|(grant[1]&&qw[47]),selected_narrow,({256{grant[0]}}&qd[46])|({256{grant[1]}}&qd[47])};end
 assign gv[94]=valid;assign gd[94]=hold;end
begin:req95
wire [1:0] eligible,grant;wire any;wire accept=!gv[95]||gr[95]; reg [362:0] hold;reg valid;wire [105:0] narrow[2];wire [105:0] selected_narrow;
assign eligible[0]=qv[158];
assign narrow[0]={106{grant[0]}}&{ql[158],qi[158]};
assign eligible[1]=qv[159];
assign narrow[1]={106{grant[1]}}&{ql[159],qi[159]};
assign selected_narrow=narrow[0]|narrow[1];
lf_select #(.N(2)) sel(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={(grant[0]&&qw[110])|(grant[1]&&qw[111]),selected_narrow,({256{grant[0]}}&qd[110])|({256{grant[1]}}&qd[111])};end
 assign gv[95]=valid;assign gd[95]=hold;end
assign gv[96]=fxv[48];assign fxr[48]=gr[96];assign gd[96]={1'b0,fxd[48*106+:106],256'b0};
begin:req97
 wire[1:0]eligible={qv[200],fxv[49]};wire[1:0]grant;wire any;wire accept=!gv[97]||gr[97];reg valid;reg[362:0]hold;
 lf_select #(.N(2)) select_(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 wire[105:0]selected_narrow=(fxd[49*106+:106]&{106{grant[0]}})|({ql[200],qi[200]}&{106{grant[1]}});
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={grant[1]&&qw[152],selected_narrow,qd[152]&{256{grant[1]}}};end
 assign gv[97]=valid;assign gd[97]=hold;assign fxr[49]=accept&&grant[0];end
begin:req98
wire [1:0] eligible,grant;wire any;wire accept=!gv[98]||gr[98]; reg [362:0] hold;reg valid;wire [105:0] narrow[2];wire [105:0] selected_narrow;
assign eligible[0]=qv[96];
assign narrow[0]={106{grant[0]}}&{ql[96],qi[96]};
assign eligible[1]=qv[97];
assign narrow[1]={106{grant[1]}}&{ql[97],qi[97]};
assign selected_narrow=narrow[0]|narrow[1];
lf_select #(.N(2)) sel(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={(grant[0]&&qw[48])|(grant[1]&&qw[49]),selected_narrow,({256{grant[0]}}&qd[48])|({256{grant[1]}}&qd[49])};end
 assign gv[98]=valid;assign gd[98]=hold;end
begin:req99
wire [1:0] eligible,grant;wire any;wire accept=!gv[99]||gr[99]; reg [362:0] hold;reg valid;wire [105:0] narrow[2];wire [105:0] selected_narrow;
assign eligible[0]=qv[160];
assign narrow[0]={106{grant[0]}}&{ql[160],qi[160]};
assign eligible[1]=qv[161];
assign narrow[1]={106{grant[1]}}&{ql[161],qi[161]};
assign selected_narrow=narrow[0]|narrow[1];
lf_select #(.N(2)) sel(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={(grant[0]&&qw[112])|(grant[1]&&qw[113]),selected_narrow,({256{grant[0]}}&qd[112])|({256{grant[1]}}&qd[113])};end
 assign gv[99]=valid;assign gd[99]=hold;end
assign gv[100]=fxv[50];assign fxr[50]=gr[100];assign gd[100]={1'b0,fxd[50*106+:106],256'b0};
begin:req101
 wire[1:0]eligible={qv[201],fxv[51]};wire[1:0]grant;wire any;wire accept=!gv[101]||gr[101];reg valid;reg[362:0]hold;
 lf_select #(.N(2)) select_(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 wire[105:0]selected_narrow=(fxd[51*106+:106]&{106{grant[0]}})|({ql[201],qi[201]}&{106{grant[1]}});
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={grant[1]&&qw[153],selected_narrow,qd[153]&{256{grant[1]}}};end
 assign gv[101]=valid;assign gd[101]=hold;assign fxr[51]=accept&&grant[0];end
begin:req102
wire [1:0] eligible,grant;wire any;wire accept=!gv[102]||gr[102]; reg [362:0] hold;reg valid;wire [105:0] narrow[2];wire [105:0] selected_narrow;
assign eligible[0]=qv[98];
assign narrow[0]={106{grant[0]}}&{ql[98],qi[98]};
assign eligible[1]=qv[99];
assign narrow[1]={106{grant[1]}}&{ql[99],qi[99]};
assign selected_narrow=narrow[0]|narrow[1];
lf_select #(.N(2)) sel(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={(grant[0]&&qw[50])|(grant[1]&&qw[51]),selected_narrow,({256{grant[0]}}&qd[50])|({256{grant[1]}}&qd[51])};end
 assign gv[102]=valid;assign gd[102]=hold;end
begin:req103
wire [1:0] eligible,grant;wire any;wire accept=!gv[103]||gr[103]; reg [362:0] hold;reg valid;wire [105:0] narrow[2];wire [105:0] selected_narrow;
assign eligible[0]=qv[162];
assign narrow[0]={106{grant[0]}}&{ql[162],qi[162]};
assign eligible[1]=qv[163];
assign narrow[1]={106{grant[1]}}&{ql[163],qi[163]};
assign selected_narrow=narrow[0]|narrow[1];
lf_select #(.N(2)) sel(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={(grant[0]&&qw[114])|(grant[1]&&qw[115]),selected_narrow,({256{grant[0]}}&qd[114])|({256{grant[1]}}&qd[115])};end
 assign gv[103]=valid;assign gd[103]=hold;end
assign gv[104]=fxv[52];assign fxr[52]=gr[104];assign gd[104]={1'b0,fxd[52*106+:106],256'b0};
begin:req105
 wire[1:0]eligible={qv[202],fxv[53]};wire[1:0]grant;wire any;wire accept=!gv[105]||gr[105];reg valid;reg[362:0]hold;
 lf_select #(.N(2)) select_(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 wire[105:0]selected_narrow=(fxd[53*106+:106]&{106{grant[0]}})|({ql[202],qi[202]}&{106{grant[1]}});
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={grant[1]&&qw[154],selected_narrow,qd[154]&{256{grant[1]}}};end
 assign gv[105]=valid;assign gd[105]=hold;assign fxr[53]=accept&&grant[0];end
begin:req106
wire [1:0] eligible,grant;wire any;wire accept=!gv[106]||gr[106]; reg [362:0] hold;reg valid;wire [105:0] narrow[2];wire [105:0] selected_narrow;
assign eligible[0]=qv[100];
assign narrow[0]={106{grant[0]}}&{ql[100],qi[100]};
assign eligible[1]=qv[101];
assign narrow[1]={106{grant[1]}}&{ql[101],qi[101]};
assign selected_narrow=narrow[0]|narrow[1];
lf_select #(.N(2)) sel(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={(grant[0]&&qw[52])|(grant[1]&&qw[53]),selected_narrow,({256{grant[0]}}&qd[52])|({256{grant[1]}}&qd[53])};end
 assign gv[106]=valid;assign gd[106]=hold;end
begin:req107
wire [1:0] eligible,grant;wire any;wire accept=!gv[107]||gr[107]; reg [362:0] hold;reg valid;wire [105:0] narrow[2];wire [105:0] selected_narrow;
assign eligible[0]=qv[164];
assign narrow[0]={106{grant[0]}}&{ql[164],qi[164]};
assign eligible[1]=qv[165];
assign narrow[1]={106{grant[1]}}&{ql[165],qi[165]};
assign selected_narrow=narrow[0]|narrow[1];
lf_select #(.N(2)) sel(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={(grant[0]&&qw[116])|(grant[1]&&qw[117]),selected_narrow,({256{grant[0]}}&qd[116])|({256{grant[1]}}&qd[117])};end
 assign gv[107]=valid;assign gd[107]=hold;end
assign gv[108]=fxv[54];assign fxr[54]=gr[108];assign gd[108]={1'b0,fxd[54*106+:106],256'b0};
begin:req109
 wire[1:0]eligible={qv[203],fxv[55]};wire[1:0]grant;wire any;wire accept=!gv[109]||gr[109];reg valid;reg[362:0]hold;
 lf_select #(.N(2)) select_(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 wire[105:0]selected_narrow=(fxd[55*106+:106]&{106{grant[0]}})|({ql[203],qi[203]}&{106{grant[1]}});
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={grant[1]&&qw[155],selected_narrow,qd[155]&{256{grant[1]}}};end
 assign gv[109]=valid;assign gd[109]=hold;assign fxr[55]=accept&&grant[0];end
begin:req110
wire [1:0] eligible,grant;wire any;wire accept=!gv[110]||gr[110]; reg [362:0] hold;reg valid;wire [105:0] narrow[2];wire [105:0] selected_narrow;
assign eligible[0]=qv[102];
assign narrow[0]={106{grant[0]}}&{ql[102],qi[102]};
assign eligible[1]=qv[103];
assign narrow[1]={106{grant[1]}}&{ql[103],qi[103]};
assign selected_narrow=narrow[0]|narrow[1];
lf_select #(.N(2)) sel(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={(grant[0]&&qw[54])|(grant[1]&&qw[55]),selected_narrow,({256{grant[0]}}&qd[54])|({256{grant[1]}}&qd[55])};end
 assign gv[110]=valid;assign gd[110]=hold;end
begin:req111
wire [1:0] eligible,grant;wire any;wire accept=!gv[111]||gr[111]; reg [362:0] hold;reg valid;wire [105:0] narrow[2];wire [105:0] selected_narrow;
assign eligible[0]=qv[166];
assign narrow[0]={106{grant[0]}}&{ql[166],qi[166]};
assign eligible[1]=qv[167];
assign narrow[1]={106{grant[1]}}&{ql[167],qi[167]};
assign selected_narrow=narrow[0]|narrow[1];
lf_select #(.N(2)) sel(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={(grant[0]&&qw[118])|(grant[1]&&qw[119]),selected_narrow,({256{grant[0]}}&qd[118])|({256{grant[1]}}&qd[119])};end
 assign gv[111]=valid;assign gd[111]=hold;end
assign gv[112]=fxv[56];assign fxr[56]=gr[112];assign gd[112]={1'b0,fxd[56*106+:106],256'b0};
begin:req113
 wire[1:0]eligible={qv[204],fxv[57]};wire[1:0]grant;wire any;wire accept=!gv[113]||gr[113];reg valid;reg[362:0]hold;
 lf_select #(.N(2)) select_(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 wire[105:0]selected_narrow=(fxd[57*106+:106]&{106{grant[0]}})|({ql[204],qi[204]}&{106{grant[1]}});
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={grant[1]&&qw[156],selected_narrow,qd[156]&{256{grant[1]}}};end
 assign gv[113]=valid;assign gd[113]=hold;assign fxr[57]=accept&&grant[0];end
begin:req114
wire [1:0] eligible,grant;wire any;wire accept=!gv[114]||gr[114]; reg [362:0] hold;reg valid;wire [105:0] narrow[2];wire [105:0] selected_narrow;
assign eligible[0]=qv[104];
assign narrow[0]={106{grant[0]}}&{ql[104],qi[104]};
assign eligible[1]=qv[105];
assign narrow[1]={106{grant[1]}}&{ql[105],qi[105]};
assign selected_narrow=narrow[0]|narrow[1];
lf_select #(.N(2)) sel(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={(grant[0]&&qw[56])|(grant[1]&&qw[57]),selected_narrow,({256{grant[0]}}&qd[56])|({256{grant[1]}}&qd[57])};end
 assign gv[114]=valid;assign gd[114]=hold;end
begin:req115
wire [1:0] eligible,grant;wire any;wire accept=!gv[115]||gr[115]; reg [362:0] hold;reg valid;wire [105:0] narrow[2];wire [105:0] selected_narrow;
assign eligible[0]=qv[168];
assign narrow[0]={106{grant[0]}}&{ql[168],qi[168]};
assign eligible[1]=qv[169];
assign narrow[1]={106{grant[1]}}&{ql[169],qi[169]};
assign selected_narrow=narrow[0]|narrow[1];
lf_select #(.N(2)) sel(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={(grant[0]&&qw[120])|(grant[1]&&qw[121]),selected_narrow,({256{grant[0]}}&qd[120])|({256{grant[1]}}&qd[121])};end
 assign gv[115]=valid;assign gd[115]=hold;end
assign gv[116]=fxv[58];assign fxr[58]=gr[116];assign gd[116]={1'b0,fxd[58*106+:106],256'b0};
begin:req117
 wire[1:0]eligible={qv[205],fxv[59]};wire[1:0]grant;wire any;wire accept=!gv[117]||gr[117];reg valid;reg[362:0]hold;
 lf_select #(.N(2)) select_(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 wire[105:0]selected_narrow=(fxd[59*106+:106]&{106{grant[0]}})|({ql[205],qi[205]}&{106{grant[1]}});
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={grant[1]&&qw[157],selected_narrow,qd[157]&{256{grant[1]}}};end
 assign gv[117]=valid;assign gd[117]=hold;assign fxr[59]=accept&&grant[0];end
begin:req118
wire [1:0] eligible,grant;wire any;wire accept=!gv[118]||gr[118]; reg [362:0] hold;reg valid;wire [105:0] narrow[2];wire [105:0] selected_narrow;
assign eligible[0]=qv[106];
assign narrow[0]={106{grant[0]}}&{ql[106],qi[106]};
assign eligible[1]=qv[107];
assign narrow[1]={106{grant[1]}}&{ql[107],qi[107]};
assign selected_narrow=narrow[0]|narrow[1];
lf_select #(.N(2)) sel(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={(grant[0]&&qw[58])|(grant[1]&&qw[59]),selected_narrow,({256{grant[0]}}&qd[58])|({256{grant[1]}}&qd[59])};end
 assign gv[118]=valid;assign gd[118]=hold;end
begin:req119
wire [1:0] eligible,grant;wire any;wire accept=!gv[119]||gr[119]; reg [362:0] hold;reg valid;wire [105:0] narrow[2];wire [105:0] selected_narrow;
assign eligible[0]=qv[170];
assign narrow[0]={106{grant[0]}}&{ql[170],qi[170]};
assign eligible[1]=qv[171];
assign narrow[1]={106{grant[1]}}&{ql[171],qi[171]};
assign selected_narrow=narrow[0]|narrow[1];
lf_select #(.N(2)) sel(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={(grant[0]&&qw[122])|(grant[1]&&qw[123]),selected_narrow,({256{grant[0]}}&qd[122])|({256{grant[1]}}&qd[123])};end
 assign gv[119]=valid;assign gd[119]=hold;end
assign gv[120]=fxv[60];assign fxr[60]=gr[120];assign gd[120]={1'b0,fxd[60*106+:106],256'b0};
begin:req121
 wire[1:0]eligible={qv[206],fxv[61]};wire[1:0]grant;wire any;wire accept=!gv[121]||gr[121];reg valid;reg[362:0]hold;
 lf_select #(.N(2)) select_(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 wire[105:0]selected_narrow=(fxd[61*106+:106]&{106{grant[0]}})|({ql[206],qi[206]}&{106{grant[1]}});
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={grant[1]&&qw[158],selected_narrow,qd[158]&{256{grant[1]}}};end
 assign gv[121]=valid;assign gd[121]=hold;assign fxr[61]=accept&&grant[0];end
begin:req122
wire [1:0] eligible,grant;wire any;wire accept=!gv[122]||gr[122]; reg [362:0] hold;reg valid;wire [105:0] narrow[2];wire [105:0] selected_narrow;
assign eligible[0]=qv[108];
assign narrow[0]={106{grant[0]}}&{ql[108],qi[108]};
assign eligible[1]=qv[109];
assign narrow[1]={106{grant[1]}}&{ql[109],qi[109]};
assign selected_narrow=narrow[0]|narrow[1];
lf_select #(.N(2)) sel(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={(grant[0]&&qw[60])|(grant[1]&&qw[61]),selected_narrow,({256{grant[0]}}&qd[60])|({256{grant[1]}}&qd[61])};end
 assign gv[122]=valid;assign gd[122]=hold;end
begin:req123
wire [1:0] eligible,grant;wire any;wire accept=!gv[123]||gr[123]; reg [362:0] hold;reg valid;wire [105:0] narrow[2];wire [105:0] selected_narrow;
assign eligible[0]=qv[172];
assign narrow[0]={106{grant[0]}}&{ql[172],qi[172]};
assign eligible[1]=qv[173];
assign narrow[1]={106{grant[1]}}&{ql[173],qi[173]};
assign selected_narrow=narrow[0]|narrow[1];
lf_select #(.N(2)) sel(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={(grant[0]&&qw[124])|(grant[1]&&qw[125]),selected_narrow,({256{grant[0]}}&qd[124])|({256{grant[1]}}&qd[125])};end
 assign gv[123]=valid;assign gd[123]=hold;end
assign gv[124]=fxv[62];assign fxr[62]=gr[124];assign gd[124]={1'b0,fxd[62*106+:106],256'b0};
begin:req125
 wire[1:0]eligible={qv[207],fxv[63]};wire[1:0]grant;wire any;wire accept=!gv[125]||gr[125];reg valid;reg[362:0]hold;
 lf_select #(.N(2)) select_(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 wire[105:0]selected_narrow=(fxd[63*106+:106]&{106{grant[0]}})|({ql[207],qi[207]}&{106{grant[1]}});
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={grant[1]&&qw[159],selected_narrow,qd[159]&{256{grant[1]}}};end
 assign gv[125]=valid;assign gd[125]=hold;assign fxr[63]=accept&&grant[0];end
begin:req126
wire [1:0] eligible,grant;wire any;wire accept=!gv[126]||gr[126]; reg [362:0] hold;reg valid;wire [105:0] narrow[2];wire [105:0] selected_narrow;
assign eligible[0]=qv[110];
assign narrow[0]={106{grant[0]}}&{ql[110],qi[110]};
assign eligible[1]=qv[111];
assign narrow[1]={106{grant[1]}}&{ql[111],qi[111]};
assign selected_narrow=narrow[0]|narrow[1];
lf_select #(.N(2)) sel(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={(grant[0]&&qw[62])|(grant[1]&&qw[63]),selected_narrow,({256{grant[0]}}&qd[62])|({256{grant[1]}}&qd[63])};end
 assign gv[126]=valid;assign gd[126]=hold;end
begin:req127
wire [1:0] eligible,grant;wire any;wire accept=!gv[127]||gr[127]; reg [362:0] hold;reg valid;wire [105:0] narrow[2];wire [105:0] selected_narrow;
assign eligible[0]=qv[174];
assign narrow[0]={106{grant[0]}}&{ql[174],qi[174]};
assign eligible[1]=qv[175];
assign narrow[1]={106{grant[1]}}&{ql[175],qi[175]};
assign selected_narrow=narrow[0]|narrow[1];
lf_select #(.N(2)) sel(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={(grant[0]&&qw[126])|(grant[1]&&qw[127]),selected_narrow,({256{grant[0]}}&qd[126])|({256{grant[1]}}&qd[127])};end
 assign gv[127]=valid;assign gd[127]=hold;end
















































assign qr[48]=(req2.accept&&req2.grant[0]);
assign qr[49]=(req2.accept&&req2.grant[1]);
assign qr[50]=(req6.accept&&req6.grant[0]);
assign qr[51]=(req6.accept&&req6.grant[1]);
assign qr[52]=(req10.accept&&req10.grant[0]);
assign qr[53]=(req10.accept&&req10.grant[1]);
assign qr[54]=(req14.accept&&req14.grant[0]);
assign qr[55]=(req14.accept&&req14.grant[1]);
assign qr[56]=(req18.accept&&req18.grant[0]);
assign qr[57]=(req18.accept&&req18.grant[1]);
assign qr[58]=(req22.accept&&req22.grant[0]);
assign qr[59]=(req22.accept&&req22.grant[1]);
assign qr[60]=(req26.accept&&req26.grant[0]);
assign qr[61]=(req26.accept&&req26.grant[1]);
assign qr[62]=(req30.accept&&req30.grant[0]);
assign qr[63]=(req30.accept&&req30.grant[1]);
assign qr[64]=(req34.accept&&req34.grant[0]);
assign qr[65]=(req34.accept&&req34.grant[1]);
assign qr[66]=(req38.accept&&req38.grant[0]);
assign qr[67]=(req38.accept&&req38.grant[1]);
assign qr[68]=(req42.accept&&req42.grant[0]);
assign qr[69]=(req42.accept&&req42.grant[1]);
assign qr[70]=(req46.accept&&req46.grant[0]);
assign qr[71]=(req46.accept&&req46.grant[1]);
assign qr[72]=(req50.accept&&req50.grant[0]);
assign qr[73]=(req50.accept&&req50.grant[1]);
assign qr[74]=(req54.accept&&req54.grant[0]);
assign qr[75]=(req54.accept&&req54.grant[1]);
assign qr[76]=(req58.accept&&req58.grant[0]);
assign qr[77]=(req58.accept&&req58.grant[1]);
assign qr[78]=(req62.accept&&req62.grant[0]);
assign qr[79]=(req62.accept&&req62.grant[1]);
assign qr[80]=(req66.accept&&req66.grant[0]);
assign qr[81]=(req66.accept&&req66.grant[1]);
assign qr[82]=(req70.accept&&req70.grant[0]);
assign qr[83]=(req70.accept&&req70.grant[1]);
assign qr[84]=(req74.accept&&req74.grant[0]);
assign qr[85]=(req74.accept&&req74.grant[1]);
assign qr[86]=(req78.accept&&req78.grant[0]);
assign qr[87]=(req78.accept&&req78.grant[1]);
assign qr[88]=(req82.accept&&req82.grant[0]);
assign qr[89]=(req82.accept&&req82.grant[1]);
assign qr[90]=(req86.accept&&req86.grant[0]);
assign qr[91]=(req86.accept&&req86.grant[1]);
assign qr[92]=(req90.accept&&req90.grant[0]);
assign qr[93]=(req90.accept&&req90.grant[1]);
assign qr[94]=(req94.accept&&req94.grant[0]);
assign qr[95]=(req94.accept&&req94.grant[1]);
assign qr[96]=(req98.accept&&req98.grant[0]);
assign qr[97]=(req98.accept&&req98.grant[1]);
assign qr[98]=(req102.accept&&req102.grant[0]);
assign qr[99]=(req102.accept&&req102.grant[1]);
assign qr[100]=(req106.accept&&req106.grant[0]);
assign qr[101]=(req106.accept&&req106.grant[1]);
assign qr[102]=(req110.accept&&req110.grant[0]);
assign qr[103]=(req110.accept&&req110.grant[1]);
assign qr[104]=(req114.accept&&req114.grant[0]);
assign qr[105]=(req114.accept&&req114.grant[1]);
assign qr[106]=(req118.accept&&req118.grant[0]);
assign qr[107]=(req118.accept&&req118.grant[1]);
assign qr[108]=(req122.accept&&req122.grant[0]);
assign qr[109]=(req122.accept&&req122.grant[1]);
assign qr[110]=(req126.accept&&req126.grant[0]);
assign qr[111]=(req126.accept&&req126.grant[1]);
assign qr[112]=(req3.accept&&req3.grant[0]);
assign qr[113]=(req3.accept&&req3.grant[1]);
assign qr[114]=(req7.accept&&req7.grant[0]);
assign qr[115]=(req7.accept&&req7.grant[1]);
assign qr[116]=(req11.accept&&req11.grant[0]);
assign qr[117]=(req11.accept&&req11.grant[1]);
assign qr[118]=(req15.accept&&req15.grant[0]);
assign qr[119]=(req15.accept&&req15.grant[1]);
assign qr[120]=(req19.accept&&req19.grant[0]);
assign qr[121]=(req19.accept&&req19.grant[1]);
assign qr[122]=(req23.accept&&req23.grant[0]);
assign qr[123]=(req23.accept&&req23.grant[1]);
assign qr[124]=(req27.accept&&req27.grant[0]);
assign qr[125]=(req27.accept&&req27.grant[1]);
assign qr[126]=(req31.accept&&req31.grant[0]);
assign qr[127]=(req31.accept&&req31.grant[1]);
assign qr[128]=(req35.accept&&req35.grant[0]);
assign qr[129]=(req35.accept&&req35.grant[1]);
assign qr[130]=(req39.accept&&req39.grant[0]);
assign qr[131]=(req39.accept&&req39.grant[1]);
assign qr[132]=(req43.accept&&req43.grant[0]);
assign qr[133]=(req43.accept&&req43.grant[1]);
assign qr[134]=(req47.accept&&req47.grant[0]);
assign qr[135]=(req47.accept&&req47.grant[1]);
assign qr[136]=(req51.accept&&req51.grant[0]);
assign qr[137]=(req51.accept&&req51.grant[1]);
assign qr[138]=(req55.accept&&req55.grant[0]);
assign qr[139]=(req55.accept&&req55.grant[1]);
assign qr[140]=(req59.accept&&req59.grant[0]);
assign qr[141]=(req59.accept&&req59.grant[1]);
assign qr[142]=(req63.accept&&req63.grant[0]);
assign qr[143]=(req63.accept&&req63.grant[1]);
assign qr[144]=(req67.accept&&req67.grant[0]);
assign qr[145]=(req67.accept&&req67.grant[1]);
assign qr[146]=(req71.accept&&req71.grant[0]);
assign qr[147]=(req71.accept&&req71.grant[1]);
assign qr[148]=(req75.accept&&req75.grant[0]);
assign qr[149]=(req75.accept&&req75.grant[1]);
assign qr[150]=(req79.accept&&req79.grant[0]);
assign qr[151]=(req79.accept&&req79.grant[1]);
assign qr[152]=(req83.accept&&req83.grant[0]);
assign qr[153]=(req83.accept&&req83.grant[1]);
assign qr[154]=(req87.accept&&req87.grant[0]);
assign qr[155]=(req87.accept&&req87.grant[1]);
assign qr[156]=(req91.accept&&req91.grant[0]);
assign qr[157]=(req91.accept&&req91.grant[1]);
assign qr[158]=(req95.accept&&req95.grant[0]);
assign qr[159]=(req95.accept&&req95.grant[1]);
assign qr[160]=(req99.accept&&req99.grant[0]);
assign qr[161]=(req99.accept&&req99.grant[1]);
assign qr[162]=(req103.accept&&req103.grant[0]);
assign qr[163]=(req103.accept&&req103.grant[1]);
assign qr[164]=(req107.accept&&req107.grant[0]);
assign qr[165]=(req107.accept&&req107.grant[1]);
assign qr[166]=(req111.accept&&req111.grant[0]);
assign qr[167]=(req111.accept&&req111.grant[1]);
assign qr[168]=(req115.accept&&req115.grant[0]);
assign qr[169]=(req115.accept&&req115.grant[1]);
assign qr[170]=(req119.accept&&req119.grant[0]);
assign qr[171]=(req119.accept&&req119.grant[1]);
assign qr[172]=(req123.accept&&req123.grant[0]);
assign qr[173]=(req123.accept&&req123.grant[1]);
assign qr[174]=(req127.accept&&req127.grant[0]);
assign qr[175]=(req127.accept&&req127.grant[1]);
assign qr[176]=(req1.accept&&req1.grant[1]);
assign qr[177]=(req5.accept&&req5.grant[1]);
assign qr[178]=(req9.accept&&req9.grant[1]);
assign qr[179]=(req13.accept&&req13.grant[1]);
assign qr[180]=(req17.accept&&req17.grant[1]);
assign qr[181]=(req21.accept&&req21.grant[1]);
assign qr[182]=(req25.accept&&req25.grant[1]);
assign qr[183]=(req29.accept&&req29.grant[1]);
assign qr[184]=(req33.accept&&req33.grant[1]);
assign qr[185]=(req37.accept&&req37.grant[1]);
assign qr[186]=(req41.accept&&req41.grant[1]);
assign qr[187]=(req45.accept&&req45.grant[1]);
assign qr[188]=(req49.accept&&req49.grant[1]);
assign qr[189]=(req53.accept&&req53.grant[1]);
assign qr[190]=(req57.accept&&req57.grant[1]);
assign qr[191]=(req61.accept&&req61.grant[1]);
assign qr[192]=(req65.accept&&req65.grant[1]);
assign qr[193]=(req69.accept&&req69.grant[1]);
assign qr[194]=(req73.accept&&req73.grant[1]);
assign qr[195]=(req77.accept&&req77.grant[1]);
assign qr[196]=(req81.accept&&req81.grant[1]);
assign qr[197]=(req85.accept&&req85.grant[1]);
assign qr[198]=(req89.accept&&req89.grant[1]);
assign qr[199]=(req93.accept&&req93.grant[1]);
assign qr[200]=(req97.accept&&req97.grant[1]);
assign qr[201]=(req101.accept&&req101.grant[1]);
assign qr[202]=(req105.accept&&req105.grant[1]);
assign qr[203]=(req109.accept&&req109.grant[1]);
assign qr[204]=(req113.accept&&req113.grant[1]);
assign qr[205]=(req117.accept&&req117.grant[1]);
assign qr[206]=(req121.accept&&req121.grant[1]);
assign qr[207]=(req125.accept&&req125.grant[1]);
begin:port0
 wire [3:0] tw;wire [127:0] tl;wire [4*74-1:0] ti,ri_;wire [1023:0] td,trd;wire[7:0] rs;
 for(genvar c=0;c<4;c=c+1)begin:client
 assign {tw[c],tl[c*32+:32],ti[c*74+:74],td[c*256+:256]}=gd[0+c];
 assign dest[0+c]=ri_[c*74+68+:6];
 assign bd[0+c]={rs[c*2+:2],ri_[c*74+:74],trd[c*256+:256]};
 end
 wire pv,pr,pw,sv2,sr2;wire[31:0] pl;wire[4:0] pt,st;wire[255:0] pd,sd2;wire[1:0] ss2;
 lf_tagged_port #(.OWNER_ID(0),.ID_W(74)) fabric(.clk,.reset,.cv(gv[0+:4]),.cr(gr[0+:4]),.cw(tw),.cl(tl),.cid(ti),.cd(td),.rv(bv[0+:4]),.rr(br[0+:4]),.rid(ri_),.rd(trd),.rstatus(rs),.mv(pv),.mr(pr),.mw(pw),.ml(pl),.mtag(pt),.md(pd),.sv(sv2),.sr(sr2),.stag(st),.sd(sd2),.sstatus(ss2),.error(port_error[0]),.idle(),.credits_used(),.peak_credits(),.client_accepted(),.physical_issued(),.physical_returned(),.client_returned());
 lf_fifo2 #(.WIDTH(294)) request_slice(.clk,.reset,.iv(pv),.ir(pr),.idata({pw,pl,pt,pd}),.ov(mv[0]),.ordy(mr[0]),.odata({mw[0],ml[0+:32],mtag[0+:5],md[0+:256]}));
 lf_fifo2 #(.WIDTH(263)) response_slice(.clk,.reset,.iv(sv[0]),.ir(sr[0]),.idata({sstatus[0+:2],stag[0+:5],sd[0+:256]}),.ov(sv2),.ordy(sr2),.odata({ss2,st,sd2}));
 end
begin:port1
 wire [3:0] tw;wire [127:0] tl;wire [4*74-1:0] ti,ri_;wire [1023:0] td,trd;wire[7:0] rs;
 for(genvar c=0;c<4;c=c+1)begin:client
 assign {tw[c],tl[c*32+:32],ti[c*74+:74],td[c*256+:256]}=gd[4+c];
 assign dest[4+c]=ri_[c*74+68+:6];
 assign bd[4+c]={rs[c*2+:2],ri_[c*74+:74],trd[c*256+:256]};
 end
 wire pv,pr,pw,sv2,sr2;wire[31:0] pl;wire[4:0] pt,st;wire[255:0] pd,sd2;wire[1:0] ss2;
 lf_tagged_port #(.OWNER_ID(1),.ID_W(74)) fabric(.clk,.reset,.cv(gv[4+:4]),.cr(gr[4+:4]),.cw(tw),.cl(tl),.cid(ti),.cd(td),.rv(bv[4+:4]),.rr(br[4+:4]),.rid(ri_),.rd(trd),.rstatus(rs),.mv(pv),.mr(pr),.mw(pw),.ml(pl),.mtag(pt),.md(pd),.sv(sv2),.sr(sr2),.stag(st),.sd(sd2),.sstatus(ss2),.error(port_error[1]),.idle(),.credits_used(),.peak_credits(),.client_accepted(),.physical_issued(),.physical_returned(),.client_returned());
 lf_fifo2 #(.WIDTH(294)) request_slice(.clk,.reset,.iv(pv),.ir(pr),.idata({pw,pl,pt,pd}),.ov(mv[1]),.ordy(mr[1]),.odata({mw[1],ml[32+:32],mtag[5+:5],md[256+:256]}));
 lf_fifo2 #(.WIDTH(263)) response_slice(.clk,.reset,.iv(sv[1]),.ir(sr[1]),.idata({sstatus[2+:2],stag[5+:5],sd[256+:256]}),.ov(sv2),.ordy(sr2),.odata({ss2,st,sd2}));
 end
begin:port2
 wire [3:0] tw;wire [127:0] tl;wire [4*74-1:0] ti,ri_;wire [1023:0] td,trd;wire[7:0] rs;
 for(genvar c=0;c<4;c=c+1)begin:client
 assign {tw[c],tl[c*32+:32],ti[c*74+:74],td[c*256+:256]}=gd[8+c];
 assign dest[8+c]=ri_[c*74+68+:6];
 assign bd[8+c]={rs[c*2+:2],ri_[c*74+:74],trd[c*256+:256]};
 end
 wire pv,pr,pw,sv2,sr2;wire[31:0] pl;wire[4:0] pt,st;wire[255:0] pd,sd2;wire[1:0] ss2;
 lf_tagged_port #(.OWNER_ID(2),.ID_W(74)) fabric(.clk,.reset,.cv(gv[8+:4]),.cr(gr[8+:4]),.cw(tw),.cl(tl),.cid(ti),.cd(td),.rv(bv[8+:4]),.rr(br[8+:4]),.rid(ri_),.rd(trd),.rstatus(rs),.mv(pv),.mr(pr),.mw(pw),.ml(pl),.mtag(pt),.md(pd),.sv(sv2),.sr(sr2),.stag(st),.sd(sd2),.sstatus(ss2),.error(port_error[2]),.idle(),.credits_used(),.peak_credits(),.client_accepted(),.physical_issued(),.physical_returned(),.client_returned());
 lf_fifo2 #(.WIDTH(294)) request_slice(.clk,.reset,.iv(pv),.ir(pr),.idata({pw,pl,pt,pd}),.ov(mv[2]),.ordy(mr[2]),.odata({mw[2],ml[64+:32],mtag[10+:5],md[512+:256]}));
 lf_fifo2 #(.WIDTH(263)) response_slice(.clk,.reset,.iv(sv[2]),.ir(sr[2]),.idata({sstatus[4+:2],stag[10+:5],sd[512+:256]}),.ov(sv2),.ordy(sr2),.odata({ss2,st,sd2}));
 end
begin:port3
 wire [3:0] tw;wire [127:0] tl;wire [4*74-1:0] ti,ri_;wire [1023:0] td,trd;wire[7:0] rs;
 for(genvar c=0;c<4;c=c+1)begin:client
 assign {tw[c],tl[c*32+:32],ti[c*74+:74],td[c*256+:256]}=gd[12+c];
 assign dest[12+c]=ri_[c*74+68+:6];
 assign bd[12+c]={rs[c*2+:2],ri_[c*74+:74],trd[c*256+:256]};
 end
 wire pv,pr,pw,sv2,sr2;wire[31:0] pl;wire[4:0] pt,st;wire[255:0] pd,sd2;wire[1:0] ss2;
 lf_tagged_port #(.OWNER_ID(3),.ID_W(74)) fabric(.clk,.reset,.cv(gv[12+:4]),.cr(gr[12+:4]),.cw(tw),.cl(tl),.cid(ti),.cd(td),.rv(bv[12+:4]),.rr(br[12+:4]),.rid(ri_),.rd(trd),.rstatus(rs),.mv(pv),.mr(pr),.mw(pw),.ml(pl),.mtag(pt),.md(pd),.sv(sv2),.sr(sr2),.stag(st),.sd(sd2),.sstatus(ss2),.error(port_error[3]),.idle(),.credits_used(),.peak_credits(),.client_accepted(),.physical_issued(),.physical_returned(),.client_returned());
 lf_fifo2 #(.WIDTH(294)) request_slice(.clk,.reset,.iv(pv),.ir(pr),.idata({pw,pl,pt,pd}),.ov(mv[3]),.ordy(mr[3]),.odata({mw[3],ml[96+:32],mtag[15+:5],md[768+:256]}));
 lf_fifo2 #(.WIDTH(263)) response_slice(.clk,.reset,.iv(sv[3]),.ir(sr[3]),.idata({sstatus[6+:2],stag[15+:5],sd[768+:256]}),.ov(sv2),.ordy(sr2),.odata({ss2,st,sd2}));
 end
begin:port4
 wire [3:0] tw;wire [127:0] tl;wire [4*74-1:0] ti,ri_;wire [1023:0] td,trd;wire[7:0] rs;
 for(genvar c=0;c<4;c=c+1)begin:client
 assign {tw[c],tl[c*32+:32],ti[c*74+:74],td[c*256+:256]}=gd[16+c];
 assign dest[16+c]=ri_[c*74+68+:6];
 assign bd[16+c]={rs[c*2+:2],ri_[c*74+:74],trd[c*256+:256]};
 end
 wire pv,pr,pw,sv2,sr2;wire[31:0] pl;wire[4:0] pt,st;wire[255:0] pd,sd2;wire[1:0] ss2;
 lf_tagged_port #(.OWNER_ID(4),.ID_W(74)) fabric(.clk,.reset,.cv(gv[16+:4]),.cr(gr[16+:4]),.cw(tw),.cl(tl),.cid(ti),.cd(td),.rv(bv[16+:4]),.rr(br[16+:4]),.rid(ri_),.rd(trd),.rstatus(rs),.mv(pv),.mr(pr),.mw(pw),.ml(pl),.mtag(pt),.md(pd),.sv(sv2),.sr(sr2),.stag(st),.sd(sd2),.sstatus(ss2),.error(port_error[4]),.idle(),.credits_used(),.peak_credits(),.client_accepted(),.physical_issued(),.physical_returned(),.client_returned());
 lf_fifo2 #(.WIDTH(294)) request_slice(.clk,.reset,.iv(pv),.ir(pr),.idata({pw,pl,pt,pd}),.ov(mv[4]),.ordy(mr[4]),.odata({mw[4],ml[128+:32],mtag[20+:5],md[1024+:256]}));
 lf_fifo2 #(.WIDTH(263)) response_slice(.clk,.reset,.iv(sv[4]),.ir(sr[4]),.idata({sstatus[8+:2],stag[20+:5],sd[1024+:256]}),.ov(sv2),.ordy(sr2),.odata({ss2,st,sd2}));
 end
begin:port5
 wire [3:0] tw;wire [127:0] tl;wire [4*74-1:0] ti,ri_;wire [1023:0] td,trd;wire[7:0] rs;
 for(genvar c=0;c<4;c=c+1)begin:client
 assign {tw[c],tl[c*32+:32],ti[c*74+:74],td[c*256+:256]}=gd[20+c];
 assign dest[20+c]=ri_[c*74+68+:6];
 assign bd[20+c]={rs[c*2+:2],ri_[c*74+:74],trd[c*256+:256]};
 end
 wire pv,pr,pw,sv2,sr2;wire[31:0] pl;wire[4:0] pt,st;wire[255:0] pd,sd2;wire[1:0] ss2;
 lf_tagged_port #(.OWNER_ID(5),.ID_W(74)) fabric(.clk,.reset,.cv(gv[20+:4]),.cr(gr[20+:4]),.cw(tw),.cl(tl),.cid(ti),.cd(td),.rv(bv[20+:4]),.rr(br[20+:4]),.rid(ri_),.rd(trd),.rstatus(rs),.mv(pv),.mr(pr),.mw(pw),.ml(pl),.mtag(pt),.md(pd),.sv(sv2),.sr(sr2),.stag(st),.sd(sd2),.sstatus(ss2),.error(port_error[5]),.idle(),.credits_used(),.peak_credits(),.client_accepted(),.physical_issued(),.physical_returned(),.client_returned());
 lf_fifo2 #(.WIDTH(294)) request_slice(.clk,.reset,.iv(pv),.ir(pr),.idata({pw,pl,pt,pd}),.ov(mv[5]),.ordy(mr[5]),.odata({mw[5],ml[160+:32],mtag[25+:5],md[1280+:256]}));
 lf_fifo2 #(.WIDTH(263)) response_slice(.clk,.reset,.iv(sv[5]),.ir(sr[5]),.idata({sstatus[10+:2],stag[25+:5],sd[1280+:256]}),.ov(sv2),.ordy(sr2),.odata({ss2,st,sd2}));
 end
begin:port6
 wire [3:0] tw;wire [127:0] tl;wire [4*74-1:0] ti,ri_;wire [1023:0] td,trd;wire[7:0] rs;
 for(genvar c=0;c<4;c=c+1)begin:client
 assign {tw[c],tl[c*32+:32],ti[c*74+:74],td[c*256+:256]}=gd[24+c];
 assign dest[24+c]=ri_[c*74+68+:6];
 assign bd[24+c]={rs[c*2+:2],ri_[c*74+:74],trd[c*256+:256]};
 end
 wire pv,pr,pw,sv2,sr2;wire[31:0] pl;wire[4:0] pt,st;wire[255:0] pd,sd2;wire[1:0] ss2;
 lf_tagged_port #(.OWNER_ID(6),.ID_W(74)) fabric(.clk,.reset,.cv(gv[24+:4]),.cr(gr[24+:4]),.cw(tw),.cl(tl),.cid(ti),.cd(td),.rv(bv[24+:4]),.rr(br[24+:4]),.rid(ri_),.rd(trd),.rstatus(rs),.mv(pv),.mr(pr),.mw(pw),.ml(pl),.mtag(pt),.md(pd),.sv(sv2),.sr(sr2),.stag(st),.sd(sd2),.sstatus(ss2),.error(port_error[6]),.idle(),.credits_used(),.peak_credits(),.client_accepted(),.physical_issued(),.physical_returned(),.client_returned());
 lf_fifo2 #(.WIDTH(294)) request_slice(.clk,.reset,.iv(pv),.ir(pr),.idata({pw,pl,pt,pd}),.ov(mv[6]),.ordy(mr[6]),.odata({mw[6],ml[192+:32],mtag[30+:5],md[1536+:256]}));
 lf_fifo2 #(.WIDTH(263)) response_slice(.clk,.reset,.iv(sv[6]),.ir(sr[6]),.idata({sstatus[12+:2],stag[30+:5],sd[1536+:256]}),.ov(sv2),.ordy(sr2),.odata({ss2,st,sd2}));
 end
begin:port7
 wire [3:0] tw;wire [127:0] tl;wire [4*74-1:0] ti,ri_;wire [1023:0] td,trd;wire[7:0] rs;
 for(genvar c=0;c<4;c=c+1)begin:client
 assign {tw[c],tl[c*32+:32],ti[c*74+:74],td[c*256+:256]}=gd[28+c];
 assign dest[28+c]=ri_[c*74+68+:6];
 assign bd[28+c]={rs[c*2+:2],ri_[c*74+:74],trd[c*256+:256]};
 end
 wire pv,pr,pw,sv2,sr2;wire[31:0] pl;wire[4:0] pt,st;wire[255:0] pd,sd2;wire[1:0] ss2;
 lf_tagged_port #(.OWNER_ID(7),.ID_W(74)) fabric(.clk,.reset,.cv(gv[28+:4]),.cr(gr[28+:4]),.cw(tw),.cl(tl),.cid(ti),.cd(td),.rv(bv[28+:4]),.rr(br[28+:4]),.rid(ri_),.rd(trd),.rstatus(rs),.mv(pv),.mr(pr),.mw(pw),.ml(pl),.mtag(pt),.md(pd),.sv(sv2),.sr(sr2),.stag(st),.sd(sd2),.sstatus(ss2),.error(port_error[7]),.idle(),.credits_used(),.peak_credits(),.client_accepted(),.physical_issued(),.physical_returned(),.client_returned());
 lf_fifo2 #(.WIDTH(294)) request_slice(.clk,.reset,.iv(pv),.ir(pr),.idata({pw,pl,pt,pd}),.ov(mv[7]),.ordy(mr[7]),.odata({mw[7],ml[224+:32],mtag[35+:5],md[1792+:256]}));
 lf_fifo2 #(.WIDTH(263)) response_slice(.clk,.reset,.iv(sv[7]),.ir(sr[7]),.idata({sstatus[14+:2],stag[35+:5],sd[1792+:256]}),.ov(sv2),.ordy(sr2),.odata({ss2,st,sd2}));
 end
begin:port8
 wire [3:0] tw;wire [127:0] tl;wire [4*74-1:0] ti,ri_;wire [1023:0] td,trd;wire[7:0] rs;
 for(genvar c=0;c<4;c=c+1)begin:client
 assign {tw[c],tl[c*32+:32],ti[c*74+:74],td[c*256+:256]}=gd[32+c];
 assign dest[32+c]=ri_[c*74+68+:6];
 assign bd[32+c]={rs[c*2+:2],ri_[c*74+:74],trd[c*256+:256]};
 end
 wire pv,pr,pw,sv2,sr2;wire[31:0] pl;wire[4:0] pt,st;wire[255:0] pd,sd2;wire[1:0] ss2;
 lf_tagged_port #(.OWNER_ID(8),.ID_W(74)) fabric(.clk,.reset,.cv(gv[32+:4]),.cr(gr[32+:4]),.cw(tw),.cl(tl),.cid(ti),.cd(td),.rv(bv[32+:4]),.rr(br[32+:4]),.rid(ri_),.rd(trd),.rstatus(rs),.mv(pv),.mr(pr),.mw(pw),.ml(pl),.mtag(pt),.md(pd),.sv(sv2),.sr(sr2),.stag(st),.sd(sd2),.sstatus(ss2),.error(port_error[8]),.idle(),.credits_used(),.peak_credits(),.client_accepted(),.physical_issued(),.physical_returned(),.client_returned());
 lf_fifo2 #(.WIDTH(294)) request_slice(.clk,.reset,.iv(pv),.ir(pr),.idata({pw,pl,pt,pd}),.ov(mv[8]),.ordy(mr[8]),.odata({mw[8],ml[256+:32],mtag[40+:5],md[2048+:256]}));
 lf_fifo2 #(.WIDTH(263)) response_slice(.clk,.reset,.iv(sv[8]),.ir(sr[8]),.idata({sstatus[16+:2],stag[40+:5],sd[2048+:256]}),.ov(sv2),.ordy(sr2),.odata({ss2,st,sd2}));
 end
begin:port9
 wire [3:0] tw;wire [127:0] tl;wire [4*74-1:0] ti,ri_;wire [1023:0] td,trd;wire[7:0] rs;
 for(genvar c=0;c<4;c=c+1)begin:client
 assign {tw[c],tl[c*32+:32],ti[c*74+:74],td[c*256+:256]}=gd[36+c];
 assign dest[36+c]=ri_[c*74+68+:6];
 assign bd[36+c]={rs[c*2+:2],ri_[c*74+:74],trd[c*256+:256]};
 end
 wire pv,pr,pw,sv2,sr2;wire[31:0] pl;wire[4:0] pt,st;wire[255:0] pd,sd2;wire[1:0] ss2;
 lf_tagged_port #(.OWNER_ID(9),.ID_W(74)) fabric(.clk,.reset,.cv(gv[36+:4]),.cr(gr[36+:4]),.cw(tw),.cl(tl),.cid(ti),.cd(td),.rv(bv[36+:4]),.rr(br[36+:4]),.rid(ri_),.rd(trd),.rstatus(rs),.mv(pv),.mr(pr),.mw(pw),.ml(pl),.mtag(pt),.md(pd),.sv(sv2),.sr(sr2),.stag(st),.sd(sd2),.sstatus(ss2),.error(port_error[9]),.idle(),.credits_used(),.peak_credits(),.client_accepted(),.physical_issued(),.physical_returned(),.client_returned());
 lf_fifo2 #(.WIDTH(294)) request_slice(.clk,.reset,.iv(pv),.ir(pr),.idata({pw,pl,pt,pd}),.ov(mv[9]),.ordy(mr[9]),.odata({mw[9],ml[288+:32],mtag[45+:5],md[2304+:256]}));
 lf_fifo2 #(.WIDTH(263)) response_slice(.clk,.reset,.iv(sv[9]),.ir(sr[9]),.idata({sstatus[18+:2],stag[45+:5],sd[2304+:256]}),.ov(sv2),.ordy(sr2),.odata({ss2,st,sd2}));
 end
begin:port10
 wire [3:0] tw;wire [127:0] tl;wire [4*74-1:0] ti,ri_;wire [1023:0] td,trd;wire[7:0] rs;
 for(genvar c=0;c<4;c=c+1)begin:client
 assign {tw[c],tl[c*32+:32],ti[c*74+:74],td[c*256+:256]}=gd[40+c];
 assign dest[40+c]=ri_[c*74+68+:6];
 assign bd[40+c]={rs[c*2+:2],ri_[c*74+:74],trd[c*256+:256]};
 end
 wire pv,pr,pw,sv2,sr2;wire[31:0] pl;wire[4:0] pt,st;wire[255:0] pd,sd2;wire[1:0] ss2;
 lf_tagged_port #(.OWNER_ID(10),.ID_W(74)) fabric(.clk,.reset,.cv(gv[40+:4]),.cr(gr[40+:4]),.cw(tw),.cl(tl),.cid(ti),.cd(td),.rv(bv[40+:4]),.rr(br[40+:4]),.rid(ri_),.rd(trd),.rstatus(rs),.mv(pv),.mr(pr),.mw(pw),.ml(pl),.mtag(pt),.md(pd),.sv(sv2),.sr(sr2),.stag(st),.sd(sd2),.sstatus(ss2),.error(port_error[10]),.idle(),.credits_used(),.peak_credits(),.client_accepted(),.physical_issued(),.physical_returned(),.client_returned());
 lf_fifo2 #(.WIDTH(294)) request_slice(.clk,.reset,.iv(pv),.ir(pr),.idata({pw,pl,pt,pd}),.ov(mv[10]),.ordy(mr[10]),.odata({mw[10],ml[320+:32],mtag[50+:5],md[2560+:256]}));
 lf_fifo2 #(.WIDTH(263)) response_slice(.clk,.reset,.iv(sv[10]),.ir(sr[10]),.idata({sstatus[20+:2],stag[50+:5],sd[2560+:256]}),.ov(sv2),.ordy(sr2),.odata({ss2,st,sd2}));
 end
begin:port11
 wire [3:0] tw;wire [127:0] tl;wire [4*74-1:0] ti,ri_;wire [1023:0] td,trd;wire[7:0] rs;
 for(genvar c=0;c<4;c=c+1)begin:client
 assign {tw[c],tl[c*32+:32],ti[c*74+:74],td[c*256+:256]}=gd[44+c];
 assign dest[44+c]=ri_[c*74+68+:6];
 assign bd[44+c]={rs[c*2+:2],ri_[c*74+:74],trd[c*256+:256]};
 end
 wire pv,pr,pw,sv2,sr2;wire[31:0] pl;wire[4:0] pt,st;wire[255:0] pd,sd2;wire[1:0] ss2;
 lf_tagged_port #(.OWNER_ID(11),.ID_W(74)) fabric(.clk,.reset,.cv(gv[44+:4]),.cr(gr[44+:4]),.cw(tw),.cl(tl),.cid(ti),.cd(td),.rv(bv[44+:4]),.rr(br[44+:4]),.rid(ri_),.rd(trd),.rstatus(rs),.mv(pv),.mr(pr),.mw(pw),.ml(pl),.mtag(pt),.md(pd),.sv(sv2),.sr(sr2),.stag(st),.sd(sd2),.sstatus(ss2),.error(port_error[11]),.idle(),.credits_used(),.peak_credits(),.client_accepted(),.physical_issued(),.physical_returned(),.client_returned());
 lf_fifo2 #(.WIDTH(294)) request_slice(.clk,.reset,.iv(pv),.ir(pr),.idata({pw,pl,pt,pd}),.ov(mv[11]),.ordy(mr[11]),.odata({mw[11],ml[352+:32],mtag[55+:5],md[2816+:256]}));
 lf_fifo2 #(.WIDTH(263)) response_slice(.clk,.reset,.iv(sv[11]),.ir(sr[11]),.idata({sstatus[22+:2],stag[55+:5],sd[2816+:256]}),.ov(sv2),.ordy(sr2),.odata({ss2,st,sd2}));
 end
begin:port12
 wire [3:0] tw;wire [127:0] tl;wire [4*74-1:0] ti,ri_;wire [1023:0] td,trd;wire[7:0] rs;
 for(genvar c=0;c<4;c=c+1)begin:client
 assign {tw[c],tl[c*32+:32],ti[c*74+:74],td[c*256+:256]}=gd[48+c];
 assign dest[48+c]=ri_[c*74+68+:6];
 assign bd[48+c]={rs[c*2+:2],ri_[c*74+:74],trd[c*256+:256]};
 end
 wire pv,pr,pw,sv2,sr2;wire[31:0] pl;wire[4:0] pt,st;wire[255:0] pd,sd2;wire[1:0] ss2;
 lf_tagged_port #(.OWNER_ID(12),.ID_W(74)) fabric(.clk,.reset,.cv(gv[48+:4]),.cr(gr[48+:4]),.cw(tw),.cl(tl),.cid(ti),.cd(td),.rv(bv[48+:4]),.rr(br[48+:4]),.rid(ri_),.rd(trd),.rstatus(rs),.mv(pv),.mr(pr),.mw(pw),.ml(pl),.mtag(pt),.md(pd),.sv(sv2),.sr(sr2),.stag(st),.sd(sd2),.sstatus(ss2),.error(port_error[12]),.idle(),.credits_used(),.peak_credits(),.client_accepted(),.physical_issued(),.physical_returned(),.client_returned());
 lf_fifo2 #(.WIDTH(294)) request_slice(.clk,.reset,.iv(pv),.ir(pr),.idata({pw,pl,pt,pd}),.ov(mv[12]),.ordy(mr[12]),.odata({mw[12],ml[384+:32],mtag[60+:5],md[3072+:256]}));
 lf_fifo2 #(.WIDTH(263)) response_slice(.clk,.reset,.iv(sv[12]),.ir(sr[12]),.idata({sstatus[24+:2],stag[60+:5],sd[3072+:256]}),.ov(sv2),.ordy(sr2),.odata({ss2,st,sd2}));
 end
begin:port13
 wire [3:0] tw;wire [127:0] tl;wire [4*74-1:0] ti,ri_;wire [1023:0] td,trd;wire[7:0] rs;
 for(genvar c=0;c<4;c=c+1)begin:client
 assign {tw[c],tl[c*32+:32],ti[c*74+:74],td[c*256+:256]}=gd[52+c];
 assign dest[52+c]=ri_[c*74+68+:6];
 assign bd[52+c]={rs[c*2+:2],ri_[c*74+:74],trd[c*256+:256]};
 end
 wire pv,pr,pw,sv2,sr2;wire[31:0] pl;wire[4:0] pt,st;wire[255:0] pd,sd2;wire[1:0] ss2;
 lf_tagged_port #(.OWNER_ID(13),.ID_W(74)) fabric(.clk,.reset,.cv(gv[52+:4]),.cr(gr[52+:4]),.cw(tw),.cl(tl),.cid(ti),.cd(td),.rv(bv[52+:4]),.rr(br[52+:4]),.rid(ri_),.rd(trd),.rstatus(rs),.mv(pv),.mr(pr),.mw(pw),.ml(pl),.mtag(pt),.md(pd),.sv(sv2),.sr(sr2),.stag(st),.sd(sd2),.sstatus(ss2),.error(port_error[13]),.idle(),.credits_used(),.peak_credits(),.client_accepted(),.physical_issued(),.physical_returned(),.client_returned());
 lf_fifo2 #(.WIDTH(294)) request_slice(.clk,.reset,.iv(pv),.ir(pr),.idata({pw,pl,pt,pd}),.ov(mv[13]),.ordy(mr[13]),.odata({mw[13],ml[416+:32],mtag[65+:5],md[3328+:256]}));
 lf_fifo2 #(.WIDTH(263)) response_slice(.clk,.reset,.iv(sv[13]),.ir(sr[13]),.idata({sstatus[26+:2],stag[65+:5],sd[3328+:256]}),.ov(sv2),.ordy(sr2),.odata({ss2,st,sd2}));
 end
begin:port14
 wire [3:0] tw;wire [127:0] tl;wire [4*74-1:0] ti,ri_;wire [1023:0] td,trd;wire[7:0] rs;
 for(genvar c=0;c<4;c=c+1)begin:client
 assign {tw[c],tl[c*32+:32],ti[c*74+:74],td[c*256+:256]}=gd[56+c];
 assign dest[56+c]=ri_[c*74+68+:6];
 assign bd[56+c]={rs[c*2+:2],ri_[c*74+:74],trd[c*256+:256]};
 end
 wire pv,pr,pw,sv2,sr2;wire[31:0] pl;wire[4:0] pt,st;wire[255:0] pd,sd2;wire[1:0] ss2;
 lf_tagged_port #(.OWNER_ID(14),.ID_W(74)) fabric(.clk,.reset,.cv(gv[56+:4]),.cr(gr[56+:4]),.cw(tw),.cl(tl),.cid(ti),.cd(td),.rv(bv[56+:4]),.rr(br[56+:4]),.rid(ri_),.rd(trd),.rstatus(rs),.mv(pv),.mr(pr),.mw(pw),.ml(pl),.mtag(pt),.md(pd),.sv(sv2),.sr(sr2),.stag(st),.sd(sd2),.sstatus(ss2),.error(port_error[14]),.idle(),.credits_used(),.peak_credits(),.client_accepted(),.physical_issued(),.physical_returned(),.client_returned());
 lf_fifo2 #(.WIDTH(294)) request_slice(.clk,.reset,.iv(pv),.ir(pr),.idata({pw,pl,pt,pd}),.ov(mv[14]),.ordy(mr[14]),.odata({mw[14],ml[448+:32],mtag[70+:5],md[3584+:256]}));
 lf_fifo2 #(.WIDTH(263)) response_slice(.clk,.reset,.iv(sv[14]),.ir(sr[14]),.idata({sstatus[28+:2],stag[70+:5],sd[3584+:256]}),.ov(sv2),.ordy(sr2),.odata({ss2,st,sd2}));
 end
begin:port15
 wire [3:0] tw;wire [127:0] tl;wire [4*74-1:0] ti,ri_;wire [1023:0] td,trd;wire[7:0] rs;
 for(genvar c=0;c<4;c=c+1)begin:client
 assign {tw[c],tl[c*32+:32],ti[c*74+:74],td[c*256+:256]}=gd[60+c];
 assign dest[60+c]=ri_[c*74+68+:6];
 assign bd[60+c]={rs[c*2+:2],ri_[c*74+:74],trd[c*256+:256]};
 end
 wire pv,pr,pw,sv2,sr2;wire[31:0] pl;wire[4:0] pt,st;wire[255:0] pd,sd2;wire[1:0] ss2;
 lf_tagged_port #(.OWNER_ID(15),.ID_W(74)) fabric(.clk,.reset,.cv(gv[60+:4]),.cr(gr[60+:4]),.cw(tw),.cl(tl),.cid(ti),.cd(td),.rv(bv[60+:4]),.rr(br[60+:4]),.rid(ri_),.rd(trd),.rstatus(rs),.mv(pv),.mr(pr),.mw(pw),.ml(pl),.mtag(pt),.md(pd),.sv(sv2),.sr(sr2),.stag(st),.sd(sd2),.sstatus(ss2),.error(port_error[15]),.idle(),.credits_used(),.peak_credits(),.client_accepted(),.physical_issued(),.physical_returned(),.client_returned());
 lf_fifo2 #(.WIDTH(294)) request_slice(.clk,.reset,.iv(pv),.ir(pr),.idata({pw,pl,pt,pd}),.ov(mv[15]),.ordy(mr[15]),.odata({mw[15],ml[480+:32],mtag[75+:5],md[3840+:256]}));
 lf_fifo2 #(.WIDTH(263)) response_slice(.clk,.reset,.iv(sv[15]),.ir(sr[15]),.idata({sstatus[30+:2],stag[75+:5],sd[3840+:256]}),.ov(sv2),.ordy(sr2),.odata({ss2,st,sd2}));
 end
begin:port16
 wire [3:0] tw;wire [127:0] tl;wire [4*74-1:0] ti,ri_;wire [1023:0] td,trd;wire[7:0] rs;
 for(genvar c=0;c<4;c=c+1)begin:client
 assign {tw[c],tl[c*32+:32],ti[c*74+:74],td[c*256+:256]}=gd[64+c];
 assign dest[64+c]=ri_[c*74+68+:6];
 assign bd[64+c]={rs[c*2+:2],ri_[c*74+:74],trd[c*256+:256]};
 end
 wire pv,pr,pw,sv2,sr2;wire[31:0] pl;wire[4:0] pt,st;wire[255:0] pd,sd2;wire[1:0] ss2;
 lf_tagged_port #(.OWNER_ID(16),.ID_W(74)) fabric(.clk,.reset,.cv(gv[64+:4]),.cr(gr[64+:4]),.cw(tw),.cl(tl),.cid(ti),.cd(td),.rv(bv[64+:4]),.rr(br[64+:4]),.rid(ri_),.rd(trd),.rstatus(rs),.mv(pv),.mr(pr),.mw(pw),.ml(pl),.mtag(pt),.md(pd),.sv(sv2),.sr(sr2),.stag(st),.sd(sd2),.sstatus(ss2),.error(port_error[16]),.idle(),.credits_used(),.peak_credits(),.client_accepted(),.physical_issued(),.physical_returned(),.client_returned());
 lf_fifo2 #(.WIDTH(294)) request_slice(.clk,.reset,.iv(pv),.ir(pr),.idata({pw,pl,pt,pd}),.ov(mv[16]),.ordy(mr[16]),.odata({mw[16],ml[512+:32],mtag[80+:5],md[4096+:256]}));
 lf_fifo2 #(.WIDTH(263)) response_slice(.clk,.reset,.iv(sv[16]),.ir(sr[16]),.idata({sstatus[32+:2],stag[80+:5],sd[4096+:256]}),.ov(sv2),.ordy(sr2),.odata({ss2,st,sd2}));
 end
begin:port17
 wire [3:0] tw;wire [127:0] tl;wire [4*74-1:0] ti,ri_;wire [1023:0] td,trd;wire[7:0] rs;
 for(genvar c=0;c<4;c=c+1)begin:client
 assign {tw[c],tl[c*32+:32],ti[c*74+:74],td[c*256+:256]}=gd[68+c];
 assign dest[68+c]=ri_[c*74+68+:6];
 assign bd[68+c]={rs[c*2+:2],ri_[c*74+:74],trd[c*256+:256]};
 end
 wire pv,pr,pw,sv2,sr2;wire[31:0] pl;wire[4:0] pt,st;wire[255:0] pd,sd2;wire[1:0] ss2;
 lf_tagged_port #(.OWNER_ID(17),.ID_W(74)) fabric(.clk,.reset,.cv(gv[68+:4]),.cr(gr[68+:4]),.cw(tw),.cl(tl),.cid(ti),.cd(td),.rv(bv[68+:4]),.rr(br[68+:4]),.rid(ri_),.rd(trd),.rstatus(rs),.mv(pv),.mr(pr),.mw(pw),.ml(pl),.mtag(pt),.md(pd),.sv(sv2),.sr(sr2),.stag(st),.sd(sd2),.sstatus(ss2),.error(port_error[17]),.idle(),.credits_used(),.peak_credits(),.client_accepted(),.physical_issued(),.physical_returned(),.client_returned());
 lf_fifo2 #(.WIDTH(294)) request_slice(.clk,.reset,.iv(pv),.ir(pr),.idata({pw,pl,pt,pd}),.ov(mv[17]),.ordy(mr[17]),.odata({mw[17],ml[544+:32],mtag[85+:5],md[4352+:256]}));
 lf_fifo2 #(.WIDTH(263)) response_slice(.clk,.reset,.iv(sv[17]),.ir(sr[17]),.idata({sstatus[34+:2],stag[85+:5],sd[4352+:256]}),.ov(sv2),.ordy(sr2),.odata({ss2,st,sd2}));
 end
begin:port18
 wire [3:0] tw;wire [127:0] tl;wire [4*74-1:0] ti,ri_;wire [1023:0] td,trd;wire[7:0] rs;
 for(genvar c=0;c<4;c=c+1)begin:client
 assign {tw[c],tl[c*32+:32],ti[c*74+:74],td[c*256+:256]}=gd[72+c];
 assign dest[72+c]=ri_[c*74+68+:6];
 assign bd[72+c]={rs[c*2+:2],ri_[c*74+:74],trd[c*256+:256]};
 end
 wire pv,pr,pw,sv2,sr2;wire[31:0] pl;wire[4:0] pt,st;wire[255:0] pd,sd2;wire[1:0] ss2;
 lf_tagged_port #(.OWNER_ID(18),.ID_W(74)) fabric(.clk,.reset,.cv(gv[72+:4]),.cr(gr[72+:4]),.cw(tw),.cl(tl),.cid(ti),.cd(td),.rv(bv[72+:4]),.rr(br[72+:4]),.rid(ri_),.rd(trd),.rstatus(rs),.mv(pv),.mr(pr),.mw(pw),.ml(pl),.mtag(pt),.md(pd),.sv(sv2),.sr(sr2),.stag(st),.sd(sd2),.sstatus(ss2),.error(port_error[18]),.idle(),.credits_used(),.peak_credits(),.client_accepted(),.physical_issued(),.physical_returned(),.client_returned());
 lf_fifo2 #(.WIDTH(294)) request_slice(.clk,.reset,.iv(pv),.ir(pr),.idata({pw,pl,pt,pd}),.ov(mv[18]),.ordy(mr[18]),.odata({mw[18],ml[576+:32],mtag[90+:5],md[4608+:256]}));
 lf_fifo2 #(.WIDTH(263)) response_slice(.clk,.reset,.iv(sv[18]),.ir(sr[18]),.idata({sstatus[36+:2],stag[90+:5],sd[4608+:256]}),.ov(sv2),.ordy(sr2),.odata({ss2,st,sd2}));
 end
begin:port19
 wire [3:0] tw;wire [127:0] tl;wire [4*74-1:0] ti,ri_;wire [1023:0] td,trd;wire[7:0] rs;
 for(genvar c=0;c<4;c=c+1)begin:client
 assign {tw[c],tl[c*32+:32],ti[c*74+:74],td[c*256+:256]}=gd[76+c];
 assign dest[76+c]=ri_[c*74+68+:6];
 assign bd[76+c]={rs[c*2+:2],ri_[c*74+:74],trd[c*256+:256]};
 end
 wire pv,pr,pw,sv2,sr2;wire[31:0] pl;wire[4:0] pt,st;wire[255:0] pd,sd2;wire[1:0] ss2;
 lf_tagged_port #(.OWNER_ID(19),.ID_W(74)) fabric(.clk,.reset,.cv(gv[76+:4]),.cr(gr[76+:4]),.cw(tw),.cl(tl),.cid(ti),.cd(td),.rv(bv[76+:4]),.rr(br[76+:4]),.rid(ri_),.rd(trd),.rstatus(rs),.mv(pv),.mr(pr),.mw(pw),.ml(pl),.mtag(pt),.md(pd),.sv(sv2),.sr(sr2),.stag(st),.sd(sd2),.sstatus(ss2),.error(port_error[19]),.idle(),.credits_used(),.peak_credits(),.client_accepted(),.physical_issued(),.physical_returned(),.client_returned());
 lf_fifo2 #(.WIDTH(294)) request_slice(.clk,.reset,.iv(pv),.ir(pr),.idata({pw,pl,pt,pd}),.ov(mv[19]),.ordy(mr[19]),.odata({mw[19],ml[608+:32],mtag[95+:5],md[4864+:256]}));
 lf_fifo2 #(.WIDTH(263)) response_slice(.clk,.reset,.iv(sv[19]),.ir(sr[19]),.idata({sstatus[38+:2],stag[95+:5],sd[4864+:256]}),.ov(sv2),.ordy(sr2),.odata({ss2,st,sd2}));
 end
begin:port20
 wire [3:0] tw;wire [127:0] tl;wire [4*74-1:0] ti,ri_;wire [1023:0] td,trd;wire[7:0] rs;
 for(genvar c=0;c<4;c=c+1)begin:client
 assign {tw[c],tl[c*32+:32],ti[c*74+:74],td[c*256+:256]}=gd[80+c];
 assign dest[80+c]=ri_[c*74+68+:6];
 assign bd[80+c]={rs[c*2+:2],ri_[c*74+:74],trd[c*256+:256]};
 end
 wire pv,pr,pw,sv2,sr2;wire[31:0] pl;wire[4:0] pt,st;wire[255:0] pd,sd2;wire[1:0] ss2;
 lf_tagged_port #(.OWNER_ID(20),.ID_W(74)) fabric(.clk,.reset,.cv(gv[80+:4]),.cr(gr[80+:4]),.cw(tw),.cl(tl),.cid(ti),.cd(td),.rv(bv[80+:4]),.rr(br[80+:4]),.rid(ri_),.rd(trd),.rstatus(rs),.mv(pv),.mr(pr),.mw(pw),.ml(pl),.mtag(pt),.md(pd),.sv(sv2),.sr(sr2),.stag(st),.sd(sd2),.sstatus(ss2),.error(port_error[20]),.idle(),.credits_used(),.peak_credits(),.client_accepted(),.physical_issued(),.physical_returned(),.client_returned());
 lf_fifo2 #(.WIDTH(294)) request_slice(.clk,.reset,.iv(pv),.ir(pr),.idata({pw,pl,pt,pd}),.ov(mv[20]),.ordy(mr[20]),.odata({mw[20],ml[640+:32],mtag[100+:5],md[5120+:256]}));
 lf_fifo2 #(.WIDTH(263)) response_slice(.clk,.reset,.iv(sv[20]),.ir(sr[20]),.idata({sstatus[40+:2],stag[100+:5],sd[5120+:256]}),.ov(sv2),.ordy(sr2),.odata({ss2,st,sd2}));
 end
begin:port21
 wire [3:0] tw;wire [127:0] tl;wire [4*74-1:0] ti,ri_;wire [1023:0] td,trd;wire[7:0] rs;
 for(genvar c=0;c<4;c=c+1)begin:client
 assign {tw[c],tl[c*32+:32],ti[c*74+:74],td[c*256+:256]}=gd[84+c];
 assign dest[84+c]=ri_[c*74+68+:6];
 assign bd[84+c]={rs[c*2+:2],ri_[c*74+:74],trd[c*256+:256]};
 end
 wire pv,pr,pw,sv2,sr2;wire[31:0] pl;wire[4:0] pt,st;wire[255:0] pd,sd2;wire[1:0] ss2;
 lf_tagged_port #(.OWNER_ID(21),.ID_W(74)) fabric(.clk,.reset,.cv(gv[84+:4]),.cr(gr[84+:4]),.cw(tw),.cl(tl),.cid(ti),.cd(td),.rv(bv[84+:4]),.rr(br[84+:4]),.rid(ri_),.rd(trd),.rstatus(rs),.mv(pv),.mr(pr),.mw(pw),.ml(pl),.mtag(pt),.md(pd),.sv(sv2),.sr(sr2),.stag(st),.sd(sd2),.sstatus(ss2),.error(port_error[21]),.idle(),.credits_used(),.peak_credits(),.client_accepted(),.physical_issued(),.physical_returned(),.client_returned());
 lf_fifo2 #(.WIDTH(294)) request_slice(.clk,.reset,.iv(pv),.ir(pr),.idata({pw,pl,pt,pd}),.ov(mv[21]),.ordy(mr[21]),.odata({mw[21],ml[672+:32],mtag[105+:5],md[5376+:256]}));
 lf_fifo2 #(.WIDTH(263)) response_slice(.clk,.reset,.iv(sv[21]),.ir(sr[21]),.idata({sstatus[42+:2],stag[105+:5],sd[5376+:256]}),.ov(sv2),.ordy(sr2),.odata({ss2,st,sd2}));
 end
begin:port22
 wire [3:0] tw;wire [127:0] tl;wire [4*74-1:0] ti,ri_;wire [1023:0] td,trd;wire[7:0] rs;
 for(genvar c=0;c<4;c=c+1)begin:client
 assign {tw[c],tl[c*32+:32],ti[c*74+:74],td[c*256+:256]}=gd[88+c];
 assign dest[88+c]=ri_[c*74+68+:6];
 assign bd[88+c]={rs[c*2+:2],ri_[c*74+:74],trd[c*256+:256]};
 end
 wire pv,pr,pw,sv2,sr2;wire[31:0] pl;wire[4:0] pt,st;wire[255:0] pd,sd2;wire[1:0] ss2;
 lf_tagged_port #(.OWNER_ID(22),.ID_W(74)) fabric(.clk,.reset,.cv(gv[88+:4]),.cr(gr[88+:4]),.cw(tw),.cl(tl),.cid(ti),.cd(td),.rv(bv[88+:4]),.rr(br[88+:4]),.rid(ri_),.rd(trd),.rstatus(rs),.mv(pv),.mr(pr),.mw(pw),.ml(pl),.mtag(pt),.md(pd),.sv(sv2),.sr(sr2),.stag(st),.sd(sd2),.sstatus(ss2),.error(port_error[22]),.idle(),.credits_used(),.peak_credits(),.client_accepted(),.physical_issued(),.physical_returned(),.client_returned());
 lf_fifo2 #(.WIDTH(294)) request_slice(.clk,.reset,.iv(pv),.ir(pr),.idata({pw,pl,pt,pd}),.ov(mv[22]),.ordy(mr[22]),.odata({mw[22],ml[704+:32],mtag[110+:5],md[5632+:256]}));
 lf_fifo2 #(.WIDTH(263)) response_slice(.clk,.reset,.iv(sv[22]),.ir(sr[22]),.idata({sstatus[44+:2],stag[110+:5],sd[5632+:256]}),.ov(sv2),.ordy(sr2),.odata({ss2,st,sd2}));
 end
begin:port23
 wire [3:0] tw;wire [127:0] tl;wire [4*74-1:0] ti,ri_;wire [1023:0] td,trd;wire[7:0] rs;
 for(genvar c=0;c<4;c=c+1)begin:client
 assign {tw[c],tl[c*32+:32],ti[c*74+:74],td[c*256+:256]}=gd[92+c];
 assign dest[92+c]=ri_[c*74+68+:6];
 assign bd[92+c]={rs[c*2+:2],ri_[c*74+:74],trd[c*256+:256]};
 end
 wire pv,pr,pw,sv2,sr2;wire[31:0] pl;wire[4:0] pt,st;wire[255:0] pd,sd2;wire[1:0] ss2;
 lf_tagged_port #(.OWNER_ID(23),.ID_W(74)) fabric(.clk,.reset,.cv(gv[92+:4]),.cr(gr[92+:4]),.cw(tw),.cl(tl),.cid(ti),.cd(td),.rv(bv[92+:4]),.rr(br[92+:4]),.rid(ri_),.rd(trd),.rstatus(rs),.mv(pv),.mr(pr),.mw(pw),.ml(pl),.mtag(pt),.md(pd),.sv(sv2),.sr(sr2),.stag(st),.sd(sd2),.sstatus(ss2),.error(port_error[23]),.idle(),.credits_used(),.peak_credits(),.client_accepted(),.physical_issued(),.physical_returned(),.client_returned());
 lf_fifo2 #(.WIDTH(294)) request_slice(.clk,.reset,.iv(pv),.ir(pr),.idata({pw,pl,pt,pd}),.ov(mv[23]),.ordy(mr[23]),.odata({mw[23],ml[736+:32],mtag[115+:5],md[5888+:256]}));
 lf_fifo2 #(.WIDTH(263)) response_slice(.clk,.reset,.iv(sv[23]),.ir(sr[23]),.idata({sstatus[46+:2],stag[115+:5],sd[5888+:256]}),.ov(sv2),.ordy(sr2),.odata({ss2,st,sd2}));
 end
begin:port24
 wire [3:0] tw;wire [127:0] tl;wire [4*74-1:0] ti,ri_;wire [1023:0] td,trd;wire[7:0] rs;
 for(genvar c=0;c<4;c=c+1)begin:client
 assign {tw[c],tl[c*32+:32],ti[c*74+:74],td[c*256+:256]}=gd[96+c];
 assign dest[96+c]=ri_[c*74+68+:6];
 assign bd[96+c]={rs[c*2+:2],ri_[c*74+:74],trd[c*256+:256]};
 end
 wire pv,pr,pw,sv2,sr2;wire[31:0] pl;wire[4:0] pt,st;wire[255:0] pd,sd2;wire[1:0] ss2;
 lf_tagged_port #(.OWNER_ID(24),.ID_W(74)) fabric(.clk,.reset,.cv(gv[96+:4]),.cr(gr[96+:4]),.cw(tw),.cl(tl),.cid(ti),.cd(td),.rv(bv[96+:4]),.rr(br[96+:4]),.rid(ri_),.rd(trd),.rstatus(rs),.mv(pv),.mr(pr),.mw(pw),.ml(pl),.mtag(pt),.md(pd),.sv(sv2),.sr(sr2),.stag(st),.sd(sd2),.sstatus(ss2),.error(port_error[24]),.idle(),.credits_used(),.peak_credits(),.client_accepted(),.physical_issued(),.physical_returned(),.client_returned());
 lf_fifo2 #(.WIDTH(294)) request_slice(.clk,.reset,.iv(pv),.ir(pr),.idata({pw,pl,pt,pd}),.ov(mv[24]),.ordy(mr[24]),.odata({mw[24],ml[768+:32],mtag[120+:5],md[6144+:256]}));
 lf_fifo2 #(.WIDTH(263)) response_slice(.clk,.reset,.iv(sv[24]),.ir(sr[24]),.idata({sstatus[48+:2],stag[120+:5],sd[6144+:256]}),.ov(sv2),.ordy(sr2),.odata({ss2,st,sd2}));
 end
begin:port25
 wire [3:0] tw;wire [127:0] tl;wire [4*74-1:0] ti,ri_;wire [1023:0] td,trd;wire[7:0] rs;
 for(genvar c=0;c<4;c=c+1)begin:client
 assign {tw[c],tl[c*32+:32],ti[c*74+:74],td[c*256+:256]}=gd[100+c];
 assign dest[100+c]=ri_[c*74+68+:6];
 assign bd[100+c]={rs[c*2+:2],ri_[c*74+:74],trd[c*256+:256]};
 end
 wire pv,pr,pw,sv2,sr2;wire[31:0] pl;wire[4:0] pt,st;wire[255:0] pd,sd2;wire[1:0] ss2;
 lf_tagged_port #(.OWNER_ID(25),.ID_W(74)) fabric(.clk,.reset,.cv(gv[100+:4]),.cr(gr[100+:4]),.cw(tw),.cl(tl),.cid(ti),.cd(td),.rv(bv[100+:4]),.rr(br[100+:4]),.rid(ri_),.rd(trd),.rstatus(rs),.mv(pv),.mr(pr),.mw(pw),.ml(pl),.mtag(pt),.md(pd),.sv(sv2),.sr(sr2),.stag(st),.sd(sd2),.sstatus(ss2),.error(port_error[25]),.idle(),.credits_used(),.peak_credits(),.client_accepted(),.physical_issued(),.physical_returned(),.client_returned());
 lf_fifo2 #(.WIDTH(294)) request_slice(.clk,.reset,.iv(pv),.ir(pr),.idata({pw,pl,pt,pd}),.ov(mv[25]),.ordy(mr[25]),.odata({mw[25],ml[800+:32],mtag[125+:5],md[6400+:256]}));
 lf_fifo2 #(.WIDTH(263)) response_slice(.clk,.reset,.iv(sv[25]),.ir(sr[25]),.idata({sstatus[50+:2],stag[125+:5],sd[6400+:256]}),.ov(sv2),.ordy(sr2),.odata({ss2,st,sd2}));
 end
begin:port26
 wire [3:0] tw;wire [127:0] tl;wire [4*74-1:0] ti,ri_;wire [1023:0] td,trd;wire[7:0] rs;
 for(genvar c=0;c<4;c=c+1)begin:client
 assign {tw[c],tl[c*32+:32],ti[c*74+:74],td[c*256+:256]}=gd[104+c];
 assign dest[104+c]=ri_[c*74+68+:6];
 assign bd[104+c]={rs[c*2+:2],ri_[c*74+:74],trd[c*256+:256]};
 end
 wire pv,pr,pw,sv2,sr2;wire[31:0] pl;wire[4:0] pt,st;wire[255:0] pd,sd2;wire[1:0] ss2;
 lf_tagged_port #(.OWNER_ID(26),.ID_W(74)) fabric(.clk,.reset,.cv(gv[104+:4]),.cr(gr[104+:4]),.cw(tw),.cl(tl),.cid(ti),.cd(td),.rv(bv[104+:4]),.rr(br[104+:4]),.rid(ri_),.rd(trd),.rstatus(rs),.mv(pv),.mr(pr),.mw(pw),.ml(pl),.mtag(pt),.md(pd),.sv(sv2),.sr(sr2),.stag(st),.sd(sd2),.sstatus(ss2),.error(port_error[26]),.idle(),.credits_used(),.peak_credits(),.client_accepted(),.physical_issued(),.physical_returned(),.client_returned());
 lf_fifo2 #(.WIDTH(294)) request_slice(.clk,.reset,.iv(pv),.ir(pr),.idata({pw,pl,pt,pd}),.ov(mv[26]),.ordy(mr[26]),.odata({mw[26],ml[832+:32],mtag[130+:5],md[6656+:256]}));
 lf_fifo2 #(.WIDTH(263)) response_slice(.clk,.reset,.iv(sv[26]),.ir(sr[26]),.idata({sstatus[52+:2],stag[130+:5],sd[6656+:256]}),.ov(sv2),.ordy(sr2),.odata({ss2,st,sd2}));
 end
begin:port27
 wire [3:0] tw;wire [127:0] tl;wire [4*74-1:0] ti,ri_;wire [1023:0] td,trd;wire[7:0] rs;
 for(genvar c=0;c<4;c=c+1)begin:client
 assign {tw[c],tl[c*32+:32],ti[c*74+:74],td[c*256+:256]}=gd[108+c];
 assign dest[108+c]=ri_[c*74+68+:6];
 assign bd[108+c]={rs[c*2+:2],ri_[c*74+:74],trd[c*256+:256]};
 end
 wire pv,pr,pw,sv2,sr2;wire[31:0] pl;wire[4:0] pt,st;wire[255:0] pd,sd2;wire[1:0] ss2;
 lf_tagged_port #(.OWNER_ID(27),.ID_W(74)) fabric(.clk,.reset,.cv(gv[108+:4]),.cr(gr[108+:4]),.cw(tw),.cl(tl),.cid(ti),.cd(td),.rv(bv[108+:4]),.rr(br[108+:4]),.rid(ri_),.rd(trd),.rstatus(rs),.mv(pv),.mr(pr),.mw(pw),.ml(pl),.mtag(pt),.md(pd),.sv(sv2),.sr(sr2),.stag(st),.sd(sd2),.sstatus(ss2),.error(port_error[27]),.idle(),.credits_used(),.peak_credits(),.client_accepted(),.physical_issued(),.physical_returned(),.client_returned());
 lf_fifo2 #(.WIDTH(294)) request_slice(.clk,.reset,.iv(pv),.ir(pr),.idata({pw,pl,pt,pd}),.ov(mv[27]),.ordy(mr[27]),.odata({mw[27],ml[864+:32],mtag[135+:5],md[6912+:256]}));
 lf_fifo2 #(.WIDTH(263)) response_slice(.clk,.reset,.iv(sv[27]),.ir(sr[27]),.idata({sstatus[54+:2],stag[135+:5],sd[6912+:256]}),.ov(sv2),.ordy(sr2),.odata({ss2,st,sd2}));
 end
begin:port28
 wire [3:0] tw;wire [127:0] tl;wire [4*74-1:0] ti,ri_;wire [1023:0] td,trd;wire[7:0] rs;
 for(genvar c=0;c<4;c=c+1)begin:client
 assign {tw[c],tl[c*32+:32],ti[c*74+:74],td[c*256+:256]}=gd[112+c];
 assign dest[112+c]=ri_[c*74+68+:6];
 assign bd[112+c]={rs[c*2+:2],ri_[c*74+:74],trd[c*256+:256]};
 end
 wire pv,pr,pw,sv2,sr2;wire[31:0] pl;wire[4:0] pt,st;wire[255:0] pd,sd2;wire[1:0] ss2;
 lf_tagged_port #(.OWNER_ID(28),.ID_W(74)) fabric(.clk,.reset,.cv(gv[112+:4]),.cr(gr[112+:4]),.cw(tw),.cl(tl),.cid(ti),.cd(td),.rv(bv[112+:4]),.rr(br[112+:4]),.rid(ri_),.rd(trd),.rstatus(rs),.mv(pv),.mr(pr),.mw(pw),.ml(pl),.mtag(pt),.md(pd),.sv(sv2),.sr(sr2),.stag(st),.sd(sd2),.sstatus(ss2),.error(port_error[28]),.idle(),.credits_used(),.peak_credits(),.client_accepted(),.physical_issued(),.physical_returned(),.client_returned());
 lf_fifo2 #(.WIDTH(294)) request_slice(.clk,.reset,.iv(pv),.ir(pr),.idata({pw,pl,pt,pd}),.ov(mv[28]),.ordy(mr[28]),.odata({mw[28],ml[896+:32],mtag[140+:5],md[7168+:256]}));
 lf_fifo2 #(.WIDTH(263)) response_slice(.clk,.reset,.iv(sv[28]),.ir(sr[28]),.idata({sstatus[56+:2],stag[140+:5],sd[7168+:256]}),.ov(sv2),.ordy(sr2),.odata({ss2,st,sd2}));
 end
begin:port29
 wire [3:0] tw;wire [127:0] tl;wire [4*74-1:0] ti,ri_;wire [1023:0] td,trd;wire[7:0] rs;
 for(genvar c=0;c<4;c=c+1)begin:client
 assign {tw[c],tl[c*32+:32],ti[c*74+:74],td[c*256+:256]}=gd[116+c];
 assign dest[116+c]=ri_[c*74+68+:6];
 assign bd[116+c]={rs[c*2+:2],ri_[c*74+:74],trd[c*256+:256]};
 end
 wire pv,pr,pw,sv2,sr2;wire[31:0] pl;wire[4:0] pt,st;wire[255:0] pd,sd2;wire[1:0] ss2;
 lf_tagged_port #(.OWNER_ID(29),.ID_W(74)) fabric(.clk,.reset,.cv(gv[116+:4]),.cr(gr[116+:4]),.cw(tw),.cl(tl),.cid(ti),.cd(td),.rv(bv[116+:4]),.rr(br[116+:4]),.rid(ri_),.rd(trd),.rstatus(rs),.mv(pv),.mr(pr),.mw(pw),.ml(pl),.mtag(pt),.md(pd),.sv(sv2),.sr(sr2),.stag(st),.sd(sd2),.sstatus(ss2),.error(port_error[29]),.idle(),.credits_used(),.peak_credits(),.client_accepted(),.physical_issued(),.physical_returned(),.client_returned());
 lf_fifo2 #(.WIDTH(294)) request_slice(.clk,.reset,.iv(pv),.ir(pr),.idata({pw,pl,pt,pd}),.ov(mv[29]),.ordy(mr[29]),.odata({mw[29],ml[928+:32],mtag[145+:5],md[7424+:256]}));
 lf_fifo2 #(.WIDTH(263)) response_slice(.clk,.reset,.iv(sv[29]),.ir(sr[29]),.idata({sstatus[58+:2],stag[145+:5],sd[7424+:256]}),.ov(sv2),.ordy(sr2),.odata({ss2,st,sd2}));
 end
begin:port30
 wire [3:0] tw;wire [127:0] tl;wire [4*74-1:0] ti,ri_;wire [1023:0] td,trd;wire[7:0] rs;
 for(genvar c=0;c<4;c=c+1)begin:client
 assign {tw[c],tl[c*32+:32],ti[c*74+:74],td[c*256+:256]}=gd[120+c];
 assign dest[120+c]=ri_[c*74+68+:6];
 assign bd[120+c]={rs[c*2+:2],ri_[c*74+:74],trd[c*256+:256]};
 end
 wire pv,pr,pw,sv2,sr2;wire[31:0] pl;wire[4:0] pt,st;wire[255:0] pd,sd2;wire[1:0] ss2;
 lf_tagged_port #(.OWNER_ID(30),.ID_W(74)) fabric(.clk,.reset,.cv(gv[120+:4]),.cr(gr[120+:4]),.cw(tw),.cl(tl),.cid(ti),.cd(td),.rv(bv[120+:4]),.rr(br[120+:4]),.rid(ri_),.rd(trd),.rstatus(rs),.mv(pv),.mr(pr),.mw(pw),.ml(pl),.mtag(pt),.md(pd),.sv(sv2),.sr(sr2),.stag(st),.sd(sd2),.sstatus(ss2),.error(port_error[30]),.idle(),.credits_used(),.peak_credits(),.client_accepted(),.physical_issued(),.physical_returned(),.client_returned());
 lf_fifo2 #(.WIDTH(294)) request_slice(.clk,.reset,.iv(pv),.ir(pr),.idata({pw,pl,pt,pd}),.ov(mv[30]),.ordy(mr[30]),.odata({mw[30],ml[960+:32],mtag[150+:5],md[7680+:256]}));
 lf_fifo2 #(.WIDTH(263)) response_slice(.clk,.reset,.iv(sv[30]),.ir(sr[30]),.idata({sstatus[60+:2],stag[150+:5],sd[7680+:256]}),.ov(sv2),.ordy(sr2),.odata({ss2,st,sd2}));
 end
begin:port31
 wire [3:0] tw;wire [127:0] tl;wire [4*74-1:0] ti,ri_;wire [1023:0] td,trd;wire[7:0] rs;
 for(genvar c=0;c<4;c=c+1)begin:client
 assign {tw[c],tl[c*32+:32],ti[c*74+:74],td[c*256+:256]}=gd[124+c];
 assign dest[124+c]=ri_[c*74+68+:6];
 assign bd[124+c]={rs[c*2+:2],ri_[c*74+:74],trd[c*256+:256]};
 end
 wire pv,pr,pw,sv2,sr2;wire[31:0] pl;wire[4:0] pt,st;wire[255:0] pd,sd2;wire[1:0] ss2;
 lf_tagged_port #(.OWNER_ID(31),.ID_W(74)) fabric(.clk,.reset,.cv(gv[124+:4]),.cr(gr[124+:4]),.cw(tw),.cl(tl),.cid(ti),.cd(td),.rv(bv[124+:4]),.rr(br[124+:4]),.rid(ri_),.rd(trd),.rstatus(rs),.mv(pv),.mr(pr),.mw(pw),.ml(pl),.mtag(pt),.md(pd),.sv(sv2),.sr(sr2),.stag(st),.sd(sd2),.sstatus(ss2),.error(port_error[31]),.idle(),.credits_used(),.peak_credits(),.client_accepted(),.physical_issued(),.physical_returned(),.client_returned());
 lf_fifo2 #(.WIDTH(294)) request_slice(.clk,.reset,.iv(pv),.ir(pr),.idata({pw,pl,pt,pd}),.ov(mv[31]),.ordy(mr[31]),.odata({mw[31],ml[992+:32],mtag[155+:5],md[7936+:256]}));
 lf_fifo2 #(.WIDTH(263)) response_slice(.clk,.reset,.iv(sv[31]),.ir(sr[31]),.idata({sstatus[62+:2],stag[155+:5],sd[7936+:256]}),.ov(sv2),.ordy(sr2),.odata({ss2,st,sd2}));
 end
assign rv[0]=frv[0];assign frr[0]=rr[0];assign {rstatus[0+:2],ri[0],raw_rd[0]}=frdata[0*332+:332];
assign rv[1]=frv[1];assign frr[1]=rr[1];assign {rstatus[2+:2],ri[1],raw_rd[1]}=frdata[1*332+:332];
assign rv[2]=frv[2];assign frr[2]=rr[2];assign {rstatus[4+:2],ri[2],raw_rd[2]}=frdata[2*332+:332];
assign rv[3]=frv[3];assign frr[3]=rr[3];assign {rstatus[6+:2],ri[3],raw_rd[3]}=frdata[3*332+:332];
assign rv[4]=frv[4];assign frr[4]=rr[4];assign {rstatus[8+:2],ri[4],raw_rd[4]}=frdata[4*332+:332];
assign rv[5]=frv[5];assign frr[5]=rr[5];assign {rstatus[10+:2],ri[5],raw_rd[5]}=frdata[5*332+:332];
assign rv[6]=frv[6];assign frr[6]=rr[6];assign {rstatus[12+:2],ri[6],raw_rd[6]}=frdata[6*332+:332];
assign rv[7]=frv[7];assign frr[7]=rr[7];assign {rstatus[14+:2],ri[7],raw_rd[7]}=frdata[7*332+:332];
assign rv[8]=frv[8];assign frr[8]=rr[8];assign {rstatus[16+:2],ri[8],raw_rd[8]}=frdata[8*332+:332];
assign rv[9]=frv[9];assign frr[9]=rr[9];assign {rstatus[18+:2],ri[9],raw_rd[9]}=frdata[9*332+:332];
assign rv[10]=frv[10];assign frr[10]=rr[10];assign {rstatus[20+:2],ri[10],raw_rd[10]}=frdata[10*332+:332];
assign rv[11]=frv[11];assign frr[11]=rr[11];assign {rstatus[22+:2],ri[11],raw_rd[11]}=frdata[11*332+:332];
assign rv[12]=frv[12];assign frr[12]=rr[12];assign {rstatus[24+:2],ri[12],raw_rd[12]}=frdata[12*332+:332];
assign rv[13]=frv[13];assign frr[13]=rr[13];assign {rstatus[26+:2],ri[13],raw_rd[13]}=frdata[13*332+:332];
assign rv[14]=frv[14];assign frr[14]=rr[14];assign {rstatus[28+:2],ri[14],raw_rd[14]}=frdata[14*332+:332];
assign rv[15]=frv[15];assign frr[15]=rr[15];assign {rstatus[30+:2],ri[15],raw_rd[15]}=frdata[15*332+:332];
assign rv[16]=frv[16];assign frr[16]=rr[16];assign {rstatus[32+:2],ri[16],raw_rd[16]}=frdata[16*332+:332];
assign rv[17]=frv[17];assign frr[17]=rr[17];assign {rstatus[34+:2],ri[17],raw_rd[17]}=frdata[17*332+:332];
assign rv[18]=frv[18];assign frr[18]=rr[18];assign {rstatus[36+:2],ri[18],raw_rd[18]}=frdata[18*332+:332];
assign rv[19]=frv[19];assign frr[19]=rr[19];assign {rstatus[38+:2],ri[19],raw_rd[19]}=frdata[19*332+:332];
assign rv[20]=frv[20];assign frr[20]=rr[20];assign {rstatus[40+:2],ri[20],raw_rd[20]}=frdata[20*332+:332];
assign rv[21]=frv[21];assign frr[21]=rr[21];assign {rstatus[42+:2],ri[21],raw_rd[21]}=frdata[21*332+:332];
assign rv[22]=frv[22];assign frr[22]=rr[22];assign {rstatus[44+:2],ri[22],raw_rd[22]}=frdata[22*332+:332];
assign rv[23]=frv[23];assign frr[23]=rr[23];assign {rstatus[46+:2],ri[23],raw_rd[23]}=frdata[23*332+:332];
assign rv[24]=frv[24];assign frr[24]=rr[24];assign {rstatus[48+:2],ri[24],raw_rd[24]}=frdata[24*332+:332];
assign rv[25]=frv[25];assign frr[25]=rr[25];assign {rstatus[50+:2],ri[25],raw_rd[25]}=frdata[25*332+:332];
assign rv[26]=frv[26];assign frr[26]=rr[26];assign {rstatus[52+:2],ri[26],raw_rd[26]}=frdata[26*332+:332];
assign rv[27]=frv[27];assign frr[27]=rr[27];assign {rstatus[54+:2],ri[27],raw_rd[27]}=frdata[27*332+:332];
assign rv[28]=frv[28];assign frr[28]=rr[28];assign {rstatus[56+:2],ri[28],raw_rd[28]}=frdata[28*332+:332];
assign rv[29]=frv[29];assign frr[29]=rr[29];assign {rstatus[58+:2],ri[29],raw_rd[29]}=frdata[29*332+:332];
assign rv[30]=frv[30];assign frr[30]=rr[30];assign {rstatus[60+:2],ri[30],raw_rd[30]}=frdata[30*332+:332];
assign rv[31]=frv[31];assign frr[31]=rr[31];assign {rstatus[62+:2],ri[31],raw_rd[31]}=frdata[31*332+:332];
assign rv[32]=frv[32];assign frr[32]=rr[32];assign {rstatus[64+:2],ri[32],raw_rd[32]}=frdata[32*332+:332];
assign rv[33]=frv[33];assign frr[33]=rr[33];assign {rstatus[66+:2],ri[33],raw_rd[33]}=frdata[33*332+:332];
assign rv[34]=frv[34];assign frr[34]=rr[34];assign {rstatus[68+:2],ri[34],raw_rd[34]}=frdata[34*332+:332];
assign rv[35]=frv[35];assign frr[35]=rr[35];assign {rstatus[70+:2],ri[35],raw_rd[35]}=frdata[35*332+:332];
assign rv[36]=frv[36];assign frr[36]=rr[36];assign {rstatus[72+:2],ri[36],raw_rd[36]}=frdata[36*332+:332];
assign rv[37]=frv[37];assign frr[37]=rr[37];assign {rstatus[74+:2],ri[37],raw_rd[37]}=frdata[37*332+:332];
assign rv[38]=frv[38];assign frr[38]=rr[38];assign {rstatus[76+:2],ri[38],raw_rd[38]}=frdata[38*332+:332];
assign rv[39]=frv[39];assign frr[39]=rr[39];assign {rstatus[78+:2],ri[39],raw_rd[39]}=frdata[39*332+:332];
assign rv[40]=frv[40];assign frr[40]=rr[40];assign {rstatus[80+:2],ri[40],raw_rd[40]}=frdata[40*332+:332];
assign rv[41]=frv[41];assign frr[41]=rr[41];assign {rstatus[82+:2],ri[41],raw_rd[41]}=frdata[41*332+:332];
assign rv[42]=frv[42];assign frr[42]=rr[42];assign {rstatus[84+:2],ri[42],raw_rd[42]}=frdata[42*332+:332];
assign rv[43]=frv[43];assign frr[43]=rr[43];assign {rstatus[86+:2],ri[43],raw_rd[43]}=frdata[43*332+:332];
assign rv[44]=frv[44];assign frr[44]=rr[44];assign {rstatus[88+:2],ri[44],raw_rd[44]}=frdata[44*332+:332];
assign rv[45]=frv[45];assign frr[45]=rr[45];assign {rstatus[90+:2],ri[45],raw_rd[45]}=frdata[45*332+:332];
assign rv[46]=frv[46];assign frr[46]=rr[46];assign {rstatus[92+:2],ri[46],raw_rd[46]}=frdata[46*332+:332];
assign rv[47]=frv[47];assign frr[47]=rr[47];assign {rstatus[94+:2],ri[47],raw_rd[47]}=frdata[47*332+:332];
begin:ret48
wire [0:0] eligible,grant;wire any;wire accept=!rv[48]||rr[48];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[2]&&dest[2]==48;assign word_[0]=bd[2]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[48]=valid;assign {rstatus[96+:2],ri[48],raw_rd[48]}=hold;end
begin:ret49
wire [0:0] eligible,grant;wire any;wire accept=!rv[49]||rr[49];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[2]&&dest[2]==49;assign word_[0]=bd[2]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[49]=valid;assign {rstatus[98+:2],ri[49],raw_rd[49]}=hold;end
begin:ret50
wire [0:0] eligible,grant;wire any;wire accept=!rv[50]||rr[50];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[6]&&dest[6]==48;assign word_[0]=bd[6]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[50]=valid;assign {rstatus[100+:2],ri[50],raw_rd[50]}=hold;end
begin:ret51
wire [0:0] eligible,grant;wire any;wire accept=!rv[51]||rr[51];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[6]&&dest[6]==49;assign word_[0]=bd[6]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[51]=valid;assign {rstatus[102+:2],ri[51],raw_rd[51]}=hold;end
begin:ret52
wire [0:0] eligible,grant;wire any;wire accept=!rv[52]||rr[52];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[10]&&dest[10]==48;assign word_[0]=bd[10]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[52]=valid;assign {rstatus[104+:2],ri[52],raw_rd[52]}=hold;end
begin:ret53
wire [0:0] eligible,grant;wire any;wire accept=!rv[53]||rr[53];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[10]&&dest[10]==49;assign word_[0]=bd[10]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[53]=valid;assign {rstatus[106+:2],ri[53],raw_rd[53]}=hold;end
begin:ret54
wire [0:0] eligible,grant;wire any;wire accept=!rv[54]||rr[54];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[14]&&dest[14]==48;assign word_[0]=bd[14]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[54]=valid;assign {rstatus[108+:2],ri[54],raw_rd[54]}=hold;end
begin:ret55
wire [0:0] eligible,grant;wire any;wire accept=!rv[55]||rr[55];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[14]&&dest[14]==49;assign word_[0]=bd[14]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[55]=valid;assign {rstatus[110+:2],ri[55],raw_rd[55]}=hold;end
begin:ret56
wire [0:0] eligible,grant;wire any;wire accept=!rv[56]||rr[56];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[18]&&dest[18]==48;assign word_[0]=bd[18]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[56]=valid;assign {rstatus[112+:2],ri[56],raw_rd[56]}=hold;end
begin:ret57
wire [0:0] eligible,grant;wire any;wire accept=!rv[57]||rr[57];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[18]&&dest[18]==49;assign word_[0]=bd[18]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[57]=valid;assign {rstatus[114+:2],ri[57],raw_rd[57]}=hold;end
begin:ret58
wire [0:0] eligible,grant;wire any;wire accept=!rv[58]||rr[58];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[22]&&dest[22]==48;assign word_[0]=bd[22]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[58]=valid;assign {rstatus[116+:2],ri[58],raw_rd[58]}=hold;end
begin:ret59
wire [0:0] eligible,grant;wire any;wire accept=!rv[59]||rr[59];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[22]&&dest[22]==49;assign word_[0]=bd[22]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[59]=valid;assign {rstatus[118+:2],ri[59],raw_rd[59]}=hold;end
begin:ret60
wire [0:0] eligible,grant;wire any;wire accept=!rv[60]||rr[60];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[26]&&dest[26]==48;assign word_[0]=bd[26]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[60]=valid;assign {rstatus[120+:2],ri[60],raw_rd[60]}=hold;end
begin:ret61
wire [0:0] eligible,grant;wire any;wire accept=!rv[61]||rr[61];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[26]&&dest[26]==49;assign word_[0]=bd[26]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[61]=valid;assign {rstatus[122+:2],ri[61],raw_rd[61]}=hold;end
begin:ret62
wire [0:0] eligible,grant;wire any;wire accept=!rv[62]||rr[62];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[30]&&dest[30]==48;assign word_[0]=bd[30]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[62]=valid;assign {rstatus[124+:2],ri[62],raw_rd[62]}=hold;end
begin:ret63
wire [0:0] eligible,grant;wire any;wire accept=!rv[63]||rr[63];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[30]&&dest[30]==49;assign word_[0]=bd[30]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[63]=valid;assign {rstatus[126+:2],ri[63],raw_rd[63]}=hold;end
begin:ret64
wire [0:0] eligible,grant;wire any;wire accept=!rv[64]||rr[64];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[34]&&dest[34]==48;assign word_[0]=bd[34]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[64]=valid;assign {rstatus[128+:2],ri[64],raw_rd[64]}=hold;end
begin:ret65
wire [0:0] eligible,grant;wire any;wire accept=!rv[65]||rr[65];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[34]&&dest[34]==49;assign word_[0]=bd[34]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[65]=valid;assign {rstatus[130+:2],ri[65],raw_rd[65]}=hold;end
begin:ret66
wire [0:0] eligible,grant;wire any;wire accept=!rv[66]||rr[66];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[38]&&dest[38]==48;assign word_[0]=bd[38]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[66]=valid;assign {rstatus[132+:2],ri[66],raw_rd[66]}=hold;end
begin:ret67
wire [0:0] eligible,grant;wire any;wire accept=!rv[67]||rr[67];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[38]&&dest[38]==49;assign word_[0]=bd[38]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[67]=valid;assign {rstatus[134+:2],ri[67],raw_rd[67]}=hold;end
begin:ret68
wire [0:0] eligible,grant;wire any;wire accept=!rv[68]||rr[68];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[42]&&dest[42]==48;assign word_[0]=bd[42]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[68]=valid;assign {rstatus[136+:2],ri[68],raw_rd[68]}=hold;end
begin:ret69
wire [0:0] eligible,grant;wire any;wire accept=!rv[69]||rr[69];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[42]&&dest[42]==49;assign word_[0]=bd[42]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[69]=valid;assign {rstatus[138+:2],ri[69],raw_rd[69]}=hold;end
begin:ret70
wire [0:0] eligible,grant;wire any;wire accept=!rv[70]||rr[70];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[46]&&dest[46]==48;assign word_[0]=bd[46]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[70]=valid;assign {rstatus[140+:2],ri[70],raw_rd[70]}=hold;end
begin:ret71
wire [0:0] eligible,grant;wire any;wire accept=!rv[71]||rr[71];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[46]&&dest[46]==49;assign word_[0]=bd[46]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[71]=valid;assign {rstatus[142+:2],ri[71],raw_rd[71]}=hold;end
begin:ret72
wire [0:0] eligible,grant;wire any;wire accept=!rv[72]||rr[72];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[50]&&dest[50]==48;assign word_[0]=bd[50]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[72]=valid;assign {rstatus[144+:2],ri[72],raw_rd[72]}=hold;end
begin:ret73
wire [0:0] eligible,grant;wire any;wire accept=!rv[73]||rr[73];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[50]&&dest[50]==49;assign word_[0]=bd[50]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[73]=valid;assign {rstatus[146+:2],ri[73],raw_rd[73]}=hold;end
begin:ret74
wire [0:0] eligible,grant;wire any;wire accept=!rv[74]||rr[74];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[54]&&dest[54]==48;assign word_[0]=bd[54]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[74]=valid;assign {rstatus[148+:2],ri[74],raw_rd[74]}=hold;end
begin:ret75
wire [0:0] eligible,grant;wire any;wire accept=!rv[75]||rr[75];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[54]&&dest[54]==49;assign word_[0]=bd[54]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[75]=valid;assign {rstatus[150+:2],ri[75],raw_rd[75]}=hold;end
begin:ret76
wire [0:0] eligible,grant;wire any;wire accept=!rv[76]||rr[76];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[58]&&dest[58]==48;assign word_[0]=bd[58]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[76]=valid;assign {rstatus[152+:2],ri[76],raw_rd[76]}=hold;end
begin:ret77
wire [0:0] eligible,grant;wire any;wire accept=!rv[77]||rr[77];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[58]&&dest[58]==49;assign word_[0]=bd[58]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[77]=valid;assign {rstatus[154+:2],ri[77],raw_rd[77]}=hold;end
begin:ret78
wire [0:0] eligible,grant;wire any;wire accept=!rv[78]||rr[78];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[62]&&dest[62]==48;assign word_[0]=bd[62]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[78]=valid;assign {rstatus[156+:2],ri[78],raw_rd[78]}=hold;end
begin:ret79
wire [0:0] eligible,grant;wire any;wire accept=!rv[79]||rr[79];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[62]&&dest[62]==49;assign word_[0]=bd[62]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[79]=valid;assign {rstatus[158+:2],ri[79],raw_rd[79]}=hold;end
begin:ret80
wire [0:0] eligible,grant;wire any;wire accept=!rv[80]||rr[80];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[66]&&dest[66]==48;assign word_[0]=bd[66]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[80]=valid;assign {rstatus[160+:2],ri[80],raw_rd[80]}=hold;end
begin:ret81
wire [0:0] eligible,grant;wire any;wire accept=!rv[81]||rr[81];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[66]&&dest[66]==49;assign word_[0]=bd[66]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[81]=valid;assign {rstatus[162+:2],ri[81],raw_rd[81]}=hold;end
begin:ret82
wire [0:0] eligible,grant;wire any;wire accept=!rv[82]||rr[82];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[70]&&dest[70]==48;assign word_[0]=bd[70]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[82]=valid;assign {rstatus[164+:2],ri[82],raw_rd[82]}=hold;end
begin:ret83
wire [0:0] eligible,grant;wire any;wire accept=!rv[83]||rr[83];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[70]&&dest[70]==49;assign word_[0]=bd[70]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[83]=valid;assign {rstatus[166+:2],ri[83],raw_rd[83]}=hold;end
begin:ret84
wire [0:0] eligible,grant;wire any;wire accept=!rv[84]||rr[84];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[74]&&dest[74]==48;assign word_[0]=bd[74]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[84]=valid;assign {rstatus[168+:2],ri[84],raw_rd[84]}=hold;end
begin:ret85
wire [0:0] eligible,grant;wire any;wire accept=!rv[85]||rr[85];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[74]&&dest[74]==49;assign word_[0]=bd[74]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[85]=valid;assign {rstatus[170+:2],ri[85],raw_rd[85]}=hold;end
begin:ret86
wire [0:0] eligible,grant;wire any;wire accept=!rv[86]||rr[86];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[78]&&dest[78]==48;assign word_[0]=bd[78]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[86]=valid;assign {rstatus[172+:2],ri[86],raw_rd[86]}=hold;end
begin:ret87
wire [0:0] eligible,grant;wire any;wire accept=!rv[87]||rr[87];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[78]&&dest[78]==49;assign word_[0]=bd[78]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[87]=valid;assign {rstatus[174+:2],ri[87],raw_rd[87]}=hold;end
begin:ret88
wire [0:0] eligible,grant;wire any;wire accept=!rv[88]||rr[88];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[82]&&dest[82]==48;assign word_[0]=bd[82]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[88]=valid;assign {rstatus[176+:2],ri[88],raw_rd[88]}=hold;end
begin:ret89
wire [0:0] eligible,grant;wire any;wire accept=!rv[89]||rr[89];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[82]&&dest[82]==49;assign word_[0]=bd[82]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[89]=valid;assign {rstatus[178+:2],ri[89],raw_rd[89]}=hold;end
begin:ret90
wire [0:0] eligible,grant;wire any;wire accept=!rv[90]||rr[90];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[86]&&dest[86]==48;assign word_[0]=bd[86]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[90]=valid;assign {rstatus[180+:2],ri[90],raw_rd[90]}=hold;end
begin:ret91
wire [0:0] eligible,grant;wire any;wire accept=!rv[91]||rr[91];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[86]&&dest[86]==49;assign word_[0]=bd[86]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[91]=valid;assign {rstatus[182+:2],ri[91],raw_rd[91]}=hold;end
begin:ret92
wire [0:0] eligible,grant;wire any;wire accept=!rv[92]||rr[92];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[90]&&dest[90]==48;assign word_[0]=bd[90]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[92]=valid;assign {rstatus[184+:2],ri[92],raw_rd[92]}=hold;end
begin:ret93
wire [0:0] eligible,grant;wire any;wire accept=!rv[93]||rr[93];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[90]&&dest[90]==49;assign word_[0]=bd[90]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[93]=valid;assign {rstatus[186+:2],ri[93],raw_rd[93]}=hold;end
begin:ret94
wire [0:0] eligible,grant;wire any;wire accept=!rv[94]||rr[94];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[94]&&dest[94]==48;assign word_[0]=bd[94]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[94]=valid;assign {rstatus[188+:2],ri[94],raw_rd[94]}=hold;end
begin:ret95
wire [0:0] eligible,grant;wire any;wire accept=!rv[95]||rr[95];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[94]&&dest[94]==49;assign word_[0]=bd[94]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[95]=valid;assign {rstatus[190+:2],ri[95],raw_rd[95]}=hold;end
begin:ret96
wire [0:0] eligible,grant;wire any;wire accept=!rv[96]||rr[96];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[98]&&dest[98]==48;assign word_[0]=bd[98]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[96]=valid;assign {rstatus[192+:2],ri[96],raw_rd[96]}=hold;end
begin:ret97
wire [0:0] eligible,grant;wire any;wire accept=!rv[97]||rr[97];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[98]&&dest[98]==49;assign word_[0]=bd[98]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[97]=valid;assign {rstatus[194+:2],ri[97],raw_rd[97]}=hold;end
begin:ret98
wire [0:0] eligible,grant;wire any;wire accept=!rv[98]||rr[98];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[102]&&dest[102]==48;assign word_[0]=bd[102]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[98]=valid;assign {rstatus[196+:2],ri[98],raw_rd[98]}=hold;end
begin:ret99
wire [0:0] eligible,grant;wire any;wire accept=!rv[99]||rr[99];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[102]&&dest[102]==49;assign word_[0]=bd[102]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[99]=valid;assign {rstatus[198+:2],ri[99],raw_rd[99]}=hold;end
begin:ret100
wire [0:0] eligible,grant;wire any;wire accept=!rv[100]||rr[100];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[106]&&dest[106]==48;assign word_[0]=bd[106]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[100]=valid;assign {rstatus[200+:2],ri[100],raw_rd[100]}=hold;end
begin:ret101
wire [0:0] eligible,grant;wire any;wire accept=!rv[101]||rr[101];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[106]&&dest[106]==49;assign word_[0]=bd[106]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[101]=valid;assign {rstatus[202+:2],ri[101],raw_rd[101]}=hold;end
begin:ret102
wire [0:0] eligible,grant;wire any;wire accept=!rv[102]||rr[102];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[110]&&dest[110]==48;assign word_[0]=bd[110]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[102]=valid;assign {rstatus[204+:2],ri[102],raw_rd[102]}=hold;end
begin:ret103
wire [0:0] eligible,grant;wire any;wire accept=!rv[103]||rr[103];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[110]&&dest[110]==49;assign word_[0]=bd[110]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[103]=valid;assign {rstatus[206+:2],ri[103],raw_rd[103]}=hold;end
begin:ret104
wire [0:0] eligible,grant;wire any;wire accept=!rv[104]||rr[104];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[114]&&dest[114]==48;assign word_[0]=bd[114]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[104]=valid;assign {rstatus[208+:2],ri[104],raw_rd[104]}=hold;end
begin:ret105
wire [0:0] eligible,grant;wire any;wire accept=!rv[105]||rr[105];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[114]&&dest[114]==49;assign word_[0]=bd[114]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[105]=valid;assign {rstatus[210+:2],ri[105],raw_rd[105]}=hold;end
begin:ret106
wire [0:0] eligible,grant;wire any;wire accept=!rv[106]||rr[106];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[118]&&dest[118]==48;assign word_[0]=bd[118]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[106]=valid;assign {rstatus[212+:2],ri[106],raw_rd[106]}=hold;end
begin:ret107
wire [0:0] eligible,grant;wire any;wire accept=!rv[107]||rr[107];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[118]&&dest[118]==49;assign word_[0]=bd[118]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[107]=valid;assign {rstatus[214+:2],ri[107],raw_rd[107]}=hold;end
begin:ret108
wire [0:0] eligible,grant;wire any;wire accept=!rv[108]||rr[108];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[122]&&dest[122]==48;assign word_[0]=bd[122]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[108]=valid;assign {rstatus[216+:2],ri[108],raw_rd[108]}=hold;end
begin:ret109
wire [0:0] eligible,grant;wire any;wire accept=!rv[109]||rr[109];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[122]&&dest[122]==49;assign word_[0]=bd[122]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[109]=valid;assign {rstatus[218+:2],ri[109],raw_rd[109]}=hold;end
begin:ret110
wire [0:0] eligible,grant;wire any;wire accept=!rv[110]||rr[110];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[126]&&dest[126]==48;assign word_[0]=bd[126]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[110]=valid;assign {rstatus[220+:2],ri[110],raw_rd[110]}=hold;end
begin:ret111
wire [0:0] eligible,grant;wire any;wire accept=!rv[111]||rr[111];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[126]&&dest[126]==49;assign word_[0]=bd[126]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[111]=valid;assign {rstatus[222+:2],ri[111],raw_rd[111]}=hold;end
begin:ret112
wire [0:0] eligible,grant;wire any;wire accept=!rv[112]||rr[112];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[3]&&dest[3]==50;assign word_[0]=bd[3]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[112]=valid;assign {rstatus[224+:2],ri[112],raw_rd[112]}=hold;end
begin:ret113
wire [0:0] eligible,grant;wire any;wire accept=!rv[113]||rr[113];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[3]&&dest[3]==51;assign word_[0]=bd[3]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[113]=valid;assign {rstatus[226+:2],ri[113],raw_rd[113]}=hold;end
begin:ret114
wire [0:0] eligible,grant;wire any;wire accept=!rv[114]||rr[114];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[7]&&dest[7]==50;assign word_[0]=bd[7]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[114]=valid;assign {rstatus[228+:2],ri[114],raw_rd[114]}=hold;end
begin:ret115
wire [0:0] eligible,grant;wire any;wire accept=!rv[115]||rr[115];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[7]&&dest[7]==51;assign word_[0]=bd[7]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[115]=valid;assign {rstatus[230+:2],ri[115],raw_rd[115]}=hold;end
begin:ret116
wire [0:0] eligible,grant;wire any;wire accept=!rv[116]||rr[116];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[11]&&dest[11]==50;assign word_[0]=bd[11]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[116]=valid;assign {rstatus[232+:2],ri[116],raw_rd[116]}=hold;end
begin:ret117
wire [0:0] eligible,grant;wire any;wire accept=!rv[117]||rr[117];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[11]&&dest[11]==51;assign word_[0]=bd[11]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[117]=valid;assign {rstatus[234+:2],ri[117],raw_rd[117]}=hold;end
begin:ret118
wire [0:0] eligible,grant;wire any;wire accept=!rv[118]||rr[118];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[15]&&dest[15]==50;assign word_[0]=bd[15]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[118]=valid;assign {rstatus[236+:2],ri[118],raw_rd[118]}=hold;end
begin:ret119
wire [0:0] eligible,grant;wire any;wire accept=!rv[119]||rr[119];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[15]&&dest[15]==51;assign word_[0]=bd[15]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[119]=valid;assign {rstatus[238+:2],ri[119],raw_rd[119]}=hold;end
begin:ret120
wire [0:0] eligible,grant;wire any;wire accept=!rv[120]||rr[120];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[19]&&dest[19]==50;assign word_[0]=bd[19]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[120]=valid;assign {rstatus[240+:2],ri[120],raw_rd[120]}=hold;end
begin:ret121
wire [0:0] eligible,grant;wire any;wire accept=!rv[121]||rr[121];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[19]&&dest[19]==51;assign word_[0]=bd[19]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[121]=valid;assign {rstatus[242+:2],ri[121],raw_rd[121]}=hold;end
begin:ret122
wire [0:0] eligible,grant;wire any;wire accept=!rv[122]||rr[122];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[23]&&dest[23]==50;assign word_[0]=bd[23]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[122]=valid;assign {rstatus[244+:2],ri[122],raw_rd[122]}=hold;end
begin:ret123
wire [0:0] eligible,grant;wire any;wire accept=!rv[123]||rr[123];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[23]&&dest[23]==51;assign word_[0]=bd[23]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[123]=valid;assign {rstatus[246+:2],ri[123],raw_rd[123]}=hold;end
begin:ret124
wire [0:0] eligible,grant;wire any;wire accept=!rv[124]||rr[124];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[27]&&dest[27]==50;assign word_[0]=bd[27]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[124]=valid;assign {rstatus[248+:2],ri[124],raw_rd[124]}=hold;end
begin:ret125
wire [0:0] eligible,grant;wire any;wire accept=!rv[125]||rr[125];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[27]&&dest[27]==51;assign word_[0]=bd[27]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[125]=valid;assign {rstatus[250+:2],ri[125],raw_rd[125]}=hold;end
begin:ret126
wire [0:0] eligible,grant;wire any;wire accept=!rv[126]||rr[126];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[31]&&dest[31]==50;assign word_[0]=bd[31]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[126]=valid;assign {rstatus[252+:2],ri[126],raw_rd[126]}=hold;end
begin:ret127
wire [0:0] eligible,grant;wire any;wire accept=!rv[127]||rr[127];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[31]&&dest[31]==51;assign word_[0]=bd[31]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[127]=valid;assign {rstatus[254+:2],ri[127],raw_rd[127]}=hold;end
begin:ret128
wire [0:0] eligible,grant;wire any;wire accept=!rv[128]||rr[128];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[35]&&dest[35]==50;assign word_[0]=bd[35]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[128]=valid;assign {rstatus[256+:2],ri[128],raw_rd[128]}=hold;end
begin:ret129
wire [0:0] eligible,grant;wire any;wire accept=!rv[129]||rr[129];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[35]&&dest[35]==51;assign word_[0]=bd[35]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[129]=valid;assign {rstatus[258+:2],ri[129],raw_rd[129]}=hold;end
begin:ret130
wire [0:0] eligible,grant;wire any;wire accept=!rv[130]||rr[130];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[39]&&dest[39]==50;assign word_[0]=bd[39]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[130]=valid;assign {rstatus[260+:2],ri[130],raw_rd[130]}=hold;end
begin:ret131
wire [0:0] eligible,grant;wire any;wire accept=!rv[131]||rr[131];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[39]&&dest[39]==51;assign word_[0]=bd[39]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[131]=valid;assign {rstatus[262+:2],ri[131],raw_rd[131]}=hold;end
begin:ret132
wire [0:0] eligible,grant;wire any;wire accept=!rv[132]||rr[132];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[43]&&dest[43]==50;assign word_[0]=bd[43]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[132]=valid;assign {rstatus[264+:2],ri[132],raw_rd[132]}=hold;end
begin:ret133
wire [0:0] eligible,grant;wire any;wire accept=!rv[133]||rr[133];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[43]&&dest[43]==51;assign word_[0]=bd[43]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[133]=valid;assign {rstatus[266+:2],ri[133],raw_rd[133]}=hold;end
begin:ret134
wire [0:0] eligible,grant;wire any;wire accept=!rv[134]||rr[134];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[47]&&dest[47]==50;assign word_[0]=bd[47]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[134]=valid;assign {rstatus[268+:2],ri[134],raw_rd[134]}=hold;end
begin:ret135
wire [0:0] eligible,grant;wire any;wire accept=!rv[135]||rr[135];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[47]&&dest[47]==51;assign word_[0]=bd[47]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[135]=valid;assign {rstatus[270+:2],ri[135],raw_rd[135]}=hold;end
begin:ret136
wire [0:0] eligible,grant;wire any;wire accept=!rv[136]||rr[136];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[51]&&dest[51]==50;assign word_[0]=bd[51]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[136]=valid;assign {rstatus[272+:2],ri[136],raw_rd[136]}=hold;end
begin:ret137
wire [0:0] eligible,grant;wire any;wire accept=!rv[137]||rr[137];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[51]&&dest[51]==51;assign word_[0]=bd[51]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[137]=valid;assign {rstatus[274+:2],ri[137],raw_rd[137]}=hold;end
begin:ret138
wire [0:0] eligible,grant;wire any;wire accept=!rv[138]||rr[138];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[55]&&dest[55]==50;assign word_[0]=bd[55]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[138]=valid;assign {rstatus[276+:2],ri[138],raw_rd[138]}=hold;end
begin:ret139
wire [0:0] eligible,grant;wire any;wire accept=!rv[139]||rr[139];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[55]&&dest[55]==51;assign word_[0]=bd[55]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[139]=valid;assign {rstatus[278+:2],ri[139],raw_rd[139]}=hold;end
begin:ret140
wire [0:0] eligible,grant;wire any;wire accept=!rv[140]||rr[140];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[59]&&dest[59]==50;assign word_[0]=bd[59]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[140]=valid;assign {rstatus[280+:2],ri[140],raw_rd[140]}=hold;end
begin:ret141
wire [0:0] eligible,grant;wire any;wire accept=!rv[141]||rr[141];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[59]&&dest[59]==51;assign word_[0]=bd[59]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[141]=valid;assign {rstatus[282+:2],ri[141],raw_rd[141]}=hold;end
begin:ret142
wire [0:0] eligible,grant;wire any;wire accept=!rv[142]||rr[142];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[63]&&dest[63]==50;assign word_[0]=bd[63]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[142]=valid;assign {rstatus[284+:2],ri[142],raw_rd[142]}=hold;end
begin:ret143
wire [0:0] eligible,grant;wire any;wire accept=!rv[143]||rr[143];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[63]&&dest[63]==51;assign word_[0]=bd[63]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[143]=valid;assign {rstatus[286+:2],ri[143],raw_rd[143]}=hold;end
begin:ret144
wire [0:0] eligible,grant;wire any;wire accept=!rv[144]||rr[144];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[67]&&dest[67]==50;assign word_[0]=bd[67]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[144]=valid;assign {rstatus[288+:2],ri[144],raw_rd[144]}=hold;end
begin:ret145
wire [0:0] eligible,grant;wire any;wire accept=!rv[145]||rr[145];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[67]&&dest[67]==51;assign word_[0]=bd[67]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[145]=valid;assign {rstatus[290+:2],ri[145],raw_rd[145]}=hold;end
begin:ret146
wire [0:0] eligible,grant;wire any;wire accept=!rv[146]||rr[146];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[71]&&dest[71]==50;assign word_[0]=bd[71]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[146]=valid;assign {rstatus[292+:2],ri[146],raw_rd[146]}=hold;end
begin:ret147
wire [0:0] eligible,grant;wire any;wire accept=!rv[147]||rr[147];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[71]&&dest[71]==51;assign word_[0]=bd[71]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[147]=valid;assign {rstatus[294+:2],ri[147],raw_rd[147]}=hold;end
begin:ret148
wire [0:0] eligible,grant;wire any;wire accept=!rv[148]||rr[148];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[75]&&dest[75]==50;assign word_[0]=bd[75]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[148]=valid;assign {rstatus[296+:2],ri[148],raw_rd[148]}=hold;end
begin:ret149
wire [0:0] eligible,grant;wire any;wire accept=!rv[149]||rr[149];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[75]&&dest[75]==51;assign word_[0]=bd[75]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[149]=valid;assign {rstatus[298+:2],ri[149],raw_rd[149]}=hold;end
begin:ret150
wire [0:0] eligible,grant;wire any;wire accept=!rv[150]||rr[150];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[79]&&dest[79]==50;assign word_[0]=bd[79]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[150]=valid;assign {rstatus[300+:2],ri[150],raw_rd[150]}=hold;end
begin:ret151
wire [0:0] eligible,grant;wire any;wire accept=!rv[151]||rr[151];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[79]&&dest[79]==51;assign word_[0]=bd[79]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[151]=valid;assign {rstatus[302+:2],ri[151],raw_rd[151]}=hold;end
begin:ret152
wire [0:0] eligible,grant;wire any;wire accept=!rv[152]||rr[152];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[83]&&dest[83]==50;assign word_[0]=bd[83]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[152]=valid;assign {rstatus[304+:2],ri[152],raw_rd[152]}=hold;end
begin:ret153
wire [0:0] eligible,grant;wire any;wire accept=!rv[153]||rr[153];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[83]&&dest[83]==51;assign word_[0]=bd[83]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[153]=valid;assign {rstatus[306+:2],ri[153],raw_rd[153]}=hold;end
begin:ret154
wire [0:0] eligible,grant;wire any;wire accept=!rv[154]||rr[154];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[87]&&dest[87]==50;assign word_[0]=bd[87]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[154]=valid;assign {rstatus[308+:2],ri[154],raw_rd[154]}=hold;end
begin:ret155
wire [0:0] eligible,grant;wire any;wire accept=!rv[155]||rr[155];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[87]&&dest[87]==51;assign word_[0]=bd[87]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[155]=valid;assign {rstatus[310+:2],ri[155],raw_rd[155]}=hold;end
begin:ret156
wire [0:0] eligible,grant;wire any;wire accept=!rv[156]||rr[156];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[91]&&dest[91]==50;assign word_[0]=bd[91]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[156]=valid;assign {rstatus[312+:2],ri[156],raw_rd[156]}=hold;end
begin:ret157
wire [0:0] eligible,grant;wire any;wire accept=!rv[157]||rr[157];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[91]&&dest[91]==51;assign word_[0]=bd[91]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[157]=valid;assign {rstatus[314+:2],ri[157],raw_rd[157]}=hold;end
begin:ret158
wire [0:0] eligible,grant;wire any;wire accept=!rv[158]||rr[158];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[95]&&dest[95]==50;assign word_[0]=bd[95]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[158]=valid;assign {rstatus[316+:2],ri[158],raw_rd[158]}=hold;end
begin:ret159
wire [0:0] eligible,grant;wire any;wire accept=!rv[159]||rr[159];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[95]&&dest[95]==51;assign word_[0]=bd[95]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[159]=valid;assign {rstatus[318+:2],ri[159],raw_rd[159]}=hold;end
begin:ret160
wire [0:0] eligible,grant;wire any;wire accept=!rv[160]||rr[160];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[99]&&dest[99]==50;assign word_[0]=bd[99]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[160]=valid;assign {rstatus[320+:2],ri[160],raw_rd[160]}=hold;end
begin:ret161
wire [0:0] eligible,grant;wire any;wire accept=!rv[161]||rr[161];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[99]&&dest[99]==51;assign word_[0]=bd[99]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[161]=valid;assign {rstatus[322+:2],ri[161],raw_rd[161]}=hold;end
begin:ret162
wire [0:0] eligible,grant;wire any;wire accept=!rv[162]||rr[162];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[103]&&dest[103]==50;assign word_[0]=bd[103]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[162]=valid;assign {rstatus[324+:2],ri[162],raw_rd[162]}=hold;end
begin:ret163
wire [0:0] eligible,grant;wire any;wire accept=!rv[163]||rr[163];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[103]&&dest[103]==51;assign word_[0]=bd[103]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[163]=valid;assign {rstatus[326+:2],ri[163],raw_rd[163]}=hold;end
begin:ret164
wire [0:0] eligible,grant;wire any;wire accept=!rv[164]||rr[164];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[107]&&dest[107]==50;assign word_[0]=bd[107]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[164]=valid;assign {rstatus[328+:2],ri[164],raw_rd[164]}=hold;end
begin:ret165
wire [0:0] eligible,grant;wire any;wire accept=!rv[165]||rr[165];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[107]&&dest[107]==51;assign word_[0]=bd[107]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[165]=valid;assign {rstatus[330+:2],ri[165],raw_rd[165]}=hold;end
begin:ret166
wire [0:0] eligible,grant;wire any;wire accept=!rv[166]||rr[166];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[111]&&dest[111]==50;assign word_[0]=bd[111]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[166]=valid;assign {rstatus[332+:2],ri[166],raw_rd[166]}=hold;end
begin:ret167
wire [0:0] eligible,grant;wire any;wire accept=!rv[167]||rr[167];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[111]&&dest[111]==51;assign word_[0]=bd[111]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[167]=valid;assign {rstatus[334+:2],ri[167],raw_rd[167]}=hold;end
begin:ret168
wire [0:0] eligible,grant;wire any;wire accept=!rv[168]||rr[168];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[115]&&dest[115]==50;assign word_[0]=bd[115]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[168]=valid;assign {rstatus[336+:2],ri[168],raw_rd[168]}=hold;end
begin:ret169
wire [0:0] eligible,grant;wire any;wire accept=!rv[169]||rr[169];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[115]&&dest[115]==51;assign word_[0]=bd[115]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[169]=valid;assign {rstatus[338+:2],ri[169],raw_rd[169]}=hold;end
begin:ret170
wire [0:0] eligible,grant;wire any;wire accept=!rv[170]||rr[170];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[119]&&dest[119]==50;assign word_[0]=bd[119]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[170]=valid;assign {rstatus[340+:2],ri[170],raw_rd[170]}=hold;end
begin:ret171
wire [0:0] eligible,grant;wire any;wire accept=!rv[171]||rr[171];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[119]&&dest[119]==51;assign word_[0]=bd[119]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[171]=valid;assign {rstatus[342+:2],ri[171],raw_rd[171]}=hold;end
begin:ret172
wire [0:0] eligible,grant;wire any;wire accept=!rv[172]||rr[172];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[123]&&dest[123]==50;assign word_[0]=bd[123]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[172]=valid;assign {rstatus[344+:2],ri[172],raw_rd[172]}=hold;end
begin:ret173
wire [0:0] eligible,grant;wire any;wire accept=!rv[173]||rr[173];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[123]&&dest[123]==51;assign word_[0]=bd[123]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[173]=valid;assign {rstatus[346+:2],ri[173],raw_rd[173]}=hold;end
begin:ret174
wire [0:0] eligible,grant;wire any;wire accept=!rv[174]||rr[174];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[127]&&dest[127]==50;assign word_[0]=bd[127]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[174]=valid;assign {rstatus[348+:2],ri[174],raw_rd[174]}=hold;end
begin:ret175
wire [0:0] eligible,grant;wire any;wire accept=!rv[175]||rr[175];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[127]&&dest[127]==51;assign word_[0]=bd[127]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[175]=valid;assign {rstatus[350+:2],ri[175],raw_rd[175]}=hold;end
begin:ret176
wire [0:0] eligible,grant;wire any;wire accept=!rv[176]||rr[176];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[1]&&dest[1]==52;assign word_[0]=bd[1]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[176]=valid;assign {rstatus[352+:2],ri[176],raw_rd[176]}=hold;end
begin:ret177
wire [0:0] eligible,grant;wire any;wire accept=!rv[177]||rr[177];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[5]&&dest[5]==52;assign word_[0]=bd[5]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[177]=valid;assign {rstatus[354+:2],ri[177],raw_rd[177]}=hold;end
begin:ret178
wire [0:0] eligible,grant;wire any;wire accept=!rv[178]||rr[178];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[9]&&dest[9]==52;assign word_[0]=bd[9]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[178]=valid;assign {rstatus[356+:2],ri[178],raw_rd[178]}=hold;end
begin:ret179
wire [0:0] eligible,grant;wire any;wire accept=!rv[179]||rr[179];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[13]&&dest[13]==52;assign word_[0]=bd[13]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[179]=valid;assign {rstatus[358+:2],ri[179],raw_rd[179]}=hold;end
begin:ret180
wire [0:0] eligible,grant;wire any;wire accept=!rv[180]||rr[180];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[17]&&dest[17]==52;assign word_[0]=bd[17]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[180]=valid;assign {rstatus[360+:2],ri[180],raw_rd[180]}=hold;end
begin:ret181
wire [0:0] eligible,grant;wire any;wire accept=!rv[181]||rr[181];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[21]&&dest[21]==52;assign word_[0]=bd[21]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[181]=valid;assign {rstatus[362+:2],ri[181],raw_rd[181]}=hold;end
begin:ret182
wire [0:0] eligible,grant;wire any;wire accept=!rv[182]||rr[182];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[25]&&dest[25]==52;assign word_[0]=bd[25]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[182]=valid;assign {rstatus[364+:2],ri[182],raw_rd[182]}=hold;end
begin:ret183
wire [0:0] eligible,grant;wire any;wire accept=!rv[183]||rr[183];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[29]&&dest[29]==52;assign word_[0]=bd[29]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[183]=valid;assign {rstatus[366+:2],ri[183],raw_rd[183]}=hold;end
begin:ret184
wire [0:0] eligible,grant;wire any;wire accept=!rv[184]||rr[184];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[33]&&dest[33]==52;assign word_[0]=bd[33]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[184]=valid;assign {rstatus[368+:2],ri[184],raw_rd[184]}=hold;end
begin:ret185
wire [0:0] eligible,grant;wire any;wire accept=!rv[185]||rr[185];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[37]&&dest[37]==52;assign word_[0]=bd[37]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[185]=valid;assign {rstatus[370+:2],ri[185],raw_rd[185]}=hold;end
begin:ret186
wire [0:0] eligible,grant;wire any;wire accept=!rv[186]||rr[186];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[41]&&dest[41]==52;assign word_[0]=bd[41]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[186]=valid;assign {rstatus[372+:2],ri[186],raw_rd[186]}=hold;end
begin:ret187
wire [0:0] eligible,grant;wire any;wire accept=!rv[187]||rr[187];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[45]&&dest[45]==52;assign word_[0]=bd[45]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[187]=valid;assign {rstatus[374+:2],ri[187],raw_rd[187]}=hold;end
begin:ret188
wire [0:0] eligible,grant;wire any;wire accept=!rv[188]||rr[188];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[49]&&dest[49]==52;assign word_[0]=bd[49]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[188]=valid;assign {rstatus[376+:2],ri[188],raw_rd[188]}=hold;end
begin:ret189
wire [0:0] eligible,grant;wire any;wire accept=!rv[189]||rr[189];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[53]&&dest[53]==52;assign word_[0]=bd[53]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[189]=valid;assign {rstatus[378+:2],ri[189],raw_rd[189]}=hold;end
begin:ret190
wire [0:0] eligible,grant;wire any;wire accept=!rv[190]||rr[190];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[57]&&dest[57]==52;assign word_[0]=bd[57]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[190]=valid;assign {rstatus[380+:2],ri[190],raw_rd[190]}=hold;end
begin:ret191
wire [0:0] eligible,grant;wire any;wire accept=!rv[191]||rr[191];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[61]&&dest[61]==52;assign word_[0]=bd[61]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[191]=valid;assign {rstatus[382+:2],ri[191],raw_rd[191]}=hold;end
begin:ret192
wire [0:0] eligible,grant;wire any;wire accept=!rv[192]||rr[192];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[65]&&dest[65]==52;assign word_[0]=bd[65]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[192]=valid;assign {rstatus[384+:2],ri[192],raw_rd[192]}=hold;end
begin:ret193
wire [0:0] eligible,grant;wire any;wire accept=!rv[193]||rr[193];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[69]&&dest[69]==52;assign word_[0]=bd[69]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[193]=valid;assign {rstatus[386+:2],ri[193],raw_rd[193]}=hold;end
begin:ret194
wire [0:0] eligible,grant;wire any;wire accept=!rv[194]||rr[194];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[73]&&dest[73]==52;assign word_[0]=bd[73]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[194]=valid;assign {rstatus[388+:2],ri[194],raw_rd[194]}=hold;end
begin:ret195
wire [0:0] eligible,grant;wire any;wire accept=!rv[195]||rr[195];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[77]&&dest[77]==52;assign word_[0]=bd[77]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[195]=valid;assign {rstatus[390+:2],ri[195],raw_rd[195]}=hold;end
begin:ret196
wire [0:0] eligible,grant;wire any;wire accept=!rv[196]||rr[196];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[81]&&dest[81]==52;assign word_[0]=bd[81]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[196]=valid;assign {rstatus[392+:2],ri[196],raw_rd[196]}=hold;end
begin:ret197
wire [0:0] eligible,grant;wire any;wire accept=!rv[197]||rr[197];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[85]&&dest[85]==52;assign word_[0]=bd[85]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[197]=valid;assign {rstatus[394+:2],ri[197],raw_rd[197]}=hold;end
begin:ret198
wire [0:0] eligible,grant;wire any;wire accept=!rv[198]||rr[198];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[89]&&dest[89]==52;assign word_[0]=bd[89]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[198]=valid;assign {rstatus[396+:2],ri[198],raw_rd[198]}=hold;end
begin:ret199
wire [0:0] eligible,grant;wire any;wire accept=!rv[199]||rr[199];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[93]&&dest[93]==52;assign word_[0]=bd[93]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[199]=valid;assign {rstatus[398+:2],ri[199],raw_rd[199]}=hold;end
begin:ret200
wire [0:0] eligible,grant;wire any;wire accept=!rv[200]||rr[200];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[97]&&dest[97]==52;assign word_[0]=bd[97]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[200]=valid;assign {rstatus[400+:2],ri[200],raw_rd[200]}=hold;end
begin:ret201
wire [0:0] eligible,grant;wire any;wire accept=!rv[201]||rr[201];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[101]&&dest[101]==52;assign word_[0]=bd[101]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[201]=valid;assign {rstatus[402+:2],ri[201],raw_rd[201]}=hold;end
begin:ret202
wire [0:0] eligible,grant;wire any;wire accept=!rv[202]||rr[202];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[105]&&dest[105]==52;assign word_[0]=bd[105]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[202]=valid;assign {rstatus[404+:2],ri[202],raw_rd[202]}=hold;end
begin:ret203
wire [0:0] eligible,grant;wire any;wire accept=!rv[203]||rr[203];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[109]&&dest[109]==52;assign word_[0]=bd[109]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[203]=valid;assign {rstatus[406+:2],ri[203],raw_rd[203]}=hold;end
begin:ret204
wire [0:0] eligible,grant;wire any;wire accept=!rv[204]||rr[204];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[113]&&dest[113]==52;assign word_[0]=bd[113]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[204]=valid;assign {rstatus[408+:2],ri[204],raw_rd[204]}=hold;end
begin:ret205
wire [0:0] eligible,grant;wire any;wire accept=!rv[205]||rr[205];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[117]&&dest[117]==52;assign word_[0]=bd[117]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[205]=valid;assign {rstatus[410+:2],ri[205],raw_rd[205]}=hold;end
begin:ret206
wire [0:0] eligible,grant;wire any;wire accept=!rv[206]||rr[206];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[121]&&dest[121]==52;assign word_[0]=bd[121]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[206]=valid;assign {rstatus[412+:2],ri[206],raw_rd[206]}=hold;end
begin:ret207
wire [0:0] eligible,grant;wire any;wire accept=!rv[207]||rr[207];reg valid;reg [331:0] hold;wire [331:0] word_[1];
assign eligible[0]=bv[125]&&dest[125]==52;assign word_[0]=bd[125]&{332{grant[0]}};
assign any=eligible[0];assign grant=eligible;
wire [331:0] selected=word_[0];
always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[207]=valid;assign {rstatus[414+:2],ri[207],raw_rd[207]}=hold;end
assign bxv[0]=bv[0]&&dest[0]<48;assign brdest[0*6+:6]=dest[0];assign brdata[0*332+:332]=bd[0];assign br[0]=(dest[0]<48&&bxr[0]);
assign bxv[1]=bv[1]&&dest[1]<48;assign brdest[1*6+:6]=dest[1];assign brdata[1*332+:332]=bd[1];assign br[1]=(dest[1]<48&&bxr[1])|(ret176.accept&&ret176.grant[0]);
assign br[2]=(ret48.accept&&ret48.grant[0])|(ret49.accept&&ret49.grant[0]);
assign br[3]=(ret112.accept&&ret112.grant[0])|(ret113.accept&&ret113.grant[0]);
assign bxv[2]=bv[4]&&dest[4]<48;assign brdest[2*6+:6]=dest[4];assign brdata[2*332+:332]=bd[4];assign br[4]=(dest[4]<48&&bxr[2]);
assign bxv[3]=bv[5]&&dest[5]<48;assign brdest[3*6+:6]=dest[5];assign brdata[3*332+:332]=bd[5];assign br[5]=(dest[5]<48&&bxr[3])|(ret177.accept&&ret177.grant[0]);
assign br[6]=(ret50.accept&&ret50.grant[0])|(ret51.accept&&ret51.grant[0]);
assign br[7]=(ret114.accept&&ret114.grant[0])|(ret115.accept&&ret115.grant[0]);
assign bxv[4]=bv[8]&&dest[8]<48;assign brdest[4*6+:6]=dest[8];assign brdata[4*332+:332]=bd[8];assign br[8]=(dest[8]<48&&bxr[4]);
assign bxv[5]=bv[9]&&dest[9]<48;assign brdest[5*6+:6]=dest[9];assign brdata[5*332+:332]=bd[9];assign br[9]=(dest[9]<48&&bxr[5])|(ret178.accept&&ret178.grant[0]);
assign br[10]=(ret52.accept&&ret52.grant[0])|(ret53.accept&&ret53.grant[0]);
assign br[11]=(ret116.accept&&ret116.grant[0])|(ret117.accept&&ret117.grant[0]);
assign bxv[6]=bv[12]&&dest[12]<48;assign brdest[6*6+:6]=dest[12];assign brdata[6*332+:332]=bd[12];assign br[12]=(dest[12]<48&&bxr[6]);
assign bxv[7]=bv[13]&&dest[13]<48;assign brdest[7*6+:6]=dest[13];assign brdata[7*332+:332]=bd[13];assign br[13]=(dest[13]<48&&bxr[7])|(ret179.accept&&ret179.grant[0]);
assign br[14]=(ret54.accept&&ret54.grant[0])|(ret55.accept&&ret55.grant[0]);
assign br[15]=(ret118.accept&&ret118.grant[0])|(ret119.accept&&ret119.grant[0]);
assign bxv[8]=bv[16]&&dest[16]<48;assign brdest[8*6+:6]=dest[16];assign brdata[8*332+:332]=bd[16];assign br[16]=(dest[16]<48&&bxr[8]);
assign bxv[9]=bv[17]&&dest[17]<48;assign brdest[9*6+:6]=dest[17];assign brdata[9*332+:332]=bd[17];assign br[17]=(dest[17]<48&&bxr[9])|(ret180.accept&&ret180.grant[0]);
assign br[18]=(ret56.accept&&ret56.grant[0])|(ret57.accept&&ret57.grant[0]);
assign br[19]=(ret120.accept&&ret120.grant[0])|(ret121.accept&&ret121.grant[0]);
assign bxv[10]=bv[20]&&dest[20]<48;assign brdest[10*6+:6]=dest[20];assign brdata[10*332+:332]=bd[20];assign br[20]=(dest[20]<48&&bxr[10]);
assign bxv[11]=bv[21]&&dest[21]<48;assign brdest[11*6+:6]=dest[21];assign brdata[11*332+:332]=bd[21];assign br[21]=(dest[21]<48&&bxr[11])|(ret181.accept&&ret181.grant[0]);
assign br[22]=(ret58.accept&&ret58.grant[0])|(ret59.accept&&ret59.grant[0]);
assign br[23]=(ret122.accept&&ret122.grant[0])|(ret123.accept&&ret123.grant[0]);
assign bxv[12]=bv[24]&&dest[24]<48;assign brdest[12*6+:6]=dest[24];assign brdata[12*332+:332]=bd[24];assign br[24]=(dest[24]<48&&bxr[12]);
assign bxv[13]=bv[25]&&dest[25]<48;assign brdest[13*6+:6]=dest[25];assign brdata[13*332+:332]=bd[25];assign br[25]=(dest[25]<48&&bxr[13])|(ret182.accept&&ret182.grant[0]);
assign br[26]=(ret60.accept&&ret60.grant[0])|(ret61.accept&&ret61.grant[0]);
assign br[27]=(ret124.accept&&ret124.grant[0])|(ret125.accept&&ret125.grant[0]);
assign bxv[14]=bv[28]&&dest[28]<48;assign brdest[14*6+:6]=dest[28];assign brdata[14*332+:332]=bd[28];assign br[28]=(dest[28]<48&&bxr[14]);
assign bxv[15]=bv[29]&&dest[29]<48;assign brdest[15*6+:6]=dest[29];assign brdata[15*332+:332]=bd[29];assign br[29]=(dest[29]<48&&bxr[15])|(ret183.accept&&ret183.grant[0]);
assign br[30]=(ret62.accept&&ret62.grant[0])|(ret63.accept&&ret63.grant[0]);
assign br[31]=(ret126.accept&&ret126.grant[0])|(ret127.accept&&ret127.grant[0]);
assign bxv[16]=bv[32]&&dest[32]<48;assign brdest[16*6+:6]=dest[32];assign brdata[16*332+:332]=bd[32];assign br[32]=(dest[32]<48&&bxr[16]);
assign bxv[17]=bv[33]&&dest[33]<48;assign brdest[17*6+:6]=dest[33];assign brdata[17*332+:332]=bd[33];assign br[33]=(dest[33]<48&&bxr[17])|(ret184.accept&&ret184.grant[0]);
assign br[34]=(ret64.accept&&ret64.grant[0])|(ret65.accept&&ret65.grant[0]);
assign br[35]=(ret128.accept&&ret128.grant[0])|(ret129.accept&&ret129.grant[0]);
assign bxv[18]=bv[36]&&dest[36]<48;assign brdest[18*6+:6]=dest[36];assign brdata[18*332+:332]=bd[36];assign br[36]=(dest[36]<48&&bxr[18]);
assign bxv[19]=bv[37]&&dest[37]<48;assign brdest[19*6+:6]=dest[37];assign brdata[19*332+:332]=bd[37];assign br[37]=(dest[37]<48&&bxr[19])|(ret185.accept&&ret185.grant[0]);
assign br[38]=(ret66.accept&&ret66.grant[0])|(ret67.accept&&ret67.grant[0]);
assign br[39]=(ret130.accept&&ret130.grant[0])|(ret131.accept&&ret131.grant[0]);
assign bxv[20]=bv[40]&&dest[40]<48;assign brdest[20*6+:6]=dest[40];assign brdata[20*332+:332]=bd[40];assign br[40]=(dest[40]<48&&bxr[20]);
assign bxv[21]=bv[41]&&dest[41]<48;assign brdest[21*6+:6]=dest[41];assign brdata[21*332+:332]=bd[41];assign br[41]=(dest[41]<48&&bxr[21])|(ret186.accept&&ret186.grant[0]);
assign br[42]=(ret68.accept&&ret68.grant[0])|(ret69.accept&&ret69.grant[0]);
assign br[43]=(ret132.accept&&ret132.grant[0])|(ret133.accept&&ret133.grant[0]);
assign bxv[22]=bv[44]&&dest[44]<48;assign brdest[22*6+:6]=dest[44];assign brdata[22*332+:332]=bd[44];assign br[44]=(dest[44]<48&&bxr[22]);
assign bxv[23]=bv[45]&&dest[45]<48;assign brdest[23*6+:6]=dest[45];assign brdata[23*332+:332]=bd[45];assign br[45]=(dest[45]<48&&bxr[23])|(ret187.accept&&ret187.grant[0]);
assign br[46]=(ret70.accept&&ret70.grant[0])|(ret71.accept&&ret71.grant[0]);
assign br[47]=(ret134.accept&&ret134.grant[0])|(ret135.accept&&ret135.grant[0]);
assign bxv[24]=bv[48]&&dest[48]<48;assign brdest[24*6+:6]=dest[48];assign brdata[24*332+:332]=bd[48];assign br[48]=(dest[48]<48&&bxr[24]);
assign bxv[25]=bv[49]&&dest[49]<48;assign brdest[25*6+:6]=dest[49];assign brdata[25*332+:332]=bd[49];assign br[49]=(dest[49]<48&&bxr[25])|(ret188.accept&&ret188.grant[0]);
assign br[50]=(ret72.accept&&ret72.grant[0])|(ret73.accept&&ret73.grant[0]);
assign br[51]=(ret136.accept&&ret136.grant[0])|(ret137.accept&&ret137.grant[0]);
assign bxv[26]=bv[52]&&dest[52]<48;assign brdest[26*6+:6]=dest[52];assign brdata[26*332+:332]=bd[52];assign br[52]=(dest[52]<48&&bxr[26]);
assign bxv[27]=bv[53]&&dest[53]<48;assign brdest[27*6+:6]=dest[53];assign brdata[27*332+:332]=bd[53];assign br[53]=(dest[53]<48&&bxr[27])|(ret189.accept&&ret189.grant[0]);
assign br[54]=(ret74.accept&&ret74.grant[0])|(ret75.accept&&ret75.grant[0]);
assign br[55]=(ret138.accept&&ret138.grant[0])|(ret139.accept&&ret139.grant[0]);
assign bxv[28]=bv[56]&&dest[56]<48;assign brdest[28*6+:6]=dest[56];assign brdata[28*332+:332]=bd[56];assign br[56]=(dest[56]<48&&bxr[28]);
assign bxv[29]=bv[57]&&dest[57]<48;assign brdest[29*6+:6]=dest[57];assign brdata[29*332+:332]=bd[57];assign br[57]=(dest[57]<48&&bxr[29])|(ret190.accept&&ret190.grant[0]);
assign br[58]=(ret76.accept&&ret76.grant[0])|(ret77.accept&&ret77.grant[0]);
assign br[59]=(ret140.accept&&ret140.grant[0])|(ret141.accept&&ret141.grant[0]);
assign bxv[30]=bv[60]&&dest[60]<48;assign brdest[30*6+:6]=dest[60];assign brdata[30*332+:332]=bd[60];assign br[60]=(dest[60]<48&&bxr[30]);
assign bxv[31]=bv[61]&&dest[61]<48;assign brdest[31*6+:6]=dest[61];assign brdata[31*332+:332]=bd[61];assign br[61]=(dest[61]<48&&bxr[31])|(ret191.accept&&ret191.grant[0]);
assign br[62]=(ret78.accept&&ret78.grant[0])|(ret79.accept&&ret79.grant[0]);
assign br[63]=(ret142.accept&&ret142.grant[0])|(ret143.accept&&ret143.grant[0]);
assign bxv[32]=bv[64]&&dest[64]<48;assign brdest[32*6+:6]=dest[64];assign brdata[32*332+:332]=bd[64];assign br[64]=(dest[64]<48&&bxr[32]);
assign bxv[33]=bv[65]&&dest[65]<48;assign brdest[33*6+:6]=dest[65];assign brdata[33*332+:332]=bd[65];assign br[65]=(dest[65]<48&&bxr[33])|(ret192.accept&&ret192.grant[0]);
assign br[66]=(ret80.accept&&ret80.grant[0])|(ret81.accept&&ret81.grant[0]);
assign br[67]=(ret144.accept&&ret144.grant[0])|(ret145.accept&&ret145.grant[0]);
assign bxv[34]=bv[68]&&dest[68]<48;assign brdest[34*6+:6]=dest[68];assign brdata[34*332+:332]=bd[68];assign br[68]=(dest[68]<48&&bxr[34]);
assign bxv[35]=bv[69]&&dest[69]<48;assign brdest[35*6+:6]=dest[69];assign brdata[35*332+:332]=bd[69];assign br[69]=(dest[69]<48&&bxr[35])|(ret193.accept&&ret193.grant[0]);
assign br[70]=(ret82.accept&&ret82.grant[0])|(ret83.accept&&ret83.grant[0]);
assign br[71]=(ret146.accept&&ret146.grant[0])|(ret147.accept&&ret147.grant[0]);
assign bxv[36]=bv[72]&&dest[72]<48;assign brdest[36*6+:6]=dest[72];assign brdata[36*332+:332]=bd[72];assign br[72]=(dest[72]<48&&bxr[36]);
assign bxv[37]=bv[73]&&dest[73]<48;assign brdest[37*6+:6]=dest[73];assign brdata[37*332+:332]=bd[73];assign br[73]=(dest[73]<48&&bxr[37])|(ret194.accept&&ret194.grant[0]);
assign br[74]=(ret84.accept&&ret84.grant[0])|(ret85.accept&&ret85.grant[0]);
assign br[75]=(ret148.accept&&ret148.grant[0])|(ret149.accept&&ret149.grant[0]);
assign bxv[38]=bv[76]&&dest[76]<48;assign brdest[38*6+:6]=dest[76];assign brdata[38*332+:332]=bd[76];assign br[76]=(dest[76]<48&&bxr[38]);
assign bxv[39]=bv[77]&&dest[77]<48;assign brdest[39*6+:6]=dest[77];assign brdata[39*332+:332]=bd[77];assign br[77]=(dest[77]<48&&bxr[39])|(ret195.accept&&ret195.grant[0]);
assign br[78]=(ret86.accept&&ret86.grant[0])|(ret87.accept&&ret87.grant[0]);
assign br[79]=(ret150.accept&&ret150.grant[0])|(ret151.accept&&ret151.grant[0]);
assign bxv[40]=bv[80]&&dest[80]<48;assign brdest[40*6+:6]=dest[80];assign brdata[40*332+:332]=bd[80];assign br[80]=(dest[80]<48&&bxr[40]);
assign bxv[41]=bv[81]&&dest[81]<48;assign brdest[41*6+:6]=dest[81];assign brdata[41*332+:332]=bd[81];assign br[81]=(dest[81]<48&&bxr[41])|(ret196.accept&&ret196.grant[0]);
assign br[82]=(ret88.accept&&ret88.grant[0])|(ret89.accept&&ret89.grant[0]);
assign br[83]=(ret152.accept&&ret152.grant[0])|(ret153.accept&&ret153.grant[0]);
assign bxv[42]=bv[84]&&dest[84]<48;assign brdest[42*6+:6]=dest[84];assign brdata[42*332+:332]=bd[84];assign br[84]=(dest[84]<48&&bxr[42]);
assign bxv[43]=bv[85]&&dest[85]<48;assign brdest[43*6+:6]=dest[85];assign brdata[43*332+:332]=bd[85];assign br[85]=(dest[85]<48&&bxr[43])|(ret197.accept&&ret197.grant[0]);
assign br[86]=(ret90.accept&&ret90.grant[0])|(ret91.accept&&ret91.grant[0]);
assign br[87]=(ret154.accept&&ret154.grant[0])|(ret155.accept&&ret155.grant[0]);
assign bxv[44]=bv[88]&&dest[88]<48;assign brdest[44*6+:6]=dest[88];assign brdata[44*332+:332]=bd[88];assign br[88]=(dest[88]<48&&bxr[44]);
assign bxv[45]=bv[89]&&dest[89]<48;assign brdest[45*6+:6]=dest[89];assign brdata[45*332+:332]=bd[89];assign br[89]=(dest[89]<48&&bxr[45])|(ret198.accept&&ret198.grant[0]);
assign br[90]=(ret92.accept&&ret92.grant[0])|(ret93.accept&&ret93.grant[0]);
assign br[91]=(ret156.accept&&ret156.grant[0])|(ret157.accept&&ret157.grant[0]);
assign bxv[46]=bv[92]&&dest[92]<48;assign brdest[46*6+:6]=dest[92];assign brdata[46*332+:332]=bd[92];assign br[92]=(dest[92]<48&&bxr[46]);
assign bxv[47]=bv[93]&&dest[93]<48;assign brdest[47*6+:6]=dest[93];assign brdata[47*332+:332]=bd[93];assign br[93]=(dest[93]<48&&bxr[47])|(ret199.accept&&ret199.grant[0]);
assign br[94]=(ret94.accept&&ret94.grant[0])|(ret95.accept&&ret95.grant[0]);
assign br[95]=(ret158.accept&&ret158.grant[0])|(ret159.accept&&ret159.grant[0]);
assign bxv[48]=bv[96]&&dest[96]<48;assign brdest[48*6+:6]=dest[96];assign brdata[48*332+:332]=bd[96];assign br[96]=(dest[96]<48&&bxr[48]);
assign bxv[49]=bv[97]&&dest[97]<48;assign brdest[49*6+:6]=dest[97];assign brdata[49*332+:332]=bd[97];assign br[97]=(dest[97]<48&&bxr[49])|(ret200.accept&&ret200.grant[0]);
assign br[98]=(ret96.accept&&ret96.grant[0])|(ret97.accept&&ret97.grant[0]);
assign br[99]=(ret160.accept&&ret160.grant[0])|(ret161.accept&&ret161.grant[0]);
assign bxv[50]=bv[100]&&dest[100]<48;assign brdest[50*6+:6]=dest[100];assign brdata[50*332+:332]=bd[100];assign br[100]=(dest[100]<48&&bxr[50]);
assign bxv[51]=bv[101]&&dest[101]<48;assign brdest[51*6+:6]=dest[101];assign brdata[51*332+:332]=bd[101];assign br[101]=(dest[101]<48&&bxr[51])|(ret201.accept&&ret201.grant[0]);
assign br[102]=(ret98.accept&&ret98.grant[0])|(ret99.accept&&ret99.grant[0]);
assign br[103]=(ret162.accept&&ret162.grant[0])|(ret163.accept&&ret163.grant[0]);
assign bxv[52]=bv[104]&&dest[104]<48;assign brdest[52*6+:6]=dest[104];assign brdata[52*332+:332]=bd[104];assign br[104]=(dest[104]<48&&bxr[52]);
assign bxv[53]=bv[105]&&dest[105]<48;assign brdest[53*6+:6]=dest[105];assign brdata[53*332+:332]=bd[105];assign br[105]=(dest[105]<48&&bxr[53])|(ret202.accept&&ret202.grant[0]);
assign br[106]=(ret100.accept&&ret100.grant[0])|(ret101.accept&&ret101.grant[0]);
assign br[107]=(ret164.accept&&ret164.grant[0])|(ret165.accept&&ret165.grant[0]);
assign bxv[54]=bv[108]&&dest[108]<48;assign brdest[54*6+:6]=dest[108];assign brdata[54*332+:332]=bd[108];assign br[108]=(dest[108]<48&&bxr[54]);
assign bxv[55]=bv[109]&&dest[109]<48;assign brdest[55*6+:6]=dest[109];assign brdata[55*332+:332]=bd[109];assign br[109]=(dest[109]<48&&bxr[55])|(ret203.accept&&ret203.grant[0]);
assign br[110]=(ret102.accept&&ret102.grant[0])|(ret103.accept&&ret103.grant[0]);
assign br[111]=(ret166.accept&&ret166.grant[0])|(ret167.accept&&ret167.grant[0]);
assign bxv[56]=bv[112]&&dest[112]<48;assign brdest[56*6+:6]=dest[112];assign brdata[56*332+:332]=bd[112];assign br[112]=(dest[112]<48&&bxr[56]);
assign bxv[57]=bv[113]&&dest[113]<48;assign brdest[57*6+:6]=dest[113];assign brdata[57*332+:332]=bd[113];assign br[113]=(dest[113]<48&&bxr[57])|(ret204.accept&&ret204.grant[0]);
assign br[114]=(ret104.accept&&ret104.grant[0])|(ret105.accept&&ret105.grant[0]);
assign br[115]=(ret168.accept&&ret168.grant[0])|(ret169.accept&&ret169.grant[0]);
assign bxv[58]=bv[116]&&dest[116]<48;assign brdest[58*6+:6]=dest[116];assign brdata[58*332+:332]=bd[116];assign br[116]=(dest[116]<48&&bxr[58]);
assign bxv[59]=bv[117]&&dest[117]<48;assign brdest[59*6+:6]=dest[117];assign brdata[59*332+:332]=bd[117];assign br[117]=(dest[117]<48&&bxr[59])|(ret205.accept&&ret205.grant[0]);
assign br[118]=(ret106.accept&&ret106.grant[0])|(ret107.accept&&ret107.grant[0]);
assign br[119]=(ret170.accept&&ret170.grant[0])|(ret171.accept&&ret171.grant[0]);
assign bxv[60]=bv[120]&&dest[120]<48;assign brdest[60*6+:6]=dest[120];assign brdata[60*332+:332]=bd[120];assign br[120]=(dest[120]<48&&bxr[60]);
assign bxv[61]=bv[121]&&dest[121]<48;assign brdest[61*6+:6]=dest[121];assign brdata[61*332+:332]=bd[121];assign br[121]=(dest[121]<48&&bxr[61])|(ret206.accept&&ret206.grant[0]);
assign br[122]=(ret108.accept&&ret108.grant[0])|(ret109.accept&&ret109.grant[0]);
assign br[123]=(ret172.accept&&ret172.grant[0])|(ret173.accept&&ret173.grant[0]);
assign bxv[62]=bv[124]&&dest[124]<48;assign brdest[62*6+:6]=dest[124];assign brdata[62*332+:332]=bd[124];assign br[124]=(dest[124]<48&&bxr[62]);
assign bxv[63]=bv[125]&&dest[125]<48;assign brdest[63*6+:6]=dest[125];assign brdata[63*332+:332]=bd[125];assign br[125]=(dest[125]<48&&bxr[63])|(ret207.accept&&ret207.grant[0]);
assign br[126]=(ret110.accept&&ret110.grant[0])|(ret111.accept&&ret111.grant[0]);
assign br[127]=(ret174.accept&&ret174.grant[0])|(ret175.accept&&ret175.grant[0]);
endmodule
