<template>
  <div id="app">
    <router-view/>
    
  </div>
</template>

<script>
export default {
  name: 'App',
  created() {
  const jwt = localStorage.getItem('jwt');
  if (jwt) {
    this.$store.dispatch('login');  // 用户仍然登录
  }
}

}
</script>
