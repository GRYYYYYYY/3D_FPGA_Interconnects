# 新电路重复与缓存退化复查

完成120项新测量，合法120项；原生及独立FULL/STA与map字节等价审计通过。旧单次数据不并入本轮。

相同八个物理核32–39、单lane共享宿主；六个既有布局各三次运行重复。另对s38417两布局使用同一pipeline ELF、共享缓存，仅切换TASKS开关，各三次。未改二进制、默认或测量计时。资格准备关闭拥塞报告，正式测量保持开启。

|缓存|控制→候选|六布局配对中位数等权几何平均|VPR内部flow敏感性指标|
|---|---|---:|---:|
|rebuild|stock→frozen|0.955245397550573|0.9515331686090581|
|rebuild|stock→pipeline|1.0575775287974833|1.062144556117011|
|rebuild|frozen→pipeline|1.0969087964740125|1.1065386475383663|
|reuse|stock→frozen|1.0220754183509577|1.0250707032801898|
|reuse|stock→pipeline|1.0205690873102442|1.0203925716127473|
|reuse|frozen→pipeline|1.0174367045611332|1.0081503737020245|

每个电路两布局，故六布局等权等价于先电路内、再三电路等权。内部flow来自原日志，计时边界不同，仅作秒级进程退出轮询影响的敏感性对照，不能替代完整进程指标。三次样本范围不是置信区间。

|阶段|布局|缓存|控制→候选|进程速度比中位[范围]|合法质量配对|
|---|---|---|---|---:|---:|
|cached_toggle|s38417_s1|reuse|same_cpu→pipeline|0.9939 [0.9727, 1.0289]|3/3|
|cached_toggle|s38417_s2|reuse|same_cpu→pipeline|0.9683 [0.9623, 0.9750]|3/3|
|repeat|alu4_s1|rebuild|stock→frozen|0.9242 [0.9239, 0.9247]|3/3|
|repeat|alu4_s1|rebuild|stock→pipeline|1.0000 [0.9613, 1.0900]|3/3|
|repeat|alu4_s1|rebuild|frozen→pipeline|1.0824 [1.0396, 1.1794]|3/3|
|repeat|alu4_s1|reuse|stock→frozen|1.0450 [0.9997, 1.0470]|3/3|
|repeat|alu4_s1|reuse|stock→pipeline|1.0465 [0.9999, 1.0940]|3/3|
|repeat|alu4_s1|reuse|frozen→pipeline|1.0469 [0.9550, 1.0469]|3/3|
|repeat|alu4_s2|rebuild|stock→frozen|0.8535 [0.7449, 0.9630]|3/3|
|repeat|alu4_s2|rebuild|stock→pipeline|1.0363 [0.8854, 1.0870]|3/3|
|repeat|alu4_s2|rebuild|frozen→pipeline|1.1287 [1.0374, 1.3913]|3/3|
|repeat|alu4_s2|reuse|stock→frozen|0.9995 [0.9548, 1.0003]|3/3|
|repeat|alu4_s2|reuse|stock→pipeline|0.9539 [0.9156, 0.9997]|3/3|
|repeat|alu4_s2|reuse|frozen→pipeline|0.9990 [0.9154, 1.0002]|3/3|
|repeat|diffeq_s1|rebuild|stock→frozen|0.9619 [0.9266, 1.0002]|3/3|
|repeat|diffeq_s1|rebuild|stock→pipeline|1.0858 [1.0405, 1.1286]|3/3|
|repeat|diffeq_s1|rebuild|frozen→pipeline|1.1284 [1.0817, 1.1718]|3/3|
|repeat|diffeq_s1|reuse|stock→frozen|1.0941 [0.9990, 1.1477]|3/3|
|repeat|diffeq_s1|reuse|stock→pipeline|1.0939 [0.9997, 1.1478]|3/3|
|repeat|diffeq_s1|reuse|frozen→pipeline|1.0001 [0.9138, 1.0950]|3/3|
|repeat|diffeq_s2|rebuild|stock→frozen|0.9999 [0.9626, 1.0001]|3/3|
|repeat|diffeq_s2|rebuild|stock→pipeline|1.1289 [1.0410, 1.1793]|3/3|
|repeat|diffeq_s2|rebuild|frozen→pipeline|1.1288 [1.0815, 1.1795]|3/3|
|repeat|diffeq_s2|reuse|stock→frozen|1.0896 [1.0451, 1.0897]|3/3|
|repeat|diffeq_s2|reuse|stock→pipeline|1.0940 [1.0899, 1.1407]|3/3|
|repeat|diffeq_s2|reuse|frozen→pipeline|1.0468 [1.0002, 1.0469]|3/3|
|repeat|s38417_s1|rebuild|stock→frozen|0.9360 [0.9136, 0.9435]|3/3|
|repeat|s38417_s1|rebuild|stock→pipeline|0.9408 [0.9286, 1.0112]|3/3|
|repeat|s38417_s1|rebuild|frozen→pipeline|1.0164 [1.0051, 1.0718]|3/3|
|repeat|s38417_s1|reuse|stock→frozen|0.8768 [0.8380, 0.8896]|3/3|
|repeat|s38417_s1|reuse|stock→pipeline|0.8824 [0.8616, 0.8896]|3/3|
|repeat|s38417_s1|reuse|frozen→pipeline|1.0000 [0.9827, 1.0530]|3/3|
|repeat|s38417_s2|rebuild|stock→frozen|1.0699 [1.0631, 1.0734]|3/3|
|repeat|s38417_s2|rebuild|stock→pipeline|1.1708 [1.1508, 1.2024]|3/3|
|repeat|s38417_s2|rebuild|frozen→pipeline|1.1012 [1.0756, 1.1201]|3/3|
|repeat|s38417_s2|reuse|stock→frozen|1.0442 [1.0261, 1.0650]|3/3|
|repeat|s38417_s2|reuse|stock→pipeline|1.0719 [1.0110, 1.0790]|3/3|
|repeat|s38417_s2|reuse|frozen→pipeline|1.0132 [0.9853, 1.0265]|3/3|

## s38417缓存工作量

|阶段|布局|实现|进程中位秒|路由中位秒|迭代轮数|heap pushes|
|---|---|---|---:|---:|---|---|
|cached_toggle|s38417_s1|pipeline|8.626|6.400|[68, 68, 68]|[19099935, 19099937, 19099935]|
|cached_toggle|s38417_s1|same_cpu|8.873|6.570|[68, 68, 68]|[19099935, 19099937, 19099937]|
|cached_toggle|s38417_s2|pipeline|7.971|5.790|[47, 47, 47]|[18875835, 18875835, 18875835]|
|cached_toggle|s38417_s2|same_cpu|7.671|5.450|[47, 47, 47]|[18875835, 18875835, 18875835]|
|repeat|s38417_s1|frozen|8.623|6.350|[68, 68, 68]|[19099935, 19099937, 19099937]|
|repeat|s38417_s1|pipeline|8.623|6.390|[68, 68, 68]|[19099935, 19099935, 19099937]|
|repeat|s38417_s1|stock|7.520|5.300|[49, 49, 49]|[16266230, 16266230, 16266230]|
|repeat|s38417_s2|frozen|7.722|5.550|[47, 47, 47]|[18875835, 18875835, 18875835]|
|repeat|s38417_s2|pipeline|7.671|5.490|[47, 47, 47]|[18875835, 18875835, 18875835]|
|repeat|s38417_s2|stock|8.222|6.010|[61, 61, 61]|[17594930, 17594930, 17594928]|

map等价不意味着原版和修复版路由轨迹一致。同ELF缓存开关对照用于判断TASKS开关是否引入稳定退化；不能据此单独分离两处状态修复各自的作用。共享宿主波动仍存在。全部配对、路由哈希和CPU工作时间见analysis.json；未改变默认。

## 本轮判断

三轮重复支持pipeline在新电路重建场景的 有限的整体增益（相对原版1.0576×、相对组内采样1.0969×），不是所有单次或缓存场景普遍加速。

s38417_s1缓存相对原版速度比中位0.8824，等价于时间增加约13.33%。原版固定49轮、改进版固定68轮；改进版之间路由相同且时间基本持平，额外路由工作是主要解释，尚未隔离两处状态修复各自的因果作用。

同一ELF缓存TASKS开关：s1配对中位0.9939、范围0.9727–1.0289；s2中位0.9683、范围0.9623–0.9750；六对路由均相同。s2约3.27%的时间退化仍未定位，不能宣布全部是噪声，也不能归于缓存中未执行的lookahead构建。

下一步优先隔离并行状态修复对s38417路由轨迹的影响，以及独占资源上的同ELF缓存交错对照；保持正确性修复和默认不变。完整结论见conclusions.json。
