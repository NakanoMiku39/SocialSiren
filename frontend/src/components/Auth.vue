<template>
  <div class="auth-container">
    <h1 class="auth-heading">Sign Up or Log In</h1>
    <form @submit.prevent="authenticate" class="auth-form">
      <input v-model="email" type="email" placeholder="Email" required class="auth-input">
      <input v-model="password" type="password" placeholder="Password" required class="auth-input">
      <button type="submit" class="auth-button submit-button">Submit</button>
      <router-link to="/" class="auth-button back-button">Back to Home</router-link>
    </form>
  </div>
</template>

<script>
import axios from 'axios';
import { mapActions } from 'vuex';

const apiBase = 'http://10.129.199.88:2222';

export default {
  data() {
    return {
      email: '',
      password: ''
    };
  },
  methods: {
    authenticate() {
      axios.post(`${apiBase}/subscribe`, {
        email: this.email,
        password: this.password
      }).then(response => {
        console.log('Login Response:', response.data);  // 输出响应数据
        if (response.data.access_token) {
          localStorage.setItem('jwt', response.data.access_token);  // 保存 JWT
          this.$store.dispatch('login');  // 更新 Vuex 状态
          alert('Authentication successful!');
          this.$router.push('/');  // 重定向到主页
        } else {
          alert('Login failed: ' + response.data.message);
        }
      }).catch(error => {
        console.error('Authentication error:', error);
        alert('Authentication failed. Please try again.');
      });
    },
    logout() {
      localStorage.removeItem('jwt');  // 移除 JWT
      this.$store.dispatch('logout');  // 更新 Vuex 状态
    }
  }
}
</script>

<style scoped>
.auth-container {
  max-width: 400px;
  margin: auto;
  padding: 30px;
  border: 1px solid #e0e0e0;
  border-radius: 10px;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
  text-align: center;
  background-color: #f9f9f9;
}

.auth-heading {
  margin-bottom: 20px;
  color: #2c3e50;
  font-size: 24px;
  font-weight: bold;
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.auth-input {
  width: 100%;
  padding: 10px;
  border: 1px solid #ccc;
  border-radius: 5px;
  box-sizing: border-box;
  font-size: 16px;
}

.auth-button {
  padding: 10px;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  font-size: 16px;
  font-weight: bold;
  text-align: center;
  text-decoration: none;
  color: white;
}

.submit-button {
  background-color: #3498db;
}

.submit-button:hover {
  background-color: #2980b9;
}

.back-button {
  background-color: #e74c3c;
  margin-top: 10px;
}

.back-button:hover {
  background-color: #c0392b;
}
</style>
