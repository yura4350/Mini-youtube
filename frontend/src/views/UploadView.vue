<script setup lang="ts">
import { reactive, ref } from 'vue'
import AppIcon from '@/components/icons/AppIcon.vue'

const loading = ref(false)
const successMessage = ref('')

const form = reactive({
  title: '',
  description: '',
  category: 'Education',
  tags: '',
})

async function onSubmit() {
  successMessage.value = ''
  loading.value = true
  await new Promise((resolve) => setTimeout(resolve, 700))
  loading.value = false
  successMessage.value = 'Upload draft submitted. Backend integration is the next step.'
}
</script>

<template>
  <main class="upload-page">
    <section class="upload-card">
      <h1><AppIcon name="upload" :size="22" /> Upload video</h1>
      <p class="sub">Match the Figma flow for creator upload. API integration can be plugged in directly.</p>

      <form class="form" @submit.prevent="onSubmit">
        <label>
          Title
          <input v-model="form.title" type="text" placeholder="Enter video title" required />
        </label>

        <label>
          Description
          <textarea v-model="form.description" rows="5" placeholder="Describe your video"></textarea>
        </label>

        <label>
          Category
          <select v-model="form.category">
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
          Tags
          <input v-model="form.tags" type="text" placeholder="tutorial, tech, guide" />
        </label>

        <button :disabled="loading" type="submit">
          <AppIcon name="upload" :size="15" /> {{ loading ? 'Submitting...' : 'Submit Upload' }}
        </button>
      </form>

      <p v-if="successMessage" class="ok">
        <AppIcon name="check" :size="15" /> {{ successMessage }}
      </p>
    </section>
  </main>
</template>

<style scoped>
.upload-page {
  max-width: 1000px;
  margin: 0 auto;
  padding: 22px 16px 34px;
}

.upload-card {
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: #1a1a1a;
  padding: 20px;
}

h1 {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: #fff;
  font-size: 28px;
}

.sub {
  color: #9ca3af;
  margin-top: 2px;
}

.form {
  margin-top: 18px;
  display: grid;
  gap: 12px;
}

label {
  display: grid;
  gap: 6px;
  color: #e8eaef;
  font-size: 14px;
}

input,
textarea,
select {
  background: #0f0f0f;
  border: 1px solid rgba(255, 255, 255, 0.17);
  color: #fff;
  border-radius: 10px;
  padding: 10px 12px;
}

button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  margin-top: 8px;
  border: none;
  border-radius: 10px;
  padding: 11px 14px;
  color: #fff;
  background: linear-gradient(135deg, #dc2626, #ef4444);
  font-weight: 600;
}

.ok {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-top: 12px;
  color: #9ff0b1;
}
</style>
