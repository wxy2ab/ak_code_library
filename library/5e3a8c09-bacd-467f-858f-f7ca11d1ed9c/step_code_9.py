import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import uuid

# 假设我们已经有了 ih_data, if_data, ic_data, im_data, ts_data, tf_data, t_data, tk_data 数据框

data_list = [ih_data, if_data, ic_data, im_data, ts_data, tf_data, t_data, tk_data]
symbols = ['IH', 'IF', 'IC', 'IM', 'TS', 'TF', 'T', 'TK']

returns_df = pd.DataFrame()

for data, symbol in zip(data_list, symbols):
    date_column = 'date' if 'date' in data.columns else '日期'
    close_column = 'close' if 'close' in data.columns else '收盘价'
    
    try:
        data[date_column] = pd.to_datetime(data[date_column])
        returns = data.set_index(date_column)[close_column].pct_change()
        returns_df[symbol] = returns
    except KeyError as e:
        print(f"处理 {symbol} 数据时出错：{e}")
        print(f"可用列：{data.columns}")

returns_df = returns_df.dropna()

correlation_matrix = returns_df.corr()

llm_factory.configure_matplotlib_for_chinese()

plt.figure(figsize=(12, 10))
sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', vmin=-1, vmax=1, center=0)

plt.title('期货收益相关性热力图')
plt.xlabel('期货品种')
plt.ylabel('期货品种')

# 创建输出目录（如果不存在）
os.makedirs('./output', exist_ok=True)

# 生成唯一的文件名并保存图片
image_filename = f"{uuid.uuid4()}.png"
image_path = os.path.join('./output', image_filename)
plt.savefig(image_path)
plt.close()

corr_unstack = correlation_matrix.unstack()
corr_unstack = corr_unstack[corr_unstack != 1.0]

highest_corr = corr_unstack.max()
highest_corr_pair = corr_unstack.idxmax()
lowest_corr = corr_unstack.min()
lowest_corr_pair = corr_unstack.idxmin()

analysis_result = f"""
# 期货收益相关性分析结果

## 1. 相关性矩阵

```
{correlation_matrix.to_string()}
```

## 2. 分析总结

- 最高相关性：{highest_corr_pair[0]} 和 {highest_corr_pair[1]} 之间的相关系数为 {highest_corr:.4f}
- 最低相关性：{lowest_corr_pair[0]} 和 {lowest_corr_pair[1]} 之间的相关系数为 {lowest_corr:.4f}
- 平均相关性：所有品种之间的平均相关系数为 {corr_unstack.mean():.4f}

## 3. 分析描述

基于 {', '.join(symbols)} 期货的日收益率数据，我们进行了相关性分析。主要发现如下：

- 最高相关性出现在 {highest_corr_pair[0]} 和 {highest_corr_pair[1]} 之间，相关系数为 {highest_corr:.4f}。
- 最低相关性出现在 {lowest_corr_pair[0]} 和 {lowest_corr_pair[1]} 之间，相关系数为 {lowest_corr:.4f}。
- 所有品种之间的平均相关系数为 {corr_unstack.mean():.4f}。

## 4. 热力图

![期货收益相关性热力图]({image_path})

热力图展示了不同期货品种之间相关性的强度。颜色越接近红色表示正相关性越强，越接近蓝色表示负相关性越强。

这些结果可用于构建多元化投资组合或设计套利策略。但请注意，相关性可能随时间变化，建议定期更新分析。
"""
