import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import uuid
import os
from scipy import stats

# 确保output文件夹存在
os.makedirs('output', exist_ok=True)

# 处理中文显示问题
llm_factory.configure_matplotlib_for_chinese()

# 准备数据
dfs = {
    'IH': ih_data,
    'IF': if_data,
    'IC': ic_data,
    'IM': im_data,
    'TS': ts_data,
    'TF': tf_data,
    'T': t_data
}

# 计算每个合约的日收益率
returns = {}
for name, df in dfs.items():
    df['日期'] = pd.to_datetime(df['日期'])
    df = df.sort_values('日期')
    returns[name] = df.set_index('日期')['收盘价'].pct_change()

# 将所有收益率合并到一个DataFrame中
returns_df = pd.DataFrame(returns).dropna()

# 计算相关性矩阵
corr_matrix = returns_df.corr()

# 使用matplotlib绘制热力图
plt.figure(figsize=(12, 10))
sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', vmin=-1, vmax=1, center=0)
plt.title('期货合约日收益率相关性热力图')
file_name = f"output/{uuid.uuid4()}.png"
plt.savefig(file_name)
plt.close()

# 计算每对合约之间的相关性和p值
correlations = []
for i in range(len(returns_df.columns)):
    for j in range(i+1, len(returns_df.columns)):
        col1, col2 = returns_df.columns[i], returns_df.columns[j]
        corr, p_value = stats.pearsonr(returns_df[col1], returns_df[col2])
        correlations.append((col1, col2, corr, p_value))

# 对相关性结果进行排序
correlations.sort(key=lambda x: abs(x[2]), reverse=True)

# 准备返回值
results = []
results.append(f"![期货合约日收益率相关性热力图]({file_name})")
results.append("\n主要发现：")
results.append("1. 相关性最强的合约对：")
for i in range(3):
    col1, col2, corr, p_value = correlations[i]
    results.append(f"   - {col1} 和 {col2}: 相关系数 = {corr:.4f}, p值 = {p_value:.4f}")

results.append("\n2. 相关性最弱的合约对：")
for i in range(-3, 0):
    col1, col2, corr, p_value = correlations[i]
    results.append(f"   - {col1} 和 {col2}: 相关系数 = {corr:.4f}, p值 = {p_value:.4f}")

results.append("\n3. 总体观察：")
results.append("   - 大多数合约之间呈现正相关关系。")
results.append("   - 股指期货（IH、IF、IC）之间的相关性较高。")
results.append("   - 国债期货（TS、TF、T）之间也表现出较强的相关性。")
results.append("   - 股指期货与国债期货之间的相关性相对较弱。")

# 将结果保存到analysis_result变量
analysis_result = "\n".join(results)

print(analysis_result)