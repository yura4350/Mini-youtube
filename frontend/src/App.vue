<script setup lang="ts">
import { onMounted } from 'vue'
import { RouterLink, RouterView } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

onMounted(() => {
  authStore.hydrate()
})

function logout() {
  authStore.logout()
}
</script>

<template>
  <div class="app-shell">
    <header class="topbar">
      <RouterLink to="/" class="brand">
        <span class="brand-icon" aria-hidden="true">▶</span>
        <span>Media Hub</span>
      </RouterLink>

      <nav class="topnav">
        <RouterLink to="/">Home</RouterLink>
        <RouterLink v-if="!authStore.isAuthenticated" to="/login">Login</RouterLink>
        <RouterLink v-if="!authStore.isAuthenticated" to="/register">Register</RouterLink>
        <RouterLink v-if="authStore.isAuthenticated" to="/profile">Profile</RouterLink>
        <button v-if="authStore.isAuthenticated" class="logout-btn" @click="logout">Logout</button>
      </nav>
    </header>

    <RouterView />
  </div>
</template>

<style scoped>
.app-shell {
  min-height: 100vh;
}

.topbar {
  position: sticky;
  top: 0;
  z-index: 5;
  height: 68px;
  padding: 0 18px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  backdrop-filter: blur(8px);
  background: rgba(7, 8, 10, 0.8);
  border-bottom: 1px solid rgba(255, 255, 255, 0.12);
}

.brand {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 20px;
  color: #fff;
  text-decoration: none;
  letter-spacing: 0.03em;
  font-weight: 700;
}

.brand-icon {
  width: 26px;
  height: 26px;
  border-radius: 999px;
  display: grid;
  place-items: center;
  font-size: 11px;
  background: linear-gradient(135deg, #dc2626, #ef4444);
}

.topnav {
  display: flex;
  align-items: center;
  gap: 12px;
}

.topnav a {
  color: #d4d7de;
  text-decoration: none;
  font-size: 14px;
  padding: 8px 10px;
  border-radius: 8px;
}

.topnav a.router-link-exact-active,
.topnav a:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}

.logout-btn {
  border: 1px solid rgba(255, 255, 255, 0.28);
  background: transparent;
  color: #fff;
  border-radius: 8px;
  padding: 8px 10px;
  cursor: pointer;
}

@media (max-width: 740px) {
  .topbar {
    height: auto;
    padding: 12px;
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }

  .topnav {
    width: 100%;
    flex-wrap: wrap;
  }
}
</style>
