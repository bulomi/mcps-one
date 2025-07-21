<template>
  <div class="test-container">
    <h1>测试页面</h1>
    <p>如果您能看到这个页面，说明Vue应用正在正常运行。</p>
    <div class="info-section">
      <h2>应用信息</h2>
      <ul>
        <li>当前时间: {{ currentTime }}</li>
        <li>路由路径: {{ $route.path }}</li>
        <li>Vue版本: {{ vueVersion }}</li>
      </ul>
    </div>
    <div class="actions">
      <button @click="updateTime">更新时间</button>
      <button @click="goToLogin">前往登录页</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { version } from 'vue'

const router = useRouter()
const currentTime = ref('')
const vueVersion = version

const updateTime = () => {
  currentTime.value = new Date().toLocaleString('zh-CN')
}

const goToLogin = () => {
  router.push('/login')
}

onMounted(() => {
  updateTime()
  // 测试页面已挂载
})
</script>

<style scoped>
.test-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
  font-family: Arial, sans-serif;
}

h1 {
  color: #2c3e50;
  text-align: center;
}

.info-section {
  background: #f8f9fa;
  padding: 20px;
  border-radius: 8px;
  margin: 20px 0;
}

.info-section ul {
  list-style-type: none;
  padding: 0;
}

.info-section li {
  padding: 8px 0;
  border-bottom: 1px solid #dee2e6;
}

.actions {
  text-align: center;
  margin-top: 20px;
}

.actions button {
  background: #007bff;
  color: white;
  border: none;
  padding: 10px 20px;
  margin: 0 10px;
  border-radius: 4px;
  cursor: pointer;
}

.actions button:hover {
  background: #0056b3;
}
</style>