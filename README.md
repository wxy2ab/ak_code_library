# ak_code_library
这个库分享由ak_interpreter编写的代码.自由取用.但是使用代码自担风险.  
![logo](https://github.com/wxy2ab/akinterpreter/raw/main/docs/logo256.png)  

无论如何，先做一些提醒，再分享其他项目
- 🔮 代码不是算命先生：
虽然代码编写的东西看上去比较帅气，但，它并不能预测未来。如果它真的能，我们现在可能已经在自己的私人岛屿上享受退休生活了。
- 💸 代码不是印钞机：
代码只是遵照固定逻辑执行的工具，面对由成千上万聪明人组成的市场，代码的力量真的微不足道，所以使用代码并一定能降低风险。
- 🤓 我是码农，不是股票经纪人：
分享这个仓库的人只是个微不足道的码农，没有证券从业资格证。也不具备任何投资建议资格。也没有专业的金融知识。只是分享一些自己觉得有趣的代码。
- 🚀 AI目前只是高级工具：
AI 目前只是比锤子高级一些的工具，善用工具的意思是你有思想，你依赖工具，但是不会依靠工具。
- 📚 做个聪明的猴子：
在使用这个库之前，请确保你了解它的工作原理。盲目使用这些工具就像是给猴子一台打字机，虽然有可能写出莎士比亚的作品，但更可能只是得到一堆乱码。

## 如何使用
```Bash
#clone 项目
git clone https://github.com/wxy2ab/ak_code_library.git

#进入项目目录
cd ak_code_library

#安装依赖
pip install -r requirements.txt

#设置配置文件 ， 如何填写参考 akinterpreter 项目的README.md
ehco 修改setting.ini, 填写key
cp setting.ini.template setting.ini

#cli 运行代码(可选web方式运行)
index = 1
python main.py $index parm1=value1 param2=value2
```

## 配置文件
需要配置setting.ini   
如何配置参考 [akinterpreter](https://github.com/wxy2ab/akinterpreter)

## 运行  
### cli运行
python main.py number_of_index parm1=value1 parm2=value2  
```bash
python main.py 1 symbol=601919
```

### web ui 运行
#### windows
```shell
./start.bat
```
#### linux mac
```bash
./start.sh
```

## 分享你的代码  
本项目的代码是由 akinterpreter 编写而成.  
如果你有好的思路，好的 idea，欢迎用 [akinterpreter](https://github.com/wxy2ab/akinterpreter) 生成代码。  
如果你想分享你的代码，请 fork 这个仓库，然后提交 pull request。  
你可以用 akinterpreter 生成代码之后，用 export 导出代码
导出的代码复制出来放在 ak_code_library/library 目录下，pull request。  
---

# Table of Contents

| 索引 | 名称 | 步骤 | 参数 |
|------|------|------|------|
| 1 | 检索并深入分析中远海控的最新研报数据，聚焦于市场机会、竞争、前景展望及潜在风险 | 3 | symbol |
| 2 | 获取个股新闻，总结内容，生成词云图 | 3 | symbol |
| 3 | 获取新浪财经的全球财经快讯信息，总结分析其内容，分析只使用LLM，不使用图表和词云(20条数据，大概10-30分钟左右数据) | 2 |  |
| 4 | 获取东方财富全球财经快讯信息，总结分析其内容(200条数据，大概10小时左右) | 2 |  |
| 5 | 获取财联社的电报信息并分析新闻内容(300条数据，大概16个小时数据) | 2 |  |
| 6 | 获取同花顺财经的全球财经直播信息，总结分析其内容。(20条数据，时间跨度大约40分钟) | 2 |  |
| 7 | 获取富途牛牛的快讯信息，总结并分析其内容(50条数据，跨度大约60分钟) | 2 |  |
| 8 | 获取个股2024年日线数据，使用LLM预测未来5天市场表现，并绘制包含历史数据和预测数据的图表，预测数据用红色表示 | 3 | num_of_predict,symbol |
| 9 | 获取某股票新闻数据和2024年以来的日线数据，使用LLM预测未来5天市场表现，并绘制包含历史数据和预测数据的图表，预测数据用红色表示 | 4 | symbol |
