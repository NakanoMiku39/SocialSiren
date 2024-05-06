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
      <textarea placeholder="Type your message here" class="input-style"></textarea>
      <button class="send-button">Send</button>
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
      messages: []  // 确保这里定义了 messages，并初始化为空数组
    };
  },
  created() {
    this.fetchMessages();
  },
  methods: {
    submitEmail() {
      axios.post('http://localhost:2222/subscribe', { email: this.email })
        .then(response => {
          alert('Subscription successful!');
        })
        .catch(error => {
          console.error('There was an error!', error);
          alert('Subscription failed.');
        });
    },
    fetchMessages() {
      axios.get('http://localhost:2222/api/messages')
        .then(response => {
          this.messages = response.data;
        })
        .catch(error => {
          console.error('Error fetching messages:', error);
        });
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
  padding: 20px;
  background-color: #2c3e50;
  border-top: 1px solid #aaa; /* 给消息框顶部添加边界线条 */
}

.message-box textarea, .message-box button {
  border-radius: 5px;
  padding: 10px;
}

.message-box textarea {
  flex: 1;
  margin-right: 10px; /* 确保文本框和按钮之间有间隔 */
}

.message-box button {
  background-color: #3498db;
  color: white;
  cursor: pointer;
  border: none;
  padding: 10px 20px; /* 按钮更大更舒适的点击区域 */
}

.message-box button:hover {
  background-color: #2980b9; /* 鼠标悬浮时变暗 */
}
</style>
