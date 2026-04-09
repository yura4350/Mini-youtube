<script setup lang="ts">
import { RouterLink } from 'vue-router'
import type { VideoItem } from '@/types/video'
import { formatViews, timeAgo } from '@/services/video-format'
import AppIcon from '@/components/icons/AppIcon.vue'

defineProps<{ video: VideoItem }>()
</script>

<template>
  <RouterLink :to="`/video/${video.id}`" class="video-card">
    <div class="thumb-wrap">
      <img :src="video.thumbnail" :alt="video.title" class="thumb" />
      <span class="duration">{{ video.duration }}</span>
    </div>

    <div class="meta">
      <img :src="video.authorAvatar" :alt="video.authorName" class="avatar" />
      <div class="meta-text">
        <h3>{{ video.title }}</h3>
        <p class="author">{{ video.authorName }}</p>
        <p class="sub">
          <span><AppIcon name="views" :size="13" /> {{ formatViews(video.views) }} views</span>
          <span>•</span>
          <span><AppIcon name="clock" :size="13" /> {{ timeAgo(video.uploadDate) }}</span>
        </p>
      </div>
    </div>
  </RouterLink>
</template>

<style scoped>
.video-card {
  display: grid;
  gap: 10px;
  text-decoration: none;
}

.thumb-wrap {
  position: relative;
  aspect-ratio: 16 / 9;
  border-radius: 14px;
  overflow: hidden;
  background: #1f1f1f;
}

.thumb {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 180ms ease;
}

.video-card:hover .thumb {
  transform: scale(1.03);
}

.duration {
  position: absolute;
  right: 8px;
  bottom: 8px;
  font-size: 12px;
  padding: 2px 6px;
  border-radius: 6px;
  color: #fff;
  background: rgba(0, 0, 0, 0.72);
}

.meta {
  display: grid;
  grid-template-columns: 38px 1fr;
  gap: 10px;
}

.avatar {
  width: 38px;
  height: 38px;
  border-radius: 999px;
  object-fit: cover;
}

.meta-text h3 {
  color: #f3f4f6;
  font-size: 14px;
  line-height: 1.3;
  margin-bottom: 2px;
}

.author {
  color: #c1c5ce;
  font-size: 13px;
}

.sub {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: #9ca3af;
  font-size: 12px;
}

.sub span {
  display: inline-flex;
  align-items: center;
  gap: 3px;
}
</style>
