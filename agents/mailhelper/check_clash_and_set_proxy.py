import wmi
import winreg
import yaml
import traceback


# 检查clash.exe进程是否存在
def check_clash_process():
    c = wmi.WMI()
    process = c.Win32_Process(name='clash.exe')
    if len(process) == 0:
        return False
    return True


# 从clash的yaml配置文件中提取proxy_server中的配置的ip和端口值
def extract_proxy_server_from_yaml():
    commandline = ''
    c = wmi.WMI()
    process = c.Win32_Process(name='clash.exe')
    if process:
        commandline = process[0].commandline

    start_idx = commandline.find("-f") + 3
    end_idx = commandline.rfind(".yaml") + 5
    config_file_path = commandline[start_idx:end_idx]
    print(config_file_path)
    with open(config_file_path, 'r') as f:
        config = yaml.load(f, Loader=yaml.FullLoader)

    if 'external-controller' in config:
        proxy_server = "127.0.0.1:" + config['external-controller'].split(':')[1]
        print(proxy_server)
        return proxy_server

    return None


# 设置代理服务器和例外的IP地址
def set_proxy(proxy_server, exceptions):
    try:
        # 打开注册表
        reg = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
        reg_key = winreg.OpenKey(reg, r"Software\Microsoft\Windows\CurrentVersion\Internet Settings", 0,
                                 winreg.KEY_READ | winreg.KEY_WRITE)

        # 检查ProxyServer是否需要设置
        existing_proxy_server = winreg.QueryValueEx(reg_key, "ProxyServer")[0]
        print("existing_proxy_server:"+existing_proxy_server)
        if existing_proxy_server == None or existing_proxy_server != proxy_server:
            # 设置代理服务器
            winreg.SetValueEx(reg_key, "ProxyServer", 0, winreg.REG_SZ, proxy_server)

        # 设置例外的IP地址
        winreg.SetValueEx(reg_key, "ProxyOverride", 0, winreg.REG_SZ, exceptions)

        # 检查ProxyEnable是否需要设置
        existing_proxy_enable = winreg.QueryValueEx(reg_key, "ProxyEnable")[0]
        if existing_proxy_enable == None or existing_proxy_enable != 1:
            # 启用代理
            winreg.SetValueEx(reg_key, "ProxyEnable", 0, winreg.REG_DWORD, 1)

        # 刷新系统代理设置
        import ctypes
        INTERNET_OPTION_SETTINGS_CHANGED = 39
        INTERNET_OPTION_REFRESH = 37
        internet_set_option = ctypes.windll.Wininet.InternetSetOptionW
        internet_set_option(0, INTERNET_OPTION_REFRESH, 0, 0)
        internet_set_option(0, INTERNET_OPTION_SETTINGS_CHANGED, 0, 0)

        print("代理设置成功！")

    except Exception as e:
        print("代理设置失败：", str(e))
        traceback.print_exc()


if check_clash_process():
    proxy_server = extract_proxy_server_from_yaml()
    if proxy_server:
        # 设置代理服务器和例外的IP地址
        exceptions = "127.0.0.1;191.168.6.*;191.168.6.232;191.168.7.240;10.*;192.168.*;191.168.1.131;191.168.5.71"
        print("set to prox:"+proxy_server)
        set_proxy(proxy_server, exceptions)
else:
    print("clash.exe进程不存在，不做任何操作。")
