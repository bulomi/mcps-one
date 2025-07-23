<template>
  <div class="tutorial-view">
    <div class="page-header">
      <div class="header-content">
        <div class="header-left">
          <h1>使用教程</h1>
          <p>了解如何使用 MCPS.ONE 的各种功能和模式</p>
        </div>
      </div>
    </div>

    <n-grid :cols="1" :y-gap="24">
      <!-- 概述卡片 -->
      <n-grid-item>
        <n-card title="MCPS.ONE 平台概述" class="overview-card">
          <template #header-extra>
            <n-icon size="24" color="#18a058">
              <BookOutline />
            </n-icon>
          </template>
          <n-space vertical size="large">
            <p>
              MCPS.ONE 是一个 MCP 工具管理平台，提供工具添加、配置管理和服务控制功能。
              支持 MCP 服务模式和 FastMCP 代理模式两种运行方式。
            </p>
            <n-alert type="info" show-icon>
              <template #icon>
                <n-icon><InformationCircleOutline /></n-icon>
              </template>
              通过 Web 界面轻松管理 MCP 工具，为 AI 客户端提供统一的工具服务。
            </n-alert>
          </n-space>
        </n-card>
      </n-grid-item>

      <!-- 模式对比 -->
      <n-grid-item>
        <n-card title="运行模式说明" class="comparison-card">
          <n-grid :cols="2" :x-gap="24">
            <n-grid-item>
              <div class="mode-card server-mode">
                <div class="mode-header">
                  <n-icon size="32" color="#2080f0">
                    <ExtensionPuzzleOutline />
                  </n-icon>
                  <h3>MCP服务模式</h3>
                </div>
                <div class="mode-content">
                  <n-space vertical size="medium">
                    <p><strong>功能：</strong>直接启动 MCP 工具服务</p>
                    <p><strong>配置：</strong>客户端直连工具端口</p>
                    <p><strong>适用：</strong>单一客户端连接</p>
                  </n-space>
                </div>
              </div>
            </n-grid-item>
            <n-grid-item>
              <div class="mode-card proxy-mode">
                <div class="mode-header">
                  <n-icon size="32" color="#f0a020">
                    <GitNetworkOutline />
                  </n-icon>
                  <h3>FastMCP代理</h3>
                </div>
                <div class="mode-content">
                  <n-space vertical size="medium">
                    <p><strong>功能：</strong>代理层管理多个工具</p>
                    <p><strong>配置：</strong>客户端连接代理端口</p>
                    <p><strong>适用：</strong>多客户端并发访问</p>
                  </n-space>
                </div>
              </div>
            </n-grid-item>
          </n-grid>
        </n-card>
      </n-grid-item>

      <!-- 快速导航 -->
      <n-grid-item>
        <n-card title="功能导航" class="navigation-card">
          <n-grid :cols="4" :x-gap="16">
            <n-grid-item>
              <n-button 
                type="success" 
                size="large" 
                block 
                @click="navigateToDoc('getting-started.md')"
                class="nav-button"
              >
                <template #icon>
                  <n-icon><BookOutline /></n-icon>
                </template>
                快速开始
              </n-button>
            </n-grid-item>
            <n-grid-item>
              <n-button 
                type="primary" 
                size="large" 
                block 
                @click="$router.push('/tools')"
                class="nav-button"
              >
                <template #icon>
                  <n-icon><ExtensionPuzzleOutline /></n-icon>
                </template>
                MCP 工具管理
              </n-button>
            </n-grid-item>
            <n-grid-item>
              <n-button 
                type="info" 
                size="large" 
                block 
                @click="navigateToDoc('configuration.md')"
                class="nav-button"
              >
                <template #icon>
                  <n-icon><GitNetworkOutline /></n-icon>
                </template>
                配置指南
              </n-button>
            </n-grid-item>
            <n-grid-item>
              <n-button 
                type="warning" 
                size="large" 
                block 
                @click="navigateToDoc('api-guide.md')"
                class="nav-button"
              >
                <template #icon>
                  <n-icon><CodeOutline /></n-icon>
                </template>
                API 使用指南
              </n-button>
            </n-grid-item>
          </n-grid>
        </n-card>
      </n-grid-item>
    </n-grid>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import {
  NGrid,
  NGridItem,
  NCard,
  NSpace,
  NButton,
  NIcon,
  NAlert
} from 'naive-ui'
import {
  BookOutline,
  ExtensionPuzzleOutline,
  GitNetworkOutline,
  CodeOutline,
  InformationCircleOutline
} from '@vicons/ionicons5'

const router = useRouter()

// 导航到文档页面并选择特定文档
const navigateToDoc = (docPath: string) => {
  router.push({ path: '/docs', query: { doc: docPath } })
}
</script>

<style scoped>
.tutorial-view {
  padding: 0;
  background: transparent;
}

.page-header {
  margin-bottom: 24px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.header-left h1 {
  margin: 0 0 8px 0;
  font-size: 28px;
  font-weight: 600;
  color: var(--n-text-color-1);
}

.header-left p {
  margin: 0;
  color: var(--n-text-color-2);
  font-size: 16px;
}

.overview-card,
.comparison-card,
.navigation-card {
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border: none;
}

.mode-card {
  padding: 20px;
  border-radius: 8px;
  border: 2px solid transparent;
  transition: all 0.3s ease;
  height: 100%;
}

.server-mode {
  background: linear-gradient(135deg, #e3f2fd 0%, #f3e5f5 100%);
  border-color: #2080f0;
}

.proxy-mode {
  background: linear-gradient(135deg, #fff8e1 0%, #fce4ec 100%);
  border-color: #f0a020;
}

.mode-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.mode-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.mode-content ul {
  margin: 8px 0;
  padding-left: 20px;
}

.mode-content li {
  margin: 4px 0;
  color: var(--n-text-color-2);
}

.nav-button {
  height: 60px;
  font-size: 16px;
  font-weight: 500;
}

.n-card {
  transition: all 0.3s ease;
}

.n-card:hover {
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
}
</style>