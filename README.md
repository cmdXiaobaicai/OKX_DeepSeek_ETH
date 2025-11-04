# ETH AI Trader 🤖

一个基于OKX交易所与DeepSeek AI的以太坊合约自动化交易程序。

[![Python Version](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

## ✨ 项目特色

- **AI驱动**：集成DeepSeek AI API，智能分析市场趋势。
- **自动化交易**：通过OKX API实现全自动的ETH合约交易。
- **策略灵活**：支持自定义交易策略与风险控制参数。
- **简洁清晰**：代码结构清晰，易于理解与二次开发。

## 🛠 工作原理

该项目通过DeepSeek AI分析市场信息，生成交易信号，并通过OKX API执行以太坊合约交易。

    A[市场数据] --> B(DeepSeek AI分析)
    B --> C{交易决策}
    C --> D[OKX API执行]
    D --> E[持仓监控]





## 在运行程序前，请确保你的环境满足以下要求：

Python 3.8 或更高版本
有效的 OKX交易所账户 并开通API权限
有效的 DeepSeek AI API 访问密钥


## Python依赖库
核心依赖库如下表所示：

库名称	用途说明
okx-sdk-python	与OKX交易所API交互
openai	调用DeepSeek AI API
pandas	数据处理与分析
python-dotenv	安全管理环境变量

## 🧪 测试建议
在投入真实资金前，强烈建议你：

使用OKX的模拟交易环境（纸钱包） 测试策略

使用历史行情数据进行回测

小额资金试运行，观察实盘表现

## ⚠️ 风险提示
加密货币合约交易属于高风险投资。

本项目为开源工具，不构成任何投资建议。

使用此程序产生的一切盈亏由用户自行承担。

AI的预测并非100%准确，市场风险无处不在。



























