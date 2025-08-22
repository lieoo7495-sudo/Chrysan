```python
#!/usr/bin/env python

#
# 文件系统监控工具 - 当磁盘空间或inode接近耗尽时发出警报
#
# 在Ubuntu系统上使用
#
# 示例:
# sudo fs-watchdog.py
#

import argparse
import socket
import subprocess
import sys
import os
import platform
import logging

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

# 分区路径配置（根据实际情况修改）
WORK_PATH = "/work"
STORE_PATH = "/store"
SCRATCH_PATH = "/scratch"
WORKSF_PATH = "/worksf"

# 日志配置
LOG_FILE = "/var/log/fs-watchdog.log"
# ===================================================

def get_message(key):
    """根据语言设置获取消息内容"""
    messages = {
        "zh": {
            "alert_title": "【紧急】文件系统即将满载",
            "scratch_full": "SCRATCH空间使用率: {:.2f}% ({:.2f}TB/{:.2f}TB)",
            "worksf_full": "WORKSF空间使用率: {:.2f}% ({:.2f}GB/{:.2f}GB)",
            "inode_full": "{} inode使用率: {:.2f}% ({:.1f}M/{:.1f}M)",
            "available_full": "{}分区可用空间不足: {:.2f}TB (低于阈值 {:.2f}TB)",
            "prompt": "请检查存储使用情况或联系管理员",
            "normal": "所有分区状态正常"
        },
        "en": {
            "alert_title": "【URGENT】File System Approaching Full",
            "scratch_full": "SCRATCH usage: {:.2f}% ({:.2f}TB/{:.2f}TB)",
            "worksf_full": "WORKSF usage: {:.2f}% ({:.2f}GB/{:.2f}GB)",
            "inode_full": "{} inode usage: {:.2f}% ({:.1f}M/{:.1f}M)",
            "available_full": "{} available space low: {:.2f}TB (below threshold {:.2f}TB)",
            "prompt": "Please check storage usage or contact admin",
            "normal": "All partitions are in good standing"
        }
    }
    return messages[MESSAGE_LANGUAGE][key]

def setup_logging():
    """配置日志系统"""
    logging.basicConfig(
        filename=LOG_FILE,
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(levelname)s: %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)

def broadcast_alert(msg):
    """向所有登录用户的终端发送警报消息"""
    if not BROADCAST_ENABLED:
        return
        
    try:
        # 使用wall命令广播消息
        broadcast_cmd = [
            "wall",
            f"\n\n***** {get_message('alert_title')} *****\n{msg}\n\n{get_message('prompt')}\n"
        ]
        
        # 需要root权限才能广播
        if os.geteuid() == 0:
            result = subprocess.run(
                broadcast_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            if result.returncode == 0:
                logging.info("警报已广播至所有终端")
            else:
                logging.error(f"广播失败: {result.stderr.strip()}")
        else:
            logging.warning("警报未广播：需要root权限以使用wall命令")
    except Exception as e:
        logging.error(f"广播过程中出错: {str(e)}")

def check_system_compatibility():
    """检查系统兼容性"""
    # 确认是Linux系统
    if platform.system() != "Linux":
        raise OSError("本脚本仅支持Linux系统")

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
        error_msg = f"命令执行失败: {' '.join(cmd)}\n错误信息: {exc.stderr.strip()}"
        logging.error(error_msg)
        if check:
            raise
        return ""

def parse_df_output(output):
    """解析df命令输出，返回分区信息的字典列表"""
    lines = output.splitlines()
    if len(lines) < 2:
        logging.warning("df命令输出不足")
        return []
    
    headers = lines[0].split()
    partitions = []
    
    try:
        for line in lines[1:]:
            parts = line.split()
            # 确保有足够的列
            if len(parts) < len(headers):
                continue
                
            partition_info = {}
            for i, header in enumerate(headers):
                partition_info[header] = parts[i]
            partitions.append(partition_info)
    except Exception as e:
        logging.error(f"解析df输出时出错: {str(e)}")
    
    return partitions

def get_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--debug", action='store_true', help="启用调试模式")
    parser.add_argument("--no-broadcast", action='store_true', help="禁用终端广播")
    parser.add_argument("--lang", choices=["zh", "en"], default=MESSAGE_LANGUAGE, 
                        help="设置消息语言 (zh: 中文, en: 英文)")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], 
                        default="INFO", help="设置日志级别")
    return parser.parse_args()

def main():
    """主监控逻辑"""
    setup_logging()
    
    try:
        # 系统兼容性检查
        check_system_compatibility()
        
        # 解析命令行参数
        args = get_args()
        
        # 设置日志级别
        logging.getLogger().setLevel(args.log_level)
        
        # 设置全局语言
        global MESSAGE_LANGUAGE
        MESSAGE_LANGUAGE = args.lang
        
        # 设置是否广播
        global BROADCAST_ENABLED
        if args.no_broadcast:
            BROADCAST_ENABLED = False

        alerts = []
        
        def get_partition_usage(mount_point):
            """获取指定挂载点的使用情况"""
            cmd = ["df", "-B1", "-P", mount_point]
            response = run_cmd(cmd, check=False)
            
            partitions = parse_df_output(response)
            if not partitions:
                logging.warning(f"无法获取分区 {mount_point} 的使用情况")
                return None, None, None
                
            partition = partitions[0]
            try:
                size_bytes = int(partition["1K-blocks"]) * 1024
                used_bytes = int(partition["Used"]) * 1024
                avail_bytes = int(partition["Available"])
                return size_bytes, used_bytes, avail_bytes
            except (ValueError, KeyError) as e:
                logging.error(f"解析分区 {mount_point} 数据时出错: {str(e)}")
                return None, None, None
        
        def get_partition_inodes(mount_point):
            """获取指定挂载点的inode使用情况"""
            cmd = ["df", "-i", "-P", mount_point]
            response = run_cmd(cmd, check=False)
            
            partitions = parse_df_output(response)
            if not partitions:
                logging.warning(f"无法获取分区 {mount_point} 的inode使用情况")
                return None, None
                
            partition = partitions[0]
            try:
                total_inodes = int(partition["Inodes"])
                used_inodes = int(partition["IUsed"])
                return total_inodes, used_inodes
            except (ValueError, KeyError) as e:
                logging.error(f"解析分区 {mount_point} inode数据时出错: {str(e)}")
                return None, None
        
        def check_partition_bytes(partition_name, mount_point, hard_limit_bytes, threshold):
            """检查分区空间使用情况"""
            logging.debug(f"检查 {partition_name} 空间使用情况...")
            size_bytes, used_bytes, _ = get_partition_usage(mount_point)
            
            if size_bytes is None or used_bytes is None:
                return
                
            # 如果未提供硬限制，使用实际分区大小
            effective_limit = hard_limit_bytes if hard_limit_bytes is not None else size_bytes
            current_usage_percent = 100 * used_bytes / effective_limit
            
            if logging.getLogger().isEnabledFor(logging.DEBUG):
                logging.debug(f"{partition_name} 空间使用: {used_bytes/2**30:.2f}GB/{effective_limit/2**30:.2f}GB ({current_usage_percent:.2f}%)")
            
            if current_usage_percent/100 > threshold:
                if partition_name == "SCRATCH":
                    msg = get_message("scratch_full").format(
                        current_usage_percent,
                        used_bytes / 2**40,
                        effective_limit / 2**40
                    )
                else:
                    msg = get_message("worksf_full").format(
                        current_usage_percent,
                        used_bytes / 2**30,
                        effective_limit / 2**30
                    )
                alerts.append(msg)

        def check_partition_inodes(partition_name, mount_point, hard_limit_inodes, threshold):
            """检查分区inode使用情况"""
            logging.debug(f"检查 {partition_name} inode使用情况...")
            total_inodes, used_inodes = get_partition_inodes(mount_point)
            
            if total_inodes is None or used_inodes is None:
                return
                
            # 如果未提供硬限制，使用实际总inode数
            effective_limit = hard_limit_inodes if hard_limit_inodes is not None else total_inodes
            current_usage_percent = 100 * used_inodes / effective_limit
            
            if logging.getLogger().isEnabledFor(logging.DEBUG):
                logging.debug(f"{partition_name} inode使用: {used_inodes/1e6:.2f}M/{effective_limit/1e6:.2f}M ({current_usage_percent:.2f}%)")
            
            if current_usage_percent/100 > threshold:
                msg = get_message("inode_full").format(
                    partition_name,
                    current_usage_percent,
                    used_inodes / 1e6,
                    effective_limit / 1e6
                )
                alerts.append(msg)

        def check_available_space(partition_name, mount_point, threshold_bytes):
            """检查分区可用空间"""
            logging.debug(f"检查 {partition_name} 可用空间...")
            _, _, avail_bytes = get_partition_usage(mount_point)
            
            if avail_bytes is None:
                return
                
            if logging.getLogger().isEnabledFor(logging.DEBUG):
                logging.debug(f"{partition_name} 可用空间: {avail_bytes/2**40:.2f}TB")
            
            if avail_bytes < threshold_bytes:
                msg = get_message("available_full").format(
                    partition_name,
                    avail_bytes / 2**40,
                    threshold_bytes / 2**40
                )
                alerts.append(msg)

        # ========================= 监控逻辑 =========================
        
        # 监控WORK分区
        check_partition_bytes("WORK", WORK_PATH, None, WORK_BYTES_THRESHOLD)
        check_partition_inodes("WORK", WORK_PATH, None, WORK_INODES_THRESHOLD)
        
        # 监控STORE分区
        check_partition_bytes("STORE", STORE_PATH, None, STORE_BYTES_THRESHOLD)
        check_partition_inodes("STORE", STORE_PATH, None, STORE_INODES_THRESHOLD)
        
        # 监控SCRATCH分区
        check_partition_bytes("SCRATCH", SCRATCH_PATH, SCRATCH_QUOTA_LIMIT, SCRATCH_QUOTA_THRESHOLD)
        check_available_space("SCRATCH", SCRATCH_PATH, SCRATCH_GLOBAL_THRESHOLD)
        
        # 监控WORKSF分区
        check_partition_bytes("WORKSF", WORKSF_PATH, WORKSF_BYTES_LIMIT, WORKSF_BYTES_THRESHOLD)
        check_partition_inodes("WORKSF", WORKSF_PATH, WORKSF_INODES_LIMIT, WORKSF_INODES_THRESHOLD)
        
        # ==========================================================
        
        if alerts:
            alert_title = get_message("alert_title")
            alert_msg = "\n".join(alerts)
            
            logging.warning(alert_title)
            logging.warning(alert_msg)
            
            # 发送广播警报
            broadcast_alert(alert_msg)
            sys.exit(1)  # 退出状态码1表示有警报
        else:
            msg = get_message("normal")
            logging.info(msg)
            print(msg)
            sys.exit(0)  # 退出状态码0表示一切正常

    except PermissionError:
        error_msg = "错误：需要root权限运行此脚本\n请使用: sudo ./fs-watchdog.py"
        logging.error(error_msg)
        print(error_msg)
        sys.exit(1)
    except Exception as e:
        error_msg = f"脚本执行出错: {str(e)}"
        logging.exception(error_msg)
        print(error_msg)
        sys.exit(1)

if __name__ == "__main__":
    main()

sudo chmod +x fs-watchdog.py
sudo ./fs-watchdog.py

sudo ./fs-watchdog.py --debug --log-level DEBUG

sudo crontab -e
*/15 * * * * /path/to/fs-watchdog.py

```

