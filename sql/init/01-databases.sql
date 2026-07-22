-- ════════════════════════════════════════════════════════════════════
-- Ghost Workspace — 数据库初始化
-- 在首次启动 PostgreSQL 容器时自动执行
-- ════════════════════════════════════════════════════════════════════
-- 共享用户: mw (由 POSTGRES_USER 环境变量创建)
-- 所有内部服务统一使用 mw 身份连接，避免权限碎片化。

-- MindFlow Map 数据库
CREATE DATABASE mindflow_map;
GRANT ALL PRIVILEGES ON DATABASE mindflow_map TO mw;

-- DS Dashboard 数据库
CREATE DATABASE ds;
GRANT ALL PRIVILEGES ON DATABASE ds TO mw;

-- AID Alpha-ID 数据库
CREATE DATABASE alpha_id;
GRANT ALL PRIVILEGES ON DATABASE alpha_id TO mw;

-- MindFlow 数据库（向后兼容）
CREATE DATABASE mindflow;
GRANT ALL PRIVILEGES ON DATABASE mindflow TO mw;
