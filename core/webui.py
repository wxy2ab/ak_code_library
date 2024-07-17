import streamlit as st
import os
import json
import time
import re
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

    st.write(f"执行步骤 {step['step_number']}: {step['description']}")
    st.write(f"运行代码来自: {step_code_path}")

    start_time = time.time()
    
    with open(step_code_path, 'r', encoding='utf-8') as file:
        code = file.read()

    for required_data in step.get("required_data", []):
        global_vars[required_data] = saved_data.get(required_data)

    result = runner.run(code, global_vars)
    
    if result["debug"]:
        st.write(result["debug"])
    if result["output"]:
        st.write(result["output"])
    if result["error"]:
        st.error(f"错误: {result['error']}")

    global_vars.update(result["updated_vars"])

    if "save_data_to" in step:
        saved_data[step["save_data_to"]] = global_vars.get(step["save_data_to"])

    if step["type"] == "data_analysis":
        analysis_result = global_vars.get("analysis_result", "")
        step_result = f"步骤 {step['step_number']}: {step['description']} 的输出是：{analysis_result}"
        analysis_results.append(step_result)
        st.write(step_result)

    end_time = time.time()
    elapsed_time = end_time - start_time
    st.write(f"步骤 {step['step_number']} 完成。执行时间: {elapsed_time:.2f} 秒\n")

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
    6. 图片和文件按 ![分析图表]({{file_name}}) 格式使用

    报告应结构清晰、表述明确，并提供有意义的结论。
    """

def get_unique_images(output_dir):
    if os.path.exists(output_dir):
        return list(set([f for f in os.listdir(output_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]))
    return []

def display_report_with_images(report, output_dir):
    unique_images = get_unique_images(output_dir)
    displayed_images = set()
    
    # 将报告拆分成段落
    paragraphs = report.split('\n\n')
    
    for paragraph in paragraphs:
        # 检查段落中的图片引用
        for img in unique_images:
            img_pattern = r'!\[.*?\]\({}\)'.format(re.escape(img))
            if re.search(img_pattern, paragraph) and img not in displayed_images:
                st.image(os.path.join(output_dir, img), caption=img)
                displayed_images.add(img)
                paragraph = re.sub(img_pattern, '', paragraph)
        
        # 显示处理后的段落文本
        if paragraph.strip():
            st.markdown(paragraph)
    
    # 显示报告中未引用的图片
    for img in unique_images:
        if img not in displayed_images:
            st.image(os.path.join(output_dir, img), caption=img)

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

        if "parameters" in step:
            for param in step["parameters"]:
                key = param["key"]
                default_value = eval(param["value"])
                value = cmd_args.get(key, default_value)
                global_vars[key] = value
                st.write(f"设置参数 {key} = {value}")

        execute_step(step, global_vars, saved_data, runner, analysis_results)

    llm_client = global_vars['llm_client']
    combined_analysis_results = "\n".join(analysis_results)
    report_message = create_report_prompt(plan_data["query_summary"], combined_analysis_results)
    final_report = llm_client.text_chat(report_message)

    # 不再在这里添加图片引用，而是依赖原始报告中的引用

    return final_report

def main():
    st.set_page_config(layout="wide")
    
    tab1, tab2 = st.tabs(["议程", "运行结果"])
    
    with tab1:
        st.title("议程")
        
        with open('./json/agenda.json', 'r', encoding='utf-8') as agenda_file:
            agenda = json.load(agenda_file)
        
        col1, col2, col3, col4, col5 = st.columns([1, 8, 1, 2, 2])
        col1.write("索引")
        col2.write("名称")
        col3.write("步骤")
        col4.write("参数")
        col5.write("操作")
        
        for item in agenda:
            col1, col2, col3, col4, col5 = st.columns([1, 8, 1, 2, 2])
            
            col1.write(item["index"])
            col2.write(item["key"])
            col3.write(item["number_of_steps"])
            col4.write(item["params"])
            if col5.button("运行", key=f"run_{item['index']}"):
                st.session_state.selected_index = item["index"]
                st.session_state.selected_params = item["params"]
                st.session_state.run_clicked = True
        
        if 'run_clicked' in st.session_state and st.session_state.run_clicked:
            st.write(f"准备运行任务 {st.session_state.selected_index}")
            
            if st.session_state.selected_params:
                st.session_state.param_values = {}
                for param in st.session_state.selected_params.split(','):
                    value = st.text_input(f"请输入 {param} 的值")
                    st.session_state.param_values[param] = value
            
            if st.button("确认运行"):
                st.session_state.confirm_run = True
                st.rerun()
    
    with tab2:
        st.title("运行结果")
        
        if 'confirm_run' in st.session_state and st.session_state.confirm_run:
            st.write(f"正在运行任务 {st.session_state.selected_index}")
            
            cmd_args = st.session_state.param_values if 'param_values' in st.session_state else {}
            
            try:
                final_report = run_content(st.session_state.selected_index, cmd_args)
                st.subheader("最终报告")
                display_report_with_images(final_report, './output')
            except Exception as e:
                st.error(f"发生错误: {str(e)}")
            
            st.session_state.confirm_run = False
            st.session_state.run_clicked = False

if __name__ == "__main__":
    main()