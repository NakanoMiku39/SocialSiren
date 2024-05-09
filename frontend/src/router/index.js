import { createRouter, createWebHistory } from 'vue-router';
import Home from '../components/Home.vue';
import Auth from '../components/Auth.vue'; // 确保路径正确

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home
  },
  {
    path: '/auth',
    name: 'Auth',
    component: Auth  // 添加认证组件为路由
  }
];

const router = createRouter({
  history: createWebHistory(import.meta.env.VITE_BASE_URL),
  routes
});

export default router;
