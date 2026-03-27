<script lang="ts" setup>
// 引入用户管理相关接口类型定义
import type { AuthApi } from '#/api';

// Modal：弹出确认框；message：全局轻提示
import { Modal, message } from 'ant-design-vue';
// computed：计算属性；onMounted：挂载钩子；ref：响应式变量
import { computed, onMounted, ref } from 'vue';

// 用户与页面管理相关 API
import {
  batchDeleteUsersApi,    // 批量删除用户
  deletePageByAdminApi,   // 管理员删除指定页面
  deleteUserApi,          // 删除单个用户
  getOperationLogsApi,    // 获取操作日志列表
  getRegisterStatsApi,    // 获取注册统计数据
  getUserPagesApi,        // 获取指定用户的页面列表
  getUsersApi,            // 获取用户列表（支持筛选）
  togglePageStatusApi,    // 切换页面展示状态
  updateUserPasswordApi,  // 修改用户密码
  updateUserQuotaApi,     // 更新用户页面配额
} from '#/api';

const loading = ref(false);
const submitting = ref(false);
const activeTab = ref<'users' | 'logs'>('users');

const stats = ref({ adminUsers: 0, superUsers: 0, totalUsers: 0 });
const users = ref<AuthApi.UserManageItem[]>([]);

// ---- 搜索筛选 ----
const filterKeyword = ref('');
const filterRole = ref('');

// ---- 批量选择 ----
const selectedIds = ref<Set<string>>(new Set());
const allSelected = computed(
  () => users.value.length > 0 && users.value.every((u) => selectedIds.value.has(u.userId)),
);

function toggleSelectAll() {
  if (allSelected.value) {
    selectedIds.value = new Set();
  } else {
    selectedIds.value = new Set(users.value.map((u) => u.userId));
  }
}

function toggleSelect(id: string) {
  const s = new Set(selectedIds.value);
  if (s.has(id)) s.delete(id);
  else s.add(id);
  selectedIds.value = s;
}

// ---- 改密弹窗 ----
const pwdUser = ref<AuthApi.UserManageItem | null>(null);
const passwordDraft = ref('');
const canSubmitPwd = computed(() => passwordDraft.value.trim().length >= 6);

// ---- 配额弹窗 ----
const quotaUser = ref<AuthApi.UserManageItem | null>(null);
const quotaDraft = ref({ maxPages: 1, startDate: '', endDate: '' });
const today = new Date().toISOString().slice(0, 10);

// ---- 页面管理弹窗 ----
const pagesUser = ref<AuthApi.UserManageItem | null>(null);
const userPages = ref<AuthApi.UserPageItem[]>([]);
const pagesLoading = ref(false);

// ---- 删除页面确认框 ----
const deletingPage = ref<AuthApi.UserPageItem | null>(null);
const deleteCountdown = ref(10);
let countdownTimer: ReturnType<typeof setInterval> | null = null;

function openDeletePageDialog(page: AuthApi.UserPageItem) {
  deletingPage.value = page;
  deleteCountdown.value = 10;
  if (countdownTimer) clearInterval(countdownTimer);
  countdownTimer = setInterval(() => {
    deleteCountdown.value--;
    if (deleteCountdown.value <= 0) {
      clearInterval(countdownTimer!);
      countdownTimer = null;
    }
  }, 1000);
}

function closeDeletePageDialog() {
  deletingPage.value = null;
  deleteCountdown.value = 10;
  if (countdownTimer) {
    clearInterval(countdownTimer);
    countdownTimer = null;
  }
}

async function confirmDeletePage() {
  if (!deletingPage.value || deleteCountdown.value > 0) return;
  try {
    await deletePageByAdminApi(deletingPage.value.id);
    message.success(`页面「${deletingPage.value.siteName}」已删除`);
    userPages.value = userPages.value.filter((p) => p.id !== deletingPage.value!.id);
    closeDeletePageDialog();
  } catch (e: any) {
    message.error(e?.message ?? '删除失败');
  }
}

