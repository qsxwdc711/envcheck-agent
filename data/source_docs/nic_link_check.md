# 线序检查工具

### **1\. 前置条件**

- ib环境：

在CPU上执行命令，需要参数`--hostfile PATH和--switch-pod-size 32`（输出hostfile中有问题的机器）

在GPU上执行命令，不需参数hostfile，需要参数`--switch-pod-size 32`（输出全网有问题的机器）

- roce环境

在CPU上执行命令，需要参数`--hostfile PATH、--switch-leaf-list PATH`和`--switch-base-manage-ip IP和--switch-pod-size 32`

- 配置文件

配置文件config\.yaml需要和线序检查工具放在同一目录下，网卡名和交换机名需要根据真实情况修改

```YAML
#config.yaml
roce:
  nic_name_patterns:
    dual:   "^eth_p([01])_rail([0-7])$"
    single: "^eth_rail([0-7])$"

ib:
  # 网卡名合规校验：
  nic_name_pattern: "^mlx5_([0-7])$"

  # leaf 交换机名匹配
  leaf_switch_pattern: "^(.*leaf)([0-9]+)$"

```

### **2\. 常用参数**

- 通过入口脚本区分网络类型：RoCE 使用 `roce_switch_check.py`，IB 使用 `ib_switch_check.py`。

- RoCE 独立脚本不接受 `--check-switch-port` 和 `--switch-network-type`；IB 脚本保留这两个兼容参数，其中 `--switch-network-type` 仅接受 `ib`。（已按本地两份脚本的参数定义核对）

- `--switch-pod-size N`：每台 leaf 对应机器数量（例如 `32`）。

- `--switch-sort {sort_gpu,switch_port}`：问题列表排序方式。

- `--switch-result-file FILE`：可选，指定结果 JSON 文件路径；省略时按所选模式自动生成结果文件。

- `--switch-base-manage-ip IP`：管理IP基准值（用于 index 计算）。

`ROCE` 额外常用参数：

- `--hostfile PATH`：主机列表。

- `--switchlist PATH` / `--switch-leaf-list PATH`：同一必填参数的两个别名，指定 leaf 列表文件（每行一个交换机名称： LLDP 上输出的 SysName\)

`IB` 额外常用参数：

- `--switch-iblinkinfo-file FILE`：iblinkinfo 文本路径（默认 `iblinkinfo.txt`）。

### **3\. ROCE 模式示例**

#### **3\.1 基础检查（推荐）**

```Bash
python3 nic_link_check/roce_switch_check.py \
          --hostfile hostfile \
          --switchlist switchlist.txt \
          --switch-pod-size 64 \
          --switch-base-manage-ip 192.0.2.5 \
          --switch-result-file roce_linkcheck_result.json
```

### **4\. IB 模式示例**

#### **4\.1 从CPU上执行（从hostfile指定检查\-推荐）**

```Bash
python3 nic_link_check/ib_switch_check.py \
          --hostfile hostfile \
          --switch-pod-size 32 \
          --switch-ib-collect-mode hostfile \
          --switch-result-file ./switch_check_result.json
```

#### **4\.2 从GPU上执行不带 hostfile（全量解析）**

```Bash
python3 ib_switch_check.py \
  --switch-pod-size 32 \
  --switch-ib-collect-mode local \
  --switch-result-file ./switch_check_result.json
```

说明：

- 会优先在当前节点执行 `iblinkinfo --cas-only`。

- 未显式传 `--hostfile` 时，不过滤主机，直接按 iblinkinfo 全量解析。

### **5\. 输出结果说明**

- 终端会打印问题统计和分项明细。

- 未指定输出路径时，RoCE 默认生成 `linkcheck_<时间戳>.json`，IB 默认生成 `ib_switch_check_<时间戳>.json`；两者均可通过 `--switch-result-file` 指定输出路径。（已按本地两份线序检查脚本核对）

- JSON 包含：

    - `params`：本次运行参数

    - `issue_report.summary`：问题统计，具体字段以所选模式的实际输出为准

    - `issue_report`：问题统计与明细

### **6\. 常见问题**

- `IB 模式需要 iblinkinfo 文件，但未找到`：

    - 请确认本机可执行 `iblinkinfo --cas-only`，或提供 `--switch-iblinkinfo-file`。

- `ROCE 模式缺少交换机列表`：

    - 请传 `--switch-leaf-list`。

- `ROCE 模式下 switch-leaf-list 需要填写交换机名称`：

    - leaf 列表应填写交换机 hostname，不应填写交换机 IP。
