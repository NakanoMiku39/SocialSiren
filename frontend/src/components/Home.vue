<template>
  <div class="container" @click.self="closeWarning">
    <div v-if="showToast" class="toast">{{ toastMessage }}</div>
    <div v-if="!isLoggedIn" class="header pre-login-header">
      <h1 class="website-name">SocialSiren</h1>
      <router-link to="/auth" class="auth-link">Login or Register</router-link>
    </div>
    <div v-else>
      <header class="header">
        <h1 class="website-name">SocialSiren</h1>
        <p>Welcome, user!</p>
        <button @click="handleLogout" class="logout-button">Logout</button>
      </header>
    </div>

    <div class="filter-section">
      <select v-model="filters.disasterType">
        <option value="all">All Types</option>
        <option value="earthquake">Earthquake</option>
        <option value="flood">Flood</option>
      </select>
      <select v-model="sortOrder">
        <option value="true">Newest First</option>
        <option value="false">Oldest First</option>
      </select>
      <button @click="fetchWarnings">Apply Filters</button>
    </div>

    <div class="main-content">
      <div class="left-panel">
        <h2>Latest Warnings</h2>
        <ul>
          <li v-for="warning in warnings" :key="warning.id" class="warning">
            <div class="warning-content" @click="selectWarning(warning)">
              <p>Disaster Type: {{ warning.disaster_type }}</p>
              <p>Time: {{ warning.disaster_time }}</p>
              <p>Location: {{ warning.disaster_location }}</p>
            </div>
            <div class="ratings">
              <div class="rating-container">
                <label v-tooltip="'Rate the authenticity of this warning.'">Authenticity:</label>
                <span v-if="warning.hasVotedAuthenticity">
                  {{ formatAverage(warning.authenticity_average) }} ({{ warning.authenticity_count || 0 }} votes)
                </span>
                <span v-if="!warning.hasVotedAuthenticity">
                  <i v-for="score in [1, 2, 3, 4, 5]" :key="score"
                    :class="['fa', 'fa-star', { 'rating-star': true, 'active': score <= warning.authenticityScore }]"
                    @mouseover="warning.authenticityScore = score"
                    @mouseleave="warning.authenticityScore = 0"
                    @click="rateWarning(warning.id, score, 'authenticity')"></i>
                </span>
              </div>
              <div class="rating-container">
                <label v-tooltip="'Rate the accuracy of this warning.'">Accuracy:</label>
                <span v-if="warning.hasVotedAccuracy">
                  {{ formatAverage(warning.accuracy_average) }} ({{ warning.accuracy_count || 0 }} votes)
                </span>
                <span v-if="!warning.hasVotedAccuracy">
                  <i v-for="score in [1, 2, 3, 4, 5]" :key="score"
                    :class="['fa', 'fa-star', { 'rating-star': true, 'active': score <= warning.accuracyScore }]"
                    @mouseover="warning.accuracyScore = score"
                    @mouseleave="warning.accuracyScore = 0"
                    @click="rateWarning(warning.id, score, 'accuracy')"></i>
                </span>
              </div>
            </div>
            <button v-if="!warning.hasVotedDelete" @click="deleteWarning(warning.id)" class="delete-button">
              Vote to Delete
            </button>
            <button v-else class="delete-button" disabled>
              Vote Recorded
            </button>
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
    </div>

    <div v-if="selectedWarning" class="modal" @click.self="closeWarning">
      <div class="modal-content">
        <h2>Warning Messages</h2>
        <button @click="closeWarning" class="close-button">X</button>
        <ul>
          <li v-for="message in selectedWarning.related_tweets" :key="message.id" class="message">
            <div class="message-content">
              <p>Posted on: {{ message.date_time }}</p>
              <p>{{ message.content }}</p>
              <p>Source: {{ message.source_type }}</p>
              <p>Location: {{ message.location }}</p>
            </div>
            <div class="ratings">
              <div class="rating-container">
                <label v-tooltip="'Rate the authenticity of this message.'">Authenticity:</label>
                <span v-if="message.hasVotedAuthenticity">
                  {{ formatAverage(message.authenticity_average) }} ({{ message.authenticity_count || 0 }} votes)
                </span>
                <span v-if="!message.hasVotedAuthenticity">
                  <i v-for="score in [1, 2, 3, 4, 5]" :key="score"
                    :class="['fa', 'fa-star', { 'rating-star': true, 'active': score <= message.authenticityScore }]"
                    @mouseover="message.authenticityScore = score"
                    @mouseleave="message.authenticityScore = 0"
                    @click="rateMessage(message.id, score, 'authenticity')"></i>
                </span>
              </div>
              <div class="rating-container">
                <label v-tooltip="'Rate the accuracy of this message.'">Accuracy:</label>
                <span v-if="message.hasVotedAccuracy">
                  {{ formatAverage(message.accuracy_average) }} ({{ message.accuracy_count || 0 }} votes)
                </span>
                <span v-if="!message.hasVotedAccuracy">
                  <i v-for="score in [1, 2, 3, 4, 5]" :key="score"
                    :class="['fa', 'fa-star', { 'rating-star': true, 'active': score <= message.accuracyScore }]"
                    @mouseover="message.accuracyScore = score"
                    @mouseleave="message.accuracyScore = 0"
                    @click="rateMessage(message.id, score, 'accuracy')"></i>
                </span>
              </div>
            </div>
            <button v-if="!message.hasVotedDelete" @click="deleteMessage(message.id)" class="delete-button">
              Vote to Delete
            </button>
            <button v-else class="delete-button" disabled>
              Vote Recorded
            </button>
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
      captchaSrc: `${apiBase}/captcha?rand=${Math.random()}`,
      filters: {
        disasterType: 'all',
      },
      sortOrder: 'true',
      apiBase,
      toastMessage: '',
      showToast: false,
      toastTimeout: null,
    };
  },
  created() {
    this.$store.dispatch('checkLoginStatus').then(() => {
      if (this.isLoggedIn) {
        this.$store.dispatch('fetchUserVotesAndRatings').then(() => {
          this.fetchWarnings();
          this.fetchGdacsMessages();
        });
      } else {
        this.fetchWarnings();
        this.fetchGdacsMessages();
      }
    });
  },
  computed: {
    ...mapState(['isLoggedIn', 'userVotesAndRatings'])
  },
  methods: {
    ...mapActions(['logout', 'fetchUserVotesAndRatings', 'login']),
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
        params
      })
      .then(response => {
        this.warnings = response.data.map(warning => ({
          ...warning,
          authenticityScore: 0,
          accuracyScore: 0,
        }));
        if (this.isLoggedIn) {
          this.updateUserVotesAndRatings();
        }
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
        this.gdacsMessages = response.data.map(message => ({
          ...message,
          authenticityScore: 0,
          accuracyScore: 0,
        }));
      })
      .catch(error => {
        console.error('Error fetching GDACS messages:', error);
        this.displayToast('Failed to fetch GDACS messages.');
      });
    },
    updateUserVotesAndRatings() {
      const { resultVotes, warningVotes, resultRatings, warningRatings } = this.userVotesAndRatings;

      this.warnings.forEach(warning => {
        warning.hasVotedDelete = warningVotes.some(vote => vote.warning_id === warning.id && vote.vote_type === 'delete');
        warning.hasVotedAuthenticity = warningRatings.some(rating => rating.warning_id === warning.id && rating.type === 'authenticity');
        warning.hasVotedAccuracy = warningRatings.some(rating => rating.warning_id === warning.id && rating.type === 'accuracy');
        
        warning.related_tweets.forEach(tweet => {
          tweet.hasVotedDelete = resultVotes.some(vote => vote.message_id === tweet.id && vote.vote_type === 'delete');
          tweet.hasVotedAuthenticity = resultRatings.some(rating => rating.message_id === tweet.id && rating.type === 'authenticity');
          tweet.hasVotedAccuracy = resultRatings.some(rating => rating.message_id === tweet.id && rating.type === 'accuracy');
        });
      });
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
          const warning = this.selectedWarning;
          if (warning) {
            const message = warning.related_tweets.find(m => m.id === messageId);
            if (message) {
              if (type === 'authenticity') {
                message.authenticity_average = response.data.authenticity_average;
                message.authenticity_count = response.data.authenticity_count;
                message.hasVotedAuthenticity = true;
              } else if (type === 'accuracy') {
                message.accuracy_average = response.data.accuracy_average;
                message.accuracy_count = response.data.accuracy_count;
                message.hasVotedAccuracy = true;
              }
            }
          }
          this.displayToast('Rating submitted successfully!');
        } else {
          this.displayToast('Error updating rating: ' + response.data.message);
        }
      }).catch(error => {
        console.error('Error submitting rating:', error.response?.data || error.message);
        this.displayToast('Failed to submit rating. Please try again later.');
      });
    },
    rateWarning(warningId, score, type) {
      const token = localStorage.getItem('jwt');
      if (!token) {
        this.displayToast("You are not logged in or your session has expired.");
        this.$router.push('/auth');
        return;
      }

      axios.post(`${this.apiBase}/api/rate-warning`, {
        warning_id: warningId,
        rating: score,
        type: type
      }, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      }).then(response => {
        if (response.data.status === 'success') {
          const warning = this.warnings.find(w => w.id === warningId);
          if (warning) {
            if (type === 'authenticity') {
              warning.authenticity_average = response.data.authenticity_average;
              warning.authenticity_count = response.data.authenticity_count;
              warning.hasVotedAuthenticity = true;
            } else if (type === 'accuracy') {
              warning.accuracy_average = response.data.accuracy_average;
              warning.accuracy_count = response.data.accuracy_count;
              warning.hasVotedAccuracy = true;
            }
          }
          this.displayToast('Rating submitted successfully!');
        } else {
          this.displayToast('Error updating rating: ' + response.data.message);
        }
      }).catch(error => {
        console.error('Error submitting rating:', error.response?.data || error.message);
        this.displayToast('Failed to submit rating. Please try again later.');
      });
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
          const messageIndex = this.selectedWarning.related_tweets.findIndex(m => m.id === messageId);
          if (messageIndex !== -1) {
            this.selectedWarning.related_tweets.splice(messageIndex, 1);
          }
          this.refreshCaptcha(); // Ensure captcha refresh after delete
        } else if (response.data.status === 'pending') {
          this.displayToast('Vote recorded. Pending more votes.');
          const message = this.selectedWarning.related_tweets.find(m => m.id === messageId);
          if (message) {
            message.hasVotedDelete = true;
          }
        } else {
          this.displayToast('Error: ' + response.data.message);
          this.refreshCaptcha(); // Ensure captcha refresh on error
        }
      })
      .catch(error => {
        console.error('Deletion failed:', error.response?.data || error.message);
        this.displayToast('Failed to delete message. Please try again later.');
        this.refreshCaptcha(); // Ensure captcha refresh on error
      });
    },
    deleteWarning(warningId) {
      const token = localStorage.getItem('jwt');
      if (!token) {
        this.displayToast("You are not logged in or your session has expired.");
        this.$router.push('/auth');
        return;
      }

      axios.post(`${this.apiBase}/api/delete-warning`, { warning_id: warningId, delete_vote: true }, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      .then(response => {
        if (response.data.status === 'success') {
          this.displayToast('Warning deleted successfully');
          this.fetchWarnings();
          this.refreshCaptcha(); // Ensure captcha refresh after delete
        } else if (response.data.status === 'pending') {
          this.displayToast('Vote recorded. Pending more votes.');
          const warning = this.warnings.find(w => w.id === warningId);
          if (warning) {
            warning.hasVotedDelete = true;
          }
          if (this.selectedWarning && this.selectedWarning.id === warningId) {
            this.selectedWarning.hasVotedDelete = true;
          }
        } else {
          this.displayToast('Error: ' + response.data.message);
          this.refreshCaptcha(); // Ensure captcha refresh on error
        }
      })
      .catch(error => {
        console.error('Deletion failed:', error.response?.data || error.message);
        this.displayToast('Failed to delete warning. Please try again later.');
        this.refreshCaptcha(); // Ensure captcha refresh on error
      });
    },
    findMessageById(messageId) {
      for (const warning of this.warnings) {
        const message = warning.related_tweets.find(m => m.id === messageId);
        if (message) {
          return message;
        }
      }
      return null;
    },
    findWarningById(warningId) {
      return this.warnings.find(w => w.id === warningId) || null;
    },
    authenticate() {
      this.login({
        email: this.email,
        password: this.password,
        captcha: this.captchaInput // 确保包含验证码输入
      })
      .then(() => {
        this.displayToast('Authentication successful!');
        this.email = '';
        this.password = '';
        this.captchaInput = '';
        this.refreshCaptcha(); // Refresh captcha image after successful login
      })
      .catch(error => {
        console.error('Authentication error:', error);
        this.displayToast('Authentication failed. Please try again.');
        this.refreshCaptcha(); // Refresh captcha image on error
      });
    },
    handleLogout() {
      this.logout();
      this.$router.push('/auth');
      this.refreshCaptcha(); // Refresh captcha image on logout
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
      axios.post(`${this.apiBase}/api/send-message`, message, { withCredentials: true })
        .then(() => {
          this.displayToast('Message sent successfully!');
          this.messageContent = '';
          this.captchaInput = '';
          this.refreshCaptcha(); // Refresh captcha image after message sent
        })
        .catch(error => {
          console.error('Error sending message:', error);
          this.displayToast('Failed to send message. Please check the captcha and try again.');
          this.refreshCaptcha(); // Refresh captcha image on error
        });
    },
    refreshCaptcha() {
      this.captchaSrc = `${this.apiBase}/captcha?rand=${Math.random()}`;
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
    },
    closeWarning() {
      this.selectedWarning = null;
    },
    formatAverage(value) {
      return value ? value.toFixed(2) : 'N/A';
    }
  }
}
</script>

<style scoped>
@import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css');

.container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  font-family: 'Arial', sans-serif;
  color: #333;
  background-color: #f9f9f9;
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
  background-color: #fff;
  border-top: 1px solid #ccc;
}

.left-panel, .right-panel {
  flex: 1;
  overflow-y: auto;
  margin: 0 10px;
  padding: 10px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  height: 500px;
}

.right-panel {
  background-color: #eef;
}

.message, .warning {
  background: #fff;
  margin-bottom: 10px;
  padding: 15px;
  border-radius: 8px;
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

.rating-star {
  color: #FFD700;
  cursor: pointer;
}

.rating-star:hover,
.rating-star.active {
  color: #FFA500;
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

.modal-content {
  background-color: white;
  padding: 20px;
  border-radius: 8px;
  max-width: 600px;
  max-height: 80vh;
  overflow-y: auto;
  position: relative;
}

.close-button {
  position: absolute;
  top: 10px;
  right: 10px;
  background: transparent;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #c0392b;
  transition: color 0.3s;
}

.close-button:hover {
  color: #e74c3c;
}
</style>
