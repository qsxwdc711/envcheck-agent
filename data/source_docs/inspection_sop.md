检查GPU数量、型号、驱动、固件版本、cuda版本
测试方法：
nvidia-smi
nvidia-smi --query-gpu=gpu_name,gpu_bus_id,vbios_version,driver_version,memory.total,ecc.mode.current,power.limit,persistence_mode --format=csv
nvidia-smi -q -d SUPPORTED_CLOCKS
测试结果：
GPU_LIST:

验证服务器系统、内核版本一致且符合要求。
测试方法:hostnamectl | grep Kernel | cut -d: -f2 | xargs
cat /etc/os-release
测试结果:OS:
KERNEL:

检查集群所有节点时钟一致.测试方法：
timedatectl
测试结果：
TIME_INFO:
