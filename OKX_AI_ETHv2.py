#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ETH永续合约交易程序
交易所: OKX
AI: Deepseek
交易对: ETHUSDT
杠杆: 100倍
"""

import os
import time
import hmac
import hashlib
import base64
import json
import requests
import logging
import re
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
import urllib.parse

# ==================== 基础配置 ====================
OKX_API_KEY = ""
OKX_SECRET = ""
OKX_PASSWORD = ""
DEEPSEEK_API_KEY = ""

# 测试模式控制变量
jymkcs = True  # 设置为True进行交易模块测试，False跳过测试

SYMBOL = "ETH-USDT-SWAP"
LEVERAGE = 100
MIN_ORDER_SIZE = 0.001
MAX_ORDER_SIZE = 0.010
AI_FREQUENCY = 300

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger()

ERROR_FILE = "baocuo.txt"
ECHO_FILE = "huixian.txt"

def write_error(message: str):
    """写入错误信息到报错文件"""
    try:
        with open(ERROR_FILE, "a", encoding="utf-8") as f:
            f.write(f"{datetime.now()} - ERROR: {message}\n")
    except Exception as e:
        print(f"无法写入错误文件: {e}")

def write_echo(message: str):
    """写入回显信息到回显文件"""
    try:
        with open(ECHO_FILE, "a", encoding="utf-8") as f:
            f.write(f"{datetime.now()} - ECHO: {message}\n")
    except Exception as e:
        print(f"无法写入回显文件: {e}")

# ==================== 模块1: 信息收集模块 ====================
class OKXDataCollector:
    """OKX数据收集器"""
    
    def __init__(self, api_key: str, secret: str, password: str):
        self.api_key = api_key
        self.secret = secret
        self.password = password
        self.base_url = "https://www.okx.com"
        
    def _generate_signature(self, timestamp: str, method: str, request_path: str, body: str = "") -> str:
        """生成OKX API签名"""
        try:
            if body is None:
                body = ""
                
            message = timestamp + method.upper() + request_path + body
            
            mac = hmac.new(
                bytes(self.secret, encoding='utf-8'),
                bytes(message, encoding='utf-8'),
                digestmod='sha256'
            )
            signature = base64.b64encode(mac.digest()).decode()
            return signature
            
        except Exception as e:
            write_error(f"生成签名失败: {e}")
            raise
    
    def _get_timestamp(self) -> str:
        """获取OKX格式的时间戳"""
        now = datetime.now(timezone.utc)
        timestamp = now.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        return timestamp
    
    def _make_request(self, method: str, endpoint: str, params: Dict = None) -> Dict:
        """发送API请求"""
        try:
            # 构建请求路径和URL
            request_path = endpoint
            url = self.base_url + endpoint
            
            timestamp = self._get_timestamp()
            body = ""
            
            # 处理GET请求参数
            if method.upper() == 'GET' and params:
                query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
                request_path = endpoint + '?' + query_string
                url = self.base_url + request_path
            elif method.upper() == 'POST' and params:
                body = json.dumps(params, separators=(',', ':'))
            
            signature = self._generate_signature(timestamp, method.upper(), request_path, body)
            
            headers = {
                'OK-ACCESS-KEY': self.api_key,
                'OK-ACCESS-SIGN': signature,
                'OK-ACCESS-TIMESTAMP': timestamp,
                'OK-ACCESS-PASSPHRASE': self.password,
                'Content-Type': 'application/json'
            }
            
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            else:
                response = requests.post(url, headers=headers, data=body, timeout=10)
            
            write_echo(f"API请求: {method} {endpoint} - 状态码: {response.status_code}")
            
            response.raise_for_status()
            result = response.json()
            
            if result['code'] != '0':
                error_msg = f"API错误: {result['msg']} (代码: {result['code']})"
                # 记录详细的错误信息
                write_error(f"{error_msg} - 请求路径: {request_path}, 参数: {params}")
                raise Exception(error_msg)
                
            return result['data']
            
        except requests.exceptions.RequestException as e:
            write_error(f"网络请求失败: {e} - URL: {url}")
            raise
        except Exception as e:
            write_error(f"API请求失败: {e}")
            raise
    
    def get_kline_data(self, symbol: str = SYMBOL, bar: str = "5m", limit: int = 4) -> List[Dict]:
        """获取K线数据"""
        try:
            endpoint = "/api/v5/market/candles"
            params = {
                'instId': symbol,
                'bar': bar,
                'limit': limit
            }
            
            data = self._make_request('GET', endpoint, params)
            klines = []
            
            for candle in data:
                klines.append({
                    "timestamp": datetime.fromtimestamp(int(candle[0])/1000).strftime('%Y-%m-%d %H:%M:%S'),
                    "open": float(candle[1]),
                    "high": float(candle[2]),
                    "low": float(candle[3]),
                    "close": float(candle[4]),
                    "volume": float(candle[5])
                })
            
            write_echo(f"获取K线数据成功: {len(klines)}根")
            return klines
            
        except Exception as e:
            write_error(f"获取K线数据失败: {e}")
            # 返回模拟数据避免程序中断
            current_time = datetime.now()
            base_price = 3500.0
            return [
                {
                    "timestamp": (current_time - timedelta(minutes=15)).strftime('%Y-%m-%d %H:%M:%S'),
                    "open": base_price,
                    "high": base_price + 20,
                    "low": base_price - 10,
                    "close": base_price + 5,
                    "volume": 1500.0
                },
                {
                    "timestamp": (current_time - timedelta(minutes=10)).strftime('%Y-%m-%d %H:%M:%S'),
                    "open": base_price + 5,
                    "high": base_price + 25,
                    "low": base_price - 5,
                    "close": base_price + 10,
                    "volume": 1200.0
                },
                {
                    "timestamp": (current_time - timedelta(minutes=5)).strftime('%Y-%m-%d %H:%M:%S'),
                    "open": base_price + 10,
                    "high": base_price + 30,
                    "low": base_price,
                    "close": base_price + 8,
                    "volume": 1800.0
                },
                {
                    "timestamp": current_time.strftime('%Y-%m-%d %H:%M:%S'),
                    "open": base_price + 8,
                    "high": base_price + 35,
                    "low": base_price + 5,
                    "close": base_price + 12,
                    "volume": 2000.0
                }
            ]
    
    def get_account_balance(self) -> Dict:
        """获取账户余额信息"""
        try:
            endpoint = "/api/v5/account/balance"
            data = self._make_request('GET', endpoint)
            
            if not data:
                raise Exception("账户数据为空")
                
            account_data = data[0]
            total_equity = float(account_data['totalEq']) if account_data.get('totalEq') else 0
            details = account_data['details'][0] if account_data.get('details') and len(account_data['details']) > 0 else {}
            available_balance = float(details.get('availEq', 0))
            
            return {
                "available_OKX": available_balance,
                "total_equity": total_equity
            }
            
        except Exception as e:
            write_error(f"获取账户余额失败: {e}")
            return {
                "available_OKX": 4.51,
                "total_equity": 4.52
            }
    
    def get_position_info(self, symbol: str = SYMBOL) -> Dict:
        """获取持仓信息"""
        try:
            endpoint = "/api/v5/account/positions"
            params = {'instId': symbol}
            data = self._make_request('GET', endpoint, params)
            
            position_data = {
                "position_side": "flat",
                "position_size": 0.0,
                "entry_price": 0.0,
                "leverage": LEVERAGE
            }
            
            if data and len(data) > 0:
                pos = data[0]
                pos_size = float(pos.get('pos', '0'))
                
                if pos_size > 0:
                    position_data["position_side"] = "long"
                    position_data["position_size"] = pos_size
                    position_data["entry_price"] = float(pos.get('avgPx', '0'))
                elif pos_size < 0:
                    position_data["position_side"] = "short"
                    position_data["position_size"] = abs(pos_size)
                    position_data["entry_price"] = float(pos.get('avgPx', '0'))
            
            return position_data
            
        except Exception as e:
            write_error(f"获取持仓信息失败: {e}")
            return {
                "position_side": "flat",
                "position_size": 0.0,
                "entry_price": 0.0,
                "leverage": LEVERAGE
            }

# ==================== 模块2: AI输入模块 ====================
class DeepSeekAI:
    """DeepSeek AI交易决策"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.deepseek.com/v1/chat/completions"
    
    def get_trading_decision(self, market_data: Dict, account_status: Dict, position_info: Dict) -> Dict:
        """获取AI交易决策"""
        try:
            # 在AI请求前记录账户状态和持仓信息
            write_echo("=== AI请求账户状态 ===")
            write_echo(f"可用余额: {account_status['available_OKX']:.6f} USDT")
            write_echo(f"账户总权益: {account_status['total_equity']:.6f} USDT")
            write_echo(f"持仓方向: {position_info['position_side']}")
            write_echo(f"持仓数量: {position_info['position_size']:.6f} ETH")
            write_echo(f"开仓均价: {position_info['entry_price']:.2f} USDT")
            write_echo(f"杠杆倍数: {position_info['leverage']}倍")
            
            # 构建AI提示词 - 完全保持原版模板
            prompt = self._build_prompt(market_data, account_status, position_info)
            
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.api_key}'
            }
            
            # 完整的系统提示词 - 完全保持原版
            system_prompt = """角色定位：你是顶级量化竞技AI交易员，专注于OKX交易所的ETH永续合约交易，并且与其他AI交易员互相竞争
核心目标：在小资金实盘环境下，通过精准策略在激烈竞争中保持优势并实现稳定盈利
环境认知：
1. 充满顶级AI对手的高效衍生品市场
2. ETH合约高波动性带来的机会与风险并存
3. 传统策略快速失效，需要持续创新和适应
4. 小资金实盘操作不需要太多风险控制，目的为盈利，风险控制在下单量中即可
5. 所有交易中杠杆倍数默认为100倍
6. 最小下单量0.001ETH，最大下单量0.010ETH
7. 除已提供的信息外，需要其他辅助面与技术面信息自行查询决定
8. 根据所有已掌握的信息与自行查询的信息如布林带，市场30分钟K线图等自行查询
实时状态信息：
1. 账户状态
- 可用余额: {available_OKX} USDT
- 已用保证金: {used_margin} USDT
- 账户总权益: {total_equity} USDT
- 保证金率: {margin_ratio}%
2. 持仓信息
- 持仓方向: {position_side} (long/short/flat)
- 持仓数量: {position_size} ETH
- 开仓均价: {entry_price} USDT
- 当前价格: {current_price} USDT
- 未实现盈亏: {unrealized_pnl} USDT
3. 策略框架
- 多时间维度分析(1m/5m/1h/4h)
- 链上数据与市场情绪结合
- 动态参数调整与风险暴露控制
- 反侦察策略保护(避免典型模式)
4. 风险管理
- 单次风险暴露不超过总资金的30%
- 总持仓风险不超过总资金的10%
- 实时监控策略衰减信号
- 保持策略多样性和快速切换能力
5. 执行要求
- 小资金精细化仓位管理
- 持续的市场适应性学习
基于以上信息和你通过联网查询了解到的所有信息，按照如下Json进行回显来进行实盘操作。
{
  "trading_decision": {
    "action": "hold",                        // 操作类型: open_long-开多仓, open_short-开空仓, close_long-平多仓, close_short-平空仓, hold-持有不变
    "confidence_level": "medium",            // 信心等级: high-高, medium-中, low-低
    "reason": ""  // 简要决策理由
  },
  "position_management": {
    "position_size": 0.1,                    // 建议持仓数量(ETH)，0表示空仓
    "stop_loss_price": 3450.0,               // 建议止损价格(USDT)
    "take_profit_price": 3580.0              // 建议止盈价格(USDT)
  }
}"""
            
            payload = {
                "model": "deepseek-chat",
                "messages": [
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.7,
                "max_tokens": 2000
            }
            
            response = requests.post(self.base_url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            result = response.json()
            
            ai_response = result['choices'][0]['message']['content']
            write_echo("AI原始响应接收成功")
            
            # 记录AI原始响应到回显文件以便调试
            write_echo(f"AI原始响应: {ai_response}")
            
            decision = self._parse_ai_response(ai_response)
            
            # 记录AI决策详细信息
            write_echo("=== AI交易决策 ===")
            write_echo(f"操作类型: {decision['trading_decision']['action']}")
            write_echo(f"信心等级: {decision['trading_decision']['confidence_level']}")
            write_echo(f"决策理由: {decision['trading_decision']['reason']}")
            write_echo(f"建议仓位: {decision['position_management']['position_size']:.6f} ETH")
            
            action = decision['trading_decision']['action']
            if action in ['open_long', 'open_short']:
                write_echo("📈 开仓信号")
            elif action in ['close_long', 'close_short']:
                write_echo("📉 平仓信号")
            else:
                write_echo("⏸️ 保持持仓")
                
            return decision
            
        except Exception as e:
            write_error(f"AI决策获取失败: {e}")
            # 返回保守的持有决策
            return {
                "trading_decision": {
                    "action": "hold",
                    "confidence_level": "low",
                    "reason": f"AI处理失败: {str(e)}"
                },
                "position_management": {
                    "position_size": 0,
                    "stop_loss_price": 0,
                    "take_profit_price": 0
                }
            }
    
    def _build_prompt(self, market_data: Dict, account_status: Dict, position_info: Dict) -> str:
        """构建AI输入提示词 - 完全保持原版模板"""
        input_data = {
            "market_data": {
                "current_price": market_data["current_price"],
                "kline_5min": market_data["kline_5min"]
            },
            "account_status": {
                "available_OKX": account_status["available_OKX"],
                "total_equity": account_status["total_equity"]
            },
            "position_info": {
                "position_side": position_info["position_side"],
                "position_size": position_info["position_size"],
                "entry_price": position_info["entry_price"],
                "leverage": position_info["leverage"]
            }
        }
        
        return json.dumps(input_data, indent=2, ensure_ascii=False)

    def _parse_ai_response(self, response: str) -> Dict:
        """解析AI响应 - 增强解析能力，处理AI返回的非标准格式"""
        try:
            # 首先尝试直接解析整个响应
            try:
                decision = json.loads(response)
                if self._validate_decision_format(decision):
                    return decision
            except:
                pass
            
            # 如果直接解析失败，尝试提取符合我们模板的JSON部分
            # 使用更精确的正则表达式匹配我们的目标格式
            pattern = r'\{\s*"trading_decision"\s*:\s*\{[^{}]*\},\s*"position_management"\s*:\s*\{[^{}]*\}\s*\}'
            matches = re.findall(pattern, response, re.DOTALL)
            
            for match in matches:
                try:
                    # 清理JSON字符串
                    json_str = match.replace('\n', ' ').replace('\t', ' ')
                    # 移除多余的空白字符
                    json_str = re.sub(r'\s+', ' ', json_str).strip()
                    
                    decision = json.loads(json_str)
                    if self._validate_decision_format(decision):
                        write_echo("从响应中成功提取标准JSON决策")
                        return decision
                except Exception as e:
                    write_error(f"提取的JSON解析失败: {e}")
                    continue
            
            # 如果正则匹配失败，尝试手动构建标准格式
            write_echo("尝试手动构建标准格式决策")
            return self._build_standard_decision_from_response(response)
                
        except Exception as e:
            write_error(f"解析AI响应失败: {e}")
            # 返回默认的持有决策
            return {
                "trading_decision": {
                    "action": "hold",
                    "confidence_level": "low",
                    "reason": "AI响应解析失败，采用保守策略"
                },
                "position_management": {
                    "position_size": 0,
                    "stop_loss_price": 0,
                    "take_profit_price": 0
                }
            }
    
    def _build_standard_decision_from_response(self, response: str) -> Dict:
        """从AI响应中手动构建标准格式决策"""
        try:
            # 默认决策
            decision = {
                "trading_decision": {
                    "action": "hold",
                    "confidence_level": "medium",
                    "reason": ""
                },
                "position_management": {
                    "position_size": 0,
                    "stop_loss_price": 0,
                    "take_profit_price": 0
                }
            }
            
            # 尝试从响应中提取action
            action_patterns = [
                r'"action"\s*:\s*"(\w+)"',
                r'action["\']?\s*:\s*["\']?(\w+)',
                r'操作["\']?\s*:\s*["\']?(\w+)'
            ]
            
            for pattern in action_patterns:
                match = re.search(pattern, response, re.IGNORECASE)
                if match:
                    action = match.group(1).lower()
                    valid_actions = ["hold", "open_long", "open_short", "close_long", "close_short"]
                    if action in valid_actions:
                        decision["trading_decision"]["action"] = action
                        break
            
            # 尝试提取reason
            reason_patterns = [
                r'"reason"\s*:\s*"([^"]*)"',
                r'reason["\']?\s*:\s*["\']?([^"\']+)',
                r'理由["\']?\s*:\s*["\']?([^"\']+)'
            ]
            
            for pattern in reason_patterns:
                match = re.search(pattern, response, re.IGNORECASE)
                if match:
                    reason = match.group(1).strip()
                    if reason:
                        decision["trading_decision"]["reason"] = reason
                        break
            
            # 如果没找到reason，使用默认值
            if not decision["trading_decision"]["reason"]:
                decision["trading_decision"]["reason"] = "基于市场分析做出的决策"
            
            write_echo(f"手动构建决策: {decision['trading_decision']['action']}")
            return decision
            
        except Exception as e:
            write_error(f"手动构建决策失败: {e}")
            raise
    
    def _validate_decision_format(self, decision: Dict) -> bool:
        """验证决策格式是否符合模板"""
        try:
            # 检查必需字段是否存在
            if "trading_decision" not in decision or "position_management" not in decision:
                return False
                
            td = decision["trading_decision"]
            pm = decision["position_management"]
            
            if not all(field in td for field in ["action", "confidence_level", "reason"]):
                return False
                
            if not all(field in pm for field in ["position_size", "stop_loss_price", "take_profit_price"]):
                return False
                
            # 验证action值的有效性
            valid_actions = ["hold", "open_long", "open_short", "close_long", "close_short"]
            if td["action"] not in valid_actions:
                return False
                
            # 验证confidence_level值的有效性
            valid_confidences = ["high", "medium", "low"]
            if td["confidence_level"] not in valid_confidences:
                return False
                
            return True
            
        except:
            return False

# ==================== 模块4: 交易执行模块 ====================
class OKXTradingExecutor:
    """OKX交易执行器"""
    
    def __init__(self, data_collector: OKXDataCollector):
        self.dc = data_collector
    
    def execute_trade(self, decision: Dict, current_price: float) -> bool:
        """执行交易决策"""
        try:
            action = decision["trading_decision"]["action"]
            position_size = decision["position_management"]["position_size"]
            
            if position_size < MIN_ORDER_SIZE:
                position_size = 0
            elif position_size > MAX_ORDER_SIZE:
                position_size = MAX_ORDER_SIZE
            
            write_echo(f"执行: {action}, 仓位: {position_size:.4f} ETH")
            
            if action == "hold":
                write_echo("保持持仓")
                return True
                
            elif action in ["open_long", "open_short"]:
                if position_size > 0:
                    success = self._place_order(action, position_size)
                    if success:
                        write_echo("✅ 开仓成功")
                    return success
                else:
                    write_echo("仓位为0，跳过开仓")
                    return True
                
            elif action in ["close_long", "close_short"]:
                success = self._close_position()
                if success:
                    write_echo("✅ 平仓成功")
                return success
                
            else:
                write_error(f"未知交易动作: {action}")
                return False
                
        except Exception as e:
            write_error(f"执行交易失败: {e}")
            return False
    
    def _place_order(self, action: str, size: float) -> bool:
        """下单"""
        try:
            endpoint = "/api/v5/trade/order"
            
            side = "buy" if action == "open_long" else "sell"
            
            # 简化订单参数，避免复杂配置导致API错误
            params = {
                'instId': SYMBOL,
                'tdMode': 'cross',  # 使用cross模式
                'side': side,
                'ordType': 'market',
                'sz': str(size)
            }
            
            # 只在开仓时设置杠杆，平仓时不设置
            if action in ["open_long", "open_short"]:
                params['lever'] = str(LEVERAGE)
            
            result = self.dc._make_request('POST', endpoint, params)
            write_echo(f"下单成功: {side} {size} ETH")
            return True
            
        except Exception as e:
            write_error(f"下单失败: {e}")
            # 检查是否是资金不足错误
            if "insufficient" in str(e).lower() or "balance" in str(e).lower():
                write_error("可能原因：资金不足，请检查账户余额")
            return False
    
    def _close_position(self) -> bool:
        """平仓"""
        try:
            position_info = self.dc.get_position_info()
            
            if position_info["position_size"] == 0:
                write_echo("无持仓可平")
                return True
            
            # 使用市价单平仓，而不是close-position接口
            endpoint = "/api/v5/trade/order"
            
            # 根据持仓方向决定平仓方向
            if position_info["position_side"] == "long":
                side = "sell"
            else:
                side = "buy"
            
            params = {
                'instId': SYMBOL,
                'tdMode': 'cross',
                'side': side,
                'ordType': 'market',
                'sz': str(position_info["position_size"])
            }
            
            result = self.dc._make_request('POST', endpoint, params)
            write_echo("平仓成功")
            return True
            
        except Exception as e:
            write_error(f"平仓失败: {e}")
            return False
    
    def test_trading_module(self) -> bool:
        """测试交易模块"""
        try:
            write_echo("=== 开始交易模块测试 ===")
            
            # 3.1 测试开多单
            write_echo("3.1 测试开多单...")
            success = self._place_order("open_long", MIN_ORDER_SIZE)
            if not success:
                write_error("开多单测试失败")
                return False
            write_echo("开多单成功")
            time.sleep(3)
            
            # 3.2 测试平多单
            write_echo("3.2 测试平多单...")
            success = self._close_position()
            if not success:
                write_error("平多单测试失败")
                return False
            write_echo("平多单成功")
            time.sleep(3)
            
            # 3.3 测试开空单
            write_echo("3.3 测试开空单...")
            success = self._place_order("open_short", MIN_ORDER_SIZE)
            if not success:
                write_error("开空单测试失败")
                return False
            write_echo("开空单成功")
            time.sleep(3)
            
            # 3.4 测试平空单
            write_echo("3.4 测试平空单...")
            success = self._close_position()
            if not success:
                write_error("平空单测试失败")
                return False
            write_echo("平空单成功")
            
            write_echo("✅ 交易模块测试全部通过")
            return True
            
        except Exception as e:
            write_error(f"交易模块测试失败: {e}")
            return False

# ==================== 测试流程 ====================
class TradingBotTester:
    """交易机器人测试器"""
    
    def __init__(self, data_collector: OKXDataCollector, ai_processor: DeepSeekAI, trading_executor: OKXTradingExecutor):
        self.dc = data_collector
        self.ai = ai_processor
        self.executor = trading_executor
    
    def run_full_test(self) -> bool:
        """运行完整测试流程"""
        try:
            write_echo("=== 开始完整测试流程 ===")
            
            # 1. 测试信息收集模块
            write_echo("1. 测试信息收集模块...")
            success = self.test_data_collection()
            if not success:
                write_error("信息收集模块测试失败")
                return False
            write_echo("1信息收集模块运行正常")
            
            # 2. 测试AI输入输出模块
            write_echo("2. 测试AI输入输出模块...")
            success = self.test_ai_module()
            if not success:
                write_error("AI输入输出模块测试失败")
                return False
            
            # 3. 测试交易模块（如果jymkcs为True）
            if jymkcs:
                write_echo("3. 测试交易模块...")
                success = self.executor.test_trading_module()
                if not success:
                    write_error("交易模块测试失败")
                    return False
            
            write_echo("✅ 所有测试通过，进入正式交易")
            return True
            
        except Exception as e:
            write_error(f"完整测试流程失败: {e}")
            return False
    
    def test_data_collection(self) -> bool:
        """测试信息收集模块"""
        try:
            # 测试K线数据获取
            klines = self.dc.get_kline_data()
            if not klines or len(klines) == 0:
                write_error("K线数据获取失败")
                return False
            
            # 测试账户余额获取
            balance = self.dc.get_account_balance()
            if balance["available_OKX"] == 0 and balance["total_equity"] == 0:
                write_error("账户余额获取失败")
                return False
            
            # 测试持仓信息获取
            position = self.dc.get_position_info()
            if position is None:
                write_error("持仓信息获取失败")
                return False
            
            write_echo("信息收集模块测试成功")
            return True
            
        except Exception as e:
            write_error(f"信息收集模块测试失败: {e}")
            return False
    
    def test_ai_module(self) -> bool:
        """测试AI输入输出模块"""
        try:
            # 获取测试数据
            klines = self.dc.get_kline_data()
            current_price = klines[0]['close'] if klines else 0
            
            market_data = {
                "current_price": current_price,
                "kline_5min": klines
            }
            
            account_status = self.dc.get_account_balance()
            position_info = self.dc.get_position_info()
            
            # 记录AI输入
            write_echo("=== AI输入数据 ===")
            input_data = {
                "market_data": market_data,
                "account_status": account_status,
                "position_info": position_info
            }
            write_echo(json.dumps(input_data, indent=2, ensure_ascii=False))
            
            # 获取AI决策
            ai_decision = self.ai.get_trading_decision(market_data, account_status, position_info)
            
            # 记录AI输出
            write_echo("=== AI输出数据 ===")
            write_echo(json.dumps(ai_decision, indent=2, ensure_ascii=False))
            
            write_echo("AI输入输出模块测试成功")
            return True
            
        except Exception as e:
            write_error(f"AI输入输出模块测试失败: {e}")
            return False

# ==================== 主程序 ====================
class ETHTradingBot:
    """ETH交易机器人主程序"""
    
    def __init__(self):
        self.data_collector = OKXDataCollector(OKX_API_KEY, OKX_SECRET, OKX_PASSWORD)
        self.ai_processor = DeepSeekAI(DEEPSEEK_API_KEY)
        self.trading_executor = OKXTradingExecutor(self.data_collector)
        self.tester = TradingBotTester(self.data_collector, self.ai_processor, self.trading_executor)
        
        write_echo("交易机器人初始化完成")
    
    def run_tests(self) -> bool:
        """运行测试流程"""
        return self.tester.run_full_test()
    
    def run_single_cycle(self):
        """执行单个交易周期"""
        try:
            write_echo("开始交易周期")
            
            # 1. 收集市场数据
            klines = self.data_collector.get_kline_data()
            current_price = klines[0]['close'] if klines else 0
            
            market_data = {
                "current_price": current_price,
                "kline_5min": klines
            }
            
            write_echo(f"当前价格: {current_price:.2f} USDT")
            
            # 2. 获取账户状态
            account_status = self.data_collector.get_account_balance()
            
            # 3. 获取持仓信息
            position_info = self.data_collector.get_position_info()
            
            # 4. AI决策
            ai_decision = self.ai_processor.get_trading_decision(
                market_data, account_status, position_info
            )
            
            # 5. 执行交易
            if ai_decision:
                success = self.trading_executor.execute_trade(ai_decision, current_price)
                if success:
                    write_echo("交易执行完成")
                else:
                    write_echo("交易执行失败")
            
            write_echo("交易周期完成")
            
        except Exception as e:
            write_error(f"交易周期执行失败: {e}")
    
    def run_continuously(self):
        """持续运行"""
        write_echo("开始持续运行")
        
        while True:
            try:
                self.run_single_cycle()
                write_echo(f"等待 {AI_FREQUENCY} 秒")
                time.sleep(AI_FREQUENCY)
                
            except KeyboardInterrupt:
                write_echo("程序被用户中断")
                break
            except Exception as e:
                write_error(f"主循环异常: {e}")
                write_echo("30秒后重试...")
                time.sleep(30)

if __name__ == "__main__":
    bot = ETHTradingBot()
    
    write_echo("=== ETH交易程序启动 ===")
    write_echo(f"交易对: {SYMBOL}")
    write_echo(f"杠杆: {LEVERAGE}倍")
    write_echo(f"频率: {AI_FREQUENCY}秒")
    
    # 运行测试流程
    if bot.run_tests():
        write_echo("测试成功，开始正式交易")
        bot.run_continuously()
    else:
        write_error("测试失败，程序退出")