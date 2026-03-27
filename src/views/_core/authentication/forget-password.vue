<script lang="ts" setup>
// message：全局轻提示，用于操作成功/失败反馈
import { message } from 'ant-design-vue';
// ref：创建响应式变量（表单字段、加载状态、成功标志）
import { ref } from 'vue';

// resetPasswordApi：忘记密码接口（通过注册密钥重置密码）
import { resetPasswordApi } from '#/api';

defineOptions({ name: 'ForgetPassword' });

const loading = ref(false);
const username = ref('');
const registerKey = ref('');
const newPassword = ref('');
const confirmPassword = ref('');
const success = ref(false);

async function handleSubmit() {
  if (!username.value.trim()) {
    message.error('请输入账号');
    return;
  }
  if (!registerKey.value.trim()) {
    message.error('请输入注册密钥');
    return;
  }
  if (newPassword.value.length < 6) {
    message.error('新密码至少6位');
    return;
  }
  if (newPassword.value !== confirmPassword.value) {
    message.error('两次密码输入不一致');
    return;
  }
  loading.value = true;
  try {
    await resetPasswordApi({
      username: username.value.trim(),
      register_key: registerKey.value.trim(),
      new_password: newPassword.value,
      confirm_password: confirmPassword.value,
    });
    success.value = true;
    message.success('密码重置成功，请重新登录');
  } catch (e: any) {
    message.error(e?.message ?? '重置失败，请检查账号或密钥');
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="fp-wrap">
    <div class="fp-box">
      <h2 class="fp-title">重置密码</h2>
      <p class="fp-sub">请输入您的账号和注册时使用的密钥来重置密码</p>

      <div v-if="success" class="fp-success">
        <div class="success-icon">✓</div>
        <p>密码已重置成功！</p>
        <a href="/auth/login" class="fp-btn">返回登录</a>
      </div>

      <form v-else class="fp-form" @submit.prevent="handleSubmit">
        <div class="fp-field">
          <label>账号</label>
          <input
            v-model="username"
            type="text"
            placeholder="请输入您的账号"
            class="fp-input"
            autocomplete="username"
          />
        </div>

        <div class="fp-field">
          <label>注册密钥</label>
          <input
            v-model="registerKey"
            type="text"
            placeholder="请输入注册时使用的密钥（KEY-XXXX）"
            class="fp-input"
          />
          <span class="fp-hint">密钥需与该账号的注册密钥一致</span>
        </div>

        <div class="fp-field">
          <label>新密码</label>
          <input
            v-model="newPassword"
            type="password"
            placeholder="请输入新密码（至少6位）"
            class="fp-input"
            autocomplete="new-password"
          />
        </div>

        <div class="fp-field">
          <label>确认密码</label>
          <input
            v-model="confirmPassword"
            type="password"
            placeholder="请再次输入新密码"
            class="fp-input"
            autocomplete="new-password"
          />
        </div>

        <button type="submit" class="fp-btn" :disabled="loading">
          {{ loading ? '重置中...' : '确认重置' }}
        </button>

        <div class="fp-back">
          <a href="/auth/login">← 返回登录</a>
        </div>
      </form>
    </div>
  </div>
</template>

<style scoped>
.fp-wrap {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f7fa;
}

.fp-box {
  width: 420px;
  background: #fff;
  border-radius: 12px;
  padding: 36px 32px;
  box-shadow: 0 4px 24px rgb(0 0 0 / 8%);
}

.fp-title {
  margin: 0 0 6px;
  font-size: 22px;
  font-weight: 700;
  color: #111827;
}

.fp-sub {
  margin: 0 0 24px;
  font-size: 13px;
  color: #6b7280;
}

.fp-field {
  margin-bottom: 16px;
}

.fp-field label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: #374151;
  margin-bottom: 6px;
}

.fp-input {
  width: 100%;
  box-sizing: border-box;
  height: 40px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  padding: 0 12px;
  font-size: 14px;
  transition: border-color 0.2s;
}

.fp-input:focus {
  outline: none;
  border-color: #1677ff;
  box-shadow: 0 0 0 2px rgb(22 119 255 / 10%);
}

.fp-hint {
  display: block;
  margin-top: 4px;
  font-size: 11px;
  color: #9ca3af;
}

.fp-btn {
  display: block;
  width: 100%;
  height: 42px;
  background: #1677ff;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  margin-top: 8px;
  text-align: center;
  line-height: 42px;
  text-decoration: none;
  transition: background 0.2s;
}

.fp-btn:hover:not(:disabled) {
  background: #0958d9;
}

.fp-btn:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

.fp-back {
  margin-top: 16px;
  text-align: center;
  font-size: 13px;
}

.fp-back a {
  color: #1677ff;
  text-decoration: none;
}

.fp-success {
  text-align: center;
  padding: 20px 0;
}

.success-icon {
  width: 56px;
  height: 56px;
  background: #dcfce7;
  color: #16a34a;
  border-radius: 50%;
  font-size: 28px;
  line-height: 56px;
  margin: 0 auto 12px;
}

.fp-success p {
  color: #374151;
  font-size: 15px;
  margin: 0 0 20px;
}
</style>
