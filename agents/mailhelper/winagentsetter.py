import winreg

def set_proxy(proxy_server, exceptions):
    try:
        # 打开注册表
        reg = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
        reg_key = winreg.OpenKey(reg, r"Software\Microsoft\Windows\CurrentVersion\Internet Settings", 0, winreg.KEY_WRITE)

        # 设置代理服务器
        winreg.SetValueEx(reg_key, "ProxyServer", 0, winreg.REG_SZ, proxy_server)
        # 设置例外的IP地址
        winreg.SetValueEx(reg_key, "ProxyOverride", 0, winreg.REG_SZ, exceptions)


        # 启用代理
        winreg.SetValueEx(reg_key, "ProxyEnable", 0, winreg.REG_DWORD, 1)

        # 刷新系统代理设置
        import ctypes
        INTERNET_OPTION_SETTINGS_CHANGED = 39
        INTERNET_OPTION_REFRESH = 37
        internet_set_option = ctypes.windll.Wininet.InternetSetOptionW
        internet_set_option(0, INTERNET_OPTION_SETTINGS_CHANGED, 0, 0)
        internet_set_option(0, INTERNET_OPTION_REFRESH, 0, 0)

        print("代理设置成功！")

    except Exception as e:
        print("代理设置失败：", str(e))

# 设置代理服务器和例外的IP地址
proxy_server = "127.0.0.1:33210"
exceptions = "127.0.0.1;191.168.6.*;191.168.7.240;10.*;192.168.*;191.168.1.131"

set_proxy(proxy_server, exceptions)