<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppIcon from '@/components/icons/AppIcon.vue'
import { useAuthStore } from '@/stores/auth'
import { authService } from '@/services/auth'
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
        status.value = payload.message
        return
      }

      if (isDirectMessagePayload(payload)) {
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

  socket.send(JSON.stringify({ message }))
  inputMessage.value = ''
}

function pickPeer(peerId: string) {
  selectedPeerId.value = peerId
  router.replace({ name: 'messages', query: { peer: peerId } })
}

onMounted(() => {
  authStore.hydrate()
  users.value = authService.getAllUsers()

  const peerFromQuery = typeof route.query.peer === 'string' ? route.query.peer : ''
  if (peerFromQuery) {
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
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 14px;
  background: #1a1a1a;
}

.contact-list {
  padding: 12px;
}

.contact-list h2 {
  color: #f4f5f8;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 10px;
}

.contact-item {
  width: 100%;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: #141414;
  color: #e5e7eb;
  border-radius: 10px;
  padding: 8px;
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  cursor: pointer;
}

.contact-item.active {
  border-color: rgba(239, 68, 68, 0.7);
  background: rgba(220, 38, 38, 0.2);
}

.avatar {
  width: 36px;
  height: 36px;
  border-radius: 999px;
}

.name {
  color: #fff;
}

.contact-item small,
.empty {
  color: #9ca3af;
}

.chat-panel {
  display: grid;
  grid-template-rows: auto 1fr auto;
}

.chat-header {
  padding: 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.chat-header h1 {
  color: #fff;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 18px;
}

.status {
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 999px;
  color: #cfd5df;
  font-size: 12px;
  padding: 2px 8px;
}

.chat-messages {
  height: 480px;
  overflow-y: auto;
  padding: 12px;
}

.msg {
  max-width: 72%;
  margin-bottom: 10px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: #121212;
  border-radius: 10px;
  padding: 8px;
}

.msg.mine {
  margin-left: auto;
  border-color: rgba(239, 68, 68, 0.6);
  background: rgba(220, 38, 38, 0.18);
}

.meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  color: #9ca3af;
  font-size: 12px;
}

.msg strong {
  color: #fff;
}

.msg p:last-child {
  margin-top: 3px;
  color: #e5e7eb;
  white-space: pre-wrap;
  word-break: break-word;
}

.composer {
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  padding: 10px;
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 8px;
}

.composer input {
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  background: #101010;
  color: #fff;
  padding: 9px 12px;
}

.composer button {
  border-radius: 999px;
  border: none;
  background: linear-gradient(135deg, #dc2626, #ef4444);
  color: #fff;
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
