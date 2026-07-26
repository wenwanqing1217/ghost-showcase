# Net\-Agent 零重复造轮子落地方案

# Net\-Agent 完整修订落地设计文档

## 修订总则

1. 剔除所有虚构开源仓库，全程仅使用 PyPI、GitHub 可查验、可安装项目；

2. 推翻错误选型：NAPALM 降级为企业路由备选，家用路由优先自研适配封装；

3. 修正库属性：区分同步/异步依赖，规避混用问题；

4. 补齐三大核心缺口：内网NAT访问方案、账号凭证加密存储、多租户权限隔离；

5. 架构不抄袭外部项目，基于FastAPI微服务\+适配器模式原生搭建，适配现有Ghost整套生态；

6. 区分两端架构：公网服务端 \+ 用户本地常驻客户端，适配全网多用户使用场景。

## 一、整体架构拓扑

### 架构模式：C/S 双向架构（解决家用内网无法被公网访问痛点）

```Plain Text
【公网集群：Ghost 服务端】
Gateway (:18080) 统一请求入口
├─ Alpha-ID：用户身份、全局权限、密钥分发、用户空间隔离
├─ Nebula：事件总线、跨服务消息推送、任务回调调度
├─ Flow：注册初始化服务
└─ Net-Agent Server 网络管控后端
    ├── 权限校验层（多用户数据隔离）
    ├── 凭证安全存储模块
    ├── 指令下发队列
    ├── 巡检日志存储 & 查询接口
    ├── LLM网络故障决策引擎
    ├── /v1/net/* 对外REST接口
    └── 反向隧道服务对接端

【用户家庭内网：本地客户端 Net-Client】（每位用户独立部署）
常驻后台进程，主动长连接公网服务端（规避NAT入站拦截）
├─ 隧道链路：Tailscale / FRP 二选一维持长连接
├─ 路由器适配器调度核心
├─ 网络指标采集组件
├─ 路由设备指令执行器
├─ 本地日志缓存 + 定时上报公网
└─ 监听服务端下发指令并本地执行
```



### 核心通信逻辑

1. 本地客户端主动向外建立长连接，公网服务器无需访问用户内网IP；

2. 用户在网页发送「重启路由、查看在线设备」指令 → 存入服务端任务队列；

3. 用户本地客户端轮询/长连接拉取指令，在内网本地操控路由器；

4. 执行结果、网速、设备列表数据回传公网存入个人数据库；

优势：彻底解决家用宽带NAT、运营商封禁端口、内网无公网IP所有问题。



## 二、可信技术依赖清单（全部可核验）

### 1\. 路由器适配层

|依赖|运行模式|适用设备|使用方式|
|---|---|---|---|
|aio\-openwrt|异步|OpenWrt 固件路由|首选家用适配，调用ubus总线，非爬虫，稳定可靠|
|python\-xiaomi\-miwifi|同步|小米全系家用路由|同步库，代码内通过`asyncio.to_thread()`封装转为异步调用，适配整体异步服务|
|Netmiko|同步SSH|华硕、网件、带SSH权限路由|底层SSH会话管理|
|自定义网页爬虫|同步|TP\-Link、水星等大众家用路由|抓取后台Web接口，轻量化封装极简驱动|
|NAPALM|同步|思科、华为企业交换机/路由|仅作为企业设备兼容兜底，不再作为首选|



### 2\. 网络探测组件

- aioping：异步 ping 延迟、丢包、抖动检测

- scapy：ARP扫描，发现局域网所有在线终端、识别陌生接入设备

- python\-traceroute：路由链路追踪，定位外网卡顿节点

### 3\. 内网穿透选型（二选一）

1. Tailscale：零配置组网，开箱即用，适合普通小白用户（主推）

2. FRP：自建反向隧道，自由度高，适合有动手能力用户

### 4\. 加密与安全组件

- cryptography：AES\-GCM 对称加密，路由器账号密码加密存储

- passlib：密钥派生，用户独立加密盐值

- python\-jose：JWT鉴权，复用Alpha\-ID现有令牌体系

### 5\. 服务基础框架

- FastAPI：前后端接口、微服务主体

