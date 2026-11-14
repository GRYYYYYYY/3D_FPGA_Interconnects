 // Read every published member through the actual control interface, in sorted
 // bucket order, checking per-bucket insertion order and all node/argument bits.
 integer control_bucket_value,control_status_value,control_ptr_value,control_next_value;
 reg[31:0]control_node_value,control_arg_value;integer drained_events[2];
 task automatic control_request(input integer bank_,input[1:0]op_,input[11:0]bucket_,input[13:0]ptr_);
  begin
   @(negedge clk);ctrl_valid[bank_]=1;ctrl_op[bank_*2+:2]=op_;ctrl_bucket[bank_*12+:12]=bucket_;ctrl_ptr[bank_*14+:14]=ptr_;ctrl_rsp_ready[bank_]=0;
   @(posedge clk);while(!ctrl_ready[bank_])@(posedge clk);
   @(negedge clk);ctrl_valid[bank_]=0;
   while(!ctrl_rsp_valid[bank_])@(negedge clk);
   if(ctrl_rsp_op[bank_*2+:2]!=op_)$fatal(1,"CONTROL_OPCODE");
   control_status_value=ctrl_rsp_status[bank_*2+:2];control_bucket_value=ctrl_rsp_bucket[bank_*12+:12];
   control_ptr_value=ctrl_rsp_ptr[bank_*14+:14];control_next_value=ctrl_rsp_next[bank_*14+:14];
   control_node_value=ctrl_rsp_node[bank_*32+:32];control_arg_value=ctrl_rsp_arg[bank_*32+:32];
   repeat(3)@(negedge clk);
   if(!ctrl_rsp_valid[bank_]||ctrl_rsp_node[bank_*32+:32]!==control_node_value||ctrl_rsp_arg[bank_*32+:32]!==control_arg_value)$fatal(1,"CONTROL_RESPONSE_HOLD");
   ctrl_rsp_ready[bank_]=1;@(negedge clk);ctrl_rsp_ready[bank_]=0;
  end
 endtask
 task automatic verify_directory(input integer bank_);
  integer bucket_,index_,ptr_,expected_count_,observed_count_,first_,previous_;
  begin
   observed_count_=0;previous_=-1;
   forever begin
    control_request(bank_,3,0,8192);
    if(control_status_value==1)break;
    if(control_status_value!=0||control_bucket_value<=previous_)$fatal(1,"DIRECTORY_MIN_ORDER");
    bucket_=control_bucket_value;previous_=bucket_;
    control_request(bank_,1,bucket_,8192);ptr_=control_ptr_value;expected_count_=0;
    for(index_=drained_events[bank_];index_<directory_count[bank_];index_=index_+1)
     if(directory[bank_][index_][11:0]==bucket_)begin
      if(ptr_==8192)$fatal(1,"DIRECTORY_CHAIN_SHORT");
      control_request(bank_,2,0,ptr_);
      if(control_status_value!=0||control_node_value!={10'b0,directory[bank_][index_][49:28]}||control_arg_value!={4'b0,directory[bank_][index_][27:0]})$fatal(1,"DIRECTORY_ACTUAL_PAYLOAD bank=%0d index=%0d got=%h/%h expected=%h",bank_,index_,control_node_value,control_arg_value,directory[bank_][index_]);
      ptr_=control_next_value;expected_count_=expected_count_+1;observed_count_=observed_count_+1;
     end
    if(ptr_!=8192||expected_count_==0)$fatal(1,"DIRECTORY_CHAIN_EXTRA");
   end
   if(observed_count_!=directory_count[bank_]-drained_events[bank_])$fatal(1,"DIRECTORY_EVENT_LOSS");
   drained_events[bank_]=directory_count[bank_];
   $display("CONTROL_DRAIN_PASS sample=%0d bank=%0d members=%0d",sample,bank_,observed_count_);
  end
 endtask
