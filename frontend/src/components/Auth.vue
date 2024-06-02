<template>
  <div class="auth-container">
    <div v-if="showToast" class="toast">{{ toastMessage }}</div>
    <h1 class="auth-heading">Sign Up or Log In</h1>
    <form @submit.prevent="authenticate" class="auth-form">
      <input v-model="email" type="email" placeholder="Email" required class="auth-input">
      <input v-model="password" type="password" placeholder="Password" required class="auth-input">
      <div class="captcha-wrapper">
        <img :src="captchaSrc" :key="captchaSrc" alt="Captcha" @click="refreshCaptcha" class="captcha-image">
        <input type="text" v-model="captchaInput" placeholder="Enter captcha" class="captcha-input">
      </div>
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
      password: '',
      captchaSrc: `${apiBase}/captcha?rand=${Math.random()}`,
      captchaInput: '',
      toastMessage: '',
      showToast: false,
    };
  },
  methods: {
    ...mapActions(['login']),
    authenticate() {
      axios.post(`${apiBase}/subscribe`, {
        email: this.email,
        password: this.password,
        captcha: this.captchaInput,
      }, {
        headers: {
          'Content-Type': 'application/json'
        },
        withCredentials: true
      }).then(response => {
        if (response.data.access_token) {
          this.login(response.data.access_token).then(() => {
            this.displayToast('Authentication successful!');
            this.$router.push('/');
            this.refreshCaptcha(); // Refresh captcha image
          });
        } else {
          this.displayToast('Login failed: ' + response.data.message);
          this.refreshCaptcha(); // Refresh captcha image
        }
      }).catch(error => {
        console.error('Authentication error:', error);
        this.displayToast('Authentication failed. Please try again.');
        this.refreshCaptcha(); // Refresh captcha image
      });
    },
    refreshCaptcha() {
      this.captchaSrc = `${apiBase}/captcha?rand=${Math.random()}`;
    },
    displayToast(message) {
      this.toastMessage = message;
      this.showToast = true;
      setTimeout(() => {
        this.showToast = false;
      }, 3000);
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

.captcha-wrapper {
  display: flex;
  align-items: center;
}

.captcha-image {
  cursor: pointer;
  margin-right: 10px;
  width: 120px;
  height: 40px;
}

.toast {
  position: fixed;
  top: 20px; 
  left: 50%;
  transform: translateX(-50%);
  padding: 10px 20px;
  background-color: #333;
  color: white;
  border-radius: 5px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.2);
  text-align: center;
  z-index: 1000;
  animation: fadeinout 3s;
}

@keyframes fadeinout {
  0%, 100% { opacity: 0; }
  10%, 90% { opacity: 1; }
}
</style>
