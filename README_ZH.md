# ESXi MCP Server

一个基于 MCP (Model Control Protocol) 的 VMware ESXi/vCenter 管理服务器，提供简单的 REST API 接口来管理虚拟机。

## 功能特性

- 支持 ESXi 和 vCenter Server 连接
- 现代 MCP 传输协议：
  - **Streamable HTTP** - HTTP 传输协议，位于 `/message` 端点
- RESTful API 接口，支持 JSON-RPC
- 支持 API 密钥认证
- 完整的虚拟机生命周期管理
- 实时性能监控
- 支持 SSL/TLS 安全连接
- 灵活的配置选项（YAML/JSON/环境变量）

## 主要功能

- 虚拟机管理
  - 创建虚拟机
  - 克隆虚拟机
  - 删除虚拟机
  - 开机/关机操作
  - 列出所有虚拟机
- 性能监控
  - CPU 使用率
  - 内存使用情况
  - 存储空间使用
  - 网络流量统计

## 安装要求

- Python 3.7+
- pyVmomi
- PyYAML
- uvicorn
- mcp-core (Machine Control Protocol 核心库)

## 快速开始

1. 安装依赖：

```bash
pip install pyvmomi pyyaml uvicorn mcp-core
```

2. 创建配置文件 `config.yaml`：

```yaml
vcenter_host: "your-vcenter-ip"
vcenter_user: "administrator@vsphere.local"
vcenter_password: "your-password"
datacenter: "your-datacenter"        # 可选
cluster: "your-cluster"              # 可选
datastore: "your-datastore"          # 可选
network: "VM Network"                # 可选
insecure: true                       # 是否跳过SSL证书验证
api_key: "your-api-key"             # API访问密钥
log_file: "./logs/vmware_mcp.log"   # 日志文件路径
log_level: "INFO"                    # 日志级别
```

3. 运行服务器：

```bash
python server.py -c config.yaml
```

## API 接口

### 传输协议

服务器使用现代 **Streamable HTTP** MCP 传输协议：

- **端点**：`/message`
- **方法**：`GET`（流式响应）、`POST`（请求）
- 现代 HTTP 传输协议，完全符合 MCP 规范

### 认证

所有需要权限的操作都需要在请求头中包含 API 密钥：

```http
Authorization: Bearer your-api-key
```

或者：

```http
X-API-Key: your-api-key
```

### 主要工具接口

1. 创建虚拟机
```json
{
    "name": "vm-name",
    "cpu": 2,
    "memory": 4096,
    "datastore": "datastore-name",
    "network": "network-name"
}
```

2. 克隆虚拟机
```json
{
    "template_name": "source-vm",
    "new_name": "new-vm-name"
}
```

3. 删除虚拟机
```json
{
    "name": "vm-name"
}
```

4. 电源操作
```json
{
    "name": "vm-name"
}
```

### 资源监控接口

获取虚拟机性能数据：
```http
GET vmstats://{vm_name}
```

## 配置说明

| 配置项 | 说明 | 必填 | 默认值 |
|--------|------|------|--------|
| vcenter_host | vCenter/ESXi服务器地址 | 是 | - |
| vcenter_user | 登录用户名 | 是 | - |
| vcenter_password | 登录密码 | 是 | - |
| datacenter | 数据中心名称 | 否 | 自动选择第一个 |
| cluster | 集群名称 | 否 | 自动选择第一个 |
| datastore | 存储名称 | 否 | 自动选择最大可用空间 |
| network | 网络名称 | 否 | VM Network |
| insecure | 是否跳过SSL验证 | 否 | false |
| api_key | API访问密钥 | 否 | - |
| log_file | 日志文件路径 | 否 | 控制台输出 |
| log_level | 日志级别 | 否 | INFO |

## 环境变量支持

所有配置项都支持通过环境变量设置，环境变量名称规则：
- VCENTER_HOST
- VCENTER_USER
- VCENTER_PASSWORD
- VCENTER_DATACENTER
- VCENTER_CLUSTER
- VCENTER_DATASTORE
- VCENTER_NETWORK
- VCENTER_INSECURE
- MCP_API_KEY
- MCP_LOG_FILE
- MCP_LOG_LEVEL

## 安全建议

1. 生产环境建议：
   - 使用有效的SSL证书
   - 启用API密钥认证
   - 设置适当的日志级别
   - 限制API访问范围

2. 测试环境可以：
   - 设置 insecure: true 跳过SSL验证
   - 使用更详细的日志级别(DEBUG)

## 许可证

MIT License

## 贡献指南

欢迎提交 Issue 和 Pull Request！

## 更新日志

### v0.0.1
- 初始版本发布
- 基本的虚拟机管理功能
- SSE 通信支持
- API 密钥认证
- 性能监控

## 作者

Bright8192

## 致谢

- VMware pyvmomi 团队
- MCP Protocol 开发团队