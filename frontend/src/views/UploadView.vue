<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import AppIcon from '@/components/icons/AppIcon.vue'
import { useAuthStore } from '@/stores/auth'
import { uploadVideo } from '@/services/videos'
import { toApiUploaderId } from '@/services/user-id'
import { fetchAiTagTaxonomy, type AiTagTaxonomyItem } from '@/services/intelligence'

const authStore = useAuthStore()
const loading = ref(false)
const successMessage = ref('')
const errorMessage = ref('')
const selectedFile = ref<File | null>(null)
const videoDuration = ref<number>(0)
const tagOptions = ref<AiTagTaxonomyItem[]>([])
const tagLoading = ref(false)
const selectedCanonicalTags = ref<string[]>([])

const form = reactive({
  title: '',
  description: '',
})

const tagsByCategory = computed<Record<string, AiTagTaxonomyItem[]>>(() => {
  const grouped: Record<string, AiTagTaxonomyItem[]> = {}
  for (const tag of tagOptions.value) {
    const category = tag.category
    const list = grouped[category] ?? []
    list.push(tag)
    grouped[category] = list
  }
  return grouped
})

function _displayCategory(raw: string): string {
  return raw
    .split('-')
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ')
}

const inferredPrimaryCategory = computed<string | null>(() => {
  if (selectedCanonicalTags.value.length === 0) return null
  const canonicalToCategory = new Map(tagOptions.value.map((item) => [item.canonical_tag, item.category]))
  const counts: Record<string, number> = {}
  for (const tag of selectedCanonicalTags.value) {
    const category = canonicalToCategory.get(tag)
    if (!category) continue
    counts[category] = (counts[category] || 0) + 1
  }
  const entries = Object.entries(counts)
  if (entries.length === 0) return null
  entries.sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
  const top = entries[0]
  if (!top) return null
  return top[0]
})

const uploadCategory = computed<string>(() => {
  if (!inferredPrimaryCategory.value) return 'General'
  return _displayCategory(inferredPrimaryCategory.value)
})

async function loadTagTaxonomy() {
  tagLoading.value = true
  try {
    const result = await fetchAiTagTaxonomy()
    tagOptions.value = result.tags || []
  } catch {
    tagOptions.value = []
  } finally {
    tagLoading.value = false
  }
}

function toggleTag(canonicalTag: string) {
  if (selectedCanonicalTags.value.includes(canonicalTag)) {
    selectedCanonicalTags.value = selectedCanonicalTags.value.filter((v) => v !== canonicalTag)
    return
  }
  selectedCanonicalTags.value = [...selectedCanonicalTags.value, canonicalTag]
}

function onFileChange(event: Event) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0] || null
  selectedFile.value = file
  
  if (file) {
    // Extract duration from video file metadata
    const video = document.createElement('video')
    video.src = URL.createObjectURL(file)
    video.onloadedmetadata = () => {
      videoDuration.value = Math.round(video.duration)
      URL.revokeObjectURL(video.src)
    }
  } else {
    videoDuration.value = 0
  }
}

async function onSubmit() {
  errorMessage.value = ''
  successMessage.value = ''

  if (!selectedFile.value) {
    errorMessage.value = 'Please choose a video file.'
    return
  }

  const uploaderId = toApiUploaderId(authStore.currentUser?.id)
  if (uploaderId === null) {
    errorMessage.value = 'Current user id is not compatible with upload API.'
    return
  }

  loading.value = true

  try {
    const created = await uploadVideo({
      file: selectedFile.value,
      title: form.title,
      description: form.description,
      category: uploadCategory.value,
      tags: selectedCanonicalTags.value.join(','),
      uploaderId,
      durationSeconds: videoDuration.value,
    })

    successMessage.value = `Uploaded "${created.title}" successfully.`
    form.title = ''
    form.description = ''
    selectedCanonicalTags.value = []
    selectedFile.value = null
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : 'Upload failed.'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  void loadTagTaxonomy()
})
</script>

