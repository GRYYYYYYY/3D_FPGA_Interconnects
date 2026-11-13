`timescale 1ns/1ps
module cache_way_tb;
 reg [3:0] match_mask,available,invalid;
 reg [1:0] cursor;
 wire hv,vv;wire [1:0] hw,vw;
 r2_cache_way_select dut(match_mask,available,invalid,cursor,hv,hw,vv,vw);
 integer v,b,t,r,s,w,k,old_hit,old_victim,cases;
 initial begin
  cases=0;
  // Includes duplicate matching tags, all busy, no available way, a live
  // pipeline slot, every replacement cursor and every valid/invalid pattern.
  for(v=0;v<16;v=v+1)for(b=0;b<16;b=b+1)
  for(t=0;t<16;t=t+1)for(r=0;r<4;r=r+1)for(s=0;s<5;s=s+1)begin
   match_mask=v&~b&t;available=(~b)&~(s<4?(1<<s):0);
   invalid=(~v)&available;cursor=r;
   old_hit=-1;old_victim=-1;
   for(w=0;w<4;w=w+1)begin
    if((v&(1<<w))&&!(b&(1<<w))&&(t&(1<<w)))old_hit=w;
    if(!(v&(1<<w))&&!(b&(1<<w))&&s!=w&&old_victim<0)old_victim=w;
   end
   if(old_victim<0)for(w=0;w<4;w=w+1)begin
    k=(r+w)%4;
    if(!(b&(1<<k))&&s!=k&&old_victim<0)old_victim=k;
   end
   #1;
   if(hv!==(old_hit>=0)||vv!==(old_victim>=0))$fatal(1,"valid mismatch");
   if(hv&&hw!=old_hit)$fatal(1,"hit mismatch");
   if(vv&&vw!=old_victim)$fatal(1,"victim mismatch");
   cases=cases+1;
  end
  $display("CACHE_WAY_PASS cases=%0d",cases);$finish;
 end
endmodule
