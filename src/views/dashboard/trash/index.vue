<script lang="ts" setup>
// 引入回收站相关的接口类型定义
import type { AuthApi } from '#/api';

// Modal：弹出确认框；message：轻提示
import { Modal, message } from 'ant-design-vue';
// computed：计算属性；onMounted：组件挂载钩子；ref：响应式变量
import { computed, onMounted, ref } from 'vue';

// 回收站相关接口：清空、获取列表、彻底删除、恢复
import {
  clearTrashApi,   // 清空整个回收站
  getTrashApi,     // 获取回收站列表
  purgeTrashApi,   // 彻底删除单条记录
  restoreTrashApi, // 恢复单条记录
} from '#/api';

/** 页面加载状态 */
const loading = ref(false);

/** 回收站原始条目列表 */
const items = ref<AuthApi.TrashItem[]>([]);

/** 当前类型筛选值（'' 表示全部） */
const filterType = ref('');

/**
 * 根据 filterType 过滤后的条目列表
 * filterType 为空时返回全部条目
 */
const filteredItems = computed(() => {
  if (!filterType.value) return items.value;
  return items.value.filter((i) => i.itemType === filterType.value);
});

/**
 * 加载回收站数据
 * 根据当前 filterType 向后端请求数据并写入 items
 */
async function loadTrash() {
  loading.value = true;
  try {
    items.value = await getTrashApi(
      filterType.value ? { item_type: filterType.value } : undefined,
    );
  } finally {
    loading.value = false;
  }
}

/**
 * 恢复指定回收站条目
 * 调用后端恢复接口，成功后重新加载列表
 * @param item 要恢复的回收站条目
 */
async function handleRestore(item: AuthApi.TrashItem) {
  try {
    await restoreTrashApi(item.id);
    message.success(`已恢复 ${typeLabel(item.itemType)}：${itemName(item)}`);
    await loadTrash();
  } catch (e: any) {
    message.error(e?.message ?? '恢复失败');
  }
}

/**
 * 彻底删除指定回收站条目
 * 弹出确认框，用户确认后调用后端永久删除接口
 * @param item 要彻底删除的回收站条目
 */
function handlePurge(item: AuthApi.TrashItem) {
  Modal.confirm({
    title: '确认彻底删除',
    content: `「${itemName(item)}」将被永久删除，无法再恢复，是否继续？`,
    okButtonProps: { danger: true },
    async onOk() {
      await purgeTrashApi(item.id);
      message.success('已彻底删除');
      await loadTrash();
    },
  });
}

/**
 * 清空整个回收站
 * 弹出二次确认框，用户确认后调用后端清空接口
 * 清空成功后重新加载列表并提示清除数量
 */
function handleClearAll() {
  Modal.confirm({
    title: '确认清空回收站',
    content: '清空后所有回收站内容将永久删除，无法恢复，是否继续？',
    okButtonProps: { danger: true },
    async onOk() {
      const res = await clearTrashApi();
      message.success(`已清空回收站，共删除 ${res.cleared} 条记录`);
      await loadTrash();
    },
  });
}

/**
 * 将条目类型枚举值转换为中文标签
 * @param type 条目类型（'user' | 'page' | 'key'）
 * @returns 对应的中文名称
 */
function typeLabel(type: string) {
  return { user: '用户', page: '页面', key: '密钥' }[type] ?? type;
}

/**
 * 根据条目类型返回对应的 CSS class 名称，用于标签配色
 * @param type 条目类型
 * @returns CSS class 字符串
 */
function typeClass(type: string) {
  return { user: 'tag-user', page: 'tag-page', key: 'tag-key' }[type] ?? '';
}

/**
 * 获取回收站条目的展示名称
 * - 用户：取 username
 * - 页面：取 site_name
 * - 密钥：取 register_key
 * - 兜底：返回 itemId
 * @param item 回收站条目
 * @returns 展示用名称字符串
 */
function itemName(item: AuthApi.TrashItem): string {
  const d = item.itemData;
  if (item.itemType === 'user') return d.username ?? item.itemId;
  if (item.itemType === 'page') return d.site_name ?? item.itemId;
  if (item.itemType === 'key') return d.register_key ?? item.itemId;
  return item.itemId;
}

/**
 * 获取回收站条目的补充详情文本
 * - 用户：角色 + 真实姓名
 * - 页面：绑定域名 + 站点路径
 * - 密钥：角色 + 使用者
 * @param item 回收站条目
 * @returns 详情描述字符串
 */
function itemDetail(item: AuthApi.TrashItem): string {
  const d = item.itemData;
  if (item.itemType === 'user') return `角色: ${d.roles ?? '—'}  真实姓名: ${d.real_name ?? '—'}`;
  if (item.itemType === 'page') return `域名: ${d.bind_domain ?? '—'}  路径: ${d.site_path ?? '—'}`;
  if (item.itemType === 'key') return `角色: ${d.role ?? '—'}  使用者: ${d.used_by ?? '未使用'}`;
  return '';
}

