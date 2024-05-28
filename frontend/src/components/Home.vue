<template>
  <div class="container">
    <div v-if="showToast" class="toast">{{ toastMessage }}</div>
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
      <select v-model="filters.disasterType">
        <option value="all">All Types</option>
        <option value="earthquake">Earthquake</option>
        <option value="flood">Flood</option>
        <!-- 添加更多灾害类型 -->
      </select>
      <select v-model="filters.disasterLocation">
        <option value="all">All Locations</option>
        <option value="city1">City 1</option>
        <option value="city2">City 2</option>
        <!-- 添加更多灾害地点 -->
      </select>
      <select v-model="sortOrder">
        <option value="true">Newest First</option>
        <option value="false">Oldest First</option>
      </select>
      <button @click="fetchWarnings">Apply Filters</button>
    </div>

    <main class="main-content">
      <div class="left-panel">
        <h2>Latest Warnings</h2>
        <ul>
          <li v-for="warning in warnings" :key="warning.id" class="warning">
            <div class="warning-content" @click="selectWarning(warning)">
              <p>Disaster Type: {{ warning.disaster_type }}</p>
              <p>Time: {{ warning.disaster_time }}</p>
              <p>Location: {{ warning.disaster_location }}</p>
            </div>
          </li>
        </ul>
      </div>
      <div class="right-panel">
        <h2>GDACS Alerts</h2>
        <ul>
          <li v-for="message in gdacsMessages" :key="message.id" class="message">
            <div class="message-content">
              <p>Posted on: {{ message.date_time }}</p>
              <p>{{ message.content }}</p>
              <p>Source: {{ message.source_type }}</p>
              <p>Location: {{ message.location }}</p>
            </div>
          </li>
        </ul>
      </div>
    </main>

    <div v-if="selectedWarning" class="modal" @click.self="selectedWarning = null">
      <div class="modal-content">
        <h3>Warning Details</h3>
        <p>Disaster Type: {{ selectedWarning.disaster_type }}</p>
        <p>Time: {{ selectedWarning.disaster_time }}</p>
        <p>Location: {{ selectedWarning.disaster_location }}</p>
        <h4>Related Tweets</h4>
        <ul>
          <li v-for="tweet in selectedWarning.related_tweets" :key="tweet.id" class="tweet">
            <div class="tweet-content">
              <p>Posted on: {{ tweet.date_time }}</p>
              <p>{{ tweet.content }}</p>
              <p>Disaster: {{ tweet.is_disaster ? 'Yes' : 'No' }}
                <span v-if="tweet.is_disaster">- Probability: {{ tweet.probability }} <p>Disaster Type: {{ tweet.disaster_type }}</p></span>
              </p>
              <p>Source: {{ tweet.source_type }} (ID: {{ tweet.source_id }})</p>
              <button v-if="!tweet.hasVotedDelete" @click="deleteMessage(tweet.id)" class="delete-button">
                Vote to Delete
              </button>
              <button v-else class="delete-button" disabled>
                Vote Recorded
              </button>
            </div>
            <div class="ratings">
              <div class="rating-container">
                <label v-tooltip="'Rate the authenticity of this message.'">Authenticity:</label>
                <span v-if="tweet.hasVotedAuthenticity">
                  {{ formatAverage(tweet.authenticity_average) }} ({{ tweet.authenticity_count || 0 }} votes)
                </span>
                <button v-if="!tweet.hasVotedAuthenticity" v-for="score in [1, 2, 3, 4, 5]" :key="score"
                  class="rating-button" @click="rateMessage(tweet.id, score, 'authenticity')">
                  {{ score }}
                </button>
              </div>
              <div class="rating-container">
                <label v-tooltip="'Rate the accuracy of this message.'">Accuracy:</label>
                <span v-if="tweet.hasVotedAccuracy">
                  {{ formatAverage(tweet.accuracy_average) }} ({{ tweet.accuracy_count || 0 }} votes)
                </span>
                <button v-if="!tweet.hasVotedAccuracy" v-for="score in [1, 2, 3, 4, 5]" :key="score"
                  class="rating-button" @click="rateMessage(tweet.id, score, 'accuracy')">
                  {{ score }}
                </button>
              </div>
            </div>
          </li>
        </ul>
      </div>
    </div>

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
      warnings: [],
      selectedWarning: null,
      gdacsMessages: [],
      captchaInput: '',
      captchaSrc: `${apiBase}/captcha`,
      filters: {
        disasterType: 'all',
        disasterLocation: 'all'
      },
      sortOrder: 'true',
      apiBase: 'http://10.129.199.88:2222',
      toastMessage: '',
      showToast: false,
      toastTimeout: null,
    };
  },
  created() {
    const token = localStorage.getItem('jwt');
    if (token) {
      console.log('JWT:', token);
    }
    console.log("Component created, isLoggedIn:", this.isLoggedIn);
    this.fetchWarnings();
    this.fetchGdacsMessages();
  },
  computed: {
    ...mapState(['isLoggedIn'])
  },
  methods: {
    ...mapActions(['logout']),
    fetchWarnings() {
      const params = {
        ...this.filters,
        orderBy: 'disaster_time',
        orderDesc: this.sortOrder
      };
      const token = localStorage.getItem('jwt');
      axios.get(`${this.apiBase}/api/warnings`, {
        headers: {
          'Authorization': `Bearer ${token}`
        },
        params: params
      })
      .then(response => {
        this.warnings = response.data;
      })
      .catch(error => {
        console.error('Error fetching warnings:', error);
        if (error.response && error.response.status === 401) {
          this.displayToast("Session expired. Please login again.");
          this.$router.push('/auth');
        }
      });
    },
    fetchGdacsMessages() {
      axios.get(`${this.apiBase}/api/gdacsMessages`, {
        params: {
          orderBy: 'date_time',
          orderDesc: true
        }
      })
      .then(response => {
        this.gdacsMessages = response.data;
      })
      .catch(error => {
        console.error('Error fetching GDACS messages:', error);
        this.displayToast('Failed to fetch GDACS messages.');
      });
    },
    authenticate() {
      axios.post(`${apiBase}/subscribe`, {
        email: this.email,
        password: this.password
      })
      .then(response => {
        this.displayToast('Authentication successful!');
        this.email = '';
        this.password = '';
      })
      .catch(error => {
        console.error('Authentication error:', error);
        this.displayToast('Authentication failed. Please try again.');
      });
    },
    handleLogout() {
      this.logout().then(() => {
        this.$router.push('/auth');
      });
    },
    sendMessage() {
      if (!this.messageContent.trim()) {
        this.displayToast('Message cannot be empty!');
        return;
      }
      if (!this.captchaInput.trim()) {
        this.displayToast('Captcha cannot be empty!');
        return;
      }
      const message = {
        content: this.messageContent,
        captcha: this.captchaInput
      };
      axios.post(`${apiBase}/api/send-message`, message, { withCredentials: true })
        .then(() => {
          this.displayToast('Message sent successfully!');
          this.messageContent = '';
          this.captchaInput = '';
          this.refreshCaptcha();
        })
        .catch(error => {
          console.error('Error sending message:', error);
          this.displayToast('Failed to send message. Please check the captcha and try again.');
          this.refreshCaptcha();
        });
    },
    refreshCaptcha() {
      this.captchaSrc = `${apiBase}/captcha?rand=${Math.random()}`;
    },
    rateMessage(messageId, score, type) {
      const token = localStorage.getItem('jwt');
      if (!token) {
        this.displayToast("You are not logged in or your session has expired.");
        this.$router.push('/auth');
        return;
      }

      axios.post(`${this.apiBase}/api/rate-message`, {
        message_id: messageId,
        rating: score,
        type: type
      }, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      }).then(response => {
        if (response.data.status === 'success') {
          const message = this.selectedWarning.related_tweets.find(m => m.id === messageId);
          if (message) {
            if (type === 'authenticity') {
              message.authenticity_average = response.data.authenticity_average;
              message.authenticity_raters = response.data.authenticity_count;
              message.hasVotedAuthenticity = true;
            } else if (type === 'accuracy') {
              message.accuracy_average = response.data.accuracy_average;
              message.accuracy_raters = response.data.accuracy_count;
              message.hasVotedAccuracy = true;
            }
          }
        } else {
          this.displayToast('Error updating rating: ' + response.data.message);
        }
      }).catch(error => {
        console.error('Error submitting rating:', error.response?.data || error.message);
        this.displayToast('Failed to submit rating. Please try again later.');
      });
    },
    formatAverage(value) {
      return value ? value.toFixed(2) : '0.00';
    },
    deleteMessage(messageId) {
      const token = localStorage.getItem('jwt');

      if (!token) {
        this.displayToast("You are not logged in or your session has expired.");
        this.$router.push('/auth');
        return;
      }

      axios.post(`${this.apiBase}/api/delete-message`, { message_id: messageId, delete_vote: true }, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      .then(response => {
        if (response.data.status === 'success') {
          this.displayToast('Message deleted successfully');
          this.fetchWarnings();
        } else if (response.data.status === 'pending') {
          this.displayToast('Vote recorded. Pending more votes.');
          const message = this.selectedWarning.related_tweets.find(m => m.id === messageId);
          if (message) {
            message.hasVotedDelete = true;
          }
        } else {
          this.displayToast('Error: ' + response.data.message);
        }
      })
      .catch(error => {
        console.error('Deletion failed:', error.response.data);
        this.displayToast('Failed to delete message: ' + error.response.data.message);
      });
    },
    displayToast(message, duration = 3000) {
      this.toastMessage = message;
      this.showToast = true;
      clearTimeout(this.toastTimeout);
      this.toastTimeout = setTimeout(() => {
        this.showToast = false;
      }, duration);
    },
    selectWarning(warning) {
      this.selectedWarning = warning;
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
  transition: background-color 0.3s ease;
}

.logout-button:hover {
  background-color: #c0392b;
}

.main-content {
  display: flex;
  padding: 20px;
  background-color: #f9f9f9;
  border-top: 1px solid #ccc;
}

.left-panel, .right-panel {
  flex: 1;
  overflow-y: auto;  /* 允许滚动 */
  margin: 0 10px;
  padding: 10px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  height: 500px; /* 或其他固定高度，取决于页面设计 */
}

.right-panel {
  background-color: #eef;  /* 轻微背景色差异 */
}

.message, .warning {
  background: #fff;
  margin-bottom: 10px;
  padding: 15px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.warning-content {
  cursor: pointer;
}

.warning-content:hover {
  background-color: #f0f0f0;
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

.delete-button {
  padding: 5px 10px;
  background-color: #e74c3c;
  color: white;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  margin-top: 10px;
}

.delete-button:hover {
  background-color: #c0392b;
}

.toast {
  position: fixed;
  top: 20px;
  left: 50%;
  transform: translateX(-50%);
  background-color: rgba(0,0,0,0.7);
  color: white;
  padding: 10px 20px;
  border-radius: 5px;
  z-index: 1000;
  animation: fadein 0.5s, fadeout 0.5s 2.5s;
}

@keyframes fadein {
  from { top: 0; opacity: 0; }
  to { top: 20px; opacity: 1; }
}

@keyframes fadeout {
  from { top: 20px; opacity: 1; }
  to { top: 0; opacity: 0; }
}

.modal-content {
  max-height: 80vh;
  overflow-y: auto;
  padding: 20px;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.5);
  z-index: 1000;
}

.modal h3 {
  margin-top: 0;
}

.tweet {
  background: #f9f9f9;
  margin-bottom: 10px;
  padding: 15px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
</style>
