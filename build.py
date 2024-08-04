from core.down_llms import download_all_files,is_socket_connected,check_proxy_running
from core.build_table_of_contents import build_table_of_contents
from core.build_markdown import build_markdown

if __name__ =="__main__":
    proxy_host = "127.0.0.1"
    proxy_port = 10809
    if is_socket_connected(proxy_host, proxy_port):
        check_proxy_running(proxy_host, proxy_port, "http")
    download_all_files()
    build_table_of_contents()
    build_markdown()