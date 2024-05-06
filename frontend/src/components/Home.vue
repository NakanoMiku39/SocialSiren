<template>
  <div class="container">
    <!-- Header section -->
    <header class="header">
      <h1 class="website-name">SocialSiren</h1>
      <div class="email-input">
        <input type="email" placeholder="Enter your email" class="input-style">
        <button class="email-button">Subscribe</button>
      </div>
    </header>

    <!-- Main content section -->
    <main class="main-content">
      <p>Welcome to SocialSiren, your hub for social updates and more. Stay connected, stay informed.</p>
    </main>

    <!-- Footer section -->
    <footer class="message-box">
      <textarea placeholder="Type your message here" class="input-style"></textarea>
      <button class="send-button">Send</button>
    </footer>
  </div>
</template>

<script>
export default {
  name: 'Home'
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

.email-input {
  display: flex;
  gap: 10px;
}

.input-style {
  padding: 10px;
  font-size: 16px;
  border: 2px solid #bdc3c7;
  border-radius: 5px;
  outline: none;
  transition: border-color 0.3s;
}

.input-style:focus {
  border-color: #3498db;
}

.email-button {
  padding: 10px 20px;
  background-color: #3498db;
  border: none;
  border-radius: 5px;
  color: white;
  cursor: pointer;
  transition: background-color 0.3s;
}

.email-button:hover {
  background-color: #2980b9;
}

.main-content {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  background-color: #ecf0f1;
  color: #2c3e50;
}

.message-box {
  display: flex;
  padding: 20px;
  background-color: #2c3e50;
}

.message-box textarea {
  flex: 1;
  margin-right: 10px;
}

.send-button {
  padding: 10px 20px;
  background-color: #3498db;
  border: none;
  border-radius: 5px;
  color: white;
  cursor: pointer;
  transition: background-color 0.3s;
}

.send-button:hover {
  background-color: #2980b9;
}
</style>
