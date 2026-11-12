"""Append verified GPU evidence without rewriting the earlier frozen snapshot."""
from pathlib import Path
import gzip
import hashlib
import json
import subprocess

root = Path(__file__).resolve().parents[4]
run = root / 'results/fpga_sim_restart_20261111T231000Z'
gpu = run / 'closed_loop/gpu_v2'
subprocess.run(['python3', str(Path(__file__).with_name('collect_gpu_v2.py'))], check=True)
summary = json.loads((gpu / 'summary.json').read_text())
platform = json.loads((gpu / 'latest_status.json').read_text())['Result']['status']
assert platform in ['job_success_reserving', 'job_succeeded', 'job_success'], platform
status = json.loads((run / 'status.json').read_text())
status['new_GPU_cohort_complete'] = True
status['new_GPU_cohort_evidence'] = 'gpu_v2_supplement/summary.json'
status['pending'] = [x for x in status['pending'] if 'new basic CUDA' not in x]
(run / 'status.json').write_text(json.dumps(status, indent=2) + '\n')
(gpu / 'updated_status.json').write_text(json.dumps(status, indent=2) + '\n')

config = root / 'accel/lookahead/fpga_sim_restart/config/experiment_spec.simulation_restart.yaml'
text = config.read_text().replace('delivered_with_negative_performance_and_GPU_timing_auth_block',
                                 'delivered_with_negative_performance_and_fresh_GPU_V2_cohort')
text = text.replace('actual_gpu: null', 'actual_gpu: NVIDIA_H100_80GB_HBM3')
text = text.replace('blocked_by_Inspire_expired_login_invalid_grant', 'complete_96_batches_all_exact')
config.write_text(text)

report = root / 'docs/lookahead_fpga_sim_restart.md'
text = report.read_text()
start, end = '<!-- GPU_V2_SUPPLEMENT_BEGIN -->', '<!-- GPU_V2_SUPPLEMENT_END -->'
section = [start, '## 授权恢复后的新 GPU V2 补测（2026-11-12）', '',
           '启智授权已恢复；作业 `job-0afcca08-4376-45b4-9711-61940a922bad` 成功执行。实际 GPU 为 NVIDIA H100 80GB HBM3，CUDA 12.8，单卡10核配额，主机控制线程固定在8个不同物理核。基础与compact CUDA顺序运行，每个输入/实现3个独立进程，每进程1次预热加3次正式测量；共96个完整batch全部输出逐字一致，统计使用72个正式测量值。BNN/LSTM每batch均为真实完整40个sample。', '',
           '基础CUDA新增resident终点，包含初始化、波次host控制、错误确认与设备输出提交，排除最终输出D2H。compact将入口host输出vector分配移出resident，算法和kernel不变。两者均排除外部准备/转换及首次H2D；保留原E1和新resident原始值，没有重命名旧E1。', '',
           '| 输入 | CUDA实现 | resident mean ± sample SD，s |',
           '|---|---|---:|']
for row in summary['rows']:
    section.append(f"| {row['case']} | {row['backend']} | {row['mean_s']:.9f} ± {row['sample_sd_s']:.9f} |")
section += ['', '每行9次正式测量，另保留3个进程均值及其SD。CPU仍为先前本机测量，未声称新GPU与CPU同主机配对。新GPU数据取代“登录阻塞/未执行”的状态；历史数据、先前失败和图表原始来源保持不变，上方历史表与末尾原图不混入新cohort。当前FPGA实现的负性能结论不变。', '',
            '补充原始日志、完整输出、编译源码/二进制、运行回执、资源查询及SHA索引见 [GPU补测证据](../results/fpga_sim_restart_20261111T231000Z/gpu_v2_supplement/index.json)。此前 `evidence_snapshot/index.json` 的源码/报告绑定对应提交 `cde531d0fb54a54e76e97aa6108fd4f237a1b847`；新索引单独绑定补测后的文件，未重写旧快照。', end, '']
addition = '\n'.join(section)
if start in text:
    a = text.index(start); b = text.index(end, a) + len(end)
    text = text[:a] + addition.rstrip() + text[b:]
else:
    text = text.replace('## 冷调用与应用占比补充', addition + '\n## 冷调用与应用占比补充')
text = text.replace('- 新基础 CUDA 及 LSTM warm GPU cohort：启智 CLI 实际返回 `invalid_grant/session expired`，未提交作业；timer-only源码变体和执行脚本已准备，未冒充已编译/运行。\n', '')
report.write_text(text)

inputs = json.loads((root / 'accel/lookahead/fpga_sim_restart/config/inputs.json').read_text())
for item in inputs:
    h = hashlib.sha256()
    with Path(item['path']).open('rb') as f:
        for block in iter(lambda: f.read(8 << 20), b''):
            h.update(block)
    assert h.hexdigest() == item['sha256']
(gpu / 'input_bindings.json').write_text(json.dumps(inputs, indent=2) + '\n')

destination = run / 'gpu_v2_supplement'
destination.mkdir(exist_ok=True)
index = {'previous_delivery_commit': 'cde531d0fb54a54e76e97aa6108fd4f237a1b847',
         'scope': summary['scope'], 'job_id': summary['job_id'], 'files': [], 'source_sha256': {}}
for path in sorted(gpu.iterdir()):
    if not path.is_file():
        continue
    data = path.read_bytes()
    compressed = path.suffix == '.bin' or path.name in ['basic', 'compact']
    output = destination / (path.name + ('.gz' if compressed else ''))
    output.write_bytes(gzip.compress(data, mtime=0) if compressed else data)
    restored = gzip.decompress(output.read_bytes()) if compressed else output.read_bytes()
    assert restored == data
    index['files'].append({'path': path.name, 'snapshot': output.name, 'bytes': len(data),
                           'sha256': hashlib.sha256(data).hexdigest(), 'compressed': compressed})
sources = [report, config, root / 'accel/lookahead/fpga_sim_restart/closed_loop/README.md']
sources += [Path(__file__), Path(__file__).with_name('collect_gpu_v2.py'), Path(__file__).with_name('gpu_worker.py')]
sources += list((root / 'accel/lookahead/include').glob('*.hpp'))
sources += list((root / 'accel/lookahead/round6').glob('*.hpp'))
sources += list((root / 'accel/lookahead/round6_1').glob('*.hpp'))
sources += [root / 'accel/lookahead/round6/cuda6.cu', root / 'accel/lookahead/round6_1/cuda61.cu', root / 'accel/lookahead/round6_1/cuda_solver61.cuh']
for path in sources:
    index['source_sha256'][str(path.relative_to(root))] = hashlib.sha256(path.read_bytes()).hexdigest()
(destination / 'index.json').write_text(json.dumps(index, indent=2) + '\n')
print('Verified supplement artifacts:', len(index['files']))
