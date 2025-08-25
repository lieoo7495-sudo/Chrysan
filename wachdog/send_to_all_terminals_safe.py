#!/usr/bin/env python3
import os
import sys
import argparse

def send_to_all_terminals(message, only_active=False):
    """
    安全地向所有终端发送消息（不干扰用户输入）
    :param message: 消息内容（自动添加换行符）
    :param only_active: 是否仅发送给活跃终端
    """
    try:
        # 格式化消息：独立行 + 换行符
        formatted_msg = f"\n{message}\n"

        if only_active:
            terminals = [f"/dev/{term}" for term in os.popen('who | awk \'{print $2}\'').read().split()]
        else:
            terminals = [f"/dev/pts/{n}" for n in os.listdir('/dev/pts') if n[0].isdigit()]

        for term in terminals:
            try:
                with open(term, 'w') as t:
                    t.write(formatted_msg)
            except PermissionError:
                print(f"跳过无权限终端: {term}", file=sys.stderr)
            except Exception as e:
                print(f"写入终端 {term} 失败: {e}", file=sys.stderr)

    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="安全地向所有终端发送消息")
    parser.add_argument("message", help="要发送的消息内容")
    parser.add_argument("--active", action="store_true", help="仅发送给活跃终端")
    args = parser.parse_args()

    send_to_all_terminals(args.message, args.active)