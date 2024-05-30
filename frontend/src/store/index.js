import { createStore } from 'vuex';
import axios from 'axios';

const apiBase = 'http://10.129.199.88:2222';

export default createStore({
  state: {
    isLoggedIn: false,
    userVotesAndRatings: {
      resultVotes: [],
      warningVotes: [],
      resultRatings: [],
      warningRatings: []
    }
  },
  mutations: {
    setLoginState(state, isLoggedIn) {
      state.isLoggedIn = isLoggedIn;
    },
    setUserVotesAndRatings(state, data) {
      state.userVotesAndRatings = data;
    }
  },
  actions: {
    async fetchUserVotesAndRatings({ commit }) {
      try {
        const token = localStorage.getItem('jwt');
        if (!token) {
          throw new Error('No JWT token found');
        }
        const response = await axios.get(`${apiBase}/api/user-votes-and-ratings`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        commit('setUserVotesAndRatings', response.data);
        return response.data;  // 添加这行
      } catch (error) {
        // Detailed error logging
        if (error.response) {
          console.error('API response error:', error.response.data);
        } else if (error.request) {
          console.error('No response received:', error.request);
        } else {
          console.error('Request setup error:', error.message);
        }
        throw error;
      }
    },
    logout({ commit }) {
      localStorage.removeItem('jwt');
      commit('setLoginState', false);
      commit('setUserVotesAndRatings', {
        resultVotes: [],
        warningVotes: [],
        resultRatings: [],
        warningRatings: []
      });
    },
    async login({ commit, dispatch }, token) {
      try {
        if (!token) {
          throw new Error('No access token received');
        }
        console.log('Saving JWT token:', token); // 打印保存的 JWT token
        localStorage.setItem('jwt', token);
        commit('setLoginState', true);
        await dispatch('fetchUserVotesAndRatings');
      } catch (error) {
        console.error('Login error:', error);
        throw error;
      }
    },
    async checkLoginStatus({ commit, dispatch }) {  // 从 context 参数中解构出 dispatch
      const token = localStorage.getItem('jwt');
      if (token) {
        commit('setLoginState', true);
        await dispatch('fetchUserVotesAndRatings');
      } else {
        commit('setLoginState', false);
      }
    }
  }
});
