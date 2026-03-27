<script lang="ts" setup>
import { computed, onMounted, onUnmounted, ref } from 'vue';
import { message } from 'ant-design-vue';

import {
  createRechargeOrderApi,
  getPlansApi,
  getRechargeOrderApi,
  getUserInfoApi,
  mockPayOrderApi,
  type AuthApi,
} from '#/api';

// ===================== 状态 =====================
const loading = ref(false);
const plans = ref<AuthApi.PlanItem[]>([]);
const currentPlan = ref<string>('free');
const submittingPlan = ref<string>('');

// 支付弹窗状态
const payVisible = ref(false);
const payOrder = ref<AuthApi.RechargeOrderResult | null>(null);
const payStatus = ref<'pending' | 'paid'>('pending');
const polling = ref(false);
let pollTimer: ReturnType<typeof setInterval> | null = null;

// ===================== 计算 =====================
const sortedPlans = computed(() => {
  const order = ['free', 'basic', 'pro', 'enterprise'];
  return [...plans.value].sort(
    (a, b) => order.indexOf(a.planType) - order.indexOf(b.planType),
  );
});

/** 根据 code_url 生成二维码图片地址（使用免费 QR API） */
const qrCodeUrl = computed(() => {
  if (!payOrder.value?.codeUrl) return '';
  return `https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=${encodeURIComponent(payOrder.value.codeUrl)}`;
});

// ===================== 方法 =====================
async function loadData() {
  loading.value = true;
  try {
    const [planList, userInfo] = await Promise.all([getPlansApi(), getUserInfoApi()]);
    const info = userInfo as unknown as { pageQuota?: { planType?: AuthApi.PlanItem['planType'] } };
    plans.value = planList;
    currentPlan.value = info.pageQuota?.planType ?? 'free';
  } finally {
    loading.value = false;
  }
}

/** 选择套餐，创建订单并弹出支付二维码 */
async function handleRecharge(planType: AuthApi.PlanItem['planType']) {
  if (submittingPlan.value) return;
  submittingPlan.value = planType;
  try {
    const res = await createRechargeOrderApi({ plan_type: planType });
    payOrder.value = res;
    payStatus.value = 'pending';
    payVisible.value = true;
    startPolling(res.orderId);
  } catch (error: any) {
    message.error(error?.message ?? '创建订单失败');
  } finally {
    submittingPlan.value = '';
  }
}

/** 开始轮询订单状态，每 3 秒查询一次 */
function startPolling(orderId: string) {
  stopPolling();
  polling.value = true;
  pollTimer = setInterval(async () => {
    try {
      const res = await getRechargeOrderApi(orderId);
      if (res.status === 'paid') {
        payStatus.value = 'paid';
        stopPolling();
        currentPlan.value = res.quota?.planType ?? currentPlan.value;
      }
    } catch {
      // 轮询失败静默忽略
    }
  }, 3000);
}

function stopPolling() {
  if (pollTimer !== null) {
    clearInterval(pollTimer);
    pollTimer = null;
  }
  polling.value = false;
}

/** 点击"我已完成支付" —— 演示环境调用 mock-pay，生产环境只查询状态 */
async function handleMockPay() {
  if (!payOrder.value) return;
  try {
    const quota = await mockPayOrderApi(payOrder.value.orderId);
    payStatus.value = 'paid';
    stopPolling();
    currentPlan.value = quota.planType ?? currentPlan.value;
    message.success(`套餐已生效：${quota.planType}（到期 ${quota.endDate}）`);
  } catch (error: any) {
    message.error(error?.message ?? '支付确认失败');
  }
}

/** 关闭支付弹窗 */
function handleCloseModal() {
  stopPolling();
  payVisible.value = false;
  payOrder.value = null;
  payStatus.value = 'pending';
}

onMounted(loadData);
onUnmounted(stopPolling);
</script>

<template>
  <div class="recharge-page">
    <header class="hero">
      <h2>充值中心</h2>
      <p>选择套餐后扫码支付（演示环境点击"我已完成支付"即可立即生效）</p>
      <div class="current">当前套餐：<b>{{ currentPlan }}</b></div>
    </header>

    <div v-if="loading" class="loading">加载中...</div>

    <div v-else class="plan-grid">
      <div
        v-for="plan in sortedPlans"
        :key="plan.planType"
        class="plan-card"
        :class="{ active: currentPlan === plan.planType }"
      >
        <div class="plan-badge" v-if="currentPlan === plan.planType">当前套餐</div>
        <div class="title">{{ plan.name }}</div>
        <div class="meta">{{ plan.planType }}</div>
        <div class="quota">可生成页面：<b>{{ plan.maxPages === -1 ? '无限' : plan.maxPages }}</b> 个</div>
        <div class="duration">有效期：<b>{{ plan.durationDays }}</b> 天</div>
        <button
          class="btn"
          :disabled="submittingPlan !== ''"
          @click="handleRecharge(plan.planType)"
        >
          {{ submittingPlan === plan.planType ? '生成中...' : currentPlan === plan.planType ? '续费该套餐' : '选择此套餐' }}
        </button>
      </div>
    </div>

    <!-- 支付弹窗 -->
    <div v-if="payVisible" class="modal-mask" @click.self="handleCloseModal">
      <div class="modal-box">
        <button class="close-btn" @click="handleCloseModal">✕</button>

        <template v-if="payStatus === 'pending'">
          <h3 class="modal-title">微信扫码支付</h3>
          <p class="modal-sub">套餐：{{ payOrder?.planName }}（{{ payOrder?.planType }}）</p>
          <div class="qr-wrap">
            <img
              v-if="qrCodeUrl"
              :src="qrCodeUrl"
              alt="支付二维码"
              class="qr-img"
            />
            <div v-else class="qr-placeholder">二维码加载中...</div>
          </div>
          <p class="qr-hint">演示环境 · 请点击下方按钮模拟支付</p>
          <button class="confirm-btn" @click="handleMockPay">我已完成支付</button>
          <p class="polling-tip" v-if="polling">正在等待支付结果...</p>
        </template>

        <template v-else>
          <div class="success-icon">✓</div>
          <h3 class="modal-title">支付成功</h3>
          <p class="modal-sub">套餐 <b>{{ payOrder?.planName }}</b> 已生效</p>
          <p class="modal-sub">当前套餐：<b>{{ currentPlan }}</b></p>
          <button class="confirm-btn" @click="handleCloseModal">完成</button>
        </template>
      </div>
    </div>
  </div>
</template>

<style scoped>
.recharge-page { padding: 16px; }
.hero { margin-bottom: 20px; }
.hero h2 { font-size: 20px; font-weight: 700; margin: 0 0 4px; }
.hero p { color: #8c8c8c; font-size: 13px; margin: 0 0 8px; }
.current { font-size: 14px; color: #1677ff; }

.plan-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}
@media (max-width: 480px) {
  .plan-grid { grid-template-columns: 1fr; }
}

.plan-card {
  position: relative;
  border: 1.5px solid #e8e8e8;
  border-radius: 12px;
  padding: 16px;
  background: #fff;
  transition: border-color .2s, box-shadow .2s;
}
.plan-card.active {
  border-color: #1677ff;
  box-shadow: 0 0 0 3px rgba(22,119,255,.12);
}
.plan-badge {
  position: absolute;
  top: 10px; right: 10px;
  background: #1677ff;
  color: #fff;
  font-size: 11px;
  border-radius: 4px;
  padding: 1px 6px;
}
.title { font-size: 17px; font-weight: 700; }
.meta { color: #aaa; font-size: 12px; margin-top: 2px; }
.quota, .duration { margin-top: 10px; font-size: 13px; color: #333; }
.btn {
  margin-top: 14px;
  width: 100%;
  border: none;
  background: #1677ff;
  color: #fff;
  border-radius: 8px;
  padding: 9px 10px;
  font-size: 14px;
  cursor: pointer;
  transition: opacity .15s;
}
.btn:disabled { opacity: .5; cursor: not-allowed; }
.btn:not(:disabled):hover { opacity: .85; }

.loading { color: #8c8c8c; }

/* 支付弹窗 */
.modal-mask {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}
.modal-box {
  position: relative;
  background: #fff;
  border-radius: 14px;
  padding: 28px 28px 24px;
  width: 320px;
  text-align: center;
  box-shadow: 0 8px 32px rgba(0,0,0,.18);
}
.close-btn {
  position: absolute;
  top: 12px; right: 14px;
  border: none;
  background: transparent;
  font-size: 16px;
  color: #999;
  cursor: pointer;
  line-height: 1;
}
.modal-title { font-size: 17px; font-weight: 700; margin: 0 0 6px; }
.modal-sub { font-size: 13px; color: #666; margin: 4px 0; }
.qr-wrap {
  margin: 14px auto;
  width: 200px;
  height: 200px;
  border: 1px solid #f0f0f0;
  border-radius: 8px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}
.qr-img { width: 200px; height: 200px; display: block; }
.qr-placeholder { color: #bbb; font-size: 13px; }
.qr-hint { font-size: 12px; color: #bbb; margin: 4px 0 12px; }
.confirm-btn {
  width: 100%;
  border: none;
  background: #07c160;
  color: #fff;
  border-radius: 8px;
  padding: 10px;
  font-size: 15px;
  cursor: pointer;
  margin-top: 4px;
  transition: opacity .15s;
}
.confirm-btn:hover { opacity: .88; }
.polling-tip { font-size: 12px; color: #aaa; margin-top: 10px; }

/* 支付成功 */
.success-icon {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: #07c160;
  color: #fff;
  font-size: 28px;
  line-height: 56px;
  margin: 0 auto 14px;
}
</style>
