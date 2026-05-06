import { createRouter, createWebHistory } from 'vue-router'
import MapView from '../views/MapView.vue'

export default createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: MapView },
    { path: '/diary', component: () => import('../views/diary/Index.vue') },
    { path: '/diary/publish', component: () => import('../views/diary/Publish.vue') },
  ]
})
