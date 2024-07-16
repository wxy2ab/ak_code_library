import sys
from core.run_content import run_content

if __name__ =="__main__":
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