from datetime import datetime
import os
import socket
import requests
import base64

# GitHub repository details
owner = "wxy2ab"
repo = "akinterpreter"
path = "core/llms"
branch = "main"  # Change this to the correct branch if it's not 'main'
path_utils = "core/utils"
path_interpreter = "core/interpreter"
files_to_download = [
    "core/utils/__init__.py",
    "core/utils/config_setting.py",
    "core/utils/log.py",
    "core/utils/retry.py",
    "core/utils/single_ton.py",
    "core/utils/stop_words.py",
    "core/utils/timer.py",
    "core/utils/handle_max_tokens.py",
    "core/interpreter/__init__.py",
    "core/interpreter/ast_code_runner.py",
    "core/interpreter/data_summarizer.py",
    "core/planner/__init__.py",
    "core/planner/llm_factor.py"
]
# GitHub API URL for repository contents
url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}?ref={branch}"

path_to_file = "core/utils/__init__.py"
local_file_path = "./core/utils/__init__.py"

def get_github_file_last_modified(owner, repo, branch, path_to_file):
    url = f"https://api.github.com/repos/{owner}/{repo}/commits"
    params = {
        "path": path_to_file,
        "sha": branch,
        "per_page": 1
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        commit_info = response.json()
        if commit_info:
            last_modified = commit_info[0]['commit']['committer']['date']
            return datetime.strptime(last_modified, '%Y-%m-%dT%H:%M:%SZ')
    return None

def get_local_file_last_modified(file_path):
    if os.path.exists(file_path):
        timestamp = os.path.getmtime(file_path)
        return datetime.fromtimestamp(timestamp)
    return None

def is_remote_file_newer(owner, repo, branch, path_to_file, local_file_path):
    remote_last_modified = get_github_file_last_modified(owner, repo, branch, path_to_file)
    local_last_modified = get_local_file_last_modified(local_file_path)

    if remote_last_modified and local_last_modified:
        return remote_last_modified > local_last_modified
    elif remote_last_modified:
        # If local file doesn't exist, consider remote file as newer
        return True
    return False


# Function to download a file from GitHub
def download_file(file_info):
    file_url = file_info["download_url"]
    file_path = os.path.join(file_info["path"])

    response = requests.get(file_url)
    if response.status_code == 200:
        with open(file_path, 'wb') as file:
            file.write(response.content)
        print(f"Downloaded: {file_path}")
    else:
        print(f"Failed to download: {file_path}")

def down_llms():
    # Fetch the list of files in the directory
    response = requests.get(url)
    if response.status_code == 200:
        files = response.json()
        for file_info in files:
            if file_info["type"] == "file":
                download_file(file_info)
    else:
        print(f"Failed to fetch file list from GitHub: {response.status_code}")

    print("Download completed.")

def download_single(file_path):
    url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{file_path}"
    local_path = os.path.join(file_path)

    # Create local directory if it does not exist
    os.makedirs(os.path.dirname(local_path), exist_ok=True)

    response = requests.get(url)
    if response.status_code == 200:
        with open(local_path, 'wb') as file:
            file.write(response.content)
        print(f"Downloaded: {local_path}")
    else:
        print(f"Failed to download: {local_path} (Status code: {response.status_code})")


def is_socket_connected(host, port):
    try:
        # 创建一个 socket 对象并尝试连接
        with socket.create_connection((host, port), timeout=5) as sock:
            return True
    except (socket.timeout, ConnectionRefusedError):
        return False


def check_proxy_running(host, port=10808,type="socks5"):
    # 要检查的地址和端口
    try:
        if is_socket_connected(host, port):
            import os
            os.environ["http_proxy"]  = f"{type}://{host}:{port}"
            os.environ["https_proxy"] = f"{type}://{host}:{port}"
        else:
            print("没有代理服务器")
    except Exception as e:
        host = "127.0.0.1"
        import os
        os.environ["http_proxy"]  = f"{type}://{host}:10808"
        os.environ["https_proxy"] = f"{type}://{host}:10808"
        print("连接到代理")

def down_all_files():

    # Create the directory if it doesn't exist
    if not os.path.exists(path):
        os.makedirs(path)
    down_llms()

    if not os.path.exists(path_interpreter):
        os.makedirs(path_interpreter)

    if not os.path.exists(path_utils):
        os.makedirs(path_utils)
    for file_path in files_to_download:
        download_single(file_path)


def is_need_update():
    proxy_host="127.0.0.1"
    proxy_port=10809
    running = is_socket_connected(proxy_host,proxy_port)
    if running:
        check_proxy_running(proxy_host,proxy_port,"http")

    return is_remote_file_newer(owner, repo, branch, path_to_file, local_file_path)

if __name__ == "__main__":
    down_all_files()
