<script setup lang="ts">
import { computed, reactive, ref, watchEffect } from 'vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const editMode = ref(false)
const message = ref('')

const profileForm = reactive({
  username: '',
  bio: '',
})

watchEffect(() => {
  if (!authStore.currentUser) return
  profileForm.username = authStore.currentUser.username
  profileForm.bio = authStore.currentUser.bio
})

const userInitial = computed(() => authStore.currentUser?.username?.charAt(0).toUpperCase() ?? 'U')

function saveProfile() {
  message.value = ''
  const result = authStore.updateProfile({
    username: profileForm.username,
    bio: profileForm.bio,
  })

  if (!result.ok) {
    message.value = result.message
    return
  }

  editMode.value = false
  message.value = result.message
}
</script>

<template>
  <section class="profile-shell" v-if="authStore.currentUser">
    <article class="profile-card">
      <div class="hero-row">
        <div class="avatar-wrap">
          <img :src="authStore.currentUser.avatar" :alt="authStore.currentUser.username" />
          <span>{{ userInitial }}</span>
        </div>

        <div class="hero-text">
          <h1>{{ authStore.currentUser.username }}</h1>
          <p class="email">{{ authStore.currentUser.email }}</p>
          <p class="bio">{{ authStore.currentUser.bio || 'This user has not added a bio yet.' }}</p>
        </div>
      </div>

      <div class="quick-stats">
        <div>
          <p class="value">{{ authStore.currentUser.subscribedTo.length }}</p>
          <p class="label">Subscriptions</p>
        </div>
        <div>
          <p class="value">{{ authStore.currentUser.notifications.length }}</p>
          <p class="label">Notifications</p>
        </div>
        <div>
          <p class="value">{{ authStore.currentUser.isAdmin ? 'ADMIN' : 'USER' }}</p>
          <p class="label">Role</p>
        </div>
      </div>

      <section class="edit-panel">
        <header>
          <h2>Account Details</h2>
          <button v-if="!editMode" class="ghost" @click="editMode = true">Edit</button>
        </header>

        <div v-if="editMode" class="edit-grid">
          <label>
            Username
            <input v-model="profileForm.username" type="text" required />
          </label>

          <label>
            Bio
            <textarea v-model="profileForm.bio" rows="4" />
          </label>

          <div class="actions">
            <button @click="saveProfile">Save Changes</button>
            <button class="ghost" @click="editMode = false">Cancel</button>
          </div>
        </div>
      </section>

      <p v-if="message" class="status">{{ message }}</p>
    </article>
  </section>
</template>

<style scoped>
.profile-shell {
  min-height: calc(100vh - 68px);
  padding: 24px;
}

.profile-card {
  max-width: 900px;
  margin: 0 auto;
  background: rgba(16, 16, 16, 0.9);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 18px;
  padding: 24px;
}

.hero-row {
  display: flex;
  gap: 20px;
  align-items: center;
  margin-bottom: 20px;
}

.avatar-wrap {
  width: 120px;
  height: 120px;
  border-radius: 999px;
  overflow: hidden;
  position: relative;
  border: 2px solid rgba(255, 255, 255, 0.2);
}

.avatar-wrap img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-wrap span {
  position: absolute;
  right: -8px;
  bottom: -8px;
  width: 34px;
  height: 34px;
  border-radius: 999px;
  display: grid;
  place-items: center;
  background: #ff5a3d;
  color: #fff;
  font-weight: 700;
}

.hero-text h1 {
  font-size: 28px;
  color: #fff;
}

.email {
  color: #b8bcc4;
}

.bio {
  margin-top: 8px;
  color: #e1e4eb;
}

.quick-stats {
  margin: 22px 0;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  padding: 12px;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.value {
  color: #fff;
  font-size: 20px;
  font-weight: 700;
}

.label {
  color: #a3a8b2;
  font-size: 13px;
}

.edit-panel {
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  padding-top: 18px;
}

.edit-panel header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.edit-panel h2 {
  color: #f6f7fb;
  font-size: 18px;
}

.edit-grid {
  display: grid;
  gap: 14px;
}

label {
  display: grid;
  gap: 6px;
  color: #e8e8ea;
  font-size: 14px;
}

input,
textarea {
  width: 100%;
  border: 1px solid rgba(255, 255, 255, 0.18);
  background: rgba(8, 8, 8, 0.88);
  color: #fff;
  border-radius: 10px;
  padding: 10px 12px;
}

.actions {
  display: flex;
  gap: 10px;
}

button {
  border: none;
  border-radius: 10px;
  padding: 10px 14px;
  color: #fff;
  background: linear-gradient(135deg, #ff482b, #ff6f39);
  cursor: pointer;
}

button.ghost {
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.3);
}

.status {
  margin-top: 14px;
  color: #99f2a8;
}

@media (max-width: 768px) {
  .hero-row {
    flex-direction: column;
    align-items: flex-start;
  }

  .quick-stats {
    grid-template-columns: 1fr;
  }
}
</style>
