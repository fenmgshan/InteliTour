import { createRouter, createWebHistory } from 'vue-router'
import MapView from '../views/MapView.vue'
import DiaryView from '../views/DiaryView.vue'

export default createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: MapView },
    { path: '/diary', component: DiaryView },
  ]
})
