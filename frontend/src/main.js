import { createApp } from 'vue';
import App from './App.vue';
import router from './router';  // 确保路由配置文件正确导入
import store from './store';  // 引入 Vuex store

// 创建应用实例
const app = createApp(App);

// 使用路由和状态管理
app.use(router);
app.use(store);

// 挂载应用到 DOM
app.mount('#app');
