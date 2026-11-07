# 论文证据补齐：新架构与真实缓存批次

状态：completed；已尝试208项，合法且独立检查通过208项；正式96/96项。

两电路tseng/des、两个布局种子、原生k6_N10_mem32K_40nm架构。共享宿主；不称独占或完整编译加速。资格失败保留，不补样。

|模式/对照|四布局等权配对中位几何平均|
|---|---:|
|rebuild/stock_to_pipeline|1.136867×|
|rebuild/fixed_serial_to_pipeline|1.099718×|
|rebuild/per_group_to_pipeline|1.040204×|
|reuse/stock_to_pipeline|0.978860×|
|reuse/fixed_serial_to_pipeline|1.005956×|
|reuse/per_group_to_pipeline|0.972745×|

|实际批次/对照/前缀长度|三次配对中位|范围|
|---|---:|---:|
|tseng_s1/stock_to_pipeline/K1|1.123454×|1.039021–1.157625|
|tseng_s1/stock_to_pipeline/K2|1.064419×|0.999764–1.106886|
|tseng_s1/stock_to_pipeline/K5|0.991886×|0.943112–1.053044|
|tseng_s1/per_group_to_pipeline/K1|1.039753×|0.999847–1.082679|
|tseng_s1/per_group_to_pipeline/K2|1.041451×|1.021522–1.042629|
|tseng_s1/per_group_to_pipeline/K5|0.974405×|0.943175–1.017988|
|des_s1/stock_to_pipeline/K1|1.126599×|1.098761–1.154258|
|des_s1/stock_to_pipeline/K2|1.105703×|1.081396–1.106680|
|des_s1/stock_to_pipeline/K5|1.061124×|1.037965–1.101700|
|des_s1/per_group_to_pipeline/K1|1.050132×|1.000304–1.075553|
|des_s1/per_group_to_pipeline/K2|1.026318×|1.000386–1.026394|
|des_s1/per_group_to_pipeline/K5|1.005850×|1.005187–1.034493|

真实批次每个臂第一次重建并写出自己的等价缓存，随后4次读取该缓存。K=1/2/5为同一批次的相关前缀，不是独立实验，也不是五个独立设计。主时间为这些原生进程wall之和，不含独立检查。

compressed_map为替代模型，对照需合法性和质量通过，不要求与map字节相等。结果与QoR见analysis.json。

第1项方法整理见method_and_ablation.md；第3项远端资源与扩展性见platform/及scaling/，须单独报告，不能把共享宿主结果包装成隔离结果。

短进程计时敏感性及大图摊销模型见amortization_and_timer_sensitivity.md；内部flow指标方向一致，但几百分点差异仍需谨慎。

![新架构与真实缓存批次](architecture_cache.png)
