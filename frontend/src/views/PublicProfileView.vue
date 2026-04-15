<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import AppIcon from '@/components/icons/AppIcon.vue'
import { authService } from '@/services/auth'
import { useAuthStore } from '@/stores/auth'
import type { User } from '@/types/auth'

const route = useRoute()
const authStore = useAuthStore()

const loading = ref(true)
const errorMessage = ref('')
const profileUser = ref<User | null>(null)

const numericUserId = computed(() => {
  const raw = route.params.userId
  const s = Array.isArray(raw) ? raw[0] : raw
  const n = Number.parseInt(String(s), 10)
  return Number.isFinite(n) ? n : NaN
})

const isOwnProfile = computed(() => {
  if (!authStore.currentUser || !profileUser.value) return false
  return authStore.currentUser.id === profileUser.value.id
})

async function loadProfile() {
  loading.value = true
  errorMessage.value = ''
  profileUser.value = null

  const id = numericUserId.value
  if (Number.isNaN(id)) {
    loading.value = false
    errorMessage.value = 'Invalid user id in the URL.'
    return
  }

  const result = await authService.fetchPublicProfile(id)
  loading.value = false

  if (result.ok) {
    profileUser.value = result.user
    return
  }

  errorMessage.value = result.message
}

onMounted(loadProfile)

watch(
  () => route.params.userId,
  () => {
    loadProfile()
  },
)
</script>

<template>
  <main class="public-profile-page">
    <nav class="back-nav">
      <RouterLink to="/" class="back-link">
        <AppIcon name="home" :size="14" /> Home
      </RouterLink>
      <RouterLink v-if="authStore.currentUser" to="/profile" class="back-link">
        <AppIcon name="user" :size="14" /> My profile
      </RouterLink>
    </nav>

    <p v-if="loading" class="muted">Loading profile…</p>

    <p v-else-if="errorMessage" class="error">{{ errorMessage }}</p>

    <section v-else-if="profileUser" class="profile-card">
      <img :src="profileUser.avatar" :alt="profileUser.username" class="avatar" />

      <div class="header-main">
        <div class="title-row">
          <h1>{{ profileUser.username }}</h1>
          <span v-if="profileUser.isAdmin" class="badge admin">Admin</span>
          <span v-else class="badge">Member</span>
        </div>

        <p class="email">{{ profileUser.email }}</p>

        <p v-if="isOwnProfile" class="own-hint">
          <AppIcon name="user" :size="14" /> This is your account.
          <RouterLink to="/profile" class="inline-link">Open full profile</RouterLink>
        </p>

        <div class="stats">
          <span><AppIcon name="users" :size="14" /> User id {{ profileUser.id }}</span>
        </div>
      </div>
    </section>
  </main>
</template>

<style scoped>
.public-profile-page {
  max-width: 720px;
  margin: 0 auto;
  padding: 22px 16px 34px;
}

.back-nav {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 16px;
}

.back-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  text-decoration: none;
  border: 1px solid var(--border-medium);
  border-radius: 9px;
  color: var(--text-body);
  padding: 8px 12px;
  background: var(--bg-5);
}

.back-link:hover {
  border-color: var(--accent-outline-soft);
  background: var(--accent-wash);
  color: var(--text-main);
}

.profile-card {
  border-radius: 14px;
  border: 1px solid var(--border-default);
  background: var(--bg-1);
  padding: 16px;
  display: grid;
  grid-template-columns: 110px 1fr;
  gap: 14px;
}

.avatar {
  width: 110px;
  height: 110px;
  border-radius: 999px;
  object-fit: cover;
}

h1 {
  color: var(--text-main);
  font-size: 28px;
  margin: 0;
}

.title-row {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.badge {
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  padding: 4px 8px;
  border-radius: 6px;
  background: var(--border-faint);
  color: var(--text-soft);
  border: 1px solid var(--border-default);
}

.badge.admin {
  background: var(--accent-wash-hover);
  border-color: var(--accent-outline);
  color: var(--accent-text-soft);
}

.email {
  color: var(--text-soft);
  margin: 6px 0 0;
}

.own-hint {
  margin-top: 10px;
  color: var(--ok-text);
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  font-size: 14px;
}

.inline-link {
  color: var(--ok-text-strong);
}

.stats {
  margin-top: 12px;
  color: var(--text-body);
  display: flex;
  gap: 14px;
  flex-wrap: wrap;
  font-size: 14px;
}

.muted {
  color: var(--text-muted);
}

.error {
  color: var(--accent-text-soft);
}

@media (max-width: 560px) {
  .profile-card {
    grid-template-columns: 1fr;
    justify-items: center;
    text-align: center;
  }

  .title-row {
    justify-content: center;
  }

  .own-hint {
    justify-content: center;
  }

  .stats {
    justify-content: center;
  }
}
</style>
