#!/usr/bin/env python

import argparse
import re
import socket
import subprocess
import sys
import os
import platform

# ===================== 配置区域 =====================
# 分区监控阈值配置
WORK_BYTES_THRESHOLD = 0.85      # WORK分区空间使用率警报阈值
WORK_INODES_THRESHOLD = 0.85     # WORK分区inode使用率警报阈值

STORE_BYTES_THRESHOLD = 0.85     # STORE分区空间使用率警报阈值
STORE_INODES_THRESHOLD = 0.85    # STORE分区inode使用率警报阈值

SCRATCH_QUOTA_THRESHOLD = 0.75   # SCRATCH分区配额使用率警报阈值
SCRATCH_GLOBAL_THRESHOLD = 100 * 2**40  # SCRATCH全局空间剩余警报阈值(100TB)

WORKSF_BYTES_THRESHOLD = 0.85    # WORKSF分区空间使用率警报阈值
WORKSF_INODES_THRESHOLD = 0.85   # WORKSF分区inode使用率警报阈值

# 分区容量配额
SCRATCH_QUOTA_LIMIT = 400 * 2**40    # SCRATCH配额限制 (400TB)
WORKSF_BYTES_LIMIT = 2 * 2**40       # WORKSF空间限制 (2TB)
WORKSF_INODES_LIMIT = 3 * 10**6      # WORKSF inode限制 (3百万)

# 广播配置
BROADCAST_ENABLED = True            # 是否启用终端广播
MESSAGE_LANGUAGE = "zh"             # 消息语言: 'zh' 中文, 'en' 英文
# ===================================================

SLURM_GROUP_NAME = "six"

def get_message(key):
    """根据语言设置获取消息内容"""
    messages = {
        "zh": {
            "alert_title": "【紧急】文件系统即将满载",
            "scratch_full": "SCRATCH空间使用率: {:.2f}% ({:.2f}TB/{:.2f}TB)",
            "worksf_full": "WORKSF空间使用率: {:.2f}% ({:.2f}GB/{:.2f}GB)",
            "inode_full": "{} inode使用率: {:.2f}% ({:.2f}K/{:.2f}K)",
            "shared_full": "共享{}分区仅剩 {:.2f}TB",
            "prompt": "请检查存储使用情况或联系管理员",
            "normal": "所有分区状态正常"
        },
        "en": {
            "alert_title": "【URGENT】File System Approaching Full",
            "scratch_full": "SCRATCH usage: {:.2f}% ({:.2f}TB/{:.2f}TB)",
            "worksf_full": "WORKSF usage: {:.2f}% ({:.2f}GB/{:.2f}GB)",
            "inode_full": "{} inode usage: {:.2f}% ({:.2f}K/{:.2f}K)",
            "shared_full": "Shared {} only has {:.2f}TB left",
            "prompt": "Please check storage usage or contact admin",
            "normal": "All partitions are in good standing"
        }
    }
    return messages[MESSAGE_LANGUAGE][key]

def broadcast_alert(msg):
    """向所有登录用户的终端发送警报消息"""
    if not BROADCAST_ENABLED:
        return
        
    # 在Ubuntu上，wall命令用于广播消息
    broadcast_cmd = [
        "wall",
        "-n",  # 不显示标题
        f"\n\n***** {get_message('alert_title')} *****\n{msg}\n\n{get_message('prompt')}\n"
    ]
    
    try:
        # 需要root权限才能广播
        if os.geteuid() == 0:
            subprocess.run(broadcast_cmd, check=True)
            print("警报已广播至所有终端")
        else:
            print("警报未广播：需要root权限以使用wall命令")
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"广播失败: {e} - 确保wall命令可用")

def check_system_compatibility():
    """检查系统兼容性"""
    # 确认是Linux系统
    if platform.system() != "Linux":
        raise OSError("本脚本仅支持Linux系统")
    
    # 确认是Ubuntu或基于Ubuntu的系统
    try:
        with open("/etc/os-release", "r") as f:
            os_info = f.read()
            if "ubuntu" not in os_info.lower():  # 检查是否为Ubuntu系统
                print("警告：本脚本主要针对Ubuntu系统测试，其他Linux发行版可能不兼容")
    except FileNotFoundError:
        print("警告：无法确定操作系统类型")