/** 组件挂载后立即加载回收站数据 */
onMounted(loadTrash);
</script>

<template>
  <div class="page">
    <div class="page-header">
      <div class="header-left">
        <h2>回收站</h2>
        <p class="sub">已删除的用户、页面、密钥将永久保存在此，可随时恢复或彻底删除</p>
      </div>
      <button class="btn btn-danger" :disabled="items.length === 0" @click="handleClearAll">清空回收站</button>
    </div>

    <div class="toolbar">
      <select v-model="filterType" class="input sel" @change="loadTrash">
        <option value="">全部类型</option>
        <option value="user">用户</option>
        <option value="page">页面</option>
        <option value="key">密钥</option>
      </select>
      <button class="btn" :disabled="loading" @click="loadTrash">
        {{ loading ? '刷新中...' : '刷新' }}
      </button>
      <span class="count">共 {{ filteredItems.length }} 条</span>
    </div>

    <div v-if="filteredItems.length === 0 && !loading" class="empty">
      <div class="empty-icon">🗑️</div>
      <p>回收站为空</p>
    </div>

    <div v-else class="list">
      <div v-for="item in filteredItems" :key="item.id" class="card">
        <div class="card-left">
          <div class="card-top">
            <span class="type-tag" :class="typeClass(item.itemType)">{{ typeLabel(item.itemType) }}</span>
            <span class="item-name">{{ itemName(item) }}</span>
          </div>
          <div class="card-detail">{{ itemDetail(item) }}</div>
          <div class="card-meta">
            删除人：{{ item.deletedBy }}
            &nbsp;·&nbsp;
            删除时间：{{ new Date(item.deletedAt).toLocaleString('zh-CN') }}
          </div>
        </div>
        <div class="card-actions">
          <button class="btn btn-restore" @click="handleRestore(item)">恢复</button>
          <button class="btn btn-purge" @click="handlePurge(item)">彻底删除</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page {
  padding: 24px;
  min-height: 100vh;
  background: #f5f7fa;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
}

.header-left h2 {
  margin: 0 0 4px;
  font-size: 22px;
  color: #111827;
}

.sub {
  margin: 0;
  font-size: 13px;
  color: #6b7280;
}

.toolbar {
  display: flex;
  gap: 10px;
  align-items: center;
  margin-bottom: 16px;
}

.count {
  font-size: 13px;
  color: #9ca3af;
  margin-left: 4px;
}

.input {
  height: 34px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  padding: 0 10px;
  font-size: 13px;
  background: #fff;
}

.sel { padding: 0 6px; }

.btn {
  border: none;
  background: #1677ff;
  color: #fff;
  border-radius: 8px;
  height: 34px;
  padding: 0 14px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  transition: background 0.2s;
}

.btn:disabled { opacity: 0.6; cursor: not-allowed; }
.btn-danger { background: #dc2626; }
.btn-danger:hover:not(:disabled) { background: #b91c1c; }
.btn-restore { background: #16a34a; height: 32px; padding: 0 12px; font-size: 12px; }
.btn-restore:hover { background: #15803d; }
.btn-purge { background: #dc2626; height: 32px; padding: 0 12px; font-size: 12px; }
.btn-purge:hover { background: #b91c1c; }

.empty {
  text-align: center;
  padding: 60px 20px;
  background: #fff;
  border-radius: 12px;
  color: #9ca3af;
}

.empty-icon { font-size: 48px; margin-bottom: 12px; }

.list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.card {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 16px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  transition: box-shadow 0.2s;
}

.card:hover { box-shadow: 0 2px 12px rgb(0 0 0 / 7%); }

.card-left { flex: 1; min-width: 0; }

.card-top {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 6px;
  flex-wrap: wrap;
}

.item-name {
  font-size: 15px;
  font-weight: 600;
  color: #111827;
  word-break: break-all;
}

.days-left {
  font-size: 12px;
  color: #6b7280;
  background: #f1f5f9;
  padding: 1px 8px;
  border-radius: 99px;
}

.days-left.urgent {
  color: #dc2626;
  background: #fee2e2;
  font-weight: 600;
}

.card-detail {
  font-size: 13px;
  color: #4b5563;
  margin-bottom: 4px;
}

.card-meta {
  font-size: 12px;
  color: #9ca3af;
}

.card-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

.type-tag {
  display: inline-block;
  padding: 2px 9px;
  border-radius: 99px;
  font-size: 11px;
  font-weight: 600;
}

.tag-user { background: #dbeafe; color: #1d4ed8; }
.tag-page { background: #dcfce7; color: #15803d; }
.tag-key  { background: #fef9c3; color: #92400e; }
</style>
