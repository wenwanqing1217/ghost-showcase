/**
 * Ghost DS — Demo Seed Script
 *
 * 为开发/演示环境插入示例商品和订单数据。
 * 使用方法：
 *   docker compose exec ghost-ds node scripts/seed-demo.mjs
 */

import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

async function main() {
  console.log('[seed] 开始插入 demo 数据...');

  // 确保存在一个 shop
  const [shop] = await prisma.shop.upsert({
    where: { domain: 'demo.ghost-platform.com' },
    update: {},
    create: {
      name: 'Ghost Demo Shop',
      domain: 'demo.ghost-platform.com',
      accessToken: 'demo-token',
      platform: 'shoplazza',
      alphaId: 'Alpha-001',
      active: true,
    },
  });
  console.log(`[seed] shop: ${shop.id} (${shop.name})`);

  // 清理旧 demo 数据
  await prisma.order.deleteMany({ where: { shopId: shop.id } });
  await prisma.product.deleteMany({ where: { shopId: shop.id } });
  console.log('[seed] 清理旧数据完成');

  // 插入 demo 商品
  const products = [
    { title: 'Ghost Platform 智能助手订阅', price: 29.99, inventory: 999, status: 'active' },
    { title: 'AI 记忆图谱高级版', price: 49.99, inventory: 500, status: 'active' },
    { title: 'A2A 智能体协作套件', price: 99.99, inventory: 200, status: 'active' },
    { title: 'DID 身份验证服务年卡', price: 19.99, inventory: 1000, status: 'active' },
    { title: 'Web4.0 开发者工具包', price: 0, inventory: 0, status: 'draft' },
  ];

  for (const p of products) {
    const product = await prisma.product.create({
      data: {
        shopId: shop.id,
        externalId: `demo-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
        title: p.title,
        price: p.price,
        inventory: p.inventory,
        status: p.status,
        images: JSON.stringify([]),
      },
    });
    console.log(`[seed] product: ${product.id} — ${product.title}`);
  }

  // 插入 demo 订单
  const allProducts = await prisma.product.findMany({ where: { shopId: shop.id } });
  const statuses = ['pending', 'processing', 'shipped', 'delivered', 'cancelled'];

  for (let i = 0; i < 12; i++) {
    const product = allProducts[i % allProducts.length];
    const status = statuses[i % statuses.length];
    const qty = 1 + Math.floor(Math.random() * 3);

    const order = await prisma.order.create({
      data: {
        shopId: shop.id,
        externalId: `ORD-${String(1000 + i).padStart(6, '0')}`,
        customerName: `Customer ${i + 1}`,
        customerEmail: `customer${i + 1}@example.com`,
        total: product.price * qty,
        currency: 'USD',
        status,
        items: JSON.stringify([{ productId: product.id, title: product.title, qty, price: product.price }]),
      },
    });
    console.log(`[seed] order: ${order.externalId} — ${status} — $${order.total}`);
  }

  // 统计
  const productCount = await prisma.product.count({ where: { shopId: shop.id } });
  const orderCount = await prisma.order.count({ where: { shopId: shop.id } });
  console.log(`[seed] 完成! products=${productCount}, orders=${orderCount}`);
}

main()
  .catch((err) => {
    console.error('[seed] 失败:', err);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