// ---- 操作日志 ----
const logs = ref<AuthApi.OperationLog[]>([]);
const logsLoading = ref(false);
const logTotal = ref(0);
const logPage = ref(1);
const logKeyword = ref('');
const logAction = ref('');

async function loadData() {
  loading.value = true;
  selectedIds.value = new Set();
  try {
    const [statsData, usersData] = await Promise.all([
      getRegisterStatsApi(),
      getUsersApi({
        keyword: filterKeyword.value || undefined,
        role: filterRole.value || undefined,
      }),
    ]);
    stats.value = statsData;
    users.value = usersData;
  } finally {
    loading.value = false;
  }
}

async function loadLogs() {
  logsLoading.value = true;
  try {
    const res = await getOperationLogsApi({
      page: logPage.value,
      page_size: 50,
      operator: logKeyword.value || undefined,
      action: logAction.value || undefined,
    });
    logs.value = res.list;
    logTotal.value = res.total;
  } finally {
    logsLoading.value = false;
  }
}

async function switchTab(tab: 'users' | 'logs') {
  activeTab.value = tab;
  if (tab === 'logs' && logs.value.length === 0) {
    await loadLogs();
  }
}

// ---------- 密码 ----------
function openPwdDialog(u: AuthApi.UserManageItem) {
  pwdUser.value = u;
  passwordDraft.value = '';
}
function closePwdDialog() {
  pwdUser.value = null;
  passwordDraft.value = '';
}
async function submitPassword() {
  if (!pwdUser.value || !canSubmitPwd.value) return;
  submitting.value = true;
  try {
    await updateUserPasswordApi(pwdUser.value.userId, {
      password: passwordDraft.value.trim(),
    });
    message.success(`用户 ${pwdUser.value.username} 密码已修改`);
    closePwdDialog();
  } finally {
    submitting.value = false;
  }
}

// ---------- 删除 ----------
function handleDelete(u: AuthApi.UserManageItem) {
  Modal.confirm({
    title: '确认删除用户',
    content: `删除用户 ${u.username} 后不可恢复，是否继续？`,
    async onOk() {
      await deleteUserApi(u.userId);
      message.success(`已删除用户 ${u.username}`);
      await loadData();
    },
  });
}

// ---------- 批量删除 ----------
function handleBatchDelete() {
  if (selectedIds.value.size === 0) {
    message.warning('请先选择要删除的用户');
    return;
  }
  Modal.confirm({
    title: '确认批量删除',
    content: `将删除选中的 ${selectedIds.value.size} 个用户，不可恢复，是否继续？`,
    async onOk() {
      const res = await batchDeleteUsersApi([...selectedIds.value]);
      message.success(`成功删除 ${res.deleted.length} 个用户`);
      await loadData();
    },
  });
}

// ---------- 配额 ----------
function openQuotaDialog(u: AuthApi.UserManageItem) {
  quotaUser.value = u;
  const currentMax = u.quota?.maxPages ?? 1;
  quotaDraft.value = {
    maxPages: currentMax === -1 ? 999 : currentMax,
    startDate: u.quota?.startDate ?? today,
    endDate: u.quota?.endDate ?? '',
  };
}
function closeQuotaDialog() { quotaUser.value = null; }
async function submitQuota() {
  if (!quotaUser.value) return;
  submitting.value = true;
  try {
    await updateUserQuotaApi(quotaUser.value.userId, {
      max_pages: quotaDraft.value.maxPages,
      start_date: quotaDraft.value.startDate || today,
      end_date: quotaDraft.value.endDate || null,
    });
    message.success(`用户 ${quotaUser.value.username} 配额已更新`);
    closeQuotaDialog();
    await loadData();
  } finally {
    submitting.value = false;
  }
}

