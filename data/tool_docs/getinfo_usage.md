# getinfo工具

getinfo 工具使用说明（getinfo.py \+ sop_json_to_md.py）

# **1.文档目标**

本说明用于指导以下两个脚本的使用：

- getinfo.py：采集服务器信息，输出 Excel / SOP JSON / 日志压缩包。

- sop_json_to_md.py：将 getinfo.py 生成的 \*_sop.json 渲染成 Markdown 报告以及word报告，并按规则做对比展示。

# **2.运行前置要求**

## 2.1 Python 依赖安装

项目 requirements.txt 当前包含：paramiko、pandas、openpyxl

在线安装：

pip3 install -r requirements.txt

离线安装（示例）：

pip3 install --no-index --find-links ./offline_packages -r requirements.txt

## 2.2Pandoc依赖安装

在线安装：

生成 Word 需要安装 Pandoc，并确保执行脚本时能找到 pandoc 命令。具体安装方式按部署环境确定。（已按本地 sop_json_to_md.py 核对）

离线安装：

dpkg -i getinfo/offline_packages/pandoc-3.9.0.2-1-amd64.deb

## 2.3 目标服务器建议具备命令

- 常用采集命令：dmidecode、lscpu、lsblk、lspci、nvidia-smi、ethtool、ibdev2netdev、ipmitool、lldpcli

- 部分命令缺失时脚本会尽量降级，不会阻塞全部节点；结果中会反映为空或 N/A。

# **3.输入文件准备**

## 3.1 hostfile（必需）

- 每行一个目标主机（IP）

示例：

192.0.2.1

192.0.2.2

192.0.2.3

192.0.2.4

## 3.2 sop_expectations.json（必需）

- 用于定义验收“期望值规则”（rules），脚本会将采集结果与期望值逐项对比；这些期望参数主要来自report_template.md中约定的验收参数（如 OS/KERNEL/HOSTNAME/ ROOT_DISK/、账号密码、TIME_INFO、GPU/CPU//NIC/磁盘规格等）。

- 规则通常包含 check、expected、description 等字段；部分规则还会包含 accounts、tolerance_minutes、allow_empty 等扩展参数。

- 可通过 --expect-file 指定其他路径

- 示例项目Aexample-b300.json的路径example/example/projects/example-b300.json

- 示例项目Bexample-h100.json的路径example/example/projects/example-h100.json

# getinfo.py 使用说明

## 4.1 常用参数

- --hostfile: hostfile文件路径（默认: \`hostfile\`，会自动从主目录查找）

- --username: SSH用户名（可选；省略时依赖SSH配置或当前用户自动检测，仍需可用的SSH认证；已按本地 getinfo.py 核对）

- --password: SSH密码（可选，如果配置了免密登录或使用密钥，可不提供）

- --key-file: SSH私钥文件路径（可选）

- --timeout: SSH 连接超时秒数，默认 30

- --max-workers: 并发数，默认 32

- --output: 输出Excel文件路径（可选，默认会自动生成带时间戳的文件名）

- --expect-file: 期望值配置，默认 sop_expectations.json（已按本地 getinfo.py 参数定义核对）

## 4.2 标准采集模式命令示例

使用默认hostfile（主目录下的hostfile）:

python3 getinfo.py --username root --hostfile hostfile

指定hostfile路径:

python3 getinfo.py --username root --hostfile /path/to/hostfile

指定输出文件路径：

python3 getinfo.py --username root --hostfile /path/to/hostfile --output test.xlsx

密码登录：

python3 getinfo.py --username root --password 'YourPassword' --hostfile hostfile

密钥登录：

python getinfo.py --username root --key-file /path/to/id_rsa

控制并发数（默认32）：
python3 getinfo.py --username root --hostfile /path/to/hostfile --max-workers 64

## 4.3 getinfo.py 输出结果

标准采集模式默认会生成：

- server_info_YYYYMMDD_HHMMSS.xlsx

- server_info_YYYYMMDD_HHMMSS_sop.json\(默认生成到当前目录下\)

- latest_test_logs_YYYYMMDD_HHMMSS.tar.gz（若采到日志）

# 5.sop_json_to_md.py 使用说明

## 5.1 作用

- 把 \*_sop.json 渲染为 Markdown 验收报告并生成word文档

- 可按期望规则输出“通过/未通过”结果

## 5.2 常用参数

- --json: 必填，getinfo.py 输出的 \*_sop.json（采集后默认生成到当前目录下）

- --template: Markdown 模板（默认 交付验收sop.md）目前已有两个模板见3.2

- --output: 输出 Markdown 路径（默认 \<json文件名\>_report.md）

- --server: 仅渲染指定 host

- --expect: 期望规则文件（默认 sop_expectations.json）

## 5.3 命令示例

基础渲染（默认模板 交付验收sop.md）：

python3 sop_json_to_md.py --json server_info_20260422_120000_sop.json

指定模板和输出word：

例：B300 示例项目：

python3 sop_json_to_md.py \\

--json server_info_20260528_025723_sop.json \\

--expect example/projects/example-b300.json \\

--template example/projects/report_template_B300.md \\

--output test26.md \\

--docx \\

--reference-doc template_docx.docx

H100 示例项目：

`python3 sop_json_to_md.py \`

`--json server_info_20260515_201228_sop.json \`

`--expect example/projects/example-h100.json \`

`--template example/projects/report_template_H100.md \`

`--output test.md \`

`--docx \`

`--reference-doc template_docx.docx`

注意：--json后面的json文件需替换成采集生成的json文件

## 5.4 输出结果

- 默认输出：\<json文件名\>_report.md

- Word 文档：成功执行 --docx 后，在 Markdown 输出文件的同目录生成同名 .docx，例如 test26.md 对应 test26.docx。（已按本地 sop_json_to_md.py 核对）

# 6.故障排查

## 6.1 SSH连接失败

- 检查 hostfile、网络连通、防火墙设置、账号密码或密钥

## **6.2命令执行失败**:

- 确认目标服务器已安装所需命令

- 检查SSH用户权限

## **6.3信息收集不完整**:

- 查看日志输出，找出具体失败的服务器

- 手动SSH到该服务器，执行相关命令检查

## 6.4**Excel文件无法打开**:

- 确保已安装openpyxl库

- 检查文件是否被其他程序占用

##
