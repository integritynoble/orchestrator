import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import DashboardView from '../views/DashboardView.vue'

let authInitialized = false

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'dashboard',
    component: DashboardView,
    meta: { requiresAuth: true },
  },
  {
    path: '/target/:id',
    name: 'target-detail',
    component: () => import('../views/TargetDetailView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/sso/callback',
    name: 'sso-callback',
    component: () => import('../views/SSOCallbackView.vue'),
    meta: { requiresAuth: false },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to) => {
  if (to.name === 'sso-callback') return true

  const authStore = useAuthStore()

  if (!authInitialized) {
    await authStore.initialize()
    authInitialized = true
  }

  if (to.meta.requiresAuth && !authStore.isLoggedIn) {
    authStore.login()
    return false
  }

  return true
})

export default router