```python
#!/usr/bin/env python

#
# 文件系统监控工具 - 当磁盘空间或inode接近耗尽时发出警报
#
# 在Ubuntu系统上使用
#
# 示例:
# sudo fs-watchdog.py
#

import argparse
import socket
import subprocess
import sys
import os
import platform
import logging
import re

# ===================== 配置区域 =====================
# 分区监控阈值配置
WORK_BYTES_THRESHOLD = 0.85      # WORK分区空间使用率警报阈值
WORK_INODES_THRESHOLD = 0.85     # WORK分区inode使用率警报阈值

STORE_BYTES_THRESHOLD = 0.85     # STORE分区空间使用率警报阈值
STORE_INODES_THRESHOLD = 0.85    # STORE分区inode使用率警报阈值

SCRATCH_QUOTA_THRESHOLD = 0.75   # SCRATCH分区配额使用率警报阈值
SCRATCH_GLOBAL_THRESHOLD = 100   # SCRATCH全局空间剩余警报阈值(100TB)

WORKSF_BYTES_THRESHOLD = 0.85    # WORKSF分区空间使用率警报阈值
WORKSF_INODES_THRESHOLD = 0.85   # WORKSF分区inode使用率警报阈值

# 分区容量配额
SCRATCH_QUOTA_LIMIT = 400        # SCRATCH配额限制 (400TB)
WORKSF_BYTES_LIMIT = 2           # WORKSF空间限制 (2TB)
WORKSF_INODES_LIMIT = 3          # WORKSF inode限制 (3百万)

# 广播配置
BROADCAST_ENABLED = True         # 是否启用终端广播
MESSAGE_LANGUAGE = "zh"          # 消息语言: 'zh' 中文, 'en' 英文

# 分区路径配置（根据实际情况修改）
WORK_PATH = "/work"
STORE_PATH = "/store"
SCRATCH_PATH = "/scratch"
WORKSF_PATH = "/worksf"

# 日志配置
LOG_FILE = "/var/log/fs-watchdog.log"
# ===================================================

def get_message(key):
    """根据语言设置获取消息内容"""
    messages = {
        "zh": {
            "alert_title": "【紧急】文件系统即将满载",
            "usage_full": "{}空间使用率: {:.2f}% ({}/{})",
            "inode_full": "{} inode使用率: {:.2f}% ({}/{})",
            "available_full": "{}分区可用空间不足: {} (低于阈值 {})",
            "prompt": "请检查存储使用情况或联系管理员",
            "normal": "所有分区状态正常"
        },
        "en": {
            "alert_title": "【URGENT】File System Approaching Full",
            "usage_full": "{} usage: {:.2f}% ({}/{})",
            "inode_full": "{} inode usage: {:.2f}% ({}/{})",
            "available_full": "{} available space low: {} (below threshold {})",
            "prompt": "Please check storage usage or contact admin",
            "normal": "All partitions are in good standing"
        }
    }
    return messages[MESSAGE_LANGUAGE][key]

def setup_logging(log_level=logging.INFO):
    """配置日志系统"""
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # 文件日志
    file_handler = logging.FileHandler(LOG_FILE)
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # 控制台日志
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

def broadcast_alert(msg):
    """向所有登录用户的终端发送警报消息"""
    if not BROADCAST_ENABLED:
        return
        
    try:
        # 使用wall命令广播消息
        broadcast_cmd = [
            "wall",
            f"\n\n***** {get_message('alert_title')} *****\n{msg}\n\n{get_message('prompt')}\n"
        ]
        
        # 需要root权限才能广播
        if os.geteuid() == 0:
            result = subprocess.run(
                broadcast_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            if result.returncode == 0:
                logging.info("警报已广播至所有终端")
            else:
                logging.error(f"广播失败: {result.stderr.strip()}")
        else:
            logging.warning("警报未广播：需要root权限以使用wall命令")
    except Exception as e:
        logging.error(f"广播过程中出错: {str(e)}")

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
        error_msg = f"命令执行失败: {' '.join(cmd)}\n错误信息: {exc.stderr.strip()}"
        logging.error(error_msg)
        if check:
            raise
        return ""
    except Exception as e:
        logging.error(f"命令执行异常: {str(e)}")
        return ""

def parse_human_size(size_str):
    """将人类可读的大小字符串转换为字节数"""
    # 示例: "100G" -> 100 * 1024^3
    # 支持的单位: K, M, G, T
    units = {"K": 1024, "M": 1024**2, "G": 1024**3, "T": 1024**4}
    
    # 尝试提取数字和单位
    match = re.match(r"(\d+(?:\.\d+)?)\s*([KMGTP]?)(i?B)?", size_str, re.IGNORECASE)
    if not match:
        return None
        
    value = float(match.group(1))
    unit = match.group(2).upper() if match.group(2) else ""
    
    if unit in units:
        return value * units[unit]
    return value * 1024  # 默认按KB处理

def get_df_output():
    """获取df -hT命令的输出并解析"""
    cmd = ["df", "-hT"]
    output = run_cmd(cmd, check=False)
    
    # 解析df输出
    lines = output.splitlines()
    if len(lines) < 2:
        logging.error("df命令返回的输出不足")
        return []
    
    # 解析标题行
    headers = re.split(r"\s+", lines[0])
    filesystems = []
    
    for line in lines[1:]:
        parts = re.split(r"\s+", line)
        if len(parts) < len(headers):
            continue
            
        filesystem = {
            "filesystem": parts[0],
            "type": parts[1],
            "size": parts[2],
            "used": parts[3],
            "available": parts[4],
            "use_percent": parts[5],
            "mounted_on": " ".join(parts[6:])  # 处理可能包含空格的挂载点
        }
        filesystems.append(filesystem)
    
    return filesystems

def get_mount_point_info(mount_point):
    """获取指定挂载点的信息"""
    df_output = get_df_output()
    if not df_output:
        return None
        
    # 查找匹配的挂载点
    for fs in df_output:
        if fs["mounted_on"] == mount_point:
            return fs
            
    logging.warning(f"未找到挂载点: {mount_point}")
    return None

def get_partition_usage(mount_point):
    """获取指定挂载点的使用情况"""
    info = get_mount_point_info(mount_point)
    if not info:
        return None, None, None
        
    try:
        # 转换大小
        size_bytes = parse_human_size(info["size"])
        used_bytes = parse_human_size(info["used"])
        available_bytes = parse_human_size(info["available"])
        
        # 解析百分比
        use_percent = float(info["use_percent"].strip('%'))
        
        # 验证数据一致性
        if size_bytes and used_bytes and available_bytes:
            calculated_percent = (used_bytes / (used_bytes + available_bytes)) * 100
            if abs(calculated_percent - use_percent) > 5:  # 允许5%的误差
                logging.warning(f"使用率不一致: 报告值={use_percent}%, 计算值={calculated_percent:.2f}%")
        
        return size_bytes, used_bytes, available_bytes
        
    except Exception as e:
        logging.error(f"解析挂载点 {mount_point} 使用情况失败: {str(e)}")
        return None, None, None

def get_partition_inodes(mount_point):
    """获取指定挂载点的inode使用情况"""
    cmd = ["df", "-i", mount_point]
    output = run_cmd(cmd, check=False)
    
    # 解析df -i输出
    lines = output.splitlines()
    if len(lines) < 2:
        logging.warning(f"无法获取分区 {mount_point} 的inode使用情况")
        return None, None
        
    # 第二行是数据行
    parts = re.split(r"\s+", lines[1])
    if len(parts) < 6:
        logging.warning(f"解析分区 {mount_point} inode数据失败")
        return None, None
        
    try:
        total_inodes = int(parts[1])
        used_inodes = int(parts[2])
        return total_inodes, used_inodes
    except (ValueError, IndexError) as e:
        logging.error(f"解析inode数据出错: {str(e)}")
        return None, None

def get_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--debug", action='store_true', help="启用调试模式")
    parser.add_argument("--no-broadcast", action='store_true', help="禁用终端广播")
    parser.add_argument("--lang", choices=["zh", "en"], default=MESSAGE_LANGUAGE, 
                        help="设置消息语言 (zh: 中文, en: 英文)")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], 
                        default="INFO", help="设置日志级别")
    return parser.parse_args()

def main():
    """主监控逻辑"""
    try:
        # 解析命令行参数
        args = get_args()
        
        # 配置日志
        log_level = getattr(logging, args.log_level.upper())
        setup_logging(log_level)
        
        # 设置全局语言
        global MESSAGE_LANGUAGE
        MESSAGE_LANGUAGE = args.lang
        
        # 设置是否广播
        global BROADCAST_ENABLED
        if args.no_broadcast:
            BROADCAST_ENABLED = False

        alerts = []
        
        def check_partition_bytes(partition_name, mount_point, hard_limit, threshold):
            """检查分区空间使用情况"""
            logging.debug(f"检查 {partition_name} 空间使用情况...")
            size_bytes, used_bytes, avail_bytes = get_partition_usage(mount_point)
            
            if size_bytes is None or used_bytes is None:
                logging.warning(f"无法获取 {partition_name} 分区空间使用数据")
                return
                
            # 如果未提供硬限制，使用实际分区大小
            effective_limit = parse_human_size(f"{hard_limit}T") if hard_limit else size_bytes
            
            if effective_limit is None:
                logging.warning(f"无法确定 {partition_name} 分区的有效限制")
                return
                
            current_usage_percent = 100 * used_bytes / effective_limit
            
            if logging.getLogger().isEnabledFor(logging.DEBUG):
                logging.debug(f"{partition_name} 空间使用: {used_bytes/1024**3:.2f}GB/{effective_limit/1024**3:.2f}GB ({current_usage_percent:.2f}%)")
            
            if current_usage_percent > threshold * 100:
                # 使用人类可读格式显示
                size_human = f"{size_bytes/1024**3:.2f}GB" if size_bytes < 1024**4 else f"{size_bytes/1024**4:.2f}TB"
                used_human = f"{used_bytes/1024**3:.2f}GB" if used_bytes < 1024**4 else f"{used_bytes/1024**4:.2f}TB"
                limit_human = f"{effective_limit/1024**3:.2f}GB" if effective_limit < 1024**4 else f"{effective_limit/1024**4:.2f}TB"
                
                msg = get_message("usage_full").format(
                    partition_name,
                    current_usage_percent,
                    used_human,
                    limit_human
                )
                alerts.append(msg)

        def check_partition_inodes(partition_name, mount_point, hard_limit, threshold):
            """检查分区inode使用情况"""
            logging.debug(f"检查 {partition_name} inode使用情况...")
            total_inodes, used_inodes = get_partition_inodes(mount_point)
            
            if total_inodes is None or used_inodes is None:
                logging.warning(f"无法获取 {partition_name} 分区inode使用数据")
                return
                
            # 如果未提供硬限制，使用实际总数
            effective_limit = hard_limit * 10**6 if hard_limit else total_inodes
            
            current_usage_percent = 100 * used_inodes / effective_limit
            
            if logging.getLogger().isEnabledFor(logging.DEBUG):
                logging.debug(f"{partition_name} inode使用: {used_inodes/1000:.2f}K/{effective_limit/1000:.2f}K ({current_usage_percent:.2f}%)")
            
            if current_usage_percent > threshold * 100:
                # 使用人类可读格式显示
                used_human = f"{used_inodes/1000000:.2f}M"
                limit_human = f"{effective_limit/1000000:.2f}M"
                
                msg = get_message("inode_full").format(
                    partition_name,
                    current_usage_percent,
                    used_human,
                    limit_human
                )
                alerts.append(msg)

        def check_available_space(partition_name, mount_point, threshold):
            """检查分区可用空间"""
            logging.debug(f"检查 {partition_name} 可用空间...")
            _, _, avail_bytes = get_partition_usage(mount_point)
            
            if avail_bytes is None:
                logging.warning(f"无法获取 {partition_name} 分区可用空间数据")
                return
                
            # 转换为TB
            avail_tb = avail_bytes / (1024**4)
            
            if logging.getLogger().isEnabledFor(logging.DEBUG):
                logging.debug(f"{partition_name} 可用空间: {avail_tb:.2f}TB")
            
            if avail_tb < threshold:
                threshold_human = f"{threshold}TB"
                avaliable_human = f"{avail_tb:.2f}TB"
                
                msg = get_message("available_full").format(
                    partition_name,
                    avaliable_human,
                    threshold_human
                )
                alerts.append(msg)

        # ========================= 监控逻辑 =========================
        
        # 监控WORK分区
        check_partition_bytes("WORK", WORK_PATH, None, WORK_BYTES_THRESHOLD)
        check_partition_inodes("WORK", WORK_PATH, None, WORK_INODES_THRESHOLD)
        
        # 监控STORE分区
        check_partition_bytes("STORE", STORE_PATH, None, STORE_BYTES_THRESHOLD)
        check_partition_inodes("STORE", STORE_PATH, None, STORE_INODES_THRESHOLD)
        
        # 监控SCRATCH分区
        check_partition_bytes("SCRATCH", SCRATCH_PATH, SCRATCH_QUOTA_LIMIT, SCRATCH_QUOTA_THRESHOLD)
        check_available_space("SCRATCH", SCRATCH_PATH, SCRATCH_GLOBAL_THRESHOLD)
        
        # 监控WORKSF分区
        check_partition_bytes("WORKSF", WORKSF_PATH, WORKSF_BYTES_LIMIT, WORKSF_BYTES_THRESHOLD)
        check_partition_inodes("WORKSF", WORKSF_PATH, WORKSF_INODES_LIMIT, WORKSF_INODES_THRESHOLD)
        
        # ==========================================================
        
        if alerts:
            alert_title = get_message("alert_title")
            alert_msg = "\n".join(alerts)
            
            logging.warning(alert_title)
            logging.warning(alert_msg)
            
            # 发送广播警报
            broadcast_alert(alert_msg)
            sys.exit(1)  # 退出状态码1表示有警报
        else:
            msg = get_message("normal")
            logging.info(msg)
            print(msg)
            sys.exit(0)  # 退出状态码0表示一切正常

    except PermissionError:
        error_msg = "错误：需要root权限运行此脚本\n请使用: sudo ./fs-watchdog.py"
        logging.error(error_msg)
        print(error_msg)
        sys.exit(1)
    except Exception as e:
        error_msg = f"脚本执行出错: {str(e)}"
        logging.exception(error_msg)
        print(error_msg)
        sys.exit(1)

if __name__ == "__main__":
    main()
```

