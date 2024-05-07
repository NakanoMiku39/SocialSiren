<template>
  <div class="container">
    <!-- Header section -->
    <header class="header">
      <h1 class="website-name">SocialSiren</h1>
      <div class="email-input">
        <input type="email" v-model="email" placeholder="Enter your email" class="input-style">
        <button class="email-button" @click="submitEmail">Subscribe</button>
      </div>
    </header>

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

    <!-- Main content section -->
    <main class="main-content">
      <h2>Latest Messages</h2>
      <ul>
        <li v-for="message in messages" :key="message.id">
          <p>Posted on: {{ message.date_time }}</p>
          <p>{{ message.content }}</p>
          <p>Disaster: {{ message.is_disaster ? 'Yes' : 'No' }} - Probability: {{ message.probability }}</p>
          <p>Source: {{ message.source_type }} (ID: {{ message.source_id }})</p>
        </li>
      </ul>
    </main>
    
    <!-- Footer section -->
    <footer class="message-box">
      <textarea v-model="messageContent" placeholder="Type your message here" class="input-style"></textarea>
      <div class="captcha-and-send">
          <div class="captcha-wrapper">
              <img :src="captchaSrc" alt="Captcha" @click="refreshCaptcha" class="captcha-image">
              <input type="text" v-model="captchaInput" placeholder="Enter captcha here" class="captcha-input">
          </div>
          <button class="send-button" @click="sendMessage">Send</button>
      </div>
    </footer>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'Home',
  data() {
    return {
      email: '',
      messageContent: '', // 添加这行确保定义了 messageContent
      messages: [],  // 确保这里定义了 messages，并初始化为空数组
      captchaInput: '',
      captchaSrc: '/captcha',  // 初始验证码图片地址
      filters: {
        isDisaster: 'true',
        sourceType: 'all'
      },
      sortOrder: 'true'
    };
  },
  created() {
    this.fetchMessages();
    this.refreshCaptcha();
  },
  methods: {
    fetchMessages() {
      const params = {
        ...this.filters,
        orderBy: 'date_time',
        orderDesc: this.sortOrder
      };
      axios.get('http://10.129.199.88:2222/api/messages', { params })
        .then(response => {
          this.messages = response.data;
        })
        .catch(error => {
          console.error('Error fetching messages:', error);
        });
    },
    submitEmail() {
      axios.post('http://10.129.199.88:2222/subscribe', { email: this.email })
        .then(response => {
          alert('Subscription successful!');
          this.email = '';
        })
        .catch(error => {
          console.error('There was an error!', error);
          alert('Subscription failed.');
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
      // const message = { content: this.messageContent };
      axios.post('http://10.129.199.88:2222/api/send-message', message, { withCredentials: true })
        .then(response => {
          alert('Message sent successfully!');
          this.messageContent = '';  // 清空输入框
          this.captchaInput = '';
          this.refreshCaptcha();  // 刷新验证码
        })
        .catch(error => {
          console.error('Error sending message:', error);
          alert('Failed to send message. Please check the captcha and try again.');
          this.refreshCaptcha();  // 出错时刷新验证码
        });
    },
    refreshCaptcha() {
      // 刷新验证码
      this.captchaSrc = `http://10.129.199.88:2222/captcha?rand=${Math.random()}`;
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

.email-input input, .email-input button {
  padding: 10px;
  font-size: 16px;
  border: none;
  border-radius: 5px;
}

.email-input button {
  background-color: #3498db;
  color: white;
  cursor: pointer;
}

.email-input button:hover {
  background-color: #2980b9;
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
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.message-box {
  display: flex;
  flex-direction: column;
  padding: 20px;
  background-color: #2c3e50;
}

.captcha-and-send {
  display: flex;
  align-items: center;
  justify-content: space-between; /* 确保验证码和发送按钮在页面宽度较宽时保持间隔 */
}

.captcha-wrapper {
  display: flex;
  align-items: center;
  margin-right: 10px; /* 确保验证码和发送按钮之间有间隔 */
}

.captcha-image {
  cursor: pointer;
  margin-right: 10px; /* 图片与输入框之间的间隔 */
  width: 120px;
  height: 40px;
}

.captcha-input {
  padding: 10px;
  border: 1px solid #aaa;
  border-radius: 5px;
  flex-grow: 1; /* 输入框填充剩余空间 */
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
  background-color: #f4f4f4; /* 轻灰色背景 */
  border-radius: 8px; /* 轻微的圆角 */
  margin: 10px 0; /* 增加一些外边距 */
  box-shadow: 0 2px 4px rgba(0,0,0,0.1); /* 添加轻微的阴影效果 */
}

.filter-section select, .filter-section button {
  padding: 10px;
  margin-right: 10px;
  border: 1px solid #ccc; /* 给下拉菜单和按钮添加边框 */
  border-radius: 5px; /* 轻微的圆角效果 */
  background: white;
  cursor: pointer;
}

.filter-section button {
  background-color: #007BFF; /* Bootstrap 主题蓝色 */
  color: white;
}

.filter-section button:hover {
  background-color: #0056b3; /* 鼠标悬停时更深的蓝色 */
}

</style>
