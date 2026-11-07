"""Offline audit, matched-iteration congestion review and local pin-access checks."""
from collections import defaultdict
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

from prepare import sha256, write_json
from report_native_joint import log_evidence
from scaling_common import metrics, verified

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'results/native_cpu_width120_20261104'


def read(p): return json.loads(Path(p).read_text())
def binding(p): return dict(path=str(Path(p).resolve()), sha256=sha256(p))


def node_attributes(line):
    # Native XML may put the node opening tag and its loc child on one line.
    return ET.fromstring(line.strip().split('>', 1)[0].rstrip('/') + '/>').attrib


def match_neighbors(adjacency):
    matched = {}
    def augment(pin, seen):
        for resource in sorted(adjacency[pin]):
            if resource in seen: continue
            seen.add(resource)
            if resource not in matched or augment(matched[resource], seen):
                matched[resource] = pin
                return True
        return False
    for pin in sorted(adjacency): augment(pin, set())
    return matched


def local_access():
    directory = OUT/'lstm_s1'
    groups = {name: {} for name in ['input_74_74_0', 'output_74_77_0', 'input_74_79_0']}
    selectors = {('IPIN', 74, 74, 0): 'input_74_74_0', ('OPIN', 74, 77, 0): 'output_74_77_0',
                 ('IPIN', 74, 79, 0): 'input_74_79_0'}
    net = None
    for line in (directory/'routed.route').open():
        m = re.match(r'Net (\d+) ', line)
        if m: net = int(m[1])
        m = re.search(r'Node:\s*(\d+)\s+(OPIN|IPIN) \((\d+),(\d+),(\d+)\)', line)
        if m:
            key = (m[2], *map(int, m.group(3, 4, 5)))
            if key in selectors: groups[selectors[key]][int(m[1])] = net
    outgoing = set(groups['output_74_77_0'])
    incoming = set(groups['input_74_74_0']) | set(groups['input_74_79_0'])
    adjacency = {pin: set() for pin in outgoing | incoming}
    graph = directory/'rr_graph.xml'
    selected = OUT/'lstm_pin_access_edges.xml'
    with selected.open('w') as out:
        out.write('<selected_edges>\n')
        for line in graph.open():
            if '<edge ' not in line: continue
            # Attribute order is not part of XML semantics.
            source = re.search(r'\bsrc_node="(\d+)"', line)
            sink = re.search(r'\bsink_node="(\d+)"', line)
            if not source or not sink: continue
            a, b = int(source[1]), int(sink[1])
            if a in outgoing or b in incoming:
                out.write(line)
                if a in outgoing: adjacency[a].add(b)
                if b in incoming: adjacency[b].add(a)
        out.write('</selected_edges>\n')
    neighbors = set().union(*adjacency.values())
    metadata = {}
    with graph.open() as f:
        for line in f:
            if '</rr_nodes>' in line: break
            if '<node ' not in line: continue
            m = re.search(r'\bid="(\d+)"', line)
            if m and int(m[1]) in neighbors:
                metadata[int(m[1])] = node_attributes(line)
    assert set(metadata) == neighbors
    assert all(int(n['capacity']) >= 1 for n in metadata.values())
    results = {}
    for name, pins in groups.items():
        assert len(pins) == len(set(pins.values())), 'Pin matching assumes distinct active nets'
        local = {pin: adjacency[pin] for pin in pins}
        matching = match_neighbors(local)
        results[name] = dict(active_pins=len(pins), distinct_active_nets=len(set(pins.values())),
                             distinct_neighbors=len(set().union(*local.values())),
                             unit_capacity_matching=len(matching), all_pins_matched=len(matching) == len(pins),
                             pin_to_net=pins, adjacency={k: sorted(v) for k, v in local.items()},
                             matched_neighbor_to_pin=matching)
    result = dict(scope='Necessary local direct-neighbor capacity check only, performed separately per DSP block/direction. Does not reserve resources used by other nets, find multi-hop disjoint paths, or prove full-graph feasibility.',
                  route=binding(directory/'routed.route'), rr_binding=read(directory/'vpr_case.json')['inputs']['rr_graph'],
                  edge_snapshot=binding(selected), groups=results, neighbor_metadata=metadata)
    write_json(OUT/'lstm_pin_access.json', result)
    print('Pin-access checks', {k: (v['active_pins'], v['unit_capacity_matching']) for k, v in results.items()}, flush=True)
    return result


