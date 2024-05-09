<template>
  <div class="container">
    <div v-if="!isLoggedIn" class="header pre-login-header">
      <h1 class="website-name">SocialSiren</h1>
      <router-link to="/auth" class="auth-link">Login or Register</router-link>
    </div>
    <div v-else>
      <header class="header">
        <h1 class="website-name">SocialSiren</h1>
        <p>Welcome, user!</p>
        <button @click="logout" class="logout-button">Logout</button>
      </header>
    </div>

    <div class="filter-section">
      <select v-model="filters.sourceType">
        <option value="all">All Sources</option>
        <option value="topic">Topic</option>
        <option value="reply">Reply</option>
        <option value="comment">User Comment</option>
      </select>
      <select v-model="filters.isDisaster">
        <option value="all">Both</option>
        <option value="true">Disaster</option>
        <option value="false">Not Disaster</option>
      </select>
      <select v-model="sortOrder">
        <option value="true">Newest First</option>
        <option value="false">Oldest First</option>
      </select>
      <button @click="fetchMessages">Apply Filters</button>
    </div>

    <main class="main-content">
      <h2>Latest Messages</h2>
      <ul>
        <li v-for="message in messages" :key="message.id" class="message">
          <div class="message-content">
            <p>Posted on: {{ message.date_time }}</p>
            <p>{{ message.content }}</p>
            <p>Disaster: {{ message.is_disaster ? 'Yes' : 'No' }} - Probability: {{ message.probability }}</p>
            <p>Source: {{ message.source_type }} (ID: {{ message.source_id }})</p>
          </div>
          <div class="ratings">
            <div class="rating-container">
              <label v-tooltip="'Rate the authenticity of this message.'">Authenticity:</label>
              <span v-if="message.hasVotedAuthenticity">
                {{ formatAverage(message.authenticity_average) }} ({{ message.authenticity_raters || 0 }} votes)
              </span>
              <button v-if="!message.hasVotedAuthenticity" v-for="score in [1, 2, 3, 4, 5]" :key="score"
                class="rating-button" @click="rateMessage(message.id, score, 'authenticity')">
                {{ score }}
              </button>
            </div>
            <div class="rating-container">
              <label v-tooltip="'Rate the accuracy of this message.'">Accuracy:</label>
              <span v-if="message.hasVotedAccuracy">
                {{ formatAverage(message.accuracy_average) }} ({{ message.accuracy_raters || 0 }} votes)
              </span>
              <button v-if="!message.hasVotedAccuracy" v-for="score in [1, 2, 3, 4, 5]" :key="score"
                class="rating-button" @click="rateMessage(message.id, score, 'accuracy')">
                {{ score }}
              </button>
            </div>
          </div>
        </li>
      </ul>
    </main>

    <footer class="message-box">
      <textarea v-model="messageContent" placeholder="Type your message here" class="message-input"></textarea>
      <div class="captcha-and-send">
        <div class="captcha-wrapper">
          <img :src="captchaSrc" alt="Captcha" @click="refreshCaptcha" class="captcha-image">
          <input type="text" v-model="captchaInput" placeholder="Enter captcha" class="captcha-input">
        </div>
        <button class="send-button" @click="sendMessage">Send</button>
      </div>
    </footer>
  </div>
</template>

<script>
import axios from 'axios';
import VTooltip from 'v-tooltip';
import { mapActions, mapState } from 'vuex';
const apiBase = 'http://10.129.199.88:2222'; 

