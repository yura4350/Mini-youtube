<script setup lang="ts">
import { computed, onMounted, reactive, ref, watchEffect } from 'vue'
import VideoCard from '@/components/VideoCard.vue'
import AppIcon from '@/components/icons/AppIcon.vue'
import { useAuthStore } from '@/stores/auth'
import { fetchVideos } from '@/services/videos'
import type { VideoItem } from '@/types/video'

const authStore = useAuthStore()
const tab = ref<'videos' | 'subscriptions'>('videos')
const editMode = ref(false)
const message = ref('')
const loadingVideos = ref(false)
const videoError = ref('')
const allVideos = ref<VideoItem[]>([])

const form = reactive({
  username: '',
  bio: '',
})

watchEffect(() => {
  if (!authStore.currentUser) return
  form.username = authStore.currentUser.username
  form.bio = authStore.currentUser.bio
})

const userVideos = computed(() => {
  if (!authStore.currentUser) return []
  return allVideos.value.filter((video) => video.authorId === authStore.currentUser?.id)
})

const subscribedVideos = computed(() => {
  if (!authStore.currentUser) return []
  return allVideos.value.filter((video) => authStore.currentUser?.subscribedTo.includes(video.authorId))
})

async function loadVideos() {
  loadingVideos.value = true
  videoError.value = ''

  try {
    allVideos.value = await fetchVideos()
  } catch (error) {
    videoError.value = error instanceof Error ? error.message : 'Failed to load videos.'
  } finally {
    loadingVideos.value = false
  }
}

function saveProfile() {
  message.value = ''
  const result = authStore.updateProfile({ username: form.username, bio: form.bio })
  if (!result.ok) {
    message.value = result.message
    return
  }

  editMode.value = false
  message.value = result.message
}

onMounted(() => {
  loadVideos()
})
</script>

<template>
  <main v-if="authStore.currentUser" class="profile-page">
    <section class="profile-header">
      <img :src="authStore.currentUser.avatar" :alt="authStore.currentUser.username" class="avatar" />

      <div class="header-main">
        <h1>{{ authStore.currentUser.username }}</h1>
        <p class="email">{{ authStore.currentUser.email }}</p>
        <p class="bio">{{ authStore.currentUser.bio || 'No bio yet.' }}</p>

        <div class="stats">
          <span><AppIcon name="video" :size="14" /> {{ userVideos.length }} videos</span>
          <span
            ><AppIcon name="users" :size="14" />
            {{ authStore.currentUser.subscribedTo.length }} subscriptions</span
          >
          <span><AppIcon name="bell" :size="14" /> Notification inbox enabled</span>
        </div>
      </div>
    </section>

    <section class="editor">
      <header>
        <h2>Profile settings</h2>
        <button v-if="!editMode" class="ghost" @click="editMode = true">
          <AppIcon name="user" :size="14" /> Edit profile
        </button>
      </header>

      <div v-if="editMode" class="form-grid">
        <label>
          Username
          <input v-model="form.username" type="text" />
        </label>

        <label>
          Bio
          <textarea v-model="form.bio" rows="3"></textarea>
        </label>

        <div class="actions">
          <button @click="saveProfile"><AppIcon name="check" :size="14" /> Save</button>
          <button class="ghost" @click="editMode = false"><AppIcon name="logout" :size="14" /> Cancel</button>
        </div>
      </div>
    </section>

    <section class="tabs">
      <button :class="{ active: tab === 'videos' }" @click="tab = 'videos'">
        <AppIcon name="video" :size="14" /> My videos
      </button>
      <button :class="{ active: tab === 'subscriptions' }" @click="tab = 'subscriptions'">
        <AppIcon name="users" :size="14" /> Subscriptions
      </button>
      <RouterLink to="/notifications" class="inbox-link">
        <AppIcon name="bell" :size="14" /> Open notification inbox
      </RouterLink>
    </section>

    <section v-if="tab === 'videos'" class="video-grid">
      <p v-if="loadingVideos" class="muted">Loading videos...</p>
      <p v-else-if="videoError" class="muted">{{ videoError }}</p>
      <VideoCard v-for="video in userVideos" :key="video.id" :video="video" />
      <p v-if="!loadingVideos && !videoError && userVideos.length === 0" class="muted">No videos uploaded yet.</p>
    </section>

    <section v-if="tab === 'subscriptions'" class="video-grid">
      <p v-if="loadingVideos" class="muted">Loading videos...</p>
      <p v-else-if="videoError" class="muted">{{ videoError }}</p>
      <VideoCard v-for="video in subscribedVideos" :key="video.id" :video="video" />
      <p v-if="!loadingVideos && !videoError && subscribedVideos.length === 0" class="muted">No subscriptions yet.</p>
    </section>

    <p v-if="message" class="ok">{{ message }}</p>
  </main>
</template>

<style scoped>
.profile-page {
  max-width: 1320px;
  margin: 0 auto;
  padding: 22px 16px 34px;
}

.profile-header,
.editor,
.notification-item {
  border-radius: 14px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: #1a1a1a;
}

.profile-header {
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
  color: #fff;
  font-size: 28px;
}

.email,
.bio {
  color: #c2c8d2;
}

.stats {
  margin-top: 8px;
  color: #e8ebf2;
  display: flex;
  gap: 14px;
  flex-wrap: wrap;
  font-size: 14px;
}

.editor {
  margin-top: 12px;
  padding: 14px;
}

.editor header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.editor h2 {
  color: #fff;
  font-size: 18px;
}

.form-grid {
  margin-top: 10px;
  display: grid;
  gap: 10px;
}

label {
  display: grid;
  gap: 6px;
  color: #e9ebef;
  font-size: 14px;
}

input,
textarea {
  background: #0f0f0f;
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: #fff;
  border-radius: 9px;
  padding: 9px 11px;
}

.actions {
  display: flex;
  gap: 8px;
}

button {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border: none;
  border-radius: 9px;
  padding: 8px 12px;
  color: #fff;
  background: linear-gradient(135deg, #dc2626, #ef4444);
}

button.ghost {
  border: 1px solid rgba(255, 255, 255, 0.24);
  background: transparent;
}

.tabs {
  margin-top: 14px;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.tabs button {
  background: #161616;
  border: 1px solid rgba(255, 255, 255, 0.14);
  color: #dadde5;
}

.tabs button.active {
  background: rgba(220, 38, 38, 0.2);
  border-color: rgba(239, 68, 68, 0.75);
  color: #fff;
}

.inbox-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  text-decoration: none;
  border: 1px solid rgba(255, 255, 255, 0.16);
  border-radius: 9px;
  color: #e5e7eb;
  padding: 8px 12px;
  background: #161616;
}

.inbox-link:hover {
  border-color: rgba(239, 68, 68, 0.75);
  background: rgba(220, 38, 38, 0.16);
  color: #fff;
}

.video-grid {
  margin-top: 12px;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 16px;
}

.muted {
  color: #a7adba;
}

.ok {
  margin-top: 10px;
  color: #a7f3be;
}

@media (max-width: 760px) {
  .profile-header {
    grid-template-columns: 1fr;
  }
}
</style>