def main():
    summary = read(OUT/'summary.json'); audit = read(OUT/'audit.json')
    assert summary['status'] == 'completed' and audit['status'] == 'passed'
    for path, digest in audit['bindings'].items(): assert sha256(path) == digest, path
    verified(summary['plan_binding'])
    for row in summary['measurements']:
        verified(row['generated_rr_graph'])
        d = Path(row['directory']); parsed = metrics((d/'process.log').read_text(errors='replace'))
        assert all(row[k] == parsed[k] for k in ['routing_success', 'full_check', 'iterations', 'critical_path_ns', 'wirelength'])
        if row['success']:
            checked = metrics((d/'independent_check.log').read_text(errors='replace'))
            assert parsed['full_check'] and checked['full_check'] and log_evidence(d)['final_overused_nodes'] == 0
            assert all(parsed[k] == checked[k] for k in ['critical_path_ns', 'wirelength'])
    print('Independent review: 41 bound artifacts and six generated graphs verified', flush=True)
    access = local_access()
    old_path = ROOT/'results/native_cpu_large_20261102/qualification/serial/summary.json'
    old = {r['case']: r for r in read(old_path)['measurements'] if r['variant'] == 'fixed_serial'}
    rows = []
    for row in summary['measurements']:
        prior = old[row['case']]
        a = {x['iteration']: x for x in prior['log_evidence']['iterations']}
        b = {x['iteration']: x for x in row['log_evidence']['iterations']}
        same = {str(i): {'width100': a[i]['overused_nodes'], 'width120': b[i]['overused_nodes']}
                for i in [20, 36, 50, 60, 75, 100, 150, 200] if i in a and i in b}
        rows.append(dict(case=row['case'], legal=row['success'], status=row['status'],
                         last_observed=list(b.values())[-1], width100_legal=prior['success'],
                         width100_last_observed=list(a.values())[-1], matched_iteration_overuse=same,
                         critical_path_ns=row['critical_path_ns'] if row['success'] else None,
                         wirelength=row['wirelength'] if row['success'] else None))
    result = dict(status='review_complete', attempted=6, legal=3, artifact_checks=len(audit['bindings']),
                  generated_graph_checks=6, rows=rows, source_bindings={n: binding(OUT/n) for n in ['summary.json', 'audit.json', 'lstm_pin_access.json']},
                  width100_source=binding(old_path), script=binding(__file__),
                  conclusions=['Uniform width120 restored feasibility in this run for LSTM_s2 and BNN_s1; BNN_s2 remained legal.',
                      'Both DLA layouts still timed out at 900s; last observed overuse97/62 is not a completed endpoint.',
                      'LSTM_s1 finished200 iterations with three CHANY layer0 conflicts at x73 near DSP pins; this does not identify a vertical bottleneck.',
                      'Single-run lower congestion is not a stable performance gain; all six outcomes remain in the denominator.'],
                  performance_claim=False, default_changed=False, formal_started=False,
                  next='Exactly one LSTM_s1 serial cached feasibility diagnostic at unchanged width120; no automatic widening or candidate performance runs.')
    write_json(OUT/'review.json', result)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(2, 3, figsize=(13, 7))
    for ax, row in zip(axes.flat, summary['measurements']):
        for name, source in [('width100', old[row['case']]), ('width120', row)]:
            trace = source['log_evidence']['iterations']
            ax.plot([x['iteration'] for x in trace], [x['overused_nodes'] for x in trace], label=name)
            if source['status'] == 'timeout': ax.plot(trace[-1]['iteration'], trace[-1]['overused_nodes'], 'x', color='black')
        ax.set_title(row['case']); ax.set_xlabel('Routing iteration'); ax.set_ylabel('Overused nodes')
        ax.set_yscale('symlog', linthresh=1); ax.grid(alpha=.25); ax.legend()
    fig.suptitle('Single-run congestion diagnostics; x = timeout, no speedup claim')
    fig.tight_layout()
    for ext in ['pdf', 'svg', 'png']: fig.savefig(OUT/f'width_congestion.{ext}', dpi=150)
    plt.close(fig)
    lines = ['# 线宽120完整结果复核', '', '六项全部完成，3项合法且独立FULL/STA通过；41份绑定产物和六份新RR图重新核验通过。', '',
             '|布局|结果|最后完成轮数|最后观察过用|', '|---|---|---:|---:|']
    for row in rows:
        last = row['last_observed']
        lines.append(f'|{row["case"]}|{"合法" if row["legal"] else row["status"]}|{last["iteration"]}|{last["overused_nodes"]}|')
    lines += ['', 'DLA的两个值是超时前最后完整迭代，不是合法终点。LSTM_s1失败路径产生的CPD/线长不作有效质量指标。', '',
              '扩宽后LSTM_s2与BNN_s1本次找到合法路由，BNN_s2保持合法；DLA两布局和LSTM_s1仍失败。不能只选三个成功布局计算泛化加速，也不能把单次结果当稳定可布通率。', '',
              'LSTM_s1的三个过用节点3619305/3619470/3619539均为层0、x=73的CHANY，容量1/占用2。分别涉及DSP输入附近、同一DSP的两个输出、另一个DSP输入附近的竞争。该观察不证明垂直资源不足或图本身无解。', '']
    for name, g in access['groups'].items():
        lines.append(f'{name}：{g["active_pins"]}个有效引脚，{g["distinct_neighbors"]}个直接邻居，单位容量匹配{g["unit_capacity_matching"]}。')
    lines += ['', '引脚匹配按块和输入/输出方向分别检查，未扣除其他网络占用，也未求多跳互不冲突路径；完整匹配仅排除这三个局部集合的直接邻居数量不足，不能证明全图可布通。', '',
              '下一步为一项同图同缓存的串行路由诊断，200轮/900秒，不报告串行一核对并行八核的速度比。没有自动扩宽或候选性能矩阵，原宽100失败及全部负例保持。', '',
              '![六布局拥塞轨迹](width_congestion.png)', '', '宽120进程生成/写图，宽100进程读图；本报告不比较进程时间。']
    (OUT/'review.md').write_text('\n'.join(lines)+'\n')


if __name__ == '__main__': main()
