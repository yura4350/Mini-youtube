<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import VideoCard from '@/components/VideoCard.vue'
import AppIcon from '@/components/icons/AppIcon.vue'
import { formatViews } from '@/services/video-format'
import { fetchVideoById, fetchVideos } from '@/services/videos'
import type { VideoItem } from '@/types/video'

const route = useRoute()

const currentVideo = ref<VideoItem | null>(null)
const allVideos = ref<VideoItem[]>([])
const loading = ref(false)
const errorMessage = ref('')

const playbackUrl = computed(() => {
  if (!currentVideo.value) return ''

  const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').replace(/\/$/, '')
  const url = currentVideo.value.videoUrl

  if (url.startsWith('http://') || url.startsWith('https://')) {
    return url
  }

  return `${apiBaseUrl}${url}`
})

async function loadCurrentVideo() {
  const videoId = String(route.params.id)
  if (!videoId) {
    currentVideo.value = null
    return
  }

  loading.value = true
  errorMessage.value = ''

  try {
    const [video, videos] = await Promise.all([fetchVideoById(videoId), fetchVideos()])
    currentVideo.value = video
    allVideos.value = videos
  } catch (error) {
    currentVideo.value = null
    errorMessage.value = error instanceof Error ? error.message : 'Failed to load video.'
  } finally {
    loading.value = false
  }
}

const relatedVideos = computed(() => {
  if (!currentVideo.value) return []
  return allVideos.value
    .filter((item) => item.id !== currentVideo.value?.id)
    .filter((item) => {
      return item.category === currentVideo.value?.category || item.tags.some((tag) => currentVideo.value?.tags.includes(tag))
    })
    .slice(0, 6)
})

onMounted(() => {
  loadCurrentVideo()
})

watch(
  () => route.params.id,
  () => {
    loadCurrentVideo()
  },
)
</script>

<template>
  <main v-if="loading" class="watch-page">
    <section class="channel-card">
      <p>Loading video...</p>
    </section>
  </main>

  <main v-if="currentVideo" class="watch-page">
    <section class="main-col">
      <div class="player-wrap">
        <video :src="playbackUrl" :poster="currentVideo.thumbnail" controls preload="metadata" />
      </div>

      <h1>{{ currentVideo.title }}</h1>
      <p class="meta">
        <span><AppIcon name="views" :size="14" /> {{ formatViews(currentVideo.views) }} views</span>
        <span>•</span>
        <span><AppIcon name="clock" :size="14" /> {{ new Date(currentVideo.uploadDate).toLocaleDateString() }}</span>
      </p>

      <section class="channel-card">
        <img :src="currentVideo.authorAvatar" :alt="currentVideo.authorName" class="avatar" />
        <div>
          <p class="name">{{ currentVideo.authorName }}</p>
          <p class="desc">{{ currentVideo.description }}</p>
        </div>
      </section>
    </section>

    <aside class="side-col">
      <h2><AppIcon name="video" :size="16" /> Related videos</h2>
      <div class="related-list">
        <VideoCard v-for="video in relatedVideos" :key="video.id" :video="video" />
      </div>
    </aside>
  </main>

  <main v-else class="watch-page">
    <section class="channel-card">
      <p>{{ errorMessage || 'Video not found.' }}</p>
    </section>
  </main>
</template>

<style scoped>
.watch-page {
  max-width: 1450px;
  margin: 0 auto;
  padding: 20px 16px 34px;
  display: grid;
  grid-template-columns: minmax(0, 2fr) minmax(300px, 1fr);
  gap: 20px;
}

.player-wrap {
  aspect-ratio: 16 / 9;
  border-radius: 14px;
  overflow: hidden;
  background: #000;
}

.player-wrap video {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

h1 {
  margin-top: 14px;
  color: #fff;
  font-size: 24px;
}

.meta {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: #9ca3af;
  margin-top: 4px;
}

.meta span {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.channel-card {
  margin-top: 14px;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: #1a1a1a;
  padding: 14px;
  display: flex;
  gap: 10px;
}

.avatar {
  width: 42px;
  height: 42px;
  border-radius: 999px;
}

.name {
  color: #fff;
  font-weight: 600;
}

.desc {
  margin-top: 4px;
  color: #c6cad2;
  font-size: 14px;
}

.side-col h2 {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: #f4f5f8;
  font-size: 18px;
  margin-bottom: 10px;
}

.related-list {
  display: grid;
  gap: 14px;
}

@media (max-width: 1100px) {
  .watch-page {
    grid-template-columns: 1fr;
  }
}
</style>
