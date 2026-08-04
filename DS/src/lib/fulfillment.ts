/**
 * Fulfillment Middleware — Order & Fulfillment Center
 *
 * Architecture:
 *  订单事件 → 自动识别归属 → 路由到履约链路 → 结果回写
 *
 * Fulfillment paths:
 *  1. Platform supply auto-shipping (货源 → OneBound API 代发)
 *  2. Merchant custom Skill fulfillment (商家 Skill → 自有物流)
 *  3. Marketplace order splitting (集市跨店购物车 → 按商家拆分子单)
 *
 * Event-driven: subscribes to order:paid, order:created events
 */

import { EventBus, EventType, Event } from '@/lib/eventbus';
import { OneBoundClient, OneBoundError } from '@/lib/onebound';
import { prisma } from '@/lib/prisma';

// ── Fulfillment Task Types ──

export type FulfillmentPath = 'platform_auto' | 'merchant_skill' | 'marketplace_split';
export type FulfillmentStatus = 'pending' | 'processing' | 'completed' | 'failed' | 'retrying' | 'cancelled';

export interface FulfillmentTask {
  id: string;
  orderId: string;
  tenantId: string;
  shopId?: string;              // OneBound 货源店铺 ID
  path: FulfillmentPath;
  status: FulfillmentStatus;
  items: FulfillmentItem[];
  trackingNumber?: string;
  trackingCompany?: string;
  error?: string;
  retryCount: number;
  createdAt: number;
  updatedAt: number;
  completedAt?: number;
}

export interface FulfillmentItem {
  productId: string;
  sourceId?: string;        // Supply source product ID
  sku?: string;             // Product SKU for OneBound
  quantity: number;
  merchantId?: string;      // For marketplace: which merchant's item
  skillId?: string;          // For merchant skill: which skill to invoke
}

// ── Fulfillment Middleware ──

export class FulfillmentMiddleware {
  private eventBus: EventBus;
  private tasks: Map<string, FulfillmentTask> = new Map();
  private processing = new Set<string>();

  constructor(eventBus: EventBus) {
    this.eventBus = eventBus;
    this.registerHandlers();
  }

  private registerHandlers(): void {
    // 订单创建 → 创建待处理任务
    this.eventBus.on('order:created', async (event: Event) => {
      await this.handleOrderCreated(event);
    });

    // 订单支付成功 → 启动履约流程
    this.eventBus.on('order:paid', async (event: Event) => {
      await this.handleOrderPaid(event);
    });

    // 订单退款 → 取消履约任务
    this.eventBus.on('order:refunded', async (event: Event) => {
      await this.handleOrderRefunded(event);
    });

    // 订单取消 → 取消履约任务
    this.eventBus.on('order:cancelled', async (event: Event) => {
      await this.handleOrderCancelled(event);
    });

    // 库存更新 → 检查是否需要暂停铺货
    this.eventBus.on('supply:inventory:updated', async (event: Event) => {
      await this.handleInventoryUpdated(event);
    });
  }

  // ── Event Handlers ──

  private async handleOrderCreated(event: Event): Promise<void> {
    const { orderId, items, storeMode, shopId } = event.data as {
      orderId: string;
      items: any[];
      storeMode: string;
      shopId?: string;
    };

    console.log(`[Fulfillment] Order created: ${orderId}, mode: ${storeMode}`);

    // 根据店铺模式决定履约路径
    let path: FulfillmentPath;
    if (storeMode === 'marketplace') {
      path = 'marketplace_split';
    } else if (storeMode === 'independent') {
      path = 'merchant_skill';
    } else {
      // 'both' — 判断订单来源
      path = 'platform_auto'; // 默认平台代发
    }

    const task: FulfillmentTask = {
      id: `fulfill-${orderId}`,
      orderId,
      tenantId: event.tenantId,
      shopId,
      path,
      status: 'pending',
      items: items.map((item: any) => ({
        productId: item.productId,
        sourceId: item.sourceId,
        quantity: item.quantity,
        merchantId: item.merchantId,
        skillId: item.skillId,
      })),
      retryCount: 0,
      createdAt: Date.now(),
      updatedAt: Date.now(),
    };

    this.tasks.set(task.id, task);

    // 发布待处理事件
    await this.eventBus.publish('fulfillment:task:created', {
      taskId: task.id,
      orderId,
      path,
      itemCount: items.length,
    }, {
      tenantId: event.tenantId,
      source: 'fulfillment-middleware',
      correlationId: event.correlationId,
    });
  }

