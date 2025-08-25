#!/usr/bin/env python3
import os
import sys
import argparse

def send_to_all_terminals(message, only_active=False):
    """
    向所有终端发送消息
    :param message: 要发送的消息内容
    :param only_active: 是否仅发送给活跃终端（通过 who 命令检测）
    """
    try:
        if only_active:
            # 通过 who 命令获取活跃终端列表（更精准）
            terminals = [f"/dev/{term}" for term in os.popen('who | awk \'{print $2}\'').read().split()]
        else:
            # 遍历所有 /dev/pts/* 终端（可能包含不活跃的）
            terminals = [f"/dev/pts/{n}" for n in os.listdir('/dev/pts') if n[0].isdigit()]

        for term in terminals:
            try:
                with open(term, 'w') as t:
                    t.write(message + '\n')
            except PermissionError:
                print(f"无权限写入终端 {term}（需要 root 权限）", file=sys.stderr)
            except Exception as e:
                print(f"写入终端 {term} 失败: {e}", file=sys.stderr)

    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="向所有终端发送消息")
    parser.add_argument("message", help="要发送的消息内容")
    parser.add_argument("--active", action="store_true", help="仅发送给活跃终端（通过 who 命令检测）")
    args = parser.parse_args()

    send_to_all_terminals(args.message, args.active)


'''
   chmod +x send_to_all_terminals.py
        ./send_to_all_terminals.py "Hello, all terminals!"
     ./send_to_all_terminals.py "Hello_to_all_terminals.py "Hello, active users!" --active
          sudo ./send_to_all_terminals.py "System will reboot in 5 minutes!"
'''