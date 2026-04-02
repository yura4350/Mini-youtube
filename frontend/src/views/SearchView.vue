<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import AppIcon from '@/components/icons/AppIcon.vue'
import VideoCard from '@/components/VideoCard.vue'
import { fetchVideos } from '@/services/videos'
import type { VideoItem } from '@/types/video'

const route = useRoute()
const videos = ref<VideoItem[]>([])
const loading = ref(false)
const errorMessage = ref('')

const query = computed(() => String(route.query.q || '').trim())

const results = computed(() => {
  if (!query.value) return []
  const q = query.value.toLowerCase()
  return videos.value.filter((video) => {
    return (
      video.title.toLowerCase().includes(q) ||
      video.description.toLowerCase().includes(q) ||
      video.authorName.toLowerCase().includes(q) ||
      video.category.toLowerCase().includes(q) ||
      video.tags.some((tag) => tag.toLowerCase().includes(q))
    )
  })
})

async function loadVideos() {
  loading.value = true
  errorMessage.value = ''

  try {
    videos.value = await fetchVideos()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : 'Failed to load videos'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadVideos()
})
</script>

<template>
  <main class="search-page">
    <header class="search-header">
      <h1><AppIcon name="search" :size="20" /> Search results for "{{ query }}"</h1>
      <p>{{ results.length }} videos found</p>
    </header>

    <section v-if="loading" class="status-box">
      <p>Loading videos...</p>
    </section>

    <section v-else-if="errorMessage" class="status-box">
      <p>{{ errorMessage }}</p>
    </section>

    <section v-else-if="results.length > 0" class="video-grid">
      <VideoCard v-for="video in results" :key="video.id" :video="video" />
    </section>

    <section v-else class="empty-state">
      <AppIcon name="empty" :size="18" />
      <p>No videos matched your search.</p>
    </section>
  </main>
</template>

<style scoped>
.search-page {
  max-width: 1320px;
  margin: 0 auto;
  padding: 22px 16px 34px;
}

.search-header h1 {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: #fff;
  font-size: 26px;
}

.search-header p {
  color: #9ca3af;
}

.video-grid {
  margin-top: 18px;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 18px;
}

.status-box {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin-top: 20px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 14px;
  padding: 20px;
  color: #c2c7d0;
  background: #1a1a1a;
}

.empty-state {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin-top: 20px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 14px;
  padding: 20px;
  color: #c2c7d0;
  background: #1a1a1a;
}
</style>
