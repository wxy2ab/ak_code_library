import os
import json
import importlib.util
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

def execute_step(step, global_vars, saved_data, runner):
    step_code_path = step["step_code_path"]
    if not os.path.exists(step_code_path):
        raise FileNotFoundError(f"{step_code_path} not found")

    with open(step_code_path, 'r', encoding='utf-8') as file:
        code = file.read()

    for required_data in step.get("required_data", []):
        global_vars[required_data] = saved_data.get(required_data)

    for result in runner.run_sse(code, global_vars):
        pass

    if "save_data_to" in step:
        saved_data[step["save_data_to"]] = global_vars.get(step["save_data_to"])

    if step["type"] == "data_analysis":
        global_vars["analysis_result"] = global_vars.get("analysis_result", "") + step.get("description", "") + "\n"

def run_content(n):
    with open('./json/agenda.json', 'r', encoding='utf-8') as agenda_file:
        agenda = json.load(agenda_file)

    item = next((entry for entry in agenda if entry["index"] == n), None)
    if not item:
        raise ValueError(f"No entry with index {n}")

    plan_path = os.path.join('./library', os.path.relpath(item["path"], start='library'))
    with open(plan_path, 'r', encoding='utf-8') as plan_file:
        plan_data = json.load(plan_file)

    global_vars = load_global_vars()
    saved_data = {}
    runner = ASTCodeRunner()

    for step in plan_data["steps"]:
        step_code_path = os.path.join(os.path.dirname(plan_path), f'step_code_{step["step_number"]}.py')
        step["step_code_path"] = step_code_path
        execute_step(step, global_vars, saved_data, runner)

    llm_client = global_vars['llm_client']
    report_message = plan_data["query_summary"] + "\n" + global_vars.get("analysis_result", "")
    final_report = llm_client.text_chat(report_message)

    print(final_report)

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python run_content.py <n>")
        sys.exit(1)
    
    n = int(sys.argv[1])
    run_content(n)
