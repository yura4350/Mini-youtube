<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink, RouterView, useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import AppIcon from '@/components/icons/AppIcon.vue'

const authStore = useAuthStore()
const router = useRouter()
const route = useRoute()
const searchInput = ref('')

const showSearch = computed(() => route.name !== 'login' && route.name !== 'register')

onMounted(() => {
  authStore.hydrate()
})

function logout() {
  authStore.logout()
  router.push('/login')
}

function submitSearch() {
  const keyword = searchInput.value.trim()
  if (!keyword) return
  router.push({ name: 'search', query: { q: keyword } })
}
</script>

<template>
  <div class="app-shell">
    <header class="topbar">
      <RouterLink to="/" class="brand">
        <span class="brand-icon" aria-hidden="true"><AppIcon name="play" :size="14" :stroke-width="1.9" /></span>
        <span>Media Hub</span>
      </RouterLink>

      <form v-if="showSearch" class="searchbar" @submit.prevent="submitSearch">
        <input v-model="searchInput" type="text" placeholder="Search videos" />
        <button type="submit" class="search-btn"><AppIcon name="search" :size="16" /> Search</button>
      </form>

      <nav class="topnav">
        <RouterLink to="/"><AppIcon name="home" :size="16" /> Home</RouterLink>
        <RouterLink v-if="authStore.isAuthenticated" to="/upload"
          ><AppIcon name="upload" :size="16" /> Upload</RouterLink
        >
        <RouterLink v-if="!authStore.isAuthenticated" to="/login"
          ><AppIcon name="login" :size="16" /> Login</RouterLink
        >
        <RouterLink v-if="!authStore.isAuthenticated" to="/register"
          ><AppIcon name="register" :size="16" /> Register</RouterLink
        >
        <RouterLink v-if="authStore.isAuthenticated" to="/profile"
          ><AppIcon name="user" :size="16" /> Profile</RouterLink
        >
        <RouterLink
          v-if="authStore.isAuthenticated && authStore.currentUser?.isAdmin"
          to="/admin"
          ><AppIcon name="admin" :size="16" /> Admin</RouterLink
        >
        <button v-if="authStore.isAuthenticated" class="logout-btn" @click="logout">
          <AppIcon name="logout" :size="16" /> Logout
        </button>
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

.searchbar {
  flex: 1;
  max-width: 640px;
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 8px;
  margin: 0 16px;
}

.searchbar input {
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  background: #121212;
  color: #fff;
  padding: 9px 14px;
}

.searchbar button {
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.22);
  background: #202020;
  color: #fff;
  padding: 9px 14px;
  cursor: pointer;
}

.search-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
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
  display: inline-flex;
  align-items: center;
  gap: 6px;
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
  display: inline-flex;
  align-items: center;
  gap: 6px;
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

  .searchbar {
    width: 100%;
    max-width: none;
    margin: 0;
  }

  .topnav {
    width: 100%;
    flex-wrap: wrap;
  }
}
</style>
