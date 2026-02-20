import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import DashboardView from '../views/DashboardView.vue'

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

router.beforeEach((to, _from, next) => {
  const authStore = useAuthStore()
  if (to.meta.requiresAuth && !authStore.isLoggedIn) {
    authStore.login()
    next(false)
  } else {
    next()
  }
})

export default router
