import json
from typing import List, Dict, Any
from core.llms.llm_factory import LLMFactory
import re

def build_parameters(path: str, user_hint: str = ""):
    """
    input:
        path: 代码库路径，形如 "code_1"
        user_hint: 用户提供的提示信息
    output:
        None
    """
    llm_client = LLMFactory().get_instance()

    # 读取 plan.json 文件
    with open(f'./library/{path}/plan.json', 'r', encoding='utf-8') as f:
        plan = json.load(f)
    
    # 找出 data_retrieval 步骤
    data_retrieval_steps = [step for step in plan['steps'] if step['type'] == 'data_retrieval']
    
    for step in data_retrieval_steps:
        step_number = step['step_number']
        code_file_path = f'./library/{path}/step_code_{step_number}.py'
        
        # 读取代码文件
        with open(code_file_path, 'r', encoding='utf-8') as f:
            original_code = f.read()
        
        # 使用 LLM API 分析代码并确定参数
        parameters = analyze_code_for_parameters(llm_client, original_code, user_hint)
        
        # 使用 LLM API 修改代码
        new_code = modify_code_with_parameters(llm_client, original_code, parameters)
        
        # 保存新的代码文件
        new_code_file_path = f'{code_file_path}.py'
        with open(new_code_file_path, 'w', encoding='utf-8') as f:
            f.write(new_code)
        
        # 更新 plan.json
        step['parameters'] = parameters
    
    # 保存更新后的 plan.json
    with open(f'./library/{path}/plan.json', 'w', encoding='utf-8') as f:
        json.dump(plan, f, ensure_ascii=False, indent=2)

def analyze_code_for_parameters(llm_client: Any, code: str, user_hint: str) -> List[Dict[str, str]]:
    prompt = f"""
    分析以下 Python 代码，并确定哪些值应该作为参数。返回一个参数列表，包括参数名和当前值。
    如果提供了用户提示，请考虑用户的建议。
    
    代码：
    {code}
    
    用户提示：{user_hint if user_hint else "无"}
    
    请以 JSON 格式返回参数列表，格式如下：
    [
        {{"key": "参数名1", "value": "参数值1"}},
        {{"key": "参数名2", "value": "参数值2"}},
        ...
    ]
    """
    
    response = llm_client.one_chat(prompt)
    
    # 使用正则表达式提取 JSON 内容
    json_match = re.search(r'\[[\s\S]*\]', response)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            print("提取的 JSON 格式无效。使用空列表作为参数。")
            return []
    else:
        print("未能在 LLM 响应中找到 JSON 内容。使用空列表作为参数。")
        return []

def modify_code_with_parameters(llm_client: Any, code: str, parameters: List[Dict[str, str]]) -> str:
    prompt = f"""
    修改以下 Python 代码，将固定值替换为参数名。使用提供的参数列表。
    只替换固定值为变量名，不要进行其他修改。
    
    原始代码：
    ```python
    {code}
    ```
    
    参数列表：
    {json.dumps(parameters, ensure_ascii=False, indent=2)}
    
    请返回修改后的完整代码，使用 ```python 和 ``` 包裹。
    """
    
    response = llm_client.one_chat(prompt)
    return extract_code(response)

def extract_code(response: str) -> str:
    code_match = re.search(r'```python\n([\s\S]*?)\n```', response)
    if code_match:
        return code_match.group(1).strip()
    else:
        print("未能在 LLM 响应中找到代码块。返回原始响应。")
        return response.strip()

# 使用示例
# build_parameters('your_path', user_hint='请将股票代码作为参数')