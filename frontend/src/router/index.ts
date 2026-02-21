import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import DashboardView from '../views/DashboardView.vue'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'dashboard',
    component: DashboardView,
  },
  {
    path: '/target/:id',
    name: 'target-detail',
    component: () => import('../views/TargetDetailView.vue'),
  },
  {
    path: '/sso/callback',
    name: 'sso-callback',
    component: () => import('../views/SSOCallbackView.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
