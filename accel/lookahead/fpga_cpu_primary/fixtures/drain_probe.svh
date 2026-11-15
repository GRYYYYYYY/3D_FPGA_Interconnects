// Observation-only q2 drain probe. Included inside tb_full_core; no DUT writes.
 wire [127:0] probe_t_live,probe_d_live;
 wire [15:0] probe_idle0,probe_next_idle,probe_edge_idle;
 wire probe_window=!reset&&busy&&sample_index==2&&cycles-cycle_begin>=21520&&cycles-cycle_begin<=21545;
 integer probe_global_file,probe_rows=0;
 for(genvar g=0;g<16;g=g+1)begin:drain_probe_summary
  assign probe_idle0[g]=dut.fronts[g].front.idle0;
  assign probe_edge_idle[g]=dut.fronts[g].front.core.edge_idle;
  assign probe_next_idle[g]=dut.fronts[g].front.idle0&&!dut.fronts[g].front.avs&&!dut.fronts[g].front.pv0&&!dut.fronts[g].front.tv&&!dut.fronts[g].front.dv&&!dut.fronts[g].front.mv&&!dut.fronts[g].front.drv0&&!dut.fronts[g].front.rv0&&!dut.fronts[g].front.yv&&!(|dut.fronts[g].front.ov);
  for(genvar k=0;k<8;k=k+1)begin:slots
   assign probe_t_live[g*8+k]=dut.fronts[g].front.core.ts[k]!=0;
   assign probe_d_live[g*8+k]=dut.fronts[g].front.core.state[k]!=0;
  end
 end
 initial begin:probe_open_global
  string path,dir;integer ignored;
  ignored=$value$plusargs("OUT=%s",dir);path=$sformatf("%s/drain_probe_global.csv",dir);probe_global_file=$fopen(path,"w");if(!probe_global_file)$fatal(1,"PROBE_OPEN_GLOBAL");
  $fdisplay(probe_global_file,"cycle,relative_cycle,sample,phase,waves_global,waves_sample,pops_done,front_idle,core_idle0,context_next_idle,edge_idle,candidate_idle,bank_expansion_idle,bank_idle,net_empty,output_idle,t_nonempty,d_nonempty,t_live_mask,d_live_mask,expand_drain_guard");
 end
 always @(posedge clk)begin:probe_global_preedge
  integer t_count,d_count;
  if(probe_window)begin
   t_count=0;d_count=0;
   for(integer k=0;k<128;k=k+1)begin t_count=t_count+probe_t_live[k];d_count=d_count+probe_d_live[k];end
   $fdisplay(probe_global_file,"%0d,%0d,%0d,%0d,%0d,%0d,%b,%h,%h,%h,%h,%b,%h,%h,%b,%b,%0d,%0d,%h,%h,%b",cycles,cycles-cycle_begin,sample_index,phase,waves,waves-last_waves,dut.pops_done,dut.front_idle,probe_idle0,probe_next_idle,probe_edge_idle,dut.candidate_idle,dut.bank_expansion_idle,dut.bank_idle,dut.net_empty,dut.output_idle,t_count,d_count,probe_t_live,probe_d_live,dut.pops_done&&(&dut.front_idle)&&dut.candidate_idle&&(&dut.bank_expansion_idle)&&dut.net_empty&&dut.output_idle);
   $fflush(probe_global_file);probe_rows=probe_rows+1;
  end
  if(!reset&&sample_done&&sample_index==2)begin
   if(probe_rows!=26)$fatal(1,"PROBE_ROW_COUNT actual=%0d",probe_rows);
   $display("DRAIN_PROBE_CAPTURED q2 relative21520..21545 rows=%0d pre-NBA",probe_rows);
  end
 end
 for(genvar g=10;g<12;g=g+1)begin:drain_probe_front
  integer fd;wire [15:0]t_states;wire[23:0]d_states;wire[7:0]edge_done_bits,target_done_bits;
  for(genvar k=0;k<8;k=k+1)begin:slots
   assign t_states[k*2+:2]=dut.fronts[g].front.core.ts[k];assign d_states[k*3+:3]=dut.fronts[g].front.core.state[k];
   assign edge_done_bits[k]=dut.fronts[g].front.core.edge_done[k];assign target_done_bits[k]=dut.fronts[g].front.core.target_done[k];
  end
  initial begin:open_detail
   string path,dir;integer ignored;
   ignored=$value$plusargs("OUT=%s",dir);path=$sformatf("%s/drain_probe_front_%0d.csv",dir,g);fd=$fopen(path,"w");if(!fd)$fatal(1,"PROBE_OPEN_FRONT");
   $fdisplay(fd,"cycle,relative_cycle,group,registered_idle,idle0,next_idle,edge_idle,t_live,d_live,t_states,d_states,edge_done,target_done,core_eh,core_th,core_ei,core_ti,core_rf_ov,core_tf_ov,core_dv,avs,pv0,tv,dv,mv,drv0,rv0,yv,ov,ov0,av,ar,pv,pr,dv0,dr0,dr,drv,drr,drr0,rv,rr,rr0");
  end
  always @(posedge clk)if(probe_window)begin
   $fdisplay(fd,"%0d,%0d,%0d,%b,%b,%b,%b,%h,%h,%h,%h,%b,%b,%h,%h,%h,%h,%h,%h,%h,%h,%h,%h,%h,%h,%h,%h,%h,%h,%h,%h,%h,%h,%h,%h,%h,%h,%h,%h,%h,%h,%h,%h",cycles,cycles-cycle_begin,g,dut.fronts[g].front.idle,dut.fronts[g].front.idle0,probe_next_idle[g],dut.fronts[g].front.core.edge_idle,probe_t_live[g*8+:8],probe_d_live[g*8+:8],t_states,d_states,edge_done_bits,target_done_bits,dut.fronts[g].front.core.eh,dut.fronts[g].front.core.th,dut.fronts[g].front.core.ei,dut.fronts[g].front.core.ti,dut.fronts[g].front.core.rf_ov,dut.fronts[g].front.core.tf_ov,dut.fronts[g].front.core.dv,dut.fronts[g].front.avs,dut.fronts[g].front.pv0,dut.fronts[g].front.tv,dut.fronts[g].front.dv,dut.fronts[g].front.mv,dut.fronts[g].front.drv0,dut.fronts[g].front.rv0,dut.fronts[g].front.yv,dut.fronts[g].front.ov,dut.fronts[g].front.ov0,dut.fronts[g].front.av,dut.fronts[g].front.ar,dut.fronts[g].front.pv,dut.fronts[g].front.pr,dut.fronts[g].front.dv0,dut.fronts[g].front.dr0,dut.fronts[g].front.dr,dut.fronts[g].front.drv,dut.fronts[g].front.drr,dut.fronts[g].front.drr0,dut.fronts[g].front.rv,dut.fronts[g].front.rr,dut.fronts[g].front.rr0);
   $fflush(fd);
  end
 end
