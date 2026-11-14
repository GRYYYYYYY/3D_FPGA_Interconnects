from pathlib import Path
import json,re,hashlib,shutil,datetime,subprocess
from read_timing import timing
ROOT=Path(__file__).resolve().parents[4];R=ROOT/'results/fpga_enum_commit_20261114';S=ROOT/'accel/lookahead/fpga_enum_commit/front'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 e=R/'front_ooc_e';terminal=json.loads((e/'final_terminal.json').read_text());assert terminal['terminal_status']=='COMPLETED' and terminal['returncode']==0 and terminal['has_completion_marker']
 required=['route.dcp','timing_route.rpt','setup_paths.rpt','hold_paths.rpt','util_route.rpt','methodology.rpt','drc.rpt','check_timing.rpt','constraints.xdc'];assert all((e/x).is_file() for x in required)
 t=timing(e/'timing_route.rpt');constraints=(e/'constraints.xdc').read_text();assert 'set_false_path' not in constraints and 'set_multicycle_path' not in constraints
 resources={}
 for line in (e/'util_route.rpt').read_text().splitlines():
  if not line.startswith('|'):continue
  cols=[v.strip() for v in line.split('|')[1:-1]]
  if len(cols)<2:continue
  label=cols[0].replace('*','').strip()
  if label in ['CLB LUTs','CLB Registers','Block RAM Tile','URAM','DSPs','LUT as Memory'] and label not in resources:
   resources[label]=cols[1]
 methods=(e/'methodology.rpt').read_text();drc=(e/'drc.rpt').read_text();ids=sorted(set(re.findall(r'(?m)^\|\s*([A-Z][A-Z0-9]*-\d+)\s*\|',methods+'\n'+drc)))
 research=json.loads((e/'workaround_research.json').read_text());research['efficacy']='VERIFIED_FOR_THIS_2022.2_RECOVERY: postroute checkpoint/reports and CLI exit0 completed with per-process preload';(e/'workaround_research.json').write_text(json.dumps(research,indent=2)+'\n')
 term={**terminal,'artifact_sha256':{p.name:sha(p) for p in e.iterdir() if p.is_file() and p.name!='final_terminal.json'},'timing_summary':t,'resources_actual':resources,'reported_check_ids':ids,'architecture_timing_qualified':t['all_setup_hold_pulse_and_coverage_pass'],'full_kernel_qualified':False,'board_measured':False};(e/'final_terminal.json').write_text(json.dumps(term,indent=2)+'\n')
 allstats=json.loads((R/'front_analysis_a/summary.json').read_text());pairs=[x for x in allstats['pairs'] if x['run']=='front_independent_a'];table='\n'.join('| '+x['case']+' '+x['wave']+' | '+str(x['FIRST_FREE_cycles'])+' | '+str(x['LANE_RR_cycles'])+' | '+f"{100*x['elapsed_reduction_fraction']:.4f}%"+' |' for x in pairs)
 old=S/'STATUS.md'
 if not (R/'front_analysis_a/checkpoint_STATUS.md').exists():shutil.copy2(old,R/'front_analysis_a/checkpoint_STATUS.md')
 verdict='未满足5ns；不能授予200MHz时序资格' if not t['all_setup_hold_pulse_and_coverage_pass'] else '在明示OOC合同下时序指标通过；全前端与完整核仍无资格'
 body=f'''# F线最终交付

八个独立组的公平分配减少了部分lane闲置，但大波次净收益有限并有负例。最终leaf实际OOC：**{verdict}**。完整报告使用本轮实际E恢复终态，A/B/C为授权取消的被替代实现，D为许可库环境崩溃；这些状态不混为架构负结果。

## 最终同资源匹配对照

| 输入/原生波次 | FIRST_FREE cycles | LANE_RR cycles | elapsed减少（负值为回退） |
|---|---:|---:|---:|
{table}

19个输入为17 frozen native wave+2已冻结连续压力窗口，未拼接、复制或改工作量。所有paired候选实际FP32、whole-pair目标、parent/request/response/流量守恒通过。小图或零候选wave全程零发射lane并不表示失衡；大输入两个代表wave的零发射lane从7变0，但最终四段16lane利用率仍明显不均。BNN为67.78/45.42/13.14/3.89%，LSTM为67.53/44.58/12.58/4.15%；总利用率32.56/32.21%。固定请求/返回优先级仍保留，不能称分配问题已经全部解决，不能把重叠stall相加为wall time。

最终policy：8组，各fork/H/M/ready16、L8、E32、64beat槽；全局L64/E256/512槽。有效POP输入边界采用跳过满组的持久fork RR，每cycle全局<=8成功预留且每组<=1。组内H、M、H->ready各最多1/cycle；E分配采用FIRST_FREE或持久laneRR，后者仅非空E分配成功推进；零度不占E。配置见configuration.json。

原因消融front_compare_a共76次（19输入×两分配×旧/8路接收），19项FIRST_FREE旧带宽逐周期和逐lane发射数复现1e312d6旧B。global组mask跟进front_grouped_a38次；追加槽/等待统计front_grouped_b38次（同机制、不是新架构）；最终独立组front_independent_a38次。总190次实际运行，95对，均有终态receipt。最终模型和global组模型同源重编译与执行binary哈希相同；四个实际workload哈希已重新核对与冻结绑定相符。

## 实际RTL和校准边界

frontend_group.sv为8lane×4contexts、每lane8槽、D1的有限leaf：每cycle接受一个已完成row读取的parent；一拍注册edge请求；tag={{generation8,slot8}}；真实descriptor/cost table驱动现有两级弹性pair_lane。E和客户端槽在候选消费后释放；物理credit由外部共享服务合同管理。

144parent（24零度）、2136真实FP32结果、378请求/响应，每模式两个epoch不reset。A为849周期；B/C/D各784周期，由独立时钟模型逐拍核对allocation/request/tagged-return/FP32位值。B/C/D外部trace哈希一致。额外1024周期global64lane/8grant仲裁RTL校准各1748grant，该模块仅属于global原因消融，最终政策为独立组。

D叶内offset为显式检查的32-bit支持域，CSR输入/存储仍64-bit。高32位非零拒绝并sticky error。最大合法begin=0xfffffffe/end=0xffffffff及越界拒绝测试通过；frozen BNN/LSTM prepared_edges38,342,776/38,985,028满足域。没有静默截断或精度降低。

leaf的ml为相对edge beat地址，本地layout EDGE_BASE=0、一个共享服务口；完整base-add/line条带映射、32port arbiter、全局return route、POP/fork/H/metadata/reducer/qid控制均未包含。leaf node/epoch注记被综合删除；epoch转换由TB在idle后驱动，不能声称已实现qid控制。MCP/CLI模拟器皆XSim2022.2，无后门注入候选答案。微TB模式间jitter相位不同，供压力/校准使用，差值不作为严格性能比较；严格比较来自上面的同合同C++pairs。

F局部C++保留有效POP来源、理想candidate sink、每wave目标重建、response bypass及同tick多逻辑入同portFIFO的旧抽象（物理issue仍1/port/cycle）。实际完整模型另有accepted_port=1等注册化服务。故即使leaf指标通过，也不能升级为wholefrontend/完整核资格。原生局部模型不外推40sample时间。

## 实际200MHz OOC和负结果

最终实际reports为results/fpga_enum_commit_20261114/front_ooc_e/，从D精确synth.dcp接续，RTL/布局参数未改变。5ns clock，所有输入/输出0.5ns预算，无false/multicycle路径或waiver。

- WNS={t['WNS_ns']}ns，WHS={t['WHS_ns']}ns，WPWS={t['WPWS_ns']}ns。
- setup/hold/pulse失败endpoint分别{t['setup_failing_endpoints']}/{t['hold_failing_endpoints']}/{t['pulse_failing_endpoints']}。
- check_timing计数：{json.dumps(t['check_timing_counts'],ensure_ascii=False)}。
- 实际资源：{json.dumps(resources,ensure_ascii=False)}。
- methodology/DRC原始check IDs：{', '.join(ids) if ids else '未发现命名违规ID'}。实际分类另见front_analysis_a/methodology_classification.json和原始报告；不通过改变外部I/O最小预算掩盖hold。最终最差路径pos_reg[29][7]/C→slot_state_reg[56][0]/R，18级（6 CARRY8），data5.917ns，其中routing4.186ns/70.745%；skew仅-0.010ns。TIMING-16五项为真实内部setup失败；XDCH-2的1560项为相同min/max0.5ns的接口假设；RTSTAT-10为785个OOC外部输出没有routable load，不能升级为完整接口路由资格。

A的综合WNS -22.723ns来自跨context的64-bit请求优先链；B将资格判定并行、分层选择和静态写回后，WNS -17.143ns落在串行完成计数；C注册完成/emit pulse并平衡popcount后，WNS -13.726ns落在槽释放选择链；D显式32-bit域和并行4context×8slot判定后，综合WNS -1.863ns。A/B/C按父任务授权取消并记CANCELLED_SUPERSEDED，保存source/synth/partialreports；没有伪造route终态。

D原始router后在libudev/FlexNet/WebTalk主机枚举中SIGABRT6，proxy退出134；保存hs_err、proxy/main日志与interruption状态，不是架构no-go。对应同类[2022.1公开报告](https://community.revenera.com/s/question/0D5PL00000NwuKu0AJ/issues-when-running-xilinx-tools-or-other-vendor-tools-in-docker-environment)建议进程级LD_PRELOAD。E使用已安装系统libudev.so.1（SHA256:1f47ab3bd9929605e30935503e339b6f5dcceb71595f0716377be1318962561d），本机2022.2实际完成route checkpoint/全部报告/route后回调正常并生成全部主要报告。原脚本末尾redirect在2022.2不支持而退出1，保留原失败回执；随后只打开已保存route DCP补出check_timing/XDC并退出0，final_terminal.json组合记录完整恢复，未重跑实现。没有安装补丁、关闭校验或修改全局设置。AMD000034450页面未取得内容，不声称匹配某个确切AMD AR。

## 可核对产物

- front_analysis_a/summary.json：完整表和逐lane/port统计；schema_notes.json说明独立组原JSON继承的legacy global-mask=false字段并非实际group policy。
- front_bindings_a：完整继承源码、实际输入、C++binary重建、XSim native binary和MCP历史绑定。
- front_rtl_a/b/c/d：源版本、输入hex、编译/模拟记录及独立cycle calibration。
- front_ooc_a/b/c/d/e：全部取消、崩溃和最终恢复证据，原始checkpoint在服务器保留。
- verify_front.py及freeze_front.py：190运行/容量/流量/正确性复核和紧凑manifest校验。旧17trace及两窗口按旧base/manifest/SHA引用，不重复归档大trace。

仅本scope达到终态；未提交、推送或改其他worker文件。board_measured=false、fpga_seconds=null、full_kernel_clock_qualified=false。当前无F线在途实验。
'''
 old.write_text(body)
 (R/'front_analysis_a/final_qualification.json').write_text(json.dumps({'status':'LOCAL_FRONT_FUNCTIONAL_CYCLE_VALIDATED' if not t['all_setup_hold_pulse_and_coverage_pass'] else 'LOCAL_LEAF_OOC_METRICS_ONLY','actual_final_OOC':'front_ooc_e','all_F_runs_terminal':True,'paired_runs':190,'distinct_final_independent_pairs':19,'timing':t,'resources':resources,'full_frontend_qualified':False,'full_kernel_clock_qualified':False,'fpga_seconds':None,'board_measured':False,'final_source_sha256':sha(S/'frontend_group.sv'),'reported_check_ids':ids},indent=2))
 print('FRONT_FINALIZATION_READY',t['WNS_ns'],t['WHS_ns'],t['WPWS_ns'],ids)
if __name__=='__main__':main()
