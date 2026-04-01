<script setup lang="ts">
import { computed, onMounted, ref, watch, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import VideoCard from '@/components/VideoCard.vue'
import AppIcon from '@/components/icons/AppIcon.vue'
import { formatViews } from '@/services/video-format'
import { fetchVideoById, fetchVideos, updateVideo, deleteVideo } from '@/services/videos'
import { useAuthStore } from '@/stores/auth'
import type { VideoItem } from '@/types/video'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const currentVideo = ref<VideoItem | null>(null)
const allVideos = ref<VideoItem[]>([])
const loading = ref(false)
const errorMessage = ref('')
const isEditing = ref(false)
const isSaving = ref(false)
const isDeleting = ref(false)
const editMessage = ref('')

const editForm = reactive({
  title: '',
  description: '',
  category: '',
  tags: '',
})

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

const isOwner = computed(() => {
  if (!currentVideo.value || !authStore.currentUser) return false
  return String(currentVideo.value.authorId) === String(authStore.currentUser.id)
})

function startEditing() {
  if (!currentVideo.value) return
  editForm.title = currentVideo.value.title
  editForm.description = currentVideo.value.description
  editForm.category = currentVideo.value.category
  editForm.tags = currentVideo.value.tags.join(', ')
  isEditing.value = true
  editMessage.value = ''
}

function cancelEditing() {
  isEditing.value = false
  editMessage.value = ''
}

async function saveChanges() {
  if (!currentVideo.value) return
  
  isSaving.value = true
  editMessage.value = ''
  
  try {
    const updated = await updateVideo({
      videoId: currentVideo.value.id,
      title: editForm.title,
      description: editForm.description,
      category: editForm.category,
      tags: editForm.tags,
    })
    currentVideo.value = updated
    isEditing.value = false
    editMessage.value = 'Video updated successfully!'
    setTimeout(() => { editMessage.value = '' }, 3000)
  } catch (error) {
    editMessage.value = error instanceof Error ? error.message : 'Failed to update video.'
  } finally {
    isSaving.value = false
  }
}

async function onDelete() {
  if (!currentVideo.value) return
  if (!confirm('Are you sure you want to delete this video?')) return
  
  isDeleting.value = true
  
  try {
    await deleteVideo(currentVideo.value.id)
    router.push('/')
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : 'Failed to delete video.'
    isDeleting.value = false
  }
}

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
      <div class="actions" v-if="isOwner">
        <button v-if="!isEditing" @click="startEditing" class="btn-edit">
          <AppIcon name="edit" :size="14" /> Edit
        </button>
        <button v-if="!isEditing" @click="onDelete" :disabled="isDeleting" class="btn-delete">
          <AppIcon name="delete" :size="14" /> {{ isDeleting ? 'Deleting...' : 'Delete' }}
        </button>
      </div>

      <div v-if="isEditing" class="edit-form">
        <h2>Edit Video</h2>
        <label>
          Title
          <input v-model="editForm.title" type="text" />
        </label>
        <label>
          Description
          <textarea v-model="editForm.description" rows="4"></textarea>
        </label>
        <label>
          Category
          <select v-model="editForm.category">
            <option>Education</option>
            <option>Technology</option>
            <option>Nature</option>
            <option>Food</option>
            <option>Fitness</option>
            <option>Music</option>
            <option>Gaming</option>
          </select>
        </label>
        <label>
          Tags (comma-separated)
          <input v-model="editForm.tags" type="text" placeholder="e.g., tutorial, beginner" />
        </label>
        <div class="edit-actions">
          <button @click="saveChanges" :disabled="isSaving" class="btn-save">
            {{ isSaving ? 'Saving...' : 'Save Changes' }}
          </button>
          <button @click="cancelEditing" :disabled="isSaving" class="btn-cancel">
            Cancel
          </button>
        </div>
        <p v-if="editMessage" class="edit-message">{{ editMessage }}</p>
      </div>

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

.actions {
  display: flex;
  gap: 8px;
  margin-top: 12px;
}

.btn-edit,
.btn-delete,
.btn-save,
.btn-cancel {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border-radius: 8px;
  border: none;
  font-size: 14px;
  cursor: pointer;
  transition: background-color 150ms ease;
}

.btn-edit {
  background: #0ea5e9;
  color: #fff;
}

.btn-edit:hover {
  background: #0284c7;
}

.btn-delete {
  background: #ef4444;
  color: #fff;
}

.btn-delete:hover:not(:disabled) {
  background: #dc2626;
}

.btn-delete:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.edit-form {
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: #1a1a1a;
  padding: 16px;
  margin-top: 14px;
}

.edit-form h2 {
  color: #fff;
  margin-bottom: 12px;
  font-size: 18px;
}

.edit-form label {
  display: block;
  color: #c6cad2;
  margin-bottom: 10px;
  font-size: 14px;
}

.edit-form input,
.edit-form textarea,
.edit-form select {
  width: 100%;
  padding: 8px 12px;
  background: #2a2a2a;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 6px;
  color: #fff;
  margin-top: 4px;
  font-family: inherit;
}

.edit-form input:focus,
.edit-form textarea:focus,
.edit-form select:focus {
  outline: none;
  border-color: #0ea5e9;
  box-shadow: 0 0 0 2px rgba(14, 165, 233, 0.2);
}

.edit-actions {
  display: flex;
  gap: 8px;
  margin-top: 14px;
}

.btn-save {
  background: #10b981;
  color: #fff;
  flex: 1;
}

.btn-save:hover:not(:disabled) {
  background: #059669;
}

.btn-save:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-cancel {
  background: #6b7280;
  color: #fff;
  flex: 1;
}

.btn-cancel:hover:not(:disabled) {
  background: #4b5563;
}

.btn-cancel:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.edit-message {
  margin-top: 10px;
  padding: 8px 12px;
  background: rgba(16, 185, 129, 0.1);
  border: 1px solid #10b981;
  border-radius: 6px;
  color: #10b981;
  font-size: 14px;
}
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
