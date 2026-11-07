# 缓存摊销模型与计时敏感性

Analytical sums of separately measured rebuild and reuse process times: T(K)=R+(K-1)H. Not new batch observations, not full compilation, no unmeasured cache hit-rate claim.

模型来自各臂独立测得的重建R和缓存H，不以实际batch重新拟合；小图实际batch另列，K前缀相关。历史大图这里只计算情景，不能称新增真实大图批次。

|历史大图/对照/K|估算速度比中位|
|---|---:|
|lstm_s2/stock_to_pipeline/K1|1.661422×|
|lstm_s2/stock_to_pipeline/K2|1.335109×|
|lstm_s2/stock_to_pipeline/K5|1.144031×|
|lstm_s2/stock_to_pipeline/K10|1.073717×|
|lstm_s2/per_group_to_pipeline/K1|1.076340×|
|lstm_s2/per_group_to_pipeline/K2|1.031774×|
|lstm_s2/per_group_to_pipeline/K5|1.004837×|
|lstm_s2/per_group_to_pipeline/K10|0.994309×|
|bnn_s1/stock_to_pipeline/K1|1.700542×|
|bnn_s1/stock_to_pipeline/K2|1.378892×|
|bnn_s1/stock_to_pipeline/K5|1.164644×|
|bnn_s1/stock_to_pipeline/K10|1.088750×|
|bnn_s1/per_group_to_pipeline/K1|1.115336×|
|bnn_s1/per_group_to_pipeline/K2|1.063182×|
|bnn_s1/per_group_to_pipeline/K5|1.028998×|
|bnn_s1/per_group_to_pipeline/K10|1.017070×|
|bnn_s2/stock_to_pipeline/K1|1.738661×|
|bnn_s2/stock_to_pipeline/K2|1.401565×|
|bnn_s2/stock_to_pipeline/K5|1.181406×|
|bnn_s2/stock_to_pipeline/K10|1.106831×|
|bnn_s2/per_group_to_pipeline/K1|1.106028×|
|bnn_s2/per_group_to_pipeline/K2|1.059996×|
|bnn_s2/per_group_to_pipeline/K5|1.029064×|
|bnn_s2/per_group_to_pipeline/K10|1.017065×|

短小2D进程约1–2秒，Python超时wait的退出检测可能影响几百分点差值。原生内部flow作为辅助敏感性指标，不替换预先声明的进程wall。

|模式/对照|原生内部flow速度比|
|---|---:|
|rebuild/stock_to_pipeline|1.152040×|
|rebuild/per_group_to_pipeline|1.045253×|
|reuse/stock_to_pipeline|0.979265×|
|reuse/per_group_to_pipeline|0.982165×|
