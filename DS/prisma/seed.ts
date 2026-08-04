/**
 * DS 种子数据 — Demo 模式下展示假数据
 * 运行: npm run db:seed
 */

import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

const FAKE_PRODUCTS = [
  { externalId: 'p001', title: '北欧简约陶瓷花瓶', description: '手工陶瓷，适合客厅装饰', price: 29.99, inventory: 150, status: 'active', images: ['https://picsum.photos/seed/vase/400/400'] },
  { externalId: 'p002', title: '智能温控保温杯', description: 'LED 显示温度，316 不锈钢', price: 39.99, inventory: 80, status: 'active', images: ['https://picsum.photos/seed/cup/400/400'] },
  { externalId: 'p003', title: '无线充电床头灯', description: '触摸调光，三色温切换', price: 24.99, inventory: 200, status: 'active', images: ['https://picsum.photos/seed/lamp/400/400'] },
  { externalId: 'p004', title: '天然乳胶枕头', description: '泰国进口，护颈助眠', price: 49.99, inventory: 45, status: 'active', images: ['https://picsum.photos/seed/pillow/400/400'] },
  { externalId: 'p005', title: '便携折叠收纳箱', description: '环保 PP 材质，多尺寸可选', price: 15.99, inventory: 320, status: 'active', images: ['https://picsum.photos/seed/box/400/400'] },
];

const FAKE_ORDERS = [
  { externalId: 'o001', orderNo: 'OB202607240001', amount: 54.98, status: 'paid', customerName: 'Alice W.', itemCount: 2 },
  { externalId: 'o002', orderNo: 'OB202607240002', amount: 29.99, status: 'fulfilled', customerName: 'Bob L.', itemCount: 1 },
  { externalId: 'o003', orderNo: 'OB202607240003', amount: 99.97, status: 'paid', customerName: 'Carol Z.', itemCount: 3 },
  { externalId: 'o004', orderNo: 'OB202607230001', amount: 15.99, status: 'pending', customerName: 'David K.', itemCount: 1 },
  { externalId: 'o005', orderNo: 'OB202607230002', amount: 74.98, status: 'fulfilled', customerName: 'Emma T.', itemCount: 2 },
  { externalId: 'o006', orderNo: 'OB202607220001', amount: 49.99, status: 'refunded', customerName: 'Frank H.', itemCount: 1 },
];

async function main() {
  console.log('🌱 Seeding demo data...');

  // 检查是否已有店铺
  let shop = await prisma.shop.findFirst();
  if (!shop) {
    shop = await prisma.shop.create({
      data: {
        name: 'OneBound 货源',
        domain: 'onebound-demo',
        accessToken: 'demo_api_key',
        platform: 'onebound',
        tenantId: 'default',
        storeMode: 'marketplace',
      },
    });
    console.log(`  ✅ Created demo shop: ${shop.id}`);
  } else {
    console.log(`  ℹ️  Shop already exists: ${shop.id}`);
  }

  // 清空旧数据再插入（保证 seed 幂等）
  await prisma.order.deleteMany({ where: { shopId: shop.id } });
  await prisma.product.deleteMany({ where: { shopId: shop.id } });

  for (const p of FAKE_PRODUCTS) {
    await prisma.product.create({
      data: {
        ...p,
        shopId: shop.id,
        tenantId: shop.tenantId,
        currency: 'USD',
        images: JSON.stringify(p.images),
        lastSyncedAt: new Date(),
      },
    });
  }
  console.log(`  ✅ Seeded ${FAKE_PRODUCTS.length} products`);

  const now = new Date();
  for (let i = 0; i < FAKE_ORDERS.length; i++) {
    const o = FAKE_ORDERS[i];
    await prisma.order.create({
      data: {
        ...o,
        shopId: shop.id,
        tenantId: shop.tenantId,
        currency: 'USD',
        paidAt: o.status !== 'pending' ? new Date(now.getTime() - i * 86400000) : null,
        fulfilledAt: o.status === 'fulfilled' ? new Date(now.getTime() - i * 43200000) : null,
        refundedAt: o.status === 'refunded' ? new Date(now.getTime() - i * 21600000) : null,
      },
    });
  }
  console.log(`  ✅ Seeded ${FAKE_ORDERS.length} orders`);

  console.log('🎉 Seed complete!');
}

main()
  .catch((e) => { console.error(e); process.exit(1); })
  .finally(async () => { await prisma.$disconnect(); });
