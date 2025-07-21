<script setup lang="ts">
import { RouterView } from 'vue-router'
import { NMessageProvider, NDialogProvider } from 'naive-ui'
import DevTools from './components/DevTools.vue'

// 只在开发环境中显示开发工具
const isDevelopment = import.meta.env.DEV
</script>

<template>
  <n-message-provider>
    <n-dialog-provider>
      <RouterView />
      <!-- 开发工具 - 仅在开发环境中显示 -->
      <DevTools v-if="isDevelopment" />
    </n-dialog-provider>
  </n-message-provider>
</template>

<style>
#app {
  height: 100vh;
  overflow: hidden;
}
</style>
