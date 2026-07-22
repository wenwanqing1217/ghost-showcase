import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

async function main() {
  // Clear existing data
  await prisma.agentRun.deleteMany();
  await prisma.approval.deleteMany();
  await prisma.alert.deleteMany();
  await prisma.order.deleteMany();
  await prisma.product.deleteMany();

  // Seed Products
  const products = await prisma.product.createMany({
    data: [
      {
        shopifyId: 'prod_001',
        title: 'Wireless Earbuds Pro',
        description: 'High-quality wireless earbuds with active noise cancellation and 24-hour battery life.',
        tags: 'audio,wireless,bluetooth',
        status: 'active',
      },
      {
        shopifyId: 'prod_002',
        title: 'Smart Watch X',
        description: 'Advanced smartwatch with health monitoring, GPS, and 7-day battery life.',
        tags: 'wearable,smartwatch,fitness',
        status: 'active',
      },
      {
        shopifyId: 'prod_003',
        title: 'Portable Power Bank 20000mAh',
        description: 'High-capacity power bank with fast charging and USB-C PD support.',
        tags: 'accessories,charging,portable',
        status: 'draft',
      },
      {
        shopifyId: 'prod_004',
        title: 'Minimalist Laptop Sleeve',
        description: 'Premium leather laptop sleeve for 13-16 inch laptops. Water-resistant and slim.',
        tags: 'accessories,laptop,leather',
        status: 'active',
      },
      {
        shopifyId: 'prod_005',
        title: 'Ergonomic Office Chair',
        description: 'Adjustable ergonomic chair with lumbar support and breathable mesh back.',
        tags: 'furniture,office,ergonomic',
        status: 'draft',
      },
    ],
  });

  // Seed Orders
  const orders = [
    {
      shopifyId: 'ord_001',
      totalPrice: '129.99',
      currency: 'USD',
      fulfillmentStatus: 'fulfilled',
      riskLevel: 'low',
    },
    {
      shopifyId: 'ord_002',
      totalPrice: '249.50',
      currency: 'USD',
      fulfillmentStatus: 'partial',
      riskLevel: 'medium',
    },
    {
      shopifyId: 'ord_003',
      totalPrice: '89.00',
      currency: 'USD',
      fulfillmentStatus: 'unfulfilled',
      riskLevel: 'low',
    },
    {
      shopifyId: 'ord_004',
      totalPrice: '399.99',
      currency: 'USD',
      fulfillmentStatus: 'fulfilled',
      riskLevel: 'low',
    },
    {
      shopifyId: 'ord_005',
      totalPrice: '59.99',
      currency: 'USD',
      fulfillmentStatus: 'fulfilled',
      riskLevel: 'high',
    },
  ];

  for (const order of orders) {
    await prisma.order.create({ data: order });
  }

  // Seed Approvals and Agent Runs
  const approval = await prisma.approval.create({
    data: {
      workflowType: 'content_generation',
      status: 'approved',
      payload: JSON.stringify({
        input: { title: 'Wireless Earbuds Pro' },
        output: { title: 'Wireless Earbuds Pro', description: '...' },
      }),
      result: 'Approved by user',
      decidedAt: new Date(),
    },
  });

  await prisma.agentRun.create({
    data: {
      agentType: 'content',
      input: JSON.stringify({ title: 'Wireless Earbuds Pro' }),
      output: JSON.stringify({ title: 'Wireless Earbuds Pro' }),
      status: 'success',
      approvalId: approval.id,
      durationMs: 1200,
    },
  });

  // Seed Alerts
  await prisma.alert.createMany({
    data: [
      {
        severity: 'P1',
        category: 'inventory',
        message: 'SKU-2847 is out of stock. 12 pending orders affected.',
        resolved: false,
      },
      {
        severity: 'P2',
        category: 'budget',
        message: '"Summer Sale" campaign has used 85% of daily budget.',
        resolved: false,
      },
      {
        severity: 'P1',
        category: 'payment',
        message: '3 consecutive payment failures detected in last hour.',
        resolved: true,
      },
      {
        severity: 'P3',
        category: 'content',
        message: 'Content approval queue has 5 pending items.',
        resolved: false,
      },
    ],
  });

  console.log('✅ Seed data created successfully');
}

main()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
