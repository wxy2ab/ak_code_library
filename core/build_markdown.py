import os
import json

def build_markdown():
    agenda_file = './json/agenda.json'
    readme_file = './README.md'
    table_header = "# Table of Contents\n\n| 索引 | 名称 | 步骤 |\n|------|------|------|\n"
    table_rows = []

    # 读取 agenda.json
    with open(agenda_file, 'r', encoding='utf-8') as file:
        agenda = json.load(file)

    # 构建表格内容
    for item in agenda:
        index = item.get("index", "")
        key = item.get("key", "")
        number_of_steps = item.get("number_of_steps", "")
        table_rows.append(f"| {index} | {key} | {number_of_steps} |")

    table_content = table_header + "\n".join(table_rows) + "\n"

    # 读取 README.md
    with open(readme_file, 'r', encoding='utf-8') as file:
        readme_content = file.read()

    # 替换 # Table of Contents 之后的内容
    if "# Table of Contents" in readme_content:
        readme_content = readme_content.split("# Table of Contents")[0] + table_content

    # 写回 README.md
    with open(readme_file, 'w', encoding='utf-8') as file:
        file.write(readme_content)

if __name__ == "__main__":
    build_markdown()
