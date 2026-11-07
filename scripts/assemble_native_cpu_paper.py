"""Build primary paper tables without pooling incompatible experiment populations."""
from pathlib import Path
import json
from prepare import sha256,write_json
from scaling_common import verified

ROOT=Path(__file__).resolve().parents[1]


def read(p):return json.loads(Path(p).read_text())
def binding(p):return dict(path=str(Path(p).resolve()),sha256=sha256(p))


def main():
    full_dir=ROOT/'results/native_cpu_width120_endtoend_20261104'
    closure_dir=ROOT/'results/native_paper_closure_20261105'
    full=read(full_dir/'independent_review.json');assert full['status']=='passed'
    verified(full['source_bindings']['analysis.json'])
    closure=read(closure_dir/'analysis.json');review=read(closure_dir/'local_review.json')
    assert sha256(closure_dir/'analysis.json')==review['bindings']['analysis.json']
    assert closure['complete_cohort'] and closure['legal']==208
    scaling=read(closure_dir/'scaling/independent_review.json');assert scaling['status']=='passed'
    sources=[binding(full_dir/'independent_review.json'),binding(closure_dir/'local_review.json'),binding(closure_dir/'analysis.json'),binding(closure_dir/'scaling/independent_review.json')]
    rows=[]
    for mode in ['rebuild','reuse']:
        for compare in ['stock_to_pipeline','per_group_to_pipeline']:
            rows.append(dict(cohort='3D width120 conditional subset',circuits=2,layouts=3,distinct_rr=2,workers=8,
                mode=mode,comparison=compare,speedup=full['geometric_mean_of_layout_paired_medians'][mode][compare]['process_seconds'],
                scope='72formal total; three legal layouts chosen by frozen baseline feasibility; BNN has2/3layout weight. Original6layouts3legal/3failed. Native routing process, not full compile.',source=str(full_dir/'review.md')))
            rows.append(dict(cohort='Native k6 tseng/des',circuits=2,layouts=4,distinct_rr=2,workers=8,mode=mode,comparison=compare,
                speedup=closure['equal_layout_aggregate'][mode+'/'+compare],scope='96formal total;1–2second processes; equal-layout geometric mean of paired medians. Timer completion granularity matters.',source=str(closure_dir/'report.md')))
    fresh={}
    for name in ['native_flat_baseline_20261105','native_large2d_followup_20261105']:
        out=ROOT/'results'/name;rp=out/'independent_review.json'
        if not rp.exists():
            state=read(out/'summary.json')['status'] if (out/'summary.json').exists() else 'frozen_not_started'
            fresh[name]=dict(status=state,reviewed=False);continue
        rev=read(rp);assert rev['status'] in ['passed','passed_failure_record']
        verified(rev['analysis']);verified(rev['summary']);data=read(out/'analysis.json');sources.append(binding(rp))
        fresh[name]=dict(status=data['status'],reviewed=True,analysis=binding(out/'analysis.json'))
        if rev['status']=='passed_failure_record':continue
        cohort='clma native k6' if name=='native_flat_baseline_20261105' else 'BNN original KOIOS2D'
        for compare in ['stock_to_pipeline','stock_to_flat','per_group_to_pipeline','per_group_to_flat','flat_to_pipeline']:
            c=data['full_process_comparisons'].get(compare)
            if c and c['eligible']:
                rows.append(dict(cohort=cohort,circuits=1,layouts=1,distinct_rr=1,workers=8,mode='rebuild',comparison=compare,
                    speedup=c['process_seconds']['median'],minimum=c['process_seconds']['minimum'],maximum=c['process_seconds']['maximum'],
                    scope='12formal total after4qualifications; same-instance paired medians; separate from historical cohorts.',source=str(out/'review.md')))
    manifest=dict(primary_process_rows=rows,new_studies=fresh,sources=sources,
        aggregation='No grand average across cohorts, timings, hosts, circuit weights or baseline types.',
        default_changed=False,strict_exclusive_cpu=False)
    write_json(ROOT/'docs/native_cpu_paper_tables.json',manifest)
    lines=['# 原生CPU lookahead论文主表','',
        '以下主表由独立复核产物生成。完整进程、构建阶段、内存诊断和缓存批次分别报告；不同宿主、架构、样本权重不混成一个总加速比。','',
        '|样本集合|核数|缓存模式|对照|完整布线进程速度比|','|---|---:|---|---|---:|']
    for r in rows:lines.append(f'|{r["cohort"]}|{r["workers"]}|{r["mode"]}|{r["comparison"]}|{r["speedup"]:.4f}×|')
    lines+=['','三维条件子集有2电路/3布局/2份不同RR图，BNN布局占2/3权重；原6布局3成功3失败保持。k6 tseng/des为2电路/4布局/2份不同RR图。新增各二维集合只含1个电路/1个布局，不能冒充多电路泛化。',
        '这里的原版stock也获得相同CPU预算，并采用原生parallel布线；stock对照包含状态修复差异。同修复ELF的组内/flat/pipeline对照更直接解释构建增量。读冻结RR/packed/place的进程不等于包含综合/pack/place的完整编译。','',
        '|已复核扩展性（另一共享宿主）|同方法1→16核|同16核组内→pipeline|','|---|---:|---:|']
    for g in ['bnn','dla_like.medium']:
        lines.append(f'|{g}|{scaling["scaling"][g+"/pipeline/16"]["median"]:.4f}×|{scaling["incremental"][g+"/16"]["median"]:.4f}×|')
    lines+=['','这一表仅是lookahead阶段；96项一轮路由均未布通。DLA四核组内→pipeline仍为'+f'{scaling["incremental"]["dla_like.medium/4"]["median"]:.4f}×，保留负例。','',
        '|新增研究|状态|','|---|---|']
    for k,v in fresh.items():lines.append(f'|{k}|{v["status"]}；独立复核={v["reviewed"]}|')
    for name,v in fresh.items():
        if not v['reviewed'] or v['status']!='reviewed':continue
        data=read(v['analysis']['path']);lines+=['','|'+name+'：阶段对照|配对速度比中位|范围|','|---|---:|---:|']
        for key,c in data['component_comparisons'].items():
            if key.endswith(('per_group_to_flat','flat_to_pipeline')):lines.append(f'|{key}|{c["median"]:.4f}×|{c["minimum"]:.4f}–{c["maximum"]:.4f}|')
        lines+=['','该研究的阶段RSS、标签容量和中间表结构计数见对应review.md；诊断样本不进入本表速度比。']
    lines+=['','|真实缓存序列|K=1 stock→pipeline|K=5 stock→pipeline|','|---|---:|---:|']
    for c in ['tseng_s1','des_s1']:
        b=closure['actual_cache_batches'];lines.append(f'|{c}|{b[c+"/stock_to_pipeline/K1"]["median"]:.4f}×|{b[c+"/stock_to_pipeline/K5"]["median"]:.4f}×|')
    lines+=['','K=1/2/5是同一实际长度5序列的相关前缀；同固定设计重复请求，不是5个独立设计。大图缓存摊销的历史情景计算不当成实测批次。','',
        '剩余边界：物理CPU独占尚未证明；RSS采样不是精确峰值，工作区标签计数不含队列/分配器；wire map字节一致不扩大为所有派生表或最终路由确定性。方法新颖性不能由更多重复测量单独建立。','',
        '方法：[等价构建论证](native_lookahead_method_argument.md)。复现：[命令与证据入口](native_cpu_paper_reproduction.md)。逐表来源和SHA256见native_cpu_paper_tables.json。']
    (ROOT/'docs/native_cpu_paper_tables.md').write_text('\n'.join(lines)+'\n')
    print('Generated',len(rows),'reviewed process rows; fresh study status:',fresh,flush=True)


if __name__=='__main__':main()
