from core.down_llms import down_all_files,is_need_update
from core.build_table_of_contents import build_table_of_contents
from core.build_markdown import build_markdown

if __name__ =="__main__":
    if is_need_update():
        down_all_files()
    build_table_of_contents()
    build_markdown()