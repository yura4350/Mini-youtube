<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppIcon from '@/components/icons/AppIcon.vue'
import { useAuthStore } from '@/stores/auth'
import { authService } from '@/services/auth'
import { fetchSubscribedChannelIds } from '@/services/dashboard'
import type { User } from '@/types/auth'

interface DirectMessage {
  type: 'direct_message'
  room_key: string
  sender_user_id: string
  sender_username: string
  peer_user_id: string
  message: string
  timestamp: string
}

function isDirectMessagePayload(value: unknown): value is DirectMessage {
  if (!value || typeof value !== 'object') return false
  const candidate = value as Record<string, unknown>
  return (
    candidate.type === 'direct_message' &&
    typeof candidate.room_key === 'string' &&
    typeof candidate.sender_user_id === 'string' &&
    typeof candidate.sender_username === 'string' &&
    typeof candidate.peer_user_id === 'string' &&
    typeof candidate.message === 'string' &&
    typeof candidate.timestamp === 'string'
  )
}

const authStore = useAuthStore()
const route = useRoute()
const router = useRouter()
const users = ref<User[]>([])
const selectedPeerId = ref('')
const messages = ref<DirectMessage[]>([])
const inputMessage = ref('')
const status = ref('Disconnected')
const chatHint = ref('')
const messagesContainer = ref<HTMLElement | null>(null)
let socket: WebSocket | null = null

const peers = computed(() => {
  const currentUser = authStore.currentUser
  if (!currentUser) return []

  const allOtherUsers = users.value.filter((user) => user.id !== currentUser.id)
  const subscribedIds = new Set(currentUser.subscribedTo)
  const subscribedUsers = allOtherUsers.filter((user) => subscribedIds.has(user.id))

  return subscribedUsers.length > 0 ? subscribedUsers : allOtherUsers
})

const selectedPeer = computed(() => peers.value.find((peer) => peer.id === selectedPeerId.value) || null)

function scrollBottom() {
  if (!messagesContainer.value) return
  messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
}

function closeSocket() {
  if (socket) {
    socket.close()
    socket = null
  }
}

function connectSocket() {
  closeSocket()

  const currentUser = authStore.currentUser
  if (!currentUser || !selectedPeer.value) {
    status.value = 'Select a conversation'
    return
  }

  const explicitWsBase = (import.meta.env.VITE_COMM_WS_BASE_URL || '').trim()
  const wsBase = explicitWsBase
    ? explicitWsBase.replace(/\/$/, '')
    : `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://localhost:8002`

  const query = new URLSearchParams({
    user_id: currentUser.id,
    username: currentUser.username,
    peer_id: selectedPeer.value.id,
  })

  status.value = 'Connecting...'
  chatHint.value = ''
  messages.value = []
  socket = new WebSocket(`${wsBase}/comm/direct-chat?${query.toString()}`)

  socket.onopen = () => {
    status.value = 'Live'
  }

  socket.onmessage = async (event) => {
    try {
      const payload = JSON.parse(event.data) as
        | { type: 'history'; messages: DirectMessage[] }
        | { type: 'direct_message'; [key: string]: unknown }
        | { type: 'error'; message: string }

      if (payload.type === 'history') {
        messages.value = payload.messages
        await nextTick()
        scrollBottom()
        return
      }

      if (payload.type === 'error') {
        if (payload.message.includes('only send one message')) {
          chatHint.value = 'You can send only one message unless both users follow each other.'
        } else {
          status.value = payload.message
        }
        return
      }

      if (isDirectMessagePayload(payload)) {
        chatHint.value = ''
        messages.value.push(payload)
        await nextTick()
        scrollBottom()
      }
    } catch {
      // Ignore malformed websocket payload.
    }
  }

  socket.onclose = () => {
    status.value = 'Disconnected'
  }

  socket.onerror = () => {
    status.value = 'Connection error'
  }
}

function sendMessage() {
  if (!socket || socket.readyState !== WebSocket.OPEN) return
  const message = inputMessage.value.trim()
  if (!message) return

  chatHint.value = ''
  socket.send(JSON.stringify({ message }))
  inputMessage.value = ''
}

function pickPeer(peerId: string) {
  selectedPeerId.value = peerId
  router.replace({ name: 'messages', query: { peer: peerId } })
}

async function refreshDirectoryAndSubscriptions() {
  const currentUser = authStore.currentUser
  if (!currentUser) {
    users.value = []
    return
  }

  users.value = await authService.getAllUsers()
  try {
    const subscribedIds = await fetchSubscribedChannelIds(currentUser.id)
    if (authStore.currentUser?.id === currentUser.id) {
      authStore.currentUser.subscribedTo = subscribedIds
    }
  } catch {
    // Keep existing values when fetch fails.
  }
}

onMounted(async () => {
  await authStore.hydrate()
  await refreshDirectoryAndSubscriptions()

  const peerFromQuery = typeof route.query.peer === 'string' ? route.query.peer : ''
  if (peerFromQuery && peers.value.some((peer) => peer.id === peerFromQuery)) {
    selectedPeerId.value = peerFromQuery
  } else if (peers.value[0]) {
    selectedPeerId.value = peers.value[0].id
  }

  connectSocket()
})

onUnmounted(() => {
  closeSocket()
})

watch(
  () => selectedPeerId.value,
  () => {
    connectSocket()
  },
)

watch(
  () => authStore.currentUser?.id,
  async () => {
    await refreshDirectoryAndSubscriptions()
  },
)
</script>

<template>
  <main class="messages-page">
    <section class="messages-shell">
      <aside class="contact-list">
        <h2><AppIcon name="users" :size="16" /> Conversations</h2>

        <button
          v-for="peer in peers"
          :key="peer.id"
          class="contact-item"
          :class="{ active: peer.id === selectedPeerId }"
          @click="pickPeer(peer.id)"
        >
          <img :src="peer.avatar" :alt="peer.username" class="avatar" />
          <div>
            <p class="name">{{ peer.username }}</p>
            <small>{{ peer.email }}</small>
          </div>
        </button>

        <p v-if="peers.length === 0" class="empty">No contacts available.</p>
      </aside>

      <section class="chat-panel">
        <header class="chat-header">
          <h1>
            <AppIcon name="bell" :size="16" />
            {{ selectedPeer ? `Chat with ${selectedPeer.username}` : 'Direct Messages' }}
          </h1>
          <span class="status">{{ status }}</span>
        </header>
        <p v-if="chatHint" class="chat-hint">{{ chatHint }}</p>

        <div ref="messagesContainer" class="chat-messages">
          <article
            v-for="(item, index) in messages"
            :key="`${item.timestamp}-${index}`"
            class="msg"
            :class="{ mine: authStore.currentUser?.id === item.sender_user_id }"
          >
            <p class="meta">
              <strong>{{ item.sender_username }}</strong>
              <small>{{ new Date(item.timestamp).toLocaleTimeString() }}</small>
            </p>
            <p>{{ item.message }}</p>
          </article>

          <p v-if="messages.length === 0" class="empty">No messages yet.</p>
        </div>

        <form class="composer" @submit.prevent="sendMessage">
          <input
            v-model="inputMessage"
            type="text"
            placeholder="Say hi..."
            maxlength="2000"
            :disabled="status !== 'Live'"
          />
          <button type="submit" :disabled="!inputMessage.trim() || status !== 'Live'">Send</button>
        </form>
      </section>
    </section>
  </main>
</template>

<style scoped>
.messages-page {
  max-width: 1320px;
  margin: 0 auto;
  padding: 20px 16px 34px;
}

.messages-shell {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 12px;
}

.contact-list,
.chat-panel {
  border: 1px solid var(--border-default);
  border-radius: 14px;
  background: var(--bg-1);
}

.contact-list {
  padding: 12px;
}

.contact-list h2 {
  color: var(--text-main);
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 10px;
}

.contact-item {
  width: 100%;
  border: 1px solid var(--border-default);
  background: var(--bg-2);
  color: var(--text-body);
  border-radius: 10px;
  padding: 8px;
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  cursor: pointer;
}

.contact-item.active {
  border-color: var(--accent-outline-soft);
  background: var(--accent-wash-hover);
}

.avatar {
  width: 36px;
  height: 36px;
  border-radius: 999px;
}

.name {
  color: var(--text-main);
}

.contact-item small,
.empty {
  color: var(--text-muted);
}

.chat-panel {
  display: grid;
  grid-template-rows: auto 1fr auto;
}

.chat-header {
  padding: 12px;
  border-bottom: 1px solid var(--border-faint);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.chat-header h1 {
  color: var(--text-main);
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 18px;
}

.status {
  border: 1px solid var(--border-strong);
  border-radius: 999px;
  color: var(--text-soft);
  font-size: 12px;
  padding: 2px 8px;
}

.chat-hint {
  margin: 10px 12px 0;
  border: 1px solid rgba(245, 158, 11, 0.45);
  background: rgba(245, 158, 11, 0.12);
  color: var(--warn-text);
  border-radius: 8px;
  padding: 8px 10px;
  font-size: 13px;
}

.chat-messages {
  height: 480px;
  overflow-y: auto;
  padding: 12px;
}

.msg {
  max-width: 72%;
  margin-bottom: 10px;
  border: 1px solid var(--border-default);
  background: var(--bg-3);
  border-radius: 10px;
  padding: 8px;
}

.msg.mine {
  margin-left: auto;
  border-color: rgba(239, 68, 68, 0.6);
  background: var(--accent-wash-hover);
}

.meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  color: var(--text-muted);
  font-size: 12px;
}

.msg strong {
  color: var(--text-main);
}

.msg p:last-child {
  margin-top: 3px;
  color: var(--text-body);
  white-space: pre-wrap;
  word-break: break-word;
}

.composer {
  border-top: 1px solid var(--border-faint);
  padding: 10px;
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 8px;
}

.composer input {
  border-radius: 999px;
  border: 1px solid var(--border-strong);
  background: var(--bg-4);
  color: var(--text-main);
  padding: 9px 12px;
}

.composer button {
  border-radius: 999px;
  border: none;
  background: linear-gradient(135deg, var(--accent), var(--accent-soft));
  color: var(--text-inverse);
  padding: 8px 14px;
}

.composer button:disabled,
.composer input:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

@media (max-width: 980px) {
  .messages-shell {
    grid-template-columns: 1fr;
  }

  .chat-messages {
    height: 360px;
  }
}
</style>
