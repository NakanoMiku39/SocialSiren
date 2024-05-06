<template>
  <div>
    <h1>发送数据到 Flask</h1>
    <input v-model="inputData" placeholder="输入一些数据">
    <button @click="sendData">发送</button>
    <p>从 Flask 收到的响应: {{ responseData }}</p>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  data() {
    return {
      inputData: '',
      responseData: ''
    };
  },
  methods: {
    async sendData() {
      try {
        const response = await axios.post('http://localhost:2222/api/data', {
          data: this.inputData
        });
        this.responseData = response.data.data;
      } catch (error) {
        console.error('There was an error!', error);
      }
    }
  }
}
</script>