<template>
  <main class="upload-page">
    <section class="upload-card">
      <h1><AppIcon name="upload" :size="22" /> Upload video</h1>
      <p class="sub">Upload a video file and metadata to the Video CRUD service.</p>
      <p class="subtle-note">
        Category is auto-derived from your selected canonical tags.
      </p>
      <p class="subtle-note">
        If you select tags manually, AI auto-tagging will be skipped for this upload. If you leave tags empty, AI
        will generate tags automatically from your video transcript.
      </p>

      <form class="form" @submit.prevent="onSubmit">
        <label>
          Video file
          <input type="file" accept="video/*,.mp4,.webm,.mov" @change="onFileChange" required />
        </label>

        <label>
          Title
          <input v-model="form.title" type="text" placeholder="Enter video title" required />
        </label>

        <label>
          Description
          <textarea v-model="form.description" rows="5" placeholder="Describe your video"></textarea>
        </label>

        <label>
          Canonical tags (optional, leave empty for AI auto-generation)
          <div class="tag-box">
            <p v-if="tagLoading" class="muted-mini">Loading canonical tags...</p>
            <template v-else>
              <div v-if="tagOptions.length === 0" class="muted-mini">
                Tag list is unavailable now. You can still upload without manual tags.
              </div>
              <div v-for="(items, category) in tagsByCategory" :key="category" class="tag-group">
                <div class="tag-category">{{ category }}</div>
                <div class="tag-grid">
                  <button
                    v-for="item in items"
                    :key="item.canonical_tag"
                    type="button"
                    class="tag-chip"
                    :class="{ active: selectedCanonicalTags.includes(item.canonical_tag) }"
                    @click="toggleTag(item.canonical_tag)"
                  >
                    {{ item.display_name }}
                  </button>
                </div>
              </div>
            </template>
          </div>
          <p class="muted-mini category-note">
            Primary category:
            {{
              inferredPrimaryCategory
                ? _displayCategory(inferredPrimaryCategory)
                : 'General (will be inferred by AI when tags are auto-generated)'
            }}
          </p>
        </label>

        <button :disabled="loading" type="submit" class="submit-btn">
          <AppIcon name="upload" :size="15" /> {{ loading ? 'Uploading...' : 'Upload Video' }}
        </button>
      </form>

      <p v-if="errorMessage" class="error">
        {{ errorMessage }}
      </p>

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
  border: 1px solid var(--border-default);
  background: var(--bg-1);
  padding: 20px;
}

h1 {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: var(--text-main);
  font-size: 28px;
}

.sub {
  color: var(--text-muted);
  margin-top: 2px;
}

.subtle-note {
  margin-top: 8px;
  color: #cbd5e1;
  font-size: 13px;
  line-height: 1.4;
}

.form {
  margin-top: 18px;
  display: grid;
  gap: 12px;
}

label {
  display: grid;
  gap: 6px;
  color: var(--text-body);
  font-size: 14px;
}

input,
textarea,
select {
  background: var(--bg-0);
  border: 1px solid var(--border-medium);
  color: var(--text-main);
  border-radius: 10px;
  padding: 10px 12px;
}

.submit-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  margin-top: 8px;
  border: none;
  border-radius: 10px;
  padding: 11px 14px;
  color: var(--text-inverse);
  background: linear-gradient(135deg, var(--accent), var(--accent-soft));
  font-weight: 600;
  cursor: pointer;
}

.submit-btn:disabled {
  cursor: not-allowed;
}

.tag-box {
  background: #0f0f0f;
  border: 1px solid rgba(255, 255, 255, 0.17);
  border-radius: 10px;
  padding: 10px;
}

.muted-mini {
  color: #9ca3af;
  font-size: 12px;
}

.tag-group + .tag-group {
  margin-top: 10px;
}

.tag-category {
  font-size: 12px;
  color: #9ca3af;
  text-transform: capitalize;
  margin-bottom: 6px;
}

.tag-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tag-chip {
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  background: #171717;
  color: #e5e7eb;
  padding: 6px 10px;
  font-size: 12px;
  line-height: 1;
  cursor: pointer;
}

.tag-chip.active {
  background: #dc2626;
  border-color: #dc2626;
  color: #fff;
}

.ok {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-top: 12px;
  color: #9ff0b1;
}

.error {
  margin-top: 12px;
  color: var(--accent-text-mid);
}
</style>
