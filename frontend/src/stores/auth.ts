import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { authService } from '@/services/auth'
import type { LoginPayload, RegisterPayload, User } from '@/types/auth'

export const useAuthStore = defineStore('auth', () => {
  const currentUser = ref<User | null>(null)

  const isAuthenticated = computed(() => currentUser.value !== null)

  function hydrate() {
    currentUser.value = authService.getCurrentUser()
  }

  function login(payload: LoginPayload) {
    const result = authService.login(payload)
    if (result.ok) {
      currentUser.value = result.user
    }
    return result
  }

  function register(payload: RegisterPayload) {
    const result = authService.register(payload)
    if (result.ok) {
      currentUser.value = result.user
    }
    return result
  }

  function updateProfile(update: Pick<User, 'username' | 'bio'>) {
    const result = authService.updateCurrentUser(update)
    if (result.ok) {
      currentUser.value = result.user
    }
    return result
  }

  function logout() {
    authService.logout()
    currentUser.value = null
  }

  return {
    currentUser,
    isAuthenticated,
    hydrate,
    login,
    register,
    updateProfile,
    logout,
  }
})
