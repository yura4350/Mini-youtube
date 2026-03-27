<script setup lang="ts">
import { reactive, ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import AppIcon from '@/components/icons/AppIcon.vue'

const authStore = useAuthStore()
const router = useRouter()

const loading = ref(false)
const errorMessage = ref('')
const form = reactive({
  email: '',
  password: '',
})

async function onSubmit() {
  loading.value = true
  errorMessage.value = ''

  await new Promise((resolve) => setTimeout(resolve, 350))
  const result = authStore.login({ email: form.email, password: form.password })

  loading.value = false
  if (!result.ok) {
    errorMessage.value = result.message
    return
  }

  router.push('/profile')
}
</script>

<template>
  <section class="auth-shell">
    <div class="auth-card">
      <div class="auth-icon" aria-hidden="true"><AppIcon name="play" :size="22" :stroke-width="2" /></div>
      <p class="brand-mark">MEDIA HUB</p>
      <h1>Welcome back</h1>
      <p class="muted">Sign in to continue to your channels and saved videos.</p>

      <form class="auth-form" @submit.prevent="onSubmit">
        <label>
          Email
          <input v-model="form.email" type="email" placeholder="you@example.com" required />
        </label>

        <label>
          Password
          <input v-model="form.password" type="password" placeholder="Enter your password" required />
        </label>

        <button type="submit" :disabled="loading">
          {{ loading ? 'Signing in...' : 'Sign In' }}
        </button>
      </form>

      <p v-if="errorMessage" class="error">{{ errorMessage }}</p>

      <div class="switch-link">
        Don't have an account?
        <RouterLink to="/register">Sign up</RouterLink>
      </div>

      <div class="demo-box">
        <p>Demo account: tech@example.com or admin@example.com</p>
        <p>Password: any non-empty text</p>
      </div>
    </div>
  </section>
</template>

<style scoped>
.auth-shell {
  min-height: calc(100vh - 68px);
  display: grid;
  place-items: center;
  padding: 24px;
}

.auth-card {
  width: min(460px, 100%);
  background: rgba(18, 18, 18, 0.88);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 18px;
  padding: 28px;
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.35);
}

.auth-icon {
  width: 52px;
  height: 52px;
  border-radius: 999px;
  display: grid;
  place-items: center;
  font-size: 18px;
  font-weight: 700;
  color: #fff;
  background: linear-gradient(135deg, #e0291b, #ff4a2a);
  margin-bottom: 14px;
}

.brand-mark {
  color: #ff5a3d;
  letter-spacing: 0.14em;
  font-size: 12px;
  font-weight: 700;
  margin-bottom: 8px;
}

h1 {
  font-size: 30px;
  color: #fff;
  margin-bottom: 6px;
}

.muted {
  color: #9ea1a7;
  margin-bottom: 20px;
}

.auth-form {
  display: grid;
  gap: 14px;
}

label {
  display: grid;
  gap: 6px;
  color: #e8e8ea;
  font-size: 14px;
}

input {
  width: 100%;
  border: 1px solid rgba(255, 255, 255, 0.2);
  background: rgba(10, 10, 10, 0.86);
  color: #fff;
  border-radius: 10px;
  padding: 11px 12px;
}

input:focus {
  outline: none;
  border-color: #ff5a3d;
  box-shadow: 0 0 0 3px rgba(255, 90, 61, 0.2);
}

button {
  border: none;
  border-radius: 10px;
  padding: 12px;
  color: #fff;
  background: linear-gradient(135deg, #dc2626, #ef4444);
  font-weight: 600;
  cursor: pointer;
}

button:disabled {
  opacity: 0.7;
  cursor: wait;
}

.error {
  margin-top: 12px;
  color: #ff9f8b;
  font-size: 14px;
}

.switch-link {
  margin-top: 18px;
  color: #cfd2d8;
  font-size: 14px;
}

.switch-link a {
  margin-left: 6px;
  color: #ff7d59;
}

.demo-box {
  margin-top: 18px;
  padding: 12px;
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(0, 0, 0, 0.35);
  color: #a5a8ae;
  font-size: 12px;
}
</style>
