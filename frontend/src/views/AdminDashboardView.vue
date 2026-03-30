<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { authService } from '@/services/auth'
import AppIcon from '@/components/icons/AppIcon.vue'
import { fetchVideos } from '@/services/videos'
import type { VideoItem } from '@/types/video'

const currentUser = computed(() => authService.getCurrentUser())
const users = computed(() => authService.getAllUsers())
const videos = ref<VideoItem[]>([])
const loadingVideos = ref(false)
const videoError = ref('')

const totalViews = computed(() => videos.value.reduce((sum, video) => sum + video.views, 0))

async function loadVideos() {
  loadingVideos.value = true
  videoError.value = ''

  try {
    videos.value = await fetchVideos()
  } catch (error) {
    videoError.value = error instanceof Error ? error.message : 'Failed to load video metrics.'
  } finally {
    loadingVideos.value = false
  }
}

onMounted(() => {
  loadVideos()
})
</script>

<template>
  <main class="admin-page">
    <section v-if="!currentUser?.isAdmin" class="admin-card">
      <h1><AppIcon name="admin" :size="18" /> Admin access required</h1>
      <p>This area is available for admin accounts only.</p>
    </section>

    <section v-else class="admin-grid">
      <article class="metric">
        <p class="label"><AppIcon name="users" :size="14" /> Total users</p>
        <p class="value">{{ users.length }}</p>
      </article>
      <article class="metric">
        <p class="label"><AppIcon name="video" :size="14" /> Total videos</p>
        <p class="value">{{ videos.length }}</p>
      </article>
      <article class="metric">
        <p class="label"><AppIcon name="views" :size="14" /> Total views</p>
        <p class="value">{{ totalViews.toLocaleString() }}</p>
      </article>

      <article v-if="loadingVideos" class="metric status">
        <p class="label">Loading video metrics...</p>
      </article>

      <article v-else-if="videoError" class="metric status">
        <p class="label">{{ videoError }}</p>
      </article>
    </section>
  </main>
</template>

<style scoped>
.admin-page {
  max-width: 1180px;
  margin: 0 auto;
  padding: 22px 16px 34px;
}

.admin-card,
.metric {
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 14px;
  background: #1a1a1a;
  padding: 16px;
}

.status {
  grid-column: 1 / -1;
}

.admin-card h1 {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: #fff;
}

.admin-card p {
  color: #a8aeba;
}

.admin-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.label {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: #9ca3af;
  font-size: 13px;
}

.value {
  color: #fff;
  font-size: 28px;
  font-weight: 700;
}

@media (max-width: 860px) {
  .admin-grid {
    grid-template-columns: 1fr;
  }
}
</style>
