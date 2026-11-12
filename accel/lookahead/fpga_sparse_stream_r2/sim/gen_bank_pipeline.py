from pathlib import Path
r=Path(__file__).resolve().parents[1]/'rtl';s=(r/'sparse_bank.sv').read_text().replace('module sparse_bank #','module sparse_bank_pipe #')
s=s.replace(' (* ram_style="block" *) reg [63:0] members[0:MC-1];',''' (* ram_style="block" *) reg [31:0] member_header[0:MC-1],member_next[0:MC-1];
 reg [31:0] header_q,next_q;
 wire pool_iv,pool_ir,pool_ov,pool_or;wire [MA-1:0] pool_in,pool_out;wire [MA:0] pool_count;
 sparse_fifo #(.WIDTH(MA),.DEPTH(MC)) pool(clk,rst,pool_iv,pool_ir,pool_in,pool_ov,pool_or,pool_out,pool_count);
''')
s=s.replace(' (* ram_style="block" *) reg [MA-1:0] free_ids[0:MC-1];','')
s=s.replace('reg [63:0] label_q,dir_q,member_q;', 'reg [63:0] label_q,dir_q;wire [63:0] member_q={header_q,next_q};')
s=s.replace('reg [MA-1:0] free_q;', '')
a=s.index(' always @(posedge clk)begin')
extra='''
 // Three overlapped commit domains: tagged proposal response selection,
 // synchronous label/pending read + allocation, directory RMW + publication.
 reg p0v,p1v;reg [3:0] p0ctx,p1ctx;reg [NA-1:0] p0idx,p1idx;reg [63:0] p0value,p1value;
 reg p1append,p1present;reg [15:0] p1version;reg [11:0] p1key;reg [MA-1:0] p1allocated;
 reg [63:0] pipeline_dir;reg last_dir_valid;reg [11:0] last_dir_key;reg [63:0] last_dir_value;
 wire select_context=command==3&&ready_context>=0;
 wire [NA-1:0] read_node=select_context?context_index[ready_context]:idx;
 wire p0append=!pending_q[28]||pending_q[11:0]!=p0value[63:52];
 wire publish=command==3&&p1v;
 wire forwarded_dir=last_dir_valid&&last_dir_key==p1key;
 wire dir_present=forwarded_dir?1'b1:p1present;
 wire [63:0] previous_dir=forwarded_dir?last_dir_value:pipeline_dir;
 wire [63:0] published_dir={dir_present?previous_dir[63:32]:{{(32-MA){1'b0}},p1allocated},{{(32-MA){1'b0}},p1allocated}};
 assign pool_iv=(state==INIT&&initidx<MC)||state==POPMETA;
 assign pool_in=state==INIT?initidx[MA-1:0]:pointer[MA-1:0];
 assign pool_or=state==ALLOC||(command==3&&p0v&&p0append);
 wire member_new_we=(state==PUBLISH)||(publish&&p1append);
 wire [MA-1:0] member_new_index=publish?p1allocated:allocated[MA-1:0];
 wire [31:0] member_new_header=publish?{p1version,{{(16-NA){1'b0}},p1idx}}:{version,{{(16-NA){1'b0}},idx}};
 wire member_tail_we=(state==TAILWRITE)||(publish&&p1append&&dir_present);
 wire [MA-1:0] member_tail_index=publish?previous_dir[MA-1:0]:tail_ptr[MA-1:0];
 wire [31:0] member_tail_next=publish?{{(32-MA){1'b0}},p1allocated}:allocated;
 // One header write port; two next-link ports. POP reads share the new-entry
 // port in a disjoint phase, so no hidden third RAM port is required.
 always @(posedge clk)begin
  if(member_new_we)begin member_header[member_new_index]<=member_new_header;member_next[member_new_index]<=NIL;end
  else begin header_q<=member_header[pointer[MA-1:0]];next_q<=member_next[pointer[MA-1:0]];end
  if(member_tail_we)member_next[member_tail_index]<=member_tail_next;
  if(command==3&&p0v)pipeline_dir<=directory[p0value[63:52]];
 end
'''
s=s[:a]+extra+s[a:]
s=s.replace('label_q<=labels[idx];pending_q<=pending[idx];dir_q<=directory[key];member_q<=members[pointer[MA-1:0]];free_q<=free_ids[(free_count-1)&(MC-1)];', 'label_q<=labels[read_node];pending_q<=pending[read_node];if(command!=3)dir_q<=directory[key];')
s=s.replace('if(rst)begin has_bucket', 'if(rst)begin p0v<=0;p1v<=0;last_dir_valid<=0;has_bucket')
s=s.replace('   ca<=0;if(mem_valid', '   ca<=0;\n   if(pool_iv&&!pool_ir)error<=1;if(pool_or&&!pool_ov)error<=1;\n   if(command!=3)begin p0v<=0;p1v<=0;last_dir_valid<=0;end\n   if(mem_valid')
s=s.replace('   if(command==3)begin', '''   if(command==3)begin
    p0v<=select_context;p1v<=p0v;
    if(select_context)begin p0ctx<=ready_context;p0idx<=context_index[ready_context];p0value<=context_value[ready_context];context_ready[ready_context]<=0;end
    if(p0v)begin
     if(p0value>=label_q)error<=1;
     p1ctx<=p0ctx;p1idx<=p0idx;p1value<=p0value;p1key<=p0value[63:52];p1version<=pending_q[27:12]+1;
     p1append<=p0append;p1present<=bitmap[p0value[63:52]];p1allocated<=pool_out;
     if(p0append)begin free_count<=free_count-1;if(!pool_ov)error<=1;if(MC-free_count+1>member_peak)member_peak<=MC-free_count+1;end
    end
    if(publish)begin
     labels[p1idx]<=p1value;commit_count<=commit_count+1;ca<=1;commit_index<=p1idx;context_valid[p1ctx]<=0;context_sent[p1ctx]<=0;
     if(p1append)begin
      pending[p1idx]<={3'b0,1'b1,p1version,p1key};directory[p1key]<=published_dir;bitmap[p1key]<=1;groups[p1key[11:6]]<=1;
      last_dir_valid<=1;last_dir_key<=p1key;last_dir_value<=published_dir;
     end
    end
''',1)
s=s.replace('    if(initidx<MC)free_ids[initidx[MA-1:0]]<=initidx[MA-1:0];','')
s=s.replace('free_ids[free_count[MA-1:0]]<=pointer[MA-1:0];', '')
a=s.index('   COMMIT:');b=s.index('   CREAD:',a)
s=s[:a]+'''   COMMIT:if(context_valid==0&&!cv&&!mem_valid&&!p0v&&!p1v)begin done<=1;state<=IDLE;end
'''+s[b:]
s=s.replace('allocated<=free_q;', 'allocated<=pool_out;')
s=s.replace('   TAILWRITE:begin members[tail_ptr[MA-1:0]]<={member_q[63:32],allocated};state<=PUBLISH;end','   TAILWRITE:state<=PUBLISH;')
s=s.replace('    members[allocated[MA-1:0]]<={version,{{(16-NA){1\'b0}},idx},NIL};','')
# Legacy CWRITE is unreachable for commit; seed retains the legacy append path.
s=s.replace('reg [63:0] label_q,dir_q;', 'reg [63:0] label_q,directory_read;wire [63:0] dir_q=directory_read;')
s=s.replace('reg [63:0] pipeline_dir;', 'wire [63:0] pipeline_dir=directory_read;')
s=s.replace('if(command==3&&p0v)pipeline_dir<=directory[p0value[63:52]];', 'if(command!=3||(command==3&&p0v))directory_read<=directory[command==3?p0value[63:52]:key];')
s=s.replace('if(command!=3)dir_q<=directory[key];', '')
# Make the physical memory ports explicit. Disjoint FSM branches alone are not
# sufficient for Vivado 2022.2 to infer the intended RAMs across pipeline blocks.
s=s.replace('labels[p1idx]<=p1value;', '').replace("pending[p1idx]<={3'b0,1'b1,p1version,p1key};directory[p1key]<=published_dir;", '')
s=s.replace("if(initidx<NC)begin labels[initidx[NA-1:0]]<=global_node(initidx[NA-1:0])==source?64'b0:INF;pending[initidx[NA-1:0]]<=0;end", '')
s=s.replace('pending[idx]<=0;', '').replace('labels[idx]<=new_label;', '')
s=s.replace("directory[key]<={bitmap[key]?tail_value[63:32]:allocated,allocated};", '')
s=s.replace("pending[idx]<={3'b0,1'b1,version,key};", '')
s=s.replace('label_q<=labels[read_node];pending_q<=pending[read_node];', '')
s=s.replace('if(command!=3||(command==3&&p0v))directory_read<=directory[command==3?p0value[63:52]:key];', '')
a=s.index(' always @(posedge clk)begin\n  if(member_new_we)');b=s.index(' always @(posedge clk)begin',a+5)
s=s[:a]+''' wire init_node=state==INIT&&initidx<NC;
 wire valid_pop=state==POPLABEL&&pending_q[28]&&pending_q[27:12]==version&&pending_q[11:0]==key;
 wire label_we=!rst&&(init_node||publish||state==CWRITE);
 wire [NA-1:0] label_wa=init_node?initidx[NA-1:0]:publish?p1idx:idx;
 wire [63:0] label_wd=init_node?(global_node(initidx[NA-1:0])==source?64'b0:INF):publish?p1value:new_label;
 wire pending_we=!rst&&(init_node||valid_pop||(publish&&p1append)||state==PUBLISH);
 wire [NA-1:0] pending_wa=init_node?initidx[NA-1:0]:publish?p1idx:idx;
 wire [31:0] pending_wd=(init_node||valid_pop)?32'b0:publish?{3'b0,1'b1,p1version,p1key}:{3'b0,1'b1,version,key};
 wire directory_we=!rst&&((publish&&p1append)||state==PUBLISH);
 wire [11:0] directory_wa=publish?p1key:key;
 wire [63:0] directory_wd=publish?published_dir:{bitmap[key]?tail_value[63:32]:allocated,allocated};
 always @(posedge clk)begin
  if(label_we)labels[label_wa]<=label_wd;
  label_q<=labels[read_node];
  if(pending_we)pending[pending_wa]<=pending_wd;
  pending_q<=pending[read_node];
  if(directory_we)directory[directory_wa]<=directory_wd;
  if(command!=3||p0v)directory_read<=directory[command==3?p0value[63:52]:key];
 end
 always @(posedge clk)begin
  if(member_new_we)member_header[member_new_index]<=member_new_header;
  else header_q<=member_header[pointer[MA-1:0]];
 end
 always @(posedge clk)begin
  if(member_new_we)member_next[member_new_index]<=NIL;
  else next_q<=member_next[pointer[MA-1:0]];
 end
 always @(posedge clk)begin
  if(member_tail_we)member_next[member_tail_index]<=member_tail_next;
 end
''' + s[b:]
(r/'bank_pipeline.sv').write_text(s)
