<script lang="ts" setup>
// 引入密钥相关接口类型定义
import type { AuthApi } from '#/api';

// Modal：弹出确认框；message：全局轻提示
import { Modal, message } from 'ant-design-vue';
// computed：计算属性；onMounted：挂载钩子；ref：响应式变量
import { computed, onMounted, ref } from 'vue';

// 密钥管理相关 API
import {
  createRegisterKeyApi,        // 生成新注册密钥
  deleteRegisterKeyApi,        // 删除指定密钥
  getRegisterKeysApi,          // 获取密钥列表（支持筛选）
  updateRegisterKeyExpiresApi, // 更新密钥有效期
} from '#/api';

type RegisterRole = 'admin' | 'super' | 'user';

// ---- 生成密钥 ----
const role = ref<RegisterRole>('user');
const generating = ref(false);
const lastKey = ref('');

const roleLabel = computed(() => {
  if (role.value === 'admin') return '管理员';
  if (role.value === 'super') return 'Super 权限';
  return '普通用户';
});

async function generateKey() {
  generating.value = true;
  try {
    const data = await createRegisterKeyApi({ role: role.value });
    lastKey.value = data.registerKey;
    await navigator.clipboard.writeText(data.registerKey);
    message.success(`已生成 ${roleLabel.value} 密钥并复制到剪贴板`);
    await loadKeys();
  } finally {
    generating.value = false;
  }
}

// ---- 密钥列表 ----
const keys = ref<AuthApi.RegisterKeyResult[]>([]);
const loading = ref(false);
const filterRole = ref('');
const filterUsed = ref<'' | 'yes' | 'no'>('');
const filterKeyword = ref('');

async function loadKeys() {
  loading.value = true;
  try {
    keys.value = await getRegisterKeysApi({
      role: filterRole.value || undefined,
      used: (filterUsed.value as any) || undefined,
      keyword: filterKeyword.value || undefined,
    });
  } finally {
    loading.value = false;
  }
}

function handleDelete(k: AuthApi.RegisterKeyResult) {
  Modal.confirm({
    title: '确认删除密钥',
    content: `删除密钥 ${k.registerKey} 后不可恢复，是否继续？`,
    async onOk() {
      await deleteRegisterKeyApi(k.id);
      message.success('密钥已删除');
      await loadKeys();
    },
  });
}

// ---- 有效期弹窗 ----
const expiresKey = ref<AuthApi.RegisterKeyResult | null>(null);
const expiresDraft = ref('');
const submittingExpires = ref(false);

function openExpiresDialog(k: AuthApi.RegisterKeyResult) {
  expiresKey.value = k;
  expiresDraft.value = k.expiresAt ? k.expiresAt.slice(0, 16) : '';
}
function closeExpiresDialog() {
  expiresKey.value = null;
  expiresDraft.value = '';
}
async function submitExpires() {
  if (!expiresKey.value) return;
  submittingExpires.value = true;
  try {
    await updateRegisterKeyExpiresApi(expiresKey.value.id, {
      expires_at: expiresDraft.value ? new Date(expiresDraft.value).toISOString() : null,
    });
    message.success('有效期已更新');
    closeExpiresDialog();
    await loadKeys();
  } finally {
    submittingExpires.value = false;
  }
}

function formatDate(d: string | null) {
  if (!d) return '—';
  return new Date(d).toLocaleString('zh-CN');
}

onMounted(loadKeys);
</script>