- SQLite：轻量化数据库（全局库，按用户ID隔离数据表/行数据）

- asyncio：整套服务异步IO，提升并发承载

## 三、适配器抽象层设计（原生自研，无外部照搬）

### 顶层抽象基类 `BaseRouterAdapter`

统一规范所有品牌路由的调用方法，新增设备仅需新建子类，上层业务代码无需改动

```Python
# 统一标准方法
async def get_wan_info(self) -> dict:
    """获取WAN拨号状态、上下行带宽、外网IP"""

async def get_lan_devices(self) -> list:
    """获取内网全部联网设备：MAC、设备名、IP、接入WiFi频段"""

async def get_network_quality(self) -> dict:
    """整合延迟、丢包、抖动，输出网络健康指标"""

async def reboot(self) -> bool:
    """重启路由器"""

async def set_wifi_channel(self, channel: int) -> bool:
    """切换WiFi信道，规避信道干扰"""

async def ban_mac(self, mac_addr: str) -> bool:
    """拉黑指定MAC地址，禁止接入内网"""

async def get_router_basic_info(self) -> dict:
    """路由型号、固件版本"""
```



首批实现子类：

1. OpenWrtAdapter（优先开发，稳定性最高）

2. XiaomiAdapter（同步库封装异步调用）

3. TPLinkWebAdapter（网页请求适配）

## 四、目录结构划分（服务端 \+ 客户端分离）

### 1\. 公网服务端：net\_agent\_server

```Plain Text
net_agent_server/
├── main.py                 # FastAPI服务启动入口
├── config/
│   └── settings.py         # 全局密钥、隧道配置、巡检周期、超时阈值
├── auth/
│   ├── permission.py       # 多用户权限隔离校验
│   └── crypto.py           # AES加解密工具、密钥处理
├── adapter_meta/           # 适配器元数据、品牌注册表
│   └── vendor_registry.py
├── task_queue/             # 指令下发队列，供本地客户端拉取
│   └── task_manager.py
├── api/                    # /v1/net 所有接口路由
│   └── routes.py
├── decision/
│   ├── static_rules.py     # 固定自愈规则：断网重启、陌生设备告警
│   └── llm_analyst.py      # LLM接收网络指标，故障诊断+自然语言指令解析
├── event/
│   └── nebula_hook.py      # 对接Nebula事件总线，全网服务联动
├── db/
│   ├── models.py           # 数据表结构定义
│   └── sqlite_store.py     # 数据库读写封装
└── utils/
    └── logger.py
```



### 2\. 用户本地客户端：net\_client

```Plain Text
net_client/
├── main.py                 # 常驻进程入口，维持长连接
├── tunnel/                 # Tailscale/FRP 调用封装
├── adapters/               # 和服务端一致的路由适配器
├── collector/              # 网速、局域网设备采集脚本
├── executor/               # 执行服务端下发的管控动作
├── config.yaml             # 用户本地配置文件
└── uploader.py             # 定时上报巡检日志至公网服务端
```



## 五、三大核心痛点完整解决方案

### 痛点1：NAT内网无法访问 → C/S长连接\+零配置组网

1. 用户下载轻量客户端，安装在自家电脑上开机自启；

2. 客户端主动连接公网Net\-Agent服务，永久维持长轮询连接；

3. 所有路由读取、控制行为**全部在内网本地执行**，结果回传云端；

4. Tailscale构建虚拟局域网，可按需打通服务端与内网设备，备选方案FRP反向隧道。

### 痛点2：路由器账号密码安全存储

1. 每位用户创建独立随机盐值，绑定Alpha\-ID用户唯一标识；

2. 路由用户名、密码采用 **AES\-GCM 算法加密** 后存入SQLite，明文绝不持久化；

3. 解密密钥仅留存用户本地客户端，公网服务端无法逆向解密完整凭证；

4. 客户端启动时拉取加密字段，本地解密后调用路由器接口，云端全程触碰不到明文密码。

### 痛点3：多用户数据严格隔离

1. 所有数据表均携带 `user_id` 主键字段，所有查询强制携带用户身份校验；

