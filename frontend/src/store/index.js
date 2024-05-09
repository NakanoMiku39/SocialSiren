// Vuex 4 导入方法
import { createStore } from 'vuex';

const store = createStore({
  state() {
    return {
      isLoggedIn: false
    };
  },
  mutations: {
    setLogin(state, status) {
      state.isLoggedIn = status;
    },
    login(state) {
      state.isLoggedIn = true;
    },
    logout(state) {
      state.isLoggedIn = false;
    }
  },
  actions: {
    login({ commit }) {
      commit('setLogin', true);
    },
    logout({ commit }) {
      localStorage.removeItem('jwt');  // 清除本地存储的 JWT
      commit('setLogin', false);
    }
  }
});

export default store;
