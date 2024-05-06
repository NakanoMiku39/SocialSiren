import { createRouter, createWebHistory } from 'vue-router';
import Home from '../components/Home.vue';
import DataSender from '../components/DataSender.vue';

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home
  },
  {
    path: '/send-data',
    name: 'SendData',
    component: DataSender
  }
];

const router = createRouter({
  history: createWebHistory(import.meta.env.VITE_BASE_URL),
  routes
});

export default router;