def run_cmd(cmd, check=True):
    """执行系统命令并返回输出"""
    try:
        result = subprocess.run(
            cmd,
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
            check=check,
            encoding="utf-8",
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as exc:
        print(f"命令执行失败: {' '.join(cmd)}")
        print(f"错误信息: {exc.stderr}")
        if check:
            raise
        return ""

def get_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--debug", action='store_true', help="启用调试模式")
    parser.add_argument("--no-broadcast", action='store_true', help="禁用终端广播")
    parser.add_argument("--lang", choices=["zh", "en"], default=MESSAGE_LANGUAGE, 
                        help="设置消息语言 (zh: 中文, en: 英文)")
    return parser.parse_args()

def main():
    """主监控逻辑"""
    
    # 系统兼容性检查
    check_system_compatibility()
    
    # 解析命令行参数
    args = get_args()
    
    # 设置全局语言
    global MESSAGE_LANGUAGE
    MESSAGE_LANGUAGE = args.lang
    
    # 设置是否广播
    global BROADCAST_ENABLED
    if args.no_broadcast:
        BROADCAST_ENABLED = False

    alerts = []
    
    def analyse_partition_bytes(partition_name, partition_path, hard_limit_bytes, threshold):
        """分析分区空间使用情况"""
        try:
            # 使用df命令获取更准确的分区使用情况
            cmd = f"df -B1 --output=used {partition_path}"
            response = run_cmd(cmd.split(), check=False)
            
            # 提取使用量（跳过标题行）
            size_bytes = int(response.split('\n')[1])
            
            if args.debug:
                print(f"{partition_name} 空间使用量: {size_bytes/2**40:.2f}TB")
            
            if size_bytes > hard_limit_bytes * threshold:
                current_usage_percent = 100 * size_bytes / hard_limit_bytes
                if partition_name == "SCRATCH":
                    msg = get_message("scratch_full").format(
                        current_usage_percent,
                        size_bytes / 2**40,
                        hard_limit_bytes / 2**40
                    )
                else:
                    msg = get_message("worksf_full").format(
                        current_usage_percent,
                        size_bytes / 2**30,
                        hard_limit_bytes / 2**30
                    )
                alerts.append(msg)
        except (ValueError, IndexError) as e:
            print(f"分析{partition_name}空间时出错: {e}")

    def analyse_partition_inodes(partition_name, partition_path, hard_limit_inodes, threshold):
        """分析分区inode使用情况"""
        try:
            # 使用df命令获取inode使用情况
            cmd = f"df -i --output=iused {partition_path}"
            response = run_cmd(cmd.split(), check=False)
            
            # 提取inode使用量（跳过标题行）
            size_inodes = int(response.split('\n')[1])
            
            if args.debug:
                print(f"{partition_name} Inode使用量: {size_inodes}")
            
            if size_inodes > hard_limit_inodes * threshold:
                current_usage_percent = 100 * size_inodes / hard_limit_inodes
                msg = get_message("inode_full").format(
                    partition_name,
                    current_usage_percent,
                    size_inodes / 1000,
                    hard_limit_inodes / 1000
                )
                alerts.append(msg)
        except (ValueError, IndexError) as e:
            print(f"分析{partition_name} inode时出错: {e}")

    def analyse_shared_disk(partition_name, threshold_bytes):
        """分析共享磁盘空间"""
        try:
            # 获取分区挂载点
            cmd = "df -B1 --output=target,avail"
            response = run_cmd(cmd.split())
            
            # 查找目标分区
            lines = response.splitlines()
            for line in lines[1:]:  # 跳过标题行
                parts = line.split()
                if len(parts) >= 2 and partition_name in parts[0]:
                    available_bytes = int(parts[1])
                    
                    if args.debug:
                        print(f"{partition_name} 可用空间: {available_bytes/2**40:.2f}TB")
                    
                    if available_bytes < threshold_bytes:
                        msg = get_message("shared_full").format(
                            partition_name,
                            available_bytes / 2**40
                        )
                        alerts.append(msg)
                    break
        except (ValueError, IndexError) as e:
            print(f"分析共享磁盘{partition_name}时出错: {e}")

    # ========================= 监控逻辑 =========================
    
    # 监控SCRATCH分区
    analyse_partition_bytes(
        "SCRATCH", 
        "/scratch", 
        SCRATCH_QUOTA_LIMIT, 
        SCRATCH_QUOTA_THRESHOLD
    )
    
    # 监控全局SCRATCH空间
    analyse_shared_disk("/scratch", SCRATCH_GLOBAL_THRESHOLD)
    
    # 监控WORKSF分区
    analyse_partition_bytes(
        "WORKSF", 
        "/worksf", 
        WORKSF_BYTES_LIMIT, 
        WORKSF_BYTES_THRESHOLD
    )
    
    analyse_partition_inodes(
        "WORKSF", 
        "/worksf", 
        WORKSF_INODES_LIMIT, 
        WORKSF_INODES_THRESHOLD
    )
    
    # 监控WORK分区（空间和inode）
    analyse_partition_bytes(
        "WORK", 
        "/work", 
        None,  # 自动检测
        WORK_BYTES_THRESHOLD
    )
    
    analyse_partition_inodes(
        "WORK", 
        "/work", 
        None,  # 自动检测
        WORK_INODES_THRESHOLD
    )
    
    # 监控STORE分区（空间和inode）
    analyse_partition_bytes(
        "STORE", 
        "/store", 
        None,  # 自动检测
        STORE_BYTES_THRESHOLD
    )
    
    analyse_partition_inodes(
        "STORE", 
        "/store", 
        None,  # 自动检测
        STORE_INODES_THRESHOLD
    )
    
    # ==========================================================
    
    if alerts:
        alert_title = get_message("alert_title")
        alert_msg = "\n".join(alerts)
        
        print(alert_title)
        print(alert_msg)
        
        # 发送广播警报
        broadcast_alert(alert_msg)
    else:
        print(get_message("normal"))

if __name__ == "__main__":
    try:
        main()
    except PermissionError:
        print("错误：需要root权限运行此脚本")
        print("请使用: sudo ./fs-watchdog.py")
    except Exception as e:
        print(f"脚本执行出错: {e}")
        sys.exit(1)

# sudo fs-watchdog.py
# 调试模式（不广播）
# sudo ./fs-watchdog.py --debug --no-broadcast
# en
# sudo ./fs-watchdog.py --lang en