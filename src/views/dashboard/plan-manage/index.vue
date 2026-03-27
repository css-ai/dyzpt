<script lang="ts" setup>
import { computed, onMounted, ref } from 'vue';
import { message } from 'ant-design-vue';

import {
  getPlansApi,
  getUsersApi,
  updateUserPlanApi,
  type AuthApi,
} from '#/api';

const loading = ref(false);
const plans = ref<AuthApi.PlanItem[]>([]);
const users = ref<AuthApi.UserManageItem[]>([]);
const keyword = ref('');
const role = ref('');
const submittingUserId = ref('');

const sortedPlans = computed(() => {
  const order = ['free', 'basic', 'pro', 'enterprise'];
  return [...plans.value].sort(
    (a, b) => order.indexOf(a.planType) - order.indexOf(b.planType),
  );
});

async function loadData() {
  loading.value = true;
  try {
    const [planList, userList] = await Promise.all([
      getPlansApi(),
      getUsersApi({ keyword: keyword.value || undefined, role: role.value || undefined }),
    ]);
    plans.value = planList;
    users.value = userList;
  } finally {
    loading.value = false;
  }
}

async function handleUpdatePlan(
  user: AuthApi.UserManageItem,
  planType: AuthApi.PlanItem['planType'],
) {
  if (submittingUserId.value) return;
  submittingUserId.value = user.userId;
  try {
    await updateUserPlanApi(user.userId, { plan_type: planType });
    message.success(`已将 ${user.username} 套餐修改为 ${planType}`);
    await loadData();
  } catch (error: any) {
    message.error(error?.message ?? '修改套餐失败');
  } finally {
    submittingUserId.value = '';
  }
}

onMounted(loadData);
</script>

<template>
  <div class="plan-manage-page">
    <div class="header">
      <h2>套餐管理</h2>
      <p>仅管理员可直接为用户调整套餐</p>
    </div>

    <div class="filters">
      <input v-model="keyword" placeholder="按用户名搜索" class="input" />
      <select v-model="role" class="input">
        <option value="">全部角色</option>
        <option value="user">user</option>
        <option value="super">super</option>
        <option value="admin">admin</option>
      </select>
      <button class="btn" @click="loadData">查询</button>
    </div>

    <div v-if="loading" class="loading">加载中...</div>

    <table v-else class="table">
      <thead>
        <tr>
          <th>用户名</th>
          <th>角色</th>
          <th>当前套餐</th>
          <th>可生成页数</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="user in users" :key="user.userId">
          <td>{{ user.username }}</td>
          <td>{{ user.roles.join(', ') }}</td>
          <td>{{ user.quota?.planType ?? 'free' }}</td>
          <td>{{ user.quota.maxPages === -1 ? '无限' : user.quota.maxPages }}</td>
          <td>
            <div class="actions">
              <button
                v-for="plan in sortedPlans"
                :key="plan.planType"
                class="mini-btn"
                :disabled="submittingUserId !== ''"
                @click="handleUpdatePlan(user, plan.planType)"
              >
                {{ plan.planType }}
              </button>
            </div>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
.plan-manage-page { padding: 16px; }
.header { margin-bottom: 12px; }
.filters { display: flex; gap: 8px; margin-bottom: 12px; }
.input { border: 1px solid #d9d9d9; border-radius: 6px; padding: 6px 10px; }
.btn { border: none; background: #1677ff; color: #fff; border-radius: 6px; padding: 6px 12px; cursor: pointer; }
.loading { color: #8c8c8c; }
.table { width: 100%; border-collapse: collapse; background: #fff; }
.table th, .table td { border: 1px solid #f0f0f0; padding: 8px; text-align: left; }
.actions { display: flex; flex-wrap: wrap; gap: 6px; }
.mini-btn { border: 1px solid #d9d9d9; background: #fafafa; border-radius: 6px; padding: 4px 8px; cursor: pointer; }
</style>

