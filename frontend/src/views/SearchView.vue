<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import AppIcon from '@/components/icons/AppIcon.vue'
import VideoCard from '@/components/VideoCard.vue'
import { mockVideos } from '@/services/mock-videos'

const route = useRoute()

const query = computed(() => String(route.query.q || '').trim())

const results = computed(() => {
  if (!query.value) return []
  const q = query.value.toLowerCase()
  return mockVideos.filter((video) => {
    return (
      video.title.toLowerCase().includes(q) ||
      video.description.toLowerCase().includes(q) ||
      video.authorName.toLowerCase().includes(q) ||
      video.category.toLowerCase().includes(q) ||
      video.tags.some((tag) => tag.toLowerCase().includes(q))
    )
  })
})
</script>

<template>
  <main class="search-page">
    <header class="search-header">
      <h1><AppIcon name="search" :size="20" /> Search results for "{{ query }}"</h1>
      <p>{{ results.length }} videos found</p>
    </header>

    <section v-if="results.length > 0" class="video-grid">
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