export default {
  name: 'Home',
  directives: {
    tooltip: VTooltip,
  },
  data() {
    return {
      email: '',
      password: '',
      messageContent: '',
      messages: [],
      captchaInput: '',
      captchaSrc: `${apiBase}/captcha`,
      filters: {
        isDisaster: 'true',
        sourceType: 'all'
      },
      sortOrder: 'true',
    };
  },
  created() {
    const token = localStorage.getItem('jwt');
    if (token) {
      console.log('JWT:', token);  // 输出查看 JWT
      // 执行已登录状态的相关操作
    }
    console.log("Component created, isLoggedIn:", this.isLoggedIn);
    this.fetchMessages();
  },
  computed: {
    ...mapState(['isLoggedIn'])
  },
  methods: {
    ...mapActions(['logout']), // 从 Vuex 引入 logout action
    fetchMessages() {
  const params = {
    ...this.filters,
    orderBy: 'date_time',
    orderDesc: this.sortOrder
  };
  // 获取存储在 localStorage 中的 JWT
      const token = localStorage.getItem('jwt');
      axios.get(`${apiBase}/api/messages`, {
        headers: {
          'Authorization': `Bearer ${token}`  // 使用 Bearer 方式添加 JWT
        },
        params: params
      })
      .then(response => {
        this.messages = response.data.map(msg => ({
          ...msg,
          hasVotedAuthenticity: false,
          hasVotedAccuracy: false
        }));
      })
      .catch(error => {
        console.error('Error fetching messages:', error);
        // 这里可以添加处理特定错误的逻辑，比如 token 过期
        if (error.response && error.response.status === 401) {
          // 处理未授权错误，比如重定向到登录页面或显示错误消息
          alert("Session expired. Please login again.");
          this.$router.push('/login');
        }
      });
    },
    authenticate() {
      axios.post(`${apiBase}/subscribe`, {
        email: this.email,
        password: this.password
      })
      .then(response => {
        alert('Authentication successful!');
        this.email = '';  // Optionally clear fields
        this.password = '';
      })
      .catch(error => {
        console.error('Authentication error:', error);
        alert('Authentication failed. Please try again.');
      });
    },
    handleLogout() {
      this.logout().then(() => {
        this.$router.push('/login'); // 在成功登出后重定向到登录页面
      });
    },
    sendMessage() {
      if (!this.messageContent.trim()) {
        alert('Message cannot be empty!');
        return;
      }
      if (!this.captchaInput.trim()) {
        alert('Captcha cannot be empty!');
        return;
      }
      const message = {
        content: this.messageContent,
        captcha: this.captchaInput
      };
      axios.post(`${apiBase}/api/send-message`, message, { withCredentials: true })
        .then(() => {
          alert('Message sent successfully!');
          this.messageContent = '';
          this.captchaInput = '';
          this.refreshCaptcha();
        })
        .catch(error => {
          console.error('Error sending message:', error);
          alert('Failed to send message. Please check the captcha and try again.');
          this.refreshCaptcha();
        });
    },
    refreshCaptcha() {
      this.captchaSrc = `${apiBase}/captcha?rand=${Math.random()}`;
    },
    rateMessage(messageId, score, type) {
      axios.post(`${apiBase}/api/rate-message`, {
        message_id: messageId,
        rating: score,
        type: type
      }).then(response => {
        if (response.data.status === 'success') {
          const message = this.messages.find(m => m.id === messageId);
          if (type === 'authenticity') {
            message.authenticity_average = response.data.authenticity_average;
            message.authenticity_raters = response.data.authenticity_count;
            message.hasVotedAuthenticity = true;
          } else if (type === 'accuracy') {
            message.accuracy_average = response.data.accuracy_average;
            message.accuracy_raters = response.data.accuracy_count;
            message.hasVotedAccuracy = true;
          }
        } else {
          alert('Error updating rating: ' + response.data.message);
        }
      }).catch(error => {
        console.error('Error submitting rating:', error);
      });
    },
    formatAverage(value) {
      return value ? value.toFixed(2) : '0.00';
    }
  }
}
</script>

<style scoped>
.container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  font-family: 'Arial', sans-serif;
  color: #333;
  background-color: #fff;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  background-color: #2c3e50;
  color: #ecf0f1;
}

.website-name {
  margin: 0;
  font-size: 24px;
}

.pre-login-header {
  background-color: #34495e;
  color: #ecf0f1;
  text-align: center;
  padding: 40px 20px;
  border-bottom: 2px solid #2c3e50;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
}

.auth-link {
  display: inline-block;
  margin-top: 20px;
  background-color: #2980b9;
  color: #ecf0f1;
  padding: 10px 20px;
  border-radius: 5px;
  text-decoration: none;
  font-size: 16px;
  font-weight: bold;
}

.auth-link:hover {
  background-color: #3498db;
}

.logout-button {
  padding: 10px 20px;
  background-color: #e74c3c;
  color: white;
  border: none;
  cursor: pointer;
  border-radius: 5px;
  transition: background-color 0.3s ease
}

.main-content {
  flex: 1;
  padding: 20px;
  background-color: #f9f9f9;
  border-top: 1px solid #ccc;
  overflow-y: auto;
  box-shadow: 0 2px 5px rgba(0,0,0,0.1);
}

.main-content h2 {
  color: #2c3e50;
  font-size: 22px;
}

.main-content ul {
  list-style-type: none;
  padding: 0;
}

.main-content li {
  background: #fff;
  margin-bottom: 10px;
  padding: 15px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.message-box {
  background-color: #ecf0f1;
  padding: 10px;
  box-shadow: 0 -2px 5px rgba(0,0,0,0.1);
}

.message-input {
  width: 100%;
  padding: 15px;
  border-radius: 5px;
  border: 1px solid #aaa;
  margin-bottom: 10px;
}

.captcha-and-send {
  display: flex;
  align-items: center;
  justify-content: space-between;
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

.captcha-input {
  padding: 10px;
  border: 1px solid #aaa;
  border-radius: 5px;
  flex-grow: 1;
}

.send-button {
  padding: 10px 20px;
  background-color: #3498db;
  color: white;
  border: none;
  cursor: pointer;
  border-radius: 5px;
}

.send-button:hover {
  background-color: #2980b9;
}

.filter-section {
  display: flex;
  justify-content: space-between;
  padding: 20px;
  background-color: #f4f4f4;
  border-radius: 8px;
  margin: 10px 0;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.filter-section select, .filter-section button {
  padding: 10px;
  margin-right: 10px;
  border: 1px solid #ccc;
  border-radius: 5px;
  background: white;
  cursor: pointer;
}

.filter-section button {
  background-color: #007BFF;
  color: white;
}

.filter-section button:hover {
  background-color: #0056b3;
}

.message {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 10px;
  border-bottom: 1px solid #ccc;
}

.message-content {
  flex-grow: 1;
}

.ratings {
  flex-basis: 250px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.rating-container {
  position: relative;
}

label {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
}

.rating-button {
  margin-right: 5px;
  background-color: #e0e0e0;
  border: none;
  padding: 5px;
  cursor: pointer;
}

.rating-button:hover {
  background-color: #d0d0d0;
}

.rating-container:hover .rating-button {
  display: inline-block;
}
</style>