  private async handleOrderPaid(event: Event): Promise<void> {
    const { orderId } = event.data as { orderId: string };
    const task = this.tasks.get(`fulfill-${orderId}`);

    if (!task) {
      console.warn(`[Fulfillment] No task found for paid order: ${orderId}`);
      return;
    }

    if (task.status === 'completed') {
      console.log(`[Fulfillment] Order ${orderId} already fulfilled`);
      return;
    }

    console.log(`[Fulfillment] Starting fulfillment for order ${orderId}, path: ${task.path}`);
    task.status = 'processing';
    task.updatedAt = Date.now();

    try {
      switch (task.path) {
        case 'platform_auto':
          await this.fulfillPlatformAuto(task, event);
          break;
        case 'merchant_skill':
          await this.fulfillMerchantSkill(task, event);
          break;
        case 'marketplace_split':
          await this.fulfillMarketplaceSplit(task, event);
          break;
      }
    } catch (error) {
      console.error(`[Fulfillment] Failed for order ${orderId}:`, error);
      task.status = 'failed';
      task.error = error instanceof Error ? error.message : String(error);
      task.updatedAt = Date.now();

      await this.eventBus.publish('fulfillment:task:failed', {
        taskId: task.id,
        orderId,
        error: task.error,
      }, {
        tenantId: event.tenantId,
        source: 'fulfillment-middleware',
        correlationId: event.correlationId,
      });
    }
  }

  private async handleOrderRefunded(event: Event): Promise<void> {
    const { orderId } = event.data as { orderId: string };
    const task = this.tasks.get(`fulfill-${orderId}`);

    if (task && task.status !== 'completed') {
      task.status = 'cancelled';
      task.updatedAt = Date.now();
      console.log(`[Fulfillment] Cancelled task for refunded order: ${orderId}`);
    }
  }

  private async handleOrderCancelled(event: Event): Promise<void> {
    const { orderId } = event.data as { orderId: string };
    const task = this.tasks.get(`fulfill-${orderId}`);

    if (task && task.status !== 'completed') {
      task.status = 'cancelled';
      task.updatedAt = Date.now();
      console.log(`[Fulfillment] Cancelled task for cancelled order: ${orderId}`);
    }
  }

  private async handleInventoryUpdated(event: Event): Promise<void> {
    // Check if any pending fulfillment tasks need to be paused due to stockout
    const { sourceId, inventory } = event.data as { sourceId: string; inventory: number };

    for (const task of this.tasks.values()) {
      if (task.status === 'pending' || task.status === 'processing') {
        const hasStockout = task.items.some(
          item => item.sourceId === sourceId && inventory < item.quantity
        );

        if (hasStockout) {
          console.warn(`[Fulfillment] Stockout detected for order ${task.orderId}, pausing`);
          task.status = 'pending';
          task.error = `Stockout: ${sourceId} has ${inventory} units`;
          task.updatedAt = Date.now();

          await this.eventBus.publish('system:alert', {
            type: 'stockout',
            orderId: task.orderId,
            sourceId,
            availableInventory: inventory,
          }, {
            tenantId: task.tenantId,
            source: 'fulfillment-middleware',
          });
        }
      }
    }
  }

  // ── Fulfillment Paths ──

  /**
   * Path 1: Platform auto-shipping via OneBound
   * Submit fulfillment order to OneBound dropshipping API
   */
  private async fulfillPlatformAuto(task: FulfillmentTask, event: Event): Promise<void> {
    console.log(`[Fulfillment] OneBound auto-shipping for order ${task.orderId}`);

    if (!task.shopId) {
      throw new Error(`Order ${task.orderId}: 缺少 shopId，无法提交 OneBound 代发`);
    }

    const shippingData = event.data as {
      customerName?: string;
      customerPhone?: string;
      shippingAddress?: {
        address?: string;
        city?: string;
        country?: string;
      };
    };

    // 查找关联店铺获取 OneBound API Key
    const shop = await prisma.shop.findFirst({
      where: { id: task.shopId, active: true },
      select: { accessToken: true, platform: true },
    });

    if (!shop || !shop.accessToken || shop.platform !== 'onebound') {
      throw new Error(`Order ${task.orderId}: 未找到 OneBound 货源连接`);
    }

    const client = new OneBoundClient(shop.accessToken);

    // 从 task.items 中获取商品信息
    const items = task.items.map((item) => ({
      productId: item.productId || item.sourceId || '',
      sku: item.sku,
      quantity: item.quantity || 1,
    }));

    if (items.length === 0) {
      throw new Error(`Order ${task.orderId}: 无商品信息，无法提交代发`);
    }

    // 调用 OneBound 创建代发订单
    const result = await client.createFulfillmentOrder({
      items,
      shippingAddress: {
        name: shippingData.customerName || 'Customer',
        phone: shippingData.customerPhone || '',
        address: shippingData.shippingAddress?.address || 'N/A',
        city: shippingData.shippingAddress?.city || 'N/A',
        country: shippingData.shippingAddress?.country || 'US',
      },
      orderNote: `Order: ${task.orderId}`,
    });

    task.status = 'completed';
    task.trackingNumber = result.trackingNumber || `ONEBOUND-${Date.now().toString(36).toUpperCase()}`;
    task.trackingCompany = result.trackingCompany || 'OneBound';
    task.completedAt = Date.now();
    task.updatedAt = Date.now();

    await this.eventBus.publish('fulfillment:task:completed', {
      taskId: task.id,
      orderId: task.orderId,
      trackingNumber: task.trackingNumber,
      trackingCompany: task.trackingCompany,
      path: 'platform_auto',
      oneBoundOrderId: result.orderId,
    }, {
      tenantId: task.tenantId,
      source: 'fulfillment-middleware',
      correlationId: event.correlationId,
    });
  }