// ---------- 页面 ----------
async function openPagesDialog(u: AuthApi.UserManageItem) {
  pagesUser.value = u;
  userPages.value = [];
  pagesLoading.value = true;
  try {
    userPages.value = await getUserPagesApi(u.userId);
  } finally {
    pagesLoading.value = false;
  }
}
function closePagesDialog() {
  pagesUser.value = null;
  userPages.value = [];
}
async function handleToggleStatus(page: AuthApi.UserPageItem) {
  const res = await togglePageStatusApi(page.id);
  page.status = res.status;
  const action = res.status === 'published' ? '已启动' : '已停止';
  message.success(`页面「${page.siteName}」${action}`);
}

function actionLabel(action: string) {
  const map: Record<string, string> = {
    reset_password: '重置密码',
    update_password: '改密',
    delete_user: '删除用户',
    batch_delete_users: '批量删除',
    update_quota: '更新配额',
    toggle_page_status: '切换页面状态',
    delete_key: '删除密钥',
    update_key_expires: '更新密钥有效期',
  };
  return map[action] ?? action;
}

onMounted(loadData);
</script>

<template>
  <div class="page">
    <h2>注册统计 &amp; 用户管理</h2>

    <!-- 统计卡片 -->
    <div class="cards">
      <div class="card">
        <div class="clabel">总注册用户</div>
        <div class="cvalue">{{ stats.totalUsers }}</div>
      </div>
      <div class="card">
        <div class="clabel">管理员注册数</div>
        <div class="cvalue">{{ stats.adminUsers }}</div>
      </div>
      <div class="card">
        <div class="clabel">Super 权限注册数</div>
        <div class="cvalue">{{ stats.superUsers }}</div>
      </div>
    </div>

    <!-- Tab 切换 -->
    <div class="tabs">
      <button :class="['tab-btn', activeTab === 'users' && 'active']" @click="switchTab('users')">用户管理</button>
      <button :class="['tab-btn', activeTab === 'logs' && 'active']" @click="switchTab('logs')">操作日志</button>
    </div>

    <!-- 用户管理 Tab -->
    <div v-if="activeTab === 'users'">
      <div class="toolbar">
        <input v-model="filterKeyword" class="input" placeholder="搜索用户名/姓名" style="width:180px" />
        <select v-model="filterRole" class="input sel">
          <option value="">全部角色</option>
          <option value="user">user</option>
          <option value="super">super</option>
          <option value="admin">admin</option>
        </select>
        <button class="btn" :disabled="loading" @click="loadData">{{ loading ? '查询中...' : '查询' }}</button>
        <button
          class="btn btn-danger"
          :disabled="selectedIds.size === 0"
          @click="handleBatchDelete"
        >批量删除({{ selectedIds.size }})</button>
      </div>

      <div class="table-wrap">
        <table class="table">
          <thead>
            <tr>
              <th><input type="checkbox" :checked="allSelected" @change="toggleSelectAll" /></th>
              <th>用户名</th>
              <th>姓名</th>
              <th>角色</th>
              <th>已生成页面</th>
              <th>最大配额</th>
              <th>配额有效期</th>
              <th>注册时间</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="u in users" :key="u.userId" :class="{ selected: selectedIds.has(u.userId) }">
              <td><input type="checkbox" :checked="selectedIds.has(u.userId)" @change="toggleSelect(u.userId)" /></td>
              <td>{{ u.username }}</td>
              <td>{{ u.realName }}</td>
              <td>
                <span v-for="r in u.roles" :key="r" class="role-tag" :class="r">{{ r }}</span>
              </td>
              <td class="center">{{ u.pageCount }}</td>
              <td class="center">{{ u.quota?.maxPages === -1 ? '无限' : (u.quota?.maxPages ?? 1) }}</td>
              <td class="small">
                <template v-if="u.quota">{{ u.quota.startDate ?? '—' }} ~ {{ u.quota.endDate ?? '永久' }}</template>
                <template v-else>默认</template>
              </td>
              <td class="small">{{ new Date(u.createdAt).toLocaleString('zh-CN') }}</td>
              <td class="actions">
                <button class="btn btn-sm btn-page" @click="openPagesDialog(u)">页面</button>
                <button class="btn btn-sm" @click="openQuotaDialog(u)">配额</button>
                <button class="btn btn-sm" @click="openPwdDialog(u)">改密</button>
                <button class="btn btn-sm btn-danger" @click="handleDelete(u)">删除</button>
              </td>
            </tr>
            <tr v-if="users.length === 0">
              <td colspan="9" class="empty">暂无用户数据</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 操作日志 Tab -->
    <div v-if="activeTab === 'logs'">
      <div class="toolbar">
        <input v-model="logKeyword" class="input" placeholder="操作人" style="width:150px" />
        <select v-model="logAction" class="input sel">
          <option value="">全部操作</option>
          <option value="reset_password">重置密码</option>
          <option value="update_password">改密</option>
          <option value="delete_user">删除用户</option>
          <option value="batch_delete_users">批量删除</option>
          <option value="update_quota">更新配额</option>
          <option value="toggle_page_status">切换页面状态</option>
          <option value="delete_key">删除密钥</option>
          <option value="update_key_expires">更新密钥有效期</option>
        </select>
        <button class="btn" :disabled="logsLoading" @click="loadLogs">{{ logsLoading ? '查询中...' : '查询' }}</button>
      </div>
      <div class="table-wrap">
        <table class="table">
          <thead>
            <tr><th>操作人</th><th>操作类型</th><th>目标</th><th>详情</th><th>时间</th></tr>
          </thead>
          <tbody>
            <tr v-for="log in logs" :key="log.id">
              <td>{{ log.operator }}</td>
              <td><span class="action-tag">{{ actionLabel(log.action) }}</span></td>
              <td class="small">{{ log.target || '—' }}</td>
              <td class="small">{{ log.detail || '—' }}</td>
              <td class="small">{{ new Date(log.createdAt).toLocaleString('zh-CN') }}</td>
            </tr>
            <tr v-if="logs.length === 0">
              <td colspan="5" class="empty">{{ logsLoading ? '加载中...' : '暂无日志' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-if="logTotal > 50" class="log-pages">
        共 {{ logTotal }} 条 &nbsp;
        <button class="btn btn-sm btn-ghost" :disabled="logPage <= 1" @click="logPage--; loadLogs()">上一页</button>
        <span style="margin:0 8px">第 {{ logPage }} 页</span>
        <button class="btn btn-sm btn-ghost" :disabled="logs.length < 50" @click="logPage++; loadLogs()">下一页</button>
      </div>
    </div>

    <!-- 页面管理弹窗 -->
    <div v-if="pagesUser" class="mask" @click.self="closePagesDialog">
      <div class="dialog dialog-wide">
        <h3>页面管理：{{ pagesUser.username }}</h3>
        <p v-if="pagesLoading" class="hint">加载中...</p>
        <p v-else-if="userPages.length === 0" class="hint">该用户暂无生成的页面</p>
        <table v-else class="table">
          <thead><tr><th>页面名称</th><th>绑定域名</th><th>状态</th><th>操作</th></tr></thead>
          <tbody>
            <tr v-for="page in userPages" :key="page.id">
              <td>{{ page.siteName }}</td>
              <td class="small">{{ page.bindDomain }}</td>
              <td><span :class="page.status === 'published' ? 'tag-on' : 'tag-off'">{{ page.status === 'published' ? '展示中' : '已停止' }}</span></td>
              <td>
                <button class="btn btn-sm" :class="page.status === 'published' ? 'btn-danger' : 'btn-green'" @click="handleToggleStatus(page)">
                  {{ page.status === 'published' ? '停止展示' : '启动展示' }}
                </button>
                <button class="btn btn-sm btn-danger" style="margin-left:6px" @click="openDeletePageDialog(page)">删除</button>
              </td>
            </tr>
          </tbody>
        </table>
        <div class="dialog-actions"><button class="btn btn-ghost" @click="closePagesDialog">关闭</button></div>
      </div>
    </div>

    <!-- 删除页面确认弹窗（10秒倒计时）-->
    <div v-if="deletingPage" class="mask" @click.self="closeDeletePageDialog">
      <div class="dialog dialog-delete">
        <div class="delete-icon">⚠️</div>
        <h3 class="delete-title">确定要删除页面吗？</h3>
        <p class="delete-desc">
          即将删除页面 <b>「{{ deletingPage.siteName }}」</b>，此操作不可恢复。
        </p>
        <div v-if="deleteCountdown > 0" class="countdown-bar">
          <div class="countdown-fill" :style="{ width: ((10 - deleteCountdown) / 10 * 100) + '%' }"></div>
        </div>
        <p v-if="deleteCountdown > 0" class="countdown-tip">
          请等待 <b>{{ deleteCountdown }}</b> 秒后才能确认删除
        </p>
        <div class="delete-actions">
          <button class="btn-cancel" @click="closeDeletePageDialog">取消</button>
          <button
            class="btn-confirm"
            :disabled="deleteCountdown > 0"
            :class="{ 'btn-confirm-disabled': deleteCountdown > 0 }"
            @click="confirmDeletePage"
          >
            {{ deleteCountdown > 0 ? `确定（${deleteCountdown}s）` : '确定删除' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 配额弹窗 -->
    <div v-if="quotaUser" class="mask" @click.self="closeQuotaDialog">
      <div class="dialog">
        <h3>配额管理：{{ quotaUser.username }}</h3>
        <p class="hint">当前已生成 <b>{{ quotaUser.pageCount }}</b> 个页面</p>
        <label class="flabel">最大页面数</label>
        <input v-model.number="quotaDraft.maxPages" class="input full" type="number" min="0" />
        <label class="flabel">开始日期</label>
        <input v-model="quotaDraft.startDate" class="input full" type="date" />
        <label class="flabel">结束日期（留空=永久）</label>
        <input v-model="quotaDraft.endDate" class="input full" type="date" />
        <div class="dialog-actions">
          <button class="btn btn-ghost" @click="closeQuotaDialog">取消</button>
          <button class="btn" :disabled="submitting" @click="submitQuota">{{ submitting ? '保存中...' : '保存配额' }}</button>
        </div>
      </div>
    </div>

    <!-- 改密弹窗 -->
    <div v-if="pwdUser" class="mask" @click.self="closePwdDialog">
      <div class="dialog">
        <h3>修改密码：{{ pwdUser.username }}</h3>
        <input v-model="passwordDraft" class="input full" type="password" placeholder="请输入新密码（至少6位）" />
        <div class="dialog-actions">
          <button class="btn btn-ghost" @click="closePwdDialog">取消</button>
          <button class="btn" :disabled="!canSubmitPwd || submitting" @click="submitPassword">{{ submitting ? '提交中...' : '确认修改' }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page { padding: 20px; }
.cards { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; margin-bottom: 14px; }
.card { background: #fff; border: 1px solid #e5e7eb; border-radius: 10px; padding: 14px; }
.clabel { font-size: 13px; color: #6b7280; }
.cvalue { margin-top: 8px; font-size: 30px; font-weight: 700; }
.tabs { display: flex; gap: 0; margin-bottom: 14px; border-bottom: 2px solid #e5e7eb; }
.tab-btn { border: none; background: none; padding: 8px 20px; font-size: 14px; cursor: pointer; color: #6b7280; border-bottom: 2px solid transparent; margin-bottom: -2px; }
.tab-btn.active { color: #1677ff; border-bottom-color: #1677ff; font-weight: 600; }
.toolbar { display: flex; gap: 8px; align-items: center; margin-bottom: 12px; flex-wrap: wrap; }
.table-wrap { background: #fff; border: 1px solid #e5e7eb; border-radius: 10px; overflow: auto; }
.table { width: 100%; border-collapse: collapse; }
.table th, .table td { border-bottom: 1px solid #f1f5f9; padding: 9px 11px; white-space: nowrap; text-align: left; }
.table th { background: #f8fafc; font-weight: 600; }
.center { text-align: center; }
.small { font-size: 12px; color: #555; }
.empty { text-align: center !important; color: #9ca3af; padding: 20px; }
.selected { background: #eff6ff; }
.role-tag { display: inline-block; padding: 1px 7px; border-radius: 99px; font-size: 11px; margin-right: 4px; background: #dbeafe; color: #1d4ed8; }
.role-tag.admin { background: #fef9c3; color: #92400e; }
.role-tag.super { background: #fce7f3; color: #9d174d; }
.action-tag { display: inline-block; padding: 1px 8px; border-radius: 99px; font-size: 11px; background: #f1f5f9; color: #374151; }
.actions { display: flex; gap: 6px; }
.log-pages { margin-top: 12px; display: flex; align-items: center; font-size: 13px; color: #6b7280; }
.btn { border: none; background: #1677ff; color: #fff; border-radius: 8px; height: 34px; padding: 0 12px; cursor: pointer; font-size: 13px; }
.btn:disabled { opacity: 0.65; cursor: not-allowed; }
.btn-sm { height: 28px; padding: 0 10px; font-size: 12px; }
.btn-danger { background: #dc2626; }
.btn-ghost { background: #e5e7eb; color: #111827; }
.btn-green { background: #16a34a; }
.btn-page { background: #7c3aed; }
.input { height: 34px; border: 1px solid #d1d5db; border-radius: 8px; padding: 0 10px; font-size: 13px; }
.sel { padding: 0 6px; }
.full { width: 100%; box-sizing: border-box; }
.mask { position: fixed; inset: 0; background: rgb(0 0 0 / 38%); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.dialog { width: 440px; background: #fff; border-radius: 12px; padding: 20px; }
.dialog h3 { margin: 0 0 10px; }
.hint { color: #6b7280; font-size: 13px; margin: 0 0 12px; }
.flabel { display: block; font-size: 13px; color: #374151; margin: 10px 0 4px; }
.dialog-actions { margin-top: 16px; display: flex; justify-content: flex-end; gap: 8px; }
.dialog-wide { width: 620px; }
.tag-on { display: inline-block; padding: 1px 8px; border-radius: 99px; font-size: 11px; background: #dcfce7; color: #15803d; }
.tag-off { display: inline-block; padding: 1px 8px; border-radius: 99px; font-size: 11px; background: #fee2e2; color: #dc2626; }

.dialog-delete {
  width: 400px;
  text-align: center;
  padding: 32px 28px;
}

.delete-icon {
  font-size: 40px;
  margin-bottom: 12px;
}

.delete-title {
  margin: 0 0 10px;
  font-size: 18px;
  color: #111827;
}

.delete-desc {
  color: #6b7280;
  font-size: 14px;
  margin: 0 0 20px;
  line-height: 1.6;
}

.countdown-bar {
  width: 100%;
  height: 6px;
  background: #f1f5f9;
  border-radius: 99px;
  overflow: hidden;
  margin-bottom: 8px;
}

.countdown-fill {
  height: 100%;
  background: linear-gradient(90deg, #fbbf24, #dc2626);
  border-radius: 99px;
  transition: width 1s linear;
}

.countdown-tip {
  font-size: 13px;
  color: #9ca3af;
  margin: 0 0 20px;
}

.delete-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
  margin-top: 8px;
}

.btn-cancel {
  min-width: 100px;
  height: 38px;
  background: #fff;
  color: #374151;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-cancel:hover {
  background: #f9fafb;
}

.btn-confirm {
  min-width: 120px;
  height: 38px;
  background: #dc2626;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-confirm:hover:not(:disabled) {
  background: #b91c1c;
}

.btn-confirm-disabled {
  background: #fca5a5 !important;
  cursor: not-allowed !important;
}
</style>
