1.拉取 aidoc_download 代码到示例工作目录

2.执行

```Markdown
bash create.sh
```

会初始化 download_resource 目录结构,并移入pack.sh

```Markdown
├── drivers
│   ├── cuda
│   ├── doca
│   ├── nvidia
│   └── ofed
├── pack.sh
├── isos
├── nvidia
│   ├── dcgm
│   ├── fm
│   └── nvlsm
├── qemu_disk（创建虚拟机的磁盘）
├── qemu_disk_bak（创建虚拟机磁盘的备份）
```

3.创建虚拟机并在后台启动

参考[使用 qemu 虚拟机便捷下载系统依赖包并打包镜像](https://example.com/internal-guides/dependency-download)的4.2.2 自动配置

4.使用aidoc_download.py工具下载所需驱动，镜像，离线包，并打包成镜像

请参考[使用 qemu 虚拟机便捷下载系统依赖包并打包镜像](https://example.com/internal-guides/dependency-download)的3使用说明

不同版本对应的虚拟机端口关系：

"220405": 10023,

"240404": 10022,

"220404": 10024,

"240402": 10025

5.得到镜像后使用launch-install.sh工具进行装机以及验证

参考[使用 qemu 虚拟机验证 autoinstall 文件](https://example.com/internal-guides/autoinstall-validation)的5操作流程

###