  /**
   * Path 2: Merchant custom Skill fulfillment
   * Invoke merchant's custom Skill to handle fulfillment
   */
  private async fulfillMerchantSkill(task: FulfillmentTask, event: Event): Promise<void> {
    console.log(`[Fulfillment] Merchant skill fulfillment for order ${task.orderId}`);

    // TODO: Invoke merchant's Skill via Nebula Skill system
    // For now, simulate success
    await this.simulateDelay(1500);

    const trackingNumber = `SKILL-${Date.now().toString(36).toUpperCase()}`;
    const trackingCompany = task.items[0]?.skillId || 'Custom Skill';

    task.status = 'completed';
    task.trackingNumber = trackingNumber;
    task.trackingCompany = trackingCompany;
    task.completedAt = Date.now();
    task.updatedAt = Date.now();

    await this.eventBus.publish('fulfillment:task:completed', {
      taskId: task.id,
      orderId: task.orderId,
      trackingNumber,
      trackingCompany,
      path: 'merchant_skill',
    }, {
      tenantId: task.tenantId,
      source: 'fulfillment-middleware',
      correlationId: event.correlationId,
    });
  }

  /**
   * Path 3: Marketplace order splitting
   * Split cross-shop cart order into sub-orders per merchant
   */
  private async fulfillMarketplaceSplit(task: FulfillmentTask, event: Event): Promise<void> {
    console.log(`[Fulfillment] Marketplace split for order ${task.orderId}`);

    // Group items by merchant
    const merchantGroups = new Map<string, FulfillmentItem[]>();
    for (const item of task.items) {
      const merchantId = item.merchantId || 'platform';
      if (!merchantGroups.has(merchantId)) {
        merchantGroups.set(merchantId, []);
      }
      merchantGroups.get(merchantId)!.push(item);
    }

    // Fulfill each merchant's sub-order in parallel
    const subResults = await Promise.allSettled(
      Array.from(merchantGroups.entries()).map(async ([merchantId, items]) => {
        // TODO: Create sub-order for merchant
        // TODO: Route to merchant's fulfillment path
        await this.simulateDelay(800);
        return { merchantId, items, success: true };
      })
    );

    const allSucceeded = subResults.every(r => r.status === 'fulfilled');

    if (allSucceeded) {
      task.status = 'completed';
      task.completedAt = Date.now();
    } else {
      task.status = 'failed';
      task.error = 'Some sub-orders failed fulfillment';
    }
    task.updatedAt = Date.now();

    await this.eventBus.publish('fulfillment:task:completed', {
      taskId: task.id,
      orderId: task.orderId,
      path: 'marketplace_split',
      subOrderCount: merchantGroups.size,
      allSucceeded,
    }, {
      tenantId: task.tenantId,
      source: 'fulfillment-middleware',
      correlationId: event.correlationId,
    });
  }

  // ── Public API ──

  /**
   * Manually trigger fulfillment for an order (bypasses event queue).
   */
  async fulfillOrder(orderId: string, trackingNumber?: string, trackingCompany?: string): Promise<FulfillmentTask | null> {
    const task = this.tasks.get(`fulfill-${orderId}`);
    if (!task) {
      console.warn(`[Fulfillment] No task found for order: ${orderId}`);
      return null;
    }

    if (task.status === 'completed') {
      console.log(`[Fulfillment] Order ${orderId} already fulfilled`);
      return task;
    }

    // Create a synthetic paid event
    const syntheticEvent: Event = {
      id: `manual-${Date.now()}`,
      type: 'order:paid',
      tenantId: task.tenantId,
      data: { orderId },
      timestamp: Date.now(),
      source: 'manual-api',
    };

    await this.handleOrderPaid(syntheticEvent);
    return this.tasks.get(`fulfill-${orderId}`) || null;
  }

  /**
   * Get fulfillment task status.
   */
  getTask(orderId: string): FulfillmentTask | undefined {
    return this.tasks.get(`fulfill-${orderId}`);
  }

  /**
   * Get all tasks for a tenant.
   */
  getTasksByTenant(tenantId: string): FulfillmentTask[] {
    return Array.from(this.tasks.values()).filter(t => t.tenantId === tenantId);
  }

  // ── Utils ──

  private async simulateDelay(ms: number): Promise<void> {
    await new Promise(r => setTimeout(r, ms));
  }
}
