import os
import json
from datetime import datetime

def get_py_files_lines_count(directory):
    total_lines = 0
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                    total_lines += len(f.readlines())
    return total_lines

def get_file_creation_time(file_path):
    return os.path.getctime(file_path)

def build_table_of_contents():
    library_dir = "./library"
    output_file = "./json/agenda.json"
    agenda = []

    for dir_name in os.listdir(library_dir):
        dir_path = os.path.join(library_dir, dir_name)
        if os.path.isdir(dir_path):
            plan_file_path = os.path.join(dir_path, "plan.json")
            if os.path.exists(plan_file_path):
                with open(plan_file_path, 'r', encoding='utf-8') as plan_file:
                    plan_data = json.load(plan_file)
                
                query_summary = plan_data.get("query_summary", "")
                number_of_steps = len(plan_data.get("steps", []))
                lines_of_code = get_py_files_lines_count(dir_path)
                create_time = datetime.fromtimestamp(get_file_creation_time(plan_file_path)).isoformat()
                relative_path = os.path.relpath(plan_file_path, start=library_dir)

                agenda_item = {
                    "key": query_summary,
                    "number_of_steps": number_of_steps,
                    "lines_of_code": lines_of_code,
                    "create_time": create_time,
                    "path": relative_path
                }
                agenda.append(agenda_item)
    
    # Sort by create_time
    agenda.sort(key=lambda x: x["create_time"])

    # Add index
    for i, item in enumerate(agenda, start=1):
        item["index"] = i

    # Write to the output file
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as out_file:
        json.dump(agenda, out_file, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    build_table_of_contents()