2. Alpha\-ID签发JWT令牌，请求 `/v1/net/*` 接口必须携带合法令牌；

3. 数据行级隔离：用户只能读写自身路由配置、巡检日志、操作记录；

4. 指令队列按用户ID分区，无法跨用户下发控制指令。

## 六、数据库表设计（SQLite，行级隔离）

### 表1：user\_router\_config 用户路由配置表

|字段|说明|
|---|---|
|id|自增主键|
|user\_id|关联Alpha\-ID用户ID，隔离依据|
|vendor|路由器品牌：openwrt/xiaomi/tplink|
|lan\_address|路由内网网关地址|
|encrypted\_username|AES加密账号|
|encrypted\_password|AES加密密码|
|create\_time|配置创建时间|



### 表2：network\_inspect\_logs 网络巡检日志

存储每小时网速、延迟、设备数量，用于AI分析网络波动

字段：id, user\_id, timestamp, latency, packet\_loss, online\_devices\_count, network\_score



### 表3：operation\_audit\_logs 运维操作审计日志

记录所有重启路由、拉黑设备、切换信道行为，方便回溯

字段：id, user\_id, operate\_action, trigger\_type\(手动/规则/AI\), result, operate\_time



### 表4：user\_task\_queue 用户指令队列

存放待客户端执行的管控指令

字段：task\_id, user\_id, task\_content, status, create\_time



## 七、分阶段落地计划（可逐行编码推进）

### Stage 1：基础通信与采集（优先落地，可运行最小版本）

1. 搭建服务端FastAPI基础框架、数据表创建、加解密工具封装；

2. 完成OpenWrt适配器异步读写能力；

3. 编写本地客户端长轮询拉取任务、内网采集网络状态；

4. 实现日志定时上报云端，网页可查看实时网络信息；

产出：只能监控网络，无AI、无自动控制。



### Stage 2：多品牌适配器补齐 \+ 权限闭环

1. 完成小米（同步转异步封装）、TP\-Link网页驱动；

2. 完善JWT鉴权、多用户隔离校验逻辑；

3. 测试Tailscale内网穿透链路稳定性。

### Stage 3：自愈决策引擎开发

1. 编写静态规则：外网掉线自动重启路由、陌生设备接入推送提醒、拥堵自动切换信道；

2. 对接本地LLM：上传网络各项指标，AI分析卡顿原因，生成优化方案并执行；

3. 支持网页端手动下发各类网络控制指令。

### Stage 4：Ghost全域生态联动

通过Nebula事件总线监听网络状态：

- 网络断开：自动暂停NAS文件同步、AI绘图、外网下载等依赖网络任务；

- 网络恢复：批量续行所有暂停任务。

### Stage 5：自然语言对话交互

嵌入全局AI聊天面板，口语化管控网络：

示例：

- 帮我看看家里有没有人蹭网

- 网速太慢了，优化一下WiFi设置

- 重启路由器

## 八、接口规划（Gateway统一前缀 /v1/net）

|接口|请求方式|功能|
|---|---|---|
|/config/save|POST|保存路由器接入配置|
|/status/realtime|GET|获取实时网络健康数据|
|/lan/devices|GET|查看内网所有接入设备|
|/action/reboot|POST|下发重启路由指令|
|/action/ban\_mac|POST|拉黑指定设备|
|/chat/command|POST|自然语言解析网络指令|
|/logs/history|GET|查询历史网络巡检日志|



## 九、方案优势总结

1. **依赖全部真实可信**：无虚构开源项目，所有库均可安装调试；

2. **适配多用户线上场景**：C/S架构彻底解决家用NAT难题；

3. **安全体系完整**：凭证加密存储、用户隔离、密钥分权；

4. **架构轻量化**：不引入重型中间件，贴合个人私有化Ghost项目定位；

5. **拓展性极强**：后续新增路由器品牌，仅需新增适配器子类即可。

需要我现在给你：

1. `BaseRouterAdapter` 抽象基类可直接运行Python源码；

2. OpenWrt适配器最简实现代码；

3. 服务端初始化启动首段代码吗？

> （注：部分内容可能由 AI 生成）
