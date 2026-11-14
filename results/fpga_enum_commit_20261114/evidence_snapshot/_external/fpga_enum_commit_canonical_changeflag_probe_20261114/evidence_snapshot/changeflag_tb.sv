`timescale 1ns/1ps
module changeflag_tb;
 reg[255:0] old_labels,line_input;reg[63:0] operand;reg[67:0] oldpv;reg[2:0] op;reg[1:0] sector;reg[27:0] argument;wire changed,reference_changed;
 probe_apply dut(.*);
 reg[63:0] edges[8];reg[16:0] pvs[4];reg[63:0] rng=64'h9e3779b97f4a7c15;integer count=0,changed_count=0,unchanged_count=0;integer a,b,p,o,z,i,k;integer by_op[8];
 function automatic[63:0] random64(input[63:0] x);reg[63:0] y;begin y=x^(x<<13);y=y^(y>>7);random64=y^(y<<17);end endfunction
 task check_one;begin #1;
  if(changed!==reference_changed)$fatal(1,"change flag mismatch op=%0d sector=%0d labels=%h operand=%h line=%h pv=%h actual=%b expected=%b",op,sector,old_labels,operand,line_input,oldpv,changed,reference_changed);
  count=count+1;by_op[op]=by_op[op]+1;if(changed)changed_count=changed_count+1;else unchanged_count=unchanged_count+1;
 end endtask
 initial begin #200000;$fatal(1,"watchdog");end
 initial begin
  edges[0]=0;edges[1]=1;edges[2]=64'h7f8000007f800000;edges[3]=64'hffffffffffffffff;edges[4]=64'h3f80000040000000;edges[5]=64'h4100000000000000;edges[6]=64'h411fffffffffffff;edges[7]=64'h8000000000000000;
  pvs[0]=0;pvs[1]=17'h10001;pvs[2]=17'h10000;pvs[3]=17'h1ffff;for(i=0;i<8;i=i+1)by_op[i]=0;
  for(a=0;a<8;a=a+1)for(b=0;b<8;b=b+1)for(p=0;p<4;p=p+1)for(o=0;o<8;o=o+1)for(z=0;z<4;z=z+1)begin
   op=o;sector=z;operand=edges[b];oldpv={4{pvs[p]}};argument={pvs[p][15:0],edges[a][63:52]};
   for(k=0;k<4;k=k+1)begin old_labels[k*64+:64]=edges[(a+k)%8];line_input[k*64+:64]=edges[(b+k)%8];end
   check_one();
  end
  for(i=0;i<65536;i=i+1)begin
   op=i%8;sector=(i/8)%4;rng=random64(rng);operand=rng;argument=rng[27:0];rng=random64(rng);oldpv={rng[3:0],rng};
   for(k=0;k<4;k=k+1)begin rng=random64(rng);old_labels[k*64+:64]=rng;rng=random64(rng);line_input[k*64+:64]=rng;end
   if(i%17==0)begin operand=old_labels[sector*64+:64];line_input=old_labels;end
   check_one();
  end
  if(count!=73728||changed_count==0||unchanged_count==0)$fatal(1,"coverage missing");for(i=0;i<8;i=i+1)if(by_op[i]!=9216)$fatal(1,"opcode coverage %0d",i);
  $display("TEST_PASS CHANGEFLAG tests=%0d all8opcodes=9216each changed=%0d unchanged=%0d fixedseed=9e3779b97f4a7c15",count,changed_count,unchanged_count);$finish;
 end
endmodule