<template>
  <div class="page">
    <h2>密钥管理</h2>

    <!-- 生成面板 -->
    <div class="panel">
      <h3>生成新密钥</h3>
      <div class="gen-row">
        <select v-model="role" class="input sel">
          <option value="user">普通用户（user）</option>
          <option value="super">Super 权限（super）</option>
          <option value="admin">管理员（admin）</option>
        </select>
        <button class="btn" :disabled="generating" @click="generateKey">
          {{ generating ? '生成中...' : `生成 ${roleLabel} 密钥` }}
        </button>
      </div>
      <p v-if="lastKey" class="last-key">
        最新密钥：<b>{{ lastKey }}</b>
        <span class="copy-tip">已自动复制到剪贴板</span>
      </p>
      <p class="tip">密钥是一次性的，注册成功后自动失效。</p>
    </div>

    <!-- 筛选栏 -->
    <div class="toolbar">
      <input
        v-model="filterKeyword"
        class="input"
        placeholder="搜索密钥/被使用者"
        style="width:200px"
      />
      <select v-model="filterRole" class="input sel">
        <option value="">全部角色</option>
        <option value="user">user</option>
        <option value="super">super</option>
        <option value="admin">admin</option>
      </select>
      <select v-model="filterUsed" class="input sel">
        <option value="">全部状态</option>
        <option value="no">未使用</option>
        <option value="yes">已使用</option>
      </select>
      <button class="btn" :disabled="loading" @click="loadKeys">
        {{ loading ? '查询中...' : '查询' }}
      </button>
    </div>

    <!-- 密钥表格 -->
    <div class="table-wrap">
      <table class="table">
        <thead>
          <tr>
            <th>密钥</th>
            <th>角色</th>
            <th>创建人</th>
            <th>使用者</th>
            <th>使用时间</th>
            <th>过期时间</th>
            <th>状态</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="k in keys" :key="k.id" :class="{ 'row-expired': k.expired }">
            <td class="mono">{{ k.registerKey }}</td>
            <td><span class="role-tag" :class="k.role">{{ k.role }}</span></td>
            <td>{{ k.createdBy }}</td>
            <td>{{ k.usedBy ?? '—' }}</td>
            <td class="small">{{ formatDate(k.usedAt) }}</td>
            <td class="small">
              <span :class="k.expired ? 'tag-expired' : ''">
                {{ k.expiresAt ? formatDate(k.expiresAt) : '永久有效' }}
              </span>
            </td>
            <td>
              <span v-if="k.expired" class="tag-off">已过期</span>
              <span v-else-if="k.usedBy" class="tag-used">已使用</span>
              <span v-else class="tag-on">可用</span>
            </td>
            <td class="actions">
              <button class="btn btn-sm btn-blue" @click="openExpiresDialog(k)">有效期</button>
              <button class="btn btn-sm btn-danger" @click="handleDelete(k)">删除</button>
            </td>
          </tr>
          <tr v-if="keys.length === 0">
            <td colspan="8" class="empty">暂无密钥数据</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 有效期弹窗 -->
    <div v-if="expiresKey" class="mask" @click.self="closeExpiresDialog">
      <div class="dialog">
        <h3>设置有效期</h3>
        <p class="hint">密钥：<b>{{ expiresKey.registerKey }}</b></p>
        <label class="flabel">过期时间（留空表示永久有效）</label>
        <input
          v-model="expiresDraft"
          type="datetime-local"
          class="input"
          style="width:100%;box-sizing:border-box"
        />
        <div class="dialog-actions">
          <button class="btn btn-ghost" @click="closeExpiresDialog">取消</button>
          <button class="btn" :disabled="submittingExpires" @click="submitExpires">
            {{ submittingExpires ? '保存中...' : '确认保存' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page { padding: 20px; }

.panel {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 16px 20px;
  margin-bottom: 16px;
  max-width: 700px;
}

.panel h3 { margin: 0 0 12px; font-size: 15px; }

.gen-row { display: flex; gap: 10px; align-items: center; }

.last-key {
  margin-top: 10px;
  word-break: break-all;
  font-size: 13px;
}

.copy-tip {
  margin-left: 8px;
  font-size: 11px;
  color: #16a34a;
  background: #dcfce7;
  padding: 1px 6px;
  border-radius: 99px;
}

.tip { margin-top: 8px; color: #9ca3af; font-size: 12px; }

.toolbar {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.input {
  height: 34px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  padding: 0 10px;
  font-size: 13px;
}

.sel { padding: 0 6px; }

.table-wrap {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  overflow: auto;
}

.table { width: 100%; border-collapse: collapse; }

.table th,
.table td {
  border-bottom: 1px solid #f1f5f9;
  padding: 9px 11px;
  white-space: nowrap;
  text-align: left;
}

.table th { background: #f8fafc; font-weight: 600; }
.small { font-size: 12px; color: #555; }
.mono { font-family: monospace; font-size: 13px; }
.empty { text-align: center !important; color: #9ca3af; padding: 20px; }

.row-expired { opacity: 0.55; }

.role-tag {
  display: inline-block;
  padding: 1px 8px;
  border-radius: 99px;
  font-size: 11px;
  background: #dbeafe;
  color: #1d4ed8;
}
.role-tag.admin { background: #fef9c3; color: #92400e; }
.role-tag.super { background: #fce7f3; color: #9d174d; }

.actions { display: flex; gap: 6px; }

.btn {
  border: none;
  background: #1677ff;
  color: #fff;
  border-radius: 8px;
  height: 34px;
  padding: 0 12px;
  cursor: pointer;
  font-size: 13px;
}
.btn:disabled { opacity: 0.65; cursor: not-allowed; }
.btn-sm { height: 28px; padding: 0 10px; font-size: 12px; }
.btn-danger { background: #dc2626; }
.btn-blue { background: #7c3aed; }
.btn-ghost { background: #e5e7eb; color: #111827; }

.tag-on { display:inline-block;padding:1px 8px;border-radius:99px;font-size:11px;background:#dcfce7;color:#15803d; }
.tag-used { display:inline-block;padding:1px 8px;border-radius:99px;font-size:11px;background:#dbeafe;color:#1d4ed8; }
.tag-off { display:inline-block;padding:1px 8px;border-radius:99px;font-size:11px;background:#fee2e2;color:#dc2626; }
.tag-expired { color: #dc2626; font-weight: 600; }

.mask {
  position: fixed;
  inset: 0;
  background: rgb(0 0 0 / 38%);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.dialog {
  width: 420px;
  background: #fff;
  border-radius: 12px;
  padding: 24px;
}

.dialog h3 { margin: 0 0 10px; }
.hint { color: #6b7280; font-size: 13px; margin: 0 0 12px; }
.flabel { display:block;font-size:13px;color:#374151;margin:10px 0 6px; }

.dialog-actions {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
</style>
