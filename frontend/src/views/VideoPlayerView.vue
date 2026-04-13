<script setup lang="ts">
import { computed, onMounted, onUnmounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import VideoCard from '@/components/VideoCard.vue'
import AppIcon from '@/components/icons/AppIcon.vue'
import { formatViews } from '@/services/video-format'
import { fetchVideoById, fetchVideos, updateVideo, deleteVideo } from '@/services/videos'
import { toApiUploaderId } from '@/services/user-id'
import { recordWatchEvent, fetchSubscribedChannelIds, subscribeToChannel, unsubscribeFromChannel } from '@/services/dashboard'
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
const subscribeLoading = ref(false)
const subscribeMessage = ref('')
const subscribedChannelIds = ref<string[]>([])
const chatMessages = ref<ChatMessage[]>([])
const chatInput = ref('')
const chatConnected = ref(false)
const chatStatus = ref('Connecting...')
const chatContainer = ref<HTMLElement | null>(null)
const videoElement = ref<HTMLVideoElement | null>(null)
let chatSocket: WebSocket | null = null
let watchEventInterval: ReturnType<typeof setInterval> | null = null

interface ChatMessage {
  type: 'chat_message' | 'system'
  video_id: string
  user_id: string
  username: string
  message: string
  timestamp: string
}

function isChatMessagePayload(value: unknown): value is ChatMessage {
  if (!value || typeof value !== 'object') return false
  const candidate = value as Record<string, unknown>
  return (
    (candidate.type === 'chat_message' || candidate.type === 'system') &&
    typeof candidate.video_id === 'string' &&
    typeof candidate.user_id === 'string' &&
    typeof candidate.username === 'string' &&
    typeof candidate.message === 'string' &&
    typeof candidate.timestamp === 'string'
  )
}

const editForm = reactive({
  title: '',
  description: '',
  category: '',
  tags: '',
})

const playbackUrl = computed(() => {
  if (!currentVideo.value) return ''

  const defaultHost =
    typeof window !== 'undefined' && window.location.hostname === 'localhost'
      ? '127.0.0.1'
      : typeof window !== 'undefined'
        ? window.location.hostname
        : 'localhost'
  const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL || `http://${defaultHost}:8000`).replace(/\/$/, '')
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

async function loadMySubscriptions() {
  if (!authStore.currentUser) {
    subscribedChannelIds.value = []
    return
  }

  try {
    subscribedChannelIds.value = await fetchSubscribedChannelIds(authStore.currentUser.id)
  } catch {
    subscribedChannelIds.value = []
  }
}

function scrollChatToBottom() {
  if (!chatContainer.value) return
  chatContainer.value.scrollTop = chatContainer.value.scrollHeight
}

function closeChatSocket() {
  if (chatSocket) {
    chatSocket.close()
    chatSocket = null
  }
}

function stopRecordingWatchEvents() {
  if (watchEventInterval) {
    clearInterval(watchEventInterval)
    watchEventInterval = null
  }
}

function startRecordingWatchEvents() {
  stopRecordingWatchEvents()

  if (!authStore.currentUser || !currentVideo.value) return

  recordWatchEvent(authStore.currentUser.id, currentVideo.value.id, 0).catch(() => {
    // Silently fail - don't show error to user
  })

  watchEventInterval = setInterval(() => {
    if (!videoElement.value || !authStore.currentUser || !currentVideo.value) return
    const currentPosition = Math.floor(videoElement.value.currentTime)
    recordWatchEvent(authStore.currentUser.id, currentVideo.value.id, currentPosition).catch(() => {
      // Silently fail - don't show error to user
    })
  }, 10000)
}

function connectChat() {
  closeChatSocket()

  if (!currentVideo.value || !authStore.currentUser) {
    chatMessages.value = []
    chatConnected.value = false
    chatStatus.value = 'Login required to join chat'
    return
  }

  const explicitWsBase = (import.meta.env.VITE_COMM_WS_BASE_URL || '').trim()
  const defaultHost =
    typeof window !== 'undefined' && window.location.hostname === 'localhost'
      ? '127.0.0.1'
      : typeof window !== 'undefined'
        ? window.location.hostname
        : 'localhost'
  const wsBase = explicitWsBase
    ? explicitWsBase.replace(/\/$/, '')
    : `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${defaultHost}:8002`

  const params = new URLSearchParams({
    video_id: currentVideo.value.id,
    user_id: authStore.currentUser.id,
    username: authStore.currentUser.username,
  })

  chatStatus.value = 'Connecting...'
  chatSocket = new WebSocket(`${wsBase}/comm/real-time-chat?${params.toString()}`)

  chatSocket.onopen = () => {
    chatConnected.value = true
    chatStatus.value = 'Live'
  }

  chatSocket.onmessage = (event) => {
    try {
      const payload = JSON.parse(event.data) as
        | { type: 'history'; messages: ChatMessage[] }
        | { type: 'chat_message' | 'system'; message: string; [key: string]: unknown }
        | { type: 'error'; message: string }

      if (payload.type === 'history') {
        chatMessages.value = payload.messages
        setTimeout(scrollChatToBottom, 0)
        return
      }

      if (payload.type === 'error') {
        chatStatus.value = payload.message
        return
      }

      if (isChatMessagePayload(payload)) {
        chatMessages.value.push(payload)
        setTimeout(scrollChatToBottom, 0)
      }
    } catch {
      // Ignore malformed messages from peers.
    }
  }

  chatSocket.onclose = () => {
    chatConnected.value = false
    chatStatus.value = 'Disconnected'
  }

  chatSocket.onerror = () => {
    chatConnected.value = false
    chatStatus.value = 'Connection error'
  }
}

function sendChatMessage() {
  if (!chatSocket || chatSocket.readyState !== WebSocket.OPEN) return
  const text = chatInput.value.trim()
  if (!text) return

  chatSocket.send(JSON.stringify({ message: text }))
  chatInput.value = ''
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
  loadMySubscriptions()
})

onUnmounted(() => {
  closeChatSocket()
  stopRecordingWatchEvents()
})

const isOwner = computed(() => {
  if (!currentVideo.value || !authStore.currentUser) return false
  const currentUserUploaderId = toApiUploaderId(authStore.currentUser.id)
  if (currentUserUploaderId === null) return false
  return String(currentVideo.value.authorId) === String(currentUserUploaderId)
})

const canSubscribe = computed(() => {
  if (!authStore.currentUser || !currentVideo.value) return false
  return !isOwner.value
})

const isSubscribed = computed(() => {
  if (!currentVideo.value) return false
  return subscribedChannelIds.value.includes(String(currentVideo.value.authorId))
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

async function toggleSubscription() {
  if (!authStore.currentUser || !currentVideo.value || isOwner.value) return

  subscribeLoading.value = true
  subscribeMessage.value = ''

  const subscriberId = authStore.currentUser.id
  const channelId = String(currentVideo.value.authorId)

  try {
    if (isSubscribed.value) {
      await unsubscribeFromChannel(subscriberId, channelId)
      subscribeMessage.value = ''
      subscribedChannelIds.value = subscribedChannelIds.value.filter((id) => id !== channelId)
      if (authStore.currentUser) {
        authStore.currentUser.subscribedTo = authStore.currentUser.subscribedTo.filter((id) => id !== channelId)
      }
    } else {
      await subscribeToChannel(subscriberId, channelId)
      subscribeMessage.value = ''
      if (!subscribedChannelIds.value.includes(channelId)) {
        subscribedChannelIds.value = [...subscribedChannelIds.value, channelId]
      }
      if (authStore.currentUser && !authStore.currentUser.subscribedTo.includes(channelId)) {
        authStore.currentUser.subscribedTo = [...authStore.currentUser.subscribedTo, channelId]
      }
    }
  } catch (error) {
    subscribeMessage.value = error instanceof Error ? error.message : 'Subscription update failed.'
  } finally {
    subscribeLoading.value = false
  }
}

watch(
  () => route.params.id,
  () => {
    subscribeMessage.value = ''
    stopRecordingWatchEvents()
    loadCurrentVideo()
  },
)

watch(
  () => [currentVideo.value?.id, authStore.currentUser?.id],
  () => {
    connectChat()
    loadMySubscriptions()
  },
)

watch(
  () => videoElement.value?.paused,
  (isPaused) => {
    if (isPaused) {
      stopRecordingWatchEvents()
    } else {
      startRecordingWatchEvents()
    }
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
        <video ref="videoElement" :src="playbackUrl" :poster="currentVideo.thumbnail" controls preload="metadata" @play="startRecordingWatchEvents" @pause="stopRecordingWatchEvents" />
      </div>

      <h1>{{ currentVideo.title }}</h1>
      <p class="meta">
        <span><AppIcon name="views" :size="14" /> {{ formatViews(currentVideo.views) }} views</span>
        <span>•</span>
        <span><AppIcon name="clock" :size="14" /> {{ new Date(currentVideo.uploadDate).toLocaleDateString() }}</span>
      </p>
      <div class="actions">
        <button v-if="canSubscribe" @click="toggleSubscription" :disabled="subscribeLoading" class="btn-subscribe">
          <AppIcon name="users" :size="14" />
          {{ subscribeLoading ? 'Updating...' : isSubscribed ? 'Unsubscribe' : 'Subscribe' }}
        </button>
        <button v-if="isOwner && !isEditing" @click="startEditing" class="btn-edit">
          <AppIcon name="video" :size="14" /> Edit
        </button>
        <button v-if="isOwner && !isEditing" @click="onDelete" :disabled="isDeleting" class="btn-delete">
          <AppIcon name="empty" :size="14" /> {{ isDeleting ? 'Deleting...' : 'Delete' }}
        </button>
      </div>
      <p v-if="subscribeMessage" class="subscribe-error">{{ subscribeMessage }}</p>

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
      <section class="chat-card">
        <header class="chat-header">
          <h3><AppIcon name="users" :size="15" /> Live chat</h3>
          <span :class="['chat-state', { live: chatConnected }]">{{ chatStatus }}</span>
        </header>

        <div ref="chatContainer" class="chat-messages">
          <p v-if="chatMessages.length === 0" class="chat-empty">No messages yet.</p>

          <article
            v-for="(item, index) in chatMessages"
            :key="`${item.timestamp}-${index}`"
            class="chat-row"
            :class="{ system: item.type === 'system' }"
          >
            <p class="chat-meta">
              <strong>{{ item.username }}</strong>
              <small>{{ new Date(item.timestamp).toLocaleTimeString() }}</small>
            </p>
            <p class="chat-text">{{ item.message }}</p>
          </article>
        </div>

        <form class="chat-form" @submit.prevent="sendChatMessage">
          <input
            v-model="chatInput"
            :disabled="!authStore.currentUser || !chatConnected"
            type="text"
            placeholder="Say something..."
            maxlength="2000"
          />
          <button type="submit" :disabled="!chatInput.trim() || !chatConnected">
            <AppIcon name="play" :size="12" /> Send
          </button>
        </form>
      </section>

      <h2 class="related-heading"><AppIcon name="video" :size="16" /> Related videos</h2>
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

.actions {
  display: flex;
  gap: 8px;
  margin-top: 12px;
}

.btn-edit,
.btn-delete,
.btn-subscribe,
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

.btn-subscribe {
  background: #f59e0b;
  color: #111827;
}

.btn-subscribe:hover:not(:disabled) {
  background: #d97706;
}

.btn-subscribe:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.subscribe-error {
  margin-top: 8px;
  color: #ff9f8b;
  font-size: 14px;
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

.related-heading {
  margin-top: 16px;
}

.chat-card {
  margin-top: 14px;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: #1a1a1a;
  padding: 12px;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.chat-header h3 {
  color: #f4f5f8;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.chat-state {
  color: #9ca3af;
  font-size: 12px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 999px;
  padding: 2px 8px;
}

.chat-state.live {
  color: #d1fae5;
  border-color: rgba(16, 185, 129, 0.65);
  background: rgba(16, 185, 129, 0.2);
}

.chat-messages {
  height: 260px;
  overflow-y: auto;
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: #111;
  padding: 10px;
}

.chat-empty {
  color: #8f97a4;
  text-align: center;
  margin-top: 100px;
}

.chat-row {
  margin-bottom: 10px;
}

.chat-row.system .chat-meta strong {
  color: #fda4af;
}

.chat-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.chat-meta strong {
  color: #fff;
  font-size: 13px;
}

.chat-meta small {
  color: #8f97a4;
  font-size: 11px;
}

.chat-text {
  color: #d5dae3;
  margin-top: 2px;
  line-height: 1.45;
  font-size: 14px;
  white-space: pre-wrap;
  word-break: break-word;
}

.chat-form {
  margin-top: 10px;
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 8px;
}

.chat-form input {
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  background: #121212;
  color: #fff;
  padding: 9px 12px;
}

.chat-form button {
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.24);
  background: rgba(220, 38, 38, 0.92);
  color: #fff;
  padding: 8px 12px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.chat-form button:disabled,
.chat-form input:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

@media (max-width: 1100px) {
  .watch-page {
    grid-template-columns: 1fr;
  }

  .chat-messages {
    height: 220px;
  }
}
</style>
