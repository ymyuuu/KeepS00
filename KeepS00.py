import os, sys, paramiko, yaml, logging

# 设置日志格式及级别
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def load_config():
    cfg = os.environ.get('CONFIG')
    if not cfg:
        logging.error("环境变量 CONFIG 未设置")
        return []
    try:
        config = yaml.safe_load(cfg)
        return config.get('accounts', [])
    except Exception as e:
        logging.error(f"加载配置失败: {e}")
        return []

def run_account(acc):
    if not isinstance(acc, dict):
        logging.error("无效的账户配置，跳过")
        return

    username = acc.get('username', '').strip()
    password = acc.get('password', '').strip()
    cmd = acc.get('cmd', '').strip()
    tip = acc.get('tip', '')
    tip = tip.strip() if isinstance(tip, str) else ''

    if not (username and password and cmd):
        logging.error("账户配置缺少必要字段，跳过")
        return

    disp = f"{username} ({tip})" if tip else username
    hostname = f"{username}.serv00.net"
    logging.info(f"处理 {disp} ...")
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname, port=22, username=username, password=password)
    except Exception as e:
        logging.error(f"{disp} 连接失败: {e}")
        return

    cmds = [
        "echo '' | crontab -",
        f'(crontab -l 2>/dev/null; echo "0 * * * * {cmd}") | crontab -',
        f'(crontab -l 2>/dev/null; echo "@reboot {cmd}") | crontab -',
        f'(crontab -l 2>/dev/null; echo "0 0 * * * kill -9 -1 && {cmd}") | crontab -',
        cmd
    ]
    for c in cmds:
        try:
            ssh.exec_command(c)[1].channel.recv_exit_status()
        except Exception as e:
            logging.error(f"{disp} 执行失败: {e}")
            ssh.close()
            return
    ssh.close()
    logging.info(f"{disp} 完成")

def print_separator():
    # 方式1：使用 print 输出换行符（但 GitHub Actions 可能合并纯换行）
    print("\n")
    
    # 方式2：输出一条横线作为分隔符
    print("--------------------------------------------------")
    
    # 方式3：使用 sys.stdout.write 输出换行符，并立即刷新
    sys.stdout.write("\n")
    sys.stdout.flush()

def main():
    accounts = load_config()
    if not accounts:
        logging.error("没有有效的账户配置")
        return
    for acc in accounts:
        run_account(acc)
        # 调用多种方式输出换行分隔符
        print_separator()

if __name__ == '__main__':
    main()
