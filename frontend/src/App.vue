<script setup lang="ts">
import { RouterView } from 'vue-router'
import { NMessageProvider, NDialogProvider } from 'naive-ui'
</script>

<template>
  <n-message-provider>
    <n-dialog-provider>
      <RouterView />
    </n-dialog-provider>
  </n-message-provider>
</template>

<style>
#app {
  height: 100vh;
  overflow: hidden;
}
</style>