```python
#!/usr/bin/env python

#
# 通用文件系统监控工具 - 自动检测所有文件系统
#
# 当磁盘空间或inode接近耗尽时发出警报
#
# 在Linux系统上使用
#
# 示例:
# sudo fs-watchdog.py
#

import argparse
import subprocess
import sys
import os
import re
import logging
import json
import platform

# ===================== 配置区域 =====================
# 默认监控阈值
DEFAULT_SPACE_THRESHOLD = 0.90      # 默认空间使用率警报阈值 (90%)
DEFAULT_INODE_THRESHOLD = 0.90      # 默认inode使用率警报阈值 (90%)
DEFAULT_AVAILABLE_THRESHOLD = 10    # 默认可用空间警报阈值 (10GB)

# 特殊分区阈值配置 (可覆盖默认阈值)
THRESHOLD_OVERRIDES = {
    # 格式: 挂载点: {"space": 阈值, "inode": 阈值, "available": 阈值(GB)}
    "/": {"space": 0.90, "inode": 0.90, "available": 5},
    "/boot": {"space": 0.85, "inode": 0.85, "available": 0.1},
    "/var": {"space": 0.85, "inode": 0.90, "available": 5},
    "/home": {"space": 0.95, "inode": 0.95, "available": 5},
    # 添加其他特殊分区配置
}

# 排除的伪文件系统类型
EXCLUDED_FS_TYPES = [
    "tmpfs", "devtmpfs", "devpts", "proc", "sysfs",
    "cgroup", "cgroup2", "overlay", "autofs", "mqueue",
    "debugfs", "tracefs", "configfs", "fusectl", "securityfs",
    "pstore", "efivarfs", "hugetlbfs", "binfmt_misc"
]

# 广播配置
BROADCAST_ENABLED = True            # 是否启用终端广播
MESSAGE_LANGUAGE = "zh"             # 消息语言: 'zh' 中文, 'en' 英文

# 日志配置
LOG_FILE = "/var/log/fs-watchdog.log"
# ===================================================

def get_message(key):
    """根据语言设置获取消息内容"""
    messages = {
        "zh": {
            "alert_title": "【紧急】文件系统即将满载",
            "usage_full": "{}空间使用率: {:.1f}% ({}/{})",
            "inode_full": "{} inode使用率: {:.1f}% ({}/{})",
            "available_full": "{}可用空间不足: {} (低于阈值 {})",
            "prompt": "请检查存储使用情况或联系管理员",
            "normal": "所有文件系统状态正常",
            "partition_header": "正在监控 {} 文件系统"
        },
        "en": {
            "alert_title": "【URGENT】File System Approaching Full",
            "usage_full": "{} usage: {:.1f}% ({}/{})",
            "inode_full": "{} inode usage: {:.1f}% ({}/{})",
            "available_full": "{} available space low: {} (below threshold {})",
            "prompt": "Please check storage usage or contact admin",
            "normal": "All file systems are in good standing",
            "partition_header": "Monitoring {} file system"
        }
    }
    return messages[MESSAGE_LANGUAGE][key]

def setup_logging(log_level=logging.INFO):
    """配置日志系统"""
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # 文件日志
    file_handler = logging.FileHandler(LOG_FILE)
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # 控制台日志
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

def broadcast_alert(msg):
    """向所有登录用户的终端发送警报消息"""
    if not BROADCAST_ENABLED:
        return
        
    try:
        # 使用wall命令广播消息
        broadcast_cmd = [
            "wall",
            f"\n\n***** {get_message('alert_title')} *****\n{msg}\n\n{get_message('prompt')}\n"
        ]
        
        # 需要root权限才能广播
        if os.geteuid() == 0:
            result = subprocess.run(
                broadcast_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            if result.returncode == 0:
                logging.info("警报已广播至所有终端")
            else:
                logging.error(f"广播失败: {result.stderr.strip()}")
        else:
            logging.warning("警报未广播：需要root权限以使用wall命令")
    except Exception as e:
        logging.error(f"广播过程中出错: {str(e)}")

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
        error_msg = f"命令执行失败: {' '.join(cmd)}\n错误信息: {exc.stderr.strip()}"
        logging.error(error_msg)
        if check:
            raise
        return ""
    except Exception as e:
        logging.error(f"命令执行异常: {str(e)}")
        return ""

def parse_human_size(size_str):
    """将人类可读的大小字符串转换为字节数"""
    # 示例: "100G" -> 100 * 1024^3
    # 支持的单位: K, M, G, T
    units = {"K": 1024, "M": 1024**2, "G": 1024**3, "T": 1024**4}
    
    # 尝试提取数字和单位
    match = re.match(r"(\d+(?:\.\d+)?)\s*([KMGTP]?)(i?B)?", size_str, re.IGNORECASE)
    if not match:
        return None
        
    value = float(match.group(1))
    unit = match.group(2).upper() if match.group(2) else ""
    
    if unit in units:
        return value * units[unit]
    return value * 1024  # 默认按KB处理

def get_file_systems():
    """获取所有文件系统的信息"""
    # 获取所有文件系统的df输出
    cmd = ["df", "-hT", "--output=source,fstype,size,used,avail,pcent,target"]
    output = run_cmd(cmd, check=False)
    
    # 解析df输出
    lines = output.splitlines()
    if len(lines) < 2:
        logging.error("df命令返回的输出不足")
        return []
    
    # 解析标题行
    headers = ["filesystem", "fstype", "size", "used", "avail", "use%", "mounted_on"]
    file_systems = []
    
    for line in lines[1:]:
        # 分割行并确保有足够的列
        parts = re.split(r"\s+", line.strip(), maxsplit=len(headers)-1)
        if len(parts) != len(headers):
            continue
            
        fs_info = dict(zip(headers, parts))
        
        # 转换百分比值为浮点数
        if fs_info["use%"].endswith('%'):
            fs_info["use%"] = float(fs_info["use%"][:-1])
        else:
            fs_info["use%"] = float(fs_info["use%"])
        
        file_systems.append(fs_info)
    
    return file_systems

def get_inode_usage(mount_point):
    """获取指定挂载点的inode使用情况"""
    cmd = ["df", "-i", "-P", mount_point]
    output = run_cmd(cmd, check=False)
    
    # 解析df -i输出
    lines = output.splitlines()
    if len(lines) < 2:
        logging.warning(f"无法获取分区 {mount_point} 的inode使用情况")
        return None, None, None
        
    # 第二行是数据行
    headers = lines[0].split()
    data = lines[1].split()
    
    if len(data) < len(headers):
        return None, None, None
        
    try:
        fs_info = dict(zip(headers, data))
        total_inodes = int(fs_info["Inodes"])
        used_inodes = int(fs_info["IUsed"])
        use_percent = float(fs_info["IUse%"].rstrip('%'))
        return total_inodes, used_inodes, use_percent
    except (ValueError, KeyError) as e:
        logging.error(f"解析inode数据出错: {str(e)}")
        return None, None, None

def get_threshold_config(mount_point):
    """获取指定挂载点的阈值配置"""
    # 检查是否有特殊配置
    if mount_point in THRESHOLD_OVERRIDES:
        return {
            "space": THRESHOLD_OVERRIDES[mount_point].get("space", DEFAULT_SPACE_THRESHOLD),
            "inode": THRESHOLD_OVERRIDES[mount_point].get("inode", DEFAULT_INODE_THRESHOLD),
            "available": THRESHOLD_OVERRIDES[mount_point].get("available", DEFAULT_AVAILABLE_THRESHOLD)
        }
    
    # 返回默认配置
    return {
        "space": DEFAULT_SPACE_THRESHOLD,
        "inode": DEFAULT_INODE_THRESHOLD,
        "available": DEFAULT_AVAILABLE_THRESHOLD
    }

def format_size(size_bytes):
    """格式化大小为人类可读字符串"""
    units = ['B', 'K', 'M', 'G', 'T', 'P']
    unit_index = 0
    size = size_bytes
    
    while size >= 1024 and unit_index < len(units)-1:
        size /= 1024
        unit_index += 1
    
    return f"{size:.2f}{units[unit_index]}"

def format_inodes(inode_count):
    """格式化inode数量为人类可读字符串"""
    if inode_count >= 1_000_000:
        return f"{inode_count/1_000_000:.2f}M"
    if inode_count >= 1_000:
        return f"{inode_count/1_000:.2f}K"
    return f"{inode_count}"

def get_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--debug", action='store_true', help="启用调试模式")
    parser.add_argument("--no-broadcast", action='store_true', help="禁用终端广播")
    parser.add_argument("--lang", choices=["zh", "en"], default=MESSAGE_LANGUAGE, 
                        help="设置消息语言 (zh: 中文, en: 英文)")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], 
                        default="INFO", help="设置日志级别")
    parser.add_argument("--dump-config", action='store_true', 
                        help="显示当前配置并退出")
    return parser.parse_args()

def main():
    """主监控逻辑"""
    try:
        # 解析命令行参数
        args = get_args()
        
        # 配置日志
        log_level = logging.DEBUG if args.debug else getattr(logging, args.log_level.upper())
        setup_logging(log_level)
        
        # 设置全局语言
        global MESSAGE_LANGUAGE
        MESSAGE_LANGUAGE = args.lang
        
        # 设置是否广播
        global BROADCAST_ENABLED
        if args.no_broadcast:
            BROADCAST_ENABLED = False
            
        # 如果请求显示配置，则打印配置并退出
        if args.dump_config:
            print("当前文件系统监控配置:")
            print(f"默认空间阈值: {DEFAULT_SPACE_THRESHOLD*100:.1f}%")
            print(f"默认inode阈值: {DEFAULT_INODE_THRESHOLD*100:.1f}%")
            print(f"默认可用空间阈值: {DEFAULT_AVAILABLE_THRESHOLD}GB")
            print("\n特殊分区配置:")
            for mount_point, config in THRESHOLD_OVERRIDES.items():
                print(f"  {mount_point}:")
                print(f"    空间阈值: {config.get('space', DEFAULT_SPACE_THRESHOLD)*100:.1f}%")
                print(f"    inode阈值: {config.get('inode', DEFAULT_INODE_THRESHOLD)*100:.1f}%")
                print(f"    可用空间阈值: {config.get('available', DEFAULT_AVAILABLE_THRESHOLD)}GB")
            sys.exit(0)

        # 获取所有文件系统
        file_systems = get_file_systems()
        if not file_systems:
            logging.error("未找到任何文件系统")
            sys.exit(1)
            
        logging.info(f"发现 {len(file_systems)} 个文件系统")
        alerts = []
        
        for fs in file_systems:
            mount_point = fs["mounted_on"]
            fs_type = fs["fstype"]
            
            # 跳过伪文件系统
            if fs_type in EXCLUDED_FS_TYPES:
                logging.debug(f"跳过伪文件系统: {mount_point} ({fs_type})")
                continue
                
            # 跳过特殊挂载点
            if mount_point.startswith(("/run", "/sys", "/proc", "/dev")):
                logging.debug(f"跳过系统挂载点: {mount_point}")
                continue
                
            logging.info(get_message("partition_header").format(mount_point))
            
            # 获取阈值配置
            config = get_threshold_config(mount_point)
            
            # 解析空间信息
            try:
                size_bytes = parse_human_size(fs["size"])
                used_bytes = parse_human_size(fs["used"])
                avail_bytes = parse_human_size(fs["avail"])
                
                # 计算空间使用率
                if size_bytes and used_bytes:
                    space_usage_percent = (used_bytes / size_bytes) * 100
                else:
                    space_usage_percent = fs["use%"]
                
                # 检查空间使用率
                if space_usage_percent > config["space"] * 100:
                    msg = get_message("usage_full").format(
                        mount_point,
                        space_usage_percent,
                        format_size(used_bytes),
                        format_size(size_bytes)
                    )
                    alerts.append(msg)
                
                # 检查可用空间
                if avail_bytes < config["available"] * (1024**3):  # 转换为字节
                    msg = get_message("available_full").format(
                        mount_point,
                        format_size(avail_bytes),
                        f"{config['available']}GB"
                    )
                    alerts.append(msg)
                
                # 获取inode使用情况
                total_inodes, used_inodes, inode_usage_percent = get_inode_usage(mount_point)
                
                if inode_usage_percent is not None and inode_usage_percent > config["inode"] * 100:
                    msg = get_message("inode_full").format(
                        mount_point,
                        inode_usage_percent,
                        format_inodes(used_inodes),
                        format_inodes(total_inodes)
                    )
                    alerts.append(msg)
                
                # 调试信息
                if logging.getLogger().isEnabledFor(logging.DEBUG):
                    debug_info = [
                        f"挂载点: {mount_point}",
                        f"类型: {fs_type}",
                        f"空间: {format_size(size_bytes)} 已用: {format_size(used_bytes)} "
                        f"可用: {format_size(avail_bytes)} 使用率: {space_usage_percent:.1f}%",
                    ]
                    
                    if inode_usage_percent is not None:
                        debug_info.append(f"inode: 总数: {format_inodes(total_inodes)} "
                                         f"已用: {format_inodes(used_inodes)} "
                                         f"使用率: {inode_usage_percent:.1f}%")
                    
                    debug_info.append(f"阈值: 空间={config['space']*100:.1f}% "
                                    f"inode={config['inode']*100:.1f}% "
                                    f"可用空间={config['available']}GB")
                    
                    logging.debug("\n  ".join(debug_info))
                    
            except Exception as e:
                logging.error(f"处理挂载点 {mount_point} 时出错: {str(e)}")
                continue
        
        # 处理报警
        if alerts:
            alert_title = get_message("alert_title")
            alert_msg = "\n".join(alerts)
            
            logging.warning(alert_title)
            logging.warning(alert_msg)
            
            # 发送广播警报
            broadcast_alert(alert_msg)
            sys.exit(1)  # 退出状态码1表示有警报
        else:
            msg = get_message("normal")
            logging.info(msg)
            print(msg)
            sys.exit(0)  # 退出状态码0表示一切正常

    except PermissionError:
        error_msg = "错误：需要root权限运行此脚本\n请使用: sudo ./fs-watchdog.py"
        logging.error(error_msg)
        print(error_msg)
        sys.exit(1)
    except Exception as e:
        error_msg = f"脚本执行出错: {str(e)}"
        logging.exception(error_msg)
        print(error_msg)
        sys.exit(1)

if __name__ == "__main__":
    main()
```