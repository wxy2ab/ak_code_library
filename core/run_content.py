import os
import json
import sys
import time
from datetime import datetime
from core.llms.llm_factory import LLMFactory
from core.interpreter.ast_code_runner import ASTCodeRunner
from core.interpreter.data_summarizer import DataSummarizer

def load_global_vars():
    llm_factory = LLMFactory()
    llm_client = llm_factory.get_instance()
    data_summarizer = DataSummarizer()
    return {
        'llm_client': llm_client,
        'llm_factory': llm_factory,
        'data_summarizer': data_summarizer
    }

def execute_step(step, global_vars, saved_data, runner, analysis_results):
    step_code_path = step["step_code_path"]
    if not os.path.exists(step_code_path):
        raise FileNotFoundError(f"{step_code_path} not found")

    print(f"Executing step {step['step_number']}: {step['description']}")
    print(f"Running code from: {step_code_path}")

    start_time = time.time()
    
    with open(step_code_path, 'r', encoding='utf-8') as file:
        code = file.read()

    for required_data in step.get("required_data", []):
        global_vars[required_data] = saved_data.get(required_data)

    result = runner.run(code, global_vars)
    
    if result["debug"]:
        print(result["debug"])
    if result["output"]:
        print(result["output"])
    if result["error"]:
        print(f"Error: {result['error']}")

    global_vars.update(result["updated_vars"])

    if "save_data_to" in step:
        saved_data[step["save_data_to"]] = global_vars.get(step["save_data_to"])

    if step["type"] == "data_analysis":
        analysis_result = global_vars.get("analysis_result", "")
        step_result=f"步骤 {step['step_number']}: {step['description']} 的输出是：{analysis_result}"
        analysis_results.append(step_result)
        print(step_result)

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Step {step['step_number']} finished. Execution time: {elapsed_time:.2f} seconds\n")

def create_report_prompt(initial_query: str, results_summary: str) -> str:
    return f"""
    基于以下初始查询和分析结果，生成一份全面的报告：

    初始查询：
    {initial_query}

    分析结果：
    {results_summary}

    请生成一份全面的报告，总结数据分析的发现和洞察。报告应该：
    1. 回答初始查询
    2. 总结每个分析任务的主要发现
    3. 提供整体的见解和结论
    4. 指出任何有趣或意外的发现
    5. 如果适用，提供进一步分析的建议

    报告应结构清晰、表述明确，并提供有意义的结论。
    """

def run_content(n, cmd_args):
    with open('./json/agenda.json', 'r', encoding='utf-8') as agenda_file:
        agenda = json.load(agenda_file)

    item = next((entry for entry in agenda if entry["index"] == n), None)
    if not item:
        raise ValueError(f"No entry with index {n}")

    plan_path = os.path.join('./library', os.path.relpath(item["path"], start='./'))
    with open(plan_path, 'r', encoding='utf-8') as plan_file:
        plan_data = json.load(plan_file)

    global_vars = load_global_vars()
    saved_data = {}
    runner = ASTCodeRunner()
    analysis_results = []

    for step in plan_data["steps"]:
        step_code_path = os.path.join(os.path.dirname(plan_path), f'step_code_{step["step_number"]}.py')
        step["step_code_path"] = step_code_path

        # 处理参数
        if "parameters" in step:
            for param in step["parameters"]:
                key = param["key"]
                default_value = eval(param["value"])  # 解析默认值
                if key in cmd_args:
                    value = cmd_args[key]
                else:
                    value = default_value
                global_vars[key] = value
                print(f"Setting parameter {key} = {value}")

        execute_step(step, global_vars, saved_data, runner, analysis_results)

    llm_client = global_vars['llm_client']
    combined_analysis_results = "\n".join(analysis_results)
    report_message = create_report_prompt(plan_data["query_summary"], combined_analysis_results)
    final_report = llm_client.text_chat(report_message)

    print("Final Report:")
    print(final_report)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run_content.py <n> [param1=value1] [param2=value2] ...")
        sys.exit(1)
    
    n = int(sys.argv[1])
    
    # 解析命令行参数
    cmd_args = {}
    for arg in sys.argv[2:]:
        key, value = arg.split('=')
        cmd_args[key] = value
    
    run_content(n, cmd_args)
