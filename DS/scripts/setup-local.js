/**
 * 本地开发环境一键搭建
 * 用法：npm run dev:setup
 *
 * 作用：
 * 1. 将 schema.local.prisma（SQLite）复制为 schema.prisma
 * 2. 确保 .env 指向 SQLite
 * 3. 执行 prisma db push + seed
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const SCHEMA_PROD = path.join(ROOT, 'prisma', 'schema.prisma');
const SCHEMA_LOCAL = path.join(ROOT, 'prisma', 'schema.local.prisma');
const ENV_FILE = path.join(ROOT, '.env');

function log(msg) {
  console.log(`  ${msg}`);
}

console.log('\n🔧 DS 本地开发环境搭建\n');

// 1. 备份生产 schema（如果当前 schema.prisma 是 PostgreSQL 的）
const currentSchema = fs.readFileSync(SCHEMA_PROD, 'utf-8');
if (currentSchema.includes('provider = "postgresql"')) {
  log('📦 检测到生产 schema，保留为 schema.prisma（生产用）');
  log('📋 复制 schema.local.prisma → schema.prisma');
}

// 2. 用 SQLite schema 覆盖
fs.copyFileSync(SCHEMA_LOCAL, SCHEMA_PROD);
log('✅ Schema 已切换为 SQLite');

// 3. 确保 .env 存在并指向 SQLite
let envContent = '';
if (fs.existsSync(ENV_FILE)) {
  envContent = fs.readFileSync(ENV_FILE, 'utf-8');
}

const lines = envContent.split('\n');
const hasUrl = lines.some((l) => l.startsWith('DATABASE_URL='));
const hasDemo = lines.some((l) => l.startsWith('DEMO_MODE='));

if (!hasUrl) {
  lines.push('DATABASE_URL="file:./dev.db"');
  log('✅ .env 添加 DATABASE_URL');
}
if (!hasDemo) {
  lines.push('DEMO_MODE=true');
  log('✅ .env 添加 DEMO_MODE=true');
}

fs.writeFileSync(ENV_FILE, lines.filter(Boolean).join('\n') + '\n');

// 4. 生成 Prisma Client + 推数据库
log('\n📊 生成 Prisma Client...');
execSync('npx prisma generate', { cwd: ROOT, stdio: 'inherit' });

log('\n🗄️  推送数据库 Schema...');
execSync('npx prisma db push --force-reset', { cwd: ROOT, stdio: 'inherit' });

log('\n🌱 插入种子数据...');
execSync('npx tsx prisma/seed.ts', { cwd: ROOT, stdio: 'inherit' });

console.log('\n🎉 本地环境就绪！运行 npm run dev 启动\n');
