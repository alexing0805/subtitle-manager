import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import Movies from '../views/Movies.vue'
import TVShows from '../views/TVShows.vue'
import BatchUpload from '../views/BatchUpload.vue'
import Settings from '../views/Settings.vue'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: Dashboard
  },
  {
    path: '/movies',
    name: 'Movies',
    component: Movies
  },
  {
    path: '/tvshows',
    name: 'TVShows',
    component: TVShows
  },
  {
    path: '/anime',
    name: 'Anime',
    component: () => import('../views/Anime.vue')
  },
  {
    path: '/batch-upload',
    name: 'BatchUpload',
    component: BatchUpload
  },
  {
    path: '/settings',
    name: 'Settings',
    component: Settings
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
