<template>
  <div class="tutorial-tools-view">
    <div class="tutorial-header">
      <h1>工具管理教程</h1>
      <p class="subtitle">学习如何管理和配置 MCP 工具</p>
    </div>

    <div class="tutorial-content">
      <!-- 工具概述 -->
      <section class="tutorial-section">
        <h2><n-icon><ExtensionPuzzleOutline /></n-icon> 工具概述</h2>
        <div class="section-content">
          <p>MCP 工具是 Model Context Protocol 的核心组件，提供了与外部系统交互的能力。通过工具管理界面，您可以：</p>
          <ul>
            <li>查看所有可用的 MCP 工具</li>
            <li>启用或禁用特定工具</li>
            <li>配置工具参数</li>
            <li>监控工具运行状态</li>
            <li>查看工具使用统计</li>
          </ul>
        </div>
      </section>

      <!-- 添加工具 -->
      <section class="tutorial-section">
        <h2><n-icon><AddOutline /></n-icon> 添加新工具</h2>
        <div class="section-content">
          <div class="step-guide">
            <div class="step">
              <div class="step-number">1</div>
              <div class="step-content">
                <h4>进入工具页面</h4>
                <p>点击左侧菜单的 "MCP 工具" 进入工具管理页面</p>
              </div>
            </div>
            <div class="step">
              <div class="step-number">2</div>
              <div class="step-content">
                <h4>点击添加工具</h4>
                <p>在工具列表页面，点击右上角的 "添加工具" 按钮</p>
              </div>
            </div>
            <div class="step">
              <div class="step-number">3</div>
              <div class="step-content">
                <h4>填写工具信息</h4>
                <p>在弹出的表单中填写以下信息：</p>
                <ul>
                  <li><strong>工具名称：</strong>工具的显示名称</li>
                  <li><strong>工具类型：</strong>选择工具类型（如 API、数据库、文件系统等）</li>
                  <li><strong>描述：</strong>工具的功能描述</li>
                  <li><strong>配置参数：</strong>根据工具类型填写相应的配置</li>
                </ul>
              </div>
            </div>
            <div class="step">
              <div class="step-number">4</div>
              <div class="step-content">
                <h4>保存并测试</h4>
                <p>保存工具配置后，系统会自动进行连接测试</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- 工具配置 -->
      <section class="tutorial-section">
        <h2><n-icon><SettingsOutline /></n-icon> 工具配置</h2>
        <div class="section-content">
          <h3>常见配置项</h3>
          <div class="config-grid">
            <div class="config-item">
              <h4>连接配置</h4>
              <ul>
                <li>服务器地址</li>
                <li>端口号</li>
                <li>认证信息</li>
                <li>超时设置</li>
              </ul>
            </div>
            <div class="config-item">
              <h4>功能配置</h4>
              <ul>
                <li>启用的功能模块</li>
                <li>权限设置</li>
                <li>缓存配置</li>
                <li>日志级别</li>
              </ul>
            </div>
            <div class="config-item">
              <h4>性能配置</h4>
              <ul>
                <li>并发连接数</li>
                <li>重试次数</li>
                <li>缓存大小</li>
                <li>刷新间隔</li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      <!-- 工具状态管理 -->
      <section class="tutorial-section">
        <h2><n-icon><PlayCircleOutline /></n-icon> 工具状态管理</h2>
        <div class="section-content">
          <h3>工具状态说明</h3>
          <div class="status-grid">
            <div class="status-item running">
              <n-tag type="success" size="large">运行中</n-tag>
              <p>工具正常运行，可以接收和处理请求</p>
            </div>
            <div class="status-item stopped">
              <n-tag type="default" size="large">已停止</n-tag>
              <p>工具已停止，不会处理任何请求</p>
            </div>
            <div class="status-item error">
              <n-tag type="error" size="large">错误</n-tag>
              <p>工具运行出现错误，需要检查配置或日志</p>
            </div>
            <div class="status-item loading">
              <n-tag type="warning" size="large">启动中</n-tag>
              <p>工具正在启动过程中，请稍等</p>
            </div>
          </div>

          <h3>状态操作</h3>
          <ul>
            <li><strong>启动工具：</strong>点击工具卡片上的启动按钮</li>
            <li><strong>停止工具：</strong>点击工具卡片上的停止按钮</li>
            <li><strong>重启工具：</strong>先停止再启动工具</li>
            <li><strong>查看日志：</strong>点击工具卡片上的日志按钮</li>
          </ul>
        </div>
      </section>

      <!-- 故障排除 -->
      <section class="tutorial-section">
        <h2><n-icon><WarningOutline /></n-icon> 故障排除</h2>
        <div class="section-content">
          <h3>常见问题</h3>
          <div class="troubleshoot-grid">
            <div class="troubleshoot-item">
              <h4>工具无法启动</h4>
              <ul>
                <li>检查配置参数是否正确</li>
                <li>确认网络连接是否正常</li>
                <li>查看系统日志获取详细错误信息</li>
                <li>检查依赖服务是否运行</li>
              </ul>
            </div>
            <div class="troubleshoot-item">
              <h4>工具响应缓慢</h4>
              <ul>
                <li>检查网络延迟</li>
                <li>调整超时设置</li>
                <li>优化查询条件</li>
                <li>检查服务器资源使用情况</li>
              </ul>
            </div>
            <div class="troubleshoot-item">
              <h4>认证失败</h4>
              <ul>
                <li>确认用户名和密码正确</li>
                <li>检查 API 密钥是否有效</li>
                <li>确认权限设置</li>
                <li>检查认证服务状态</li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      <!-- 最佳实践 -->
      <section class="tutorial-section">
        <h2><n-icon><CheckmarkCircleOutline /></n-icon> 最佳实践</h2>
        <div class="section-content">
          <div class="best-practices">
            <div class="practice-item">
              <h4>定期监控</h4>
              <p>定期检查工具运行状态，及时发现和解决问题</p>
            </div>
            <div class="practice-item">
              <h4>合理配置</h4>
              <p>根据实际需求配置工具参数，避免资源浪费</p>
            </div>
            <div class="practice-item">
              <h4>备份配置</h4>
              <p>定期备份工具配置，便于快速恢复</p>
            </div>
            <div class="practice-item">
              <h4>文档记录</h4>
              <p>记录工具配置和使用说明，便于团队协作</p>
            </div>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { NIcon, NTag } from 'naive-ui'
import {
  ExtensionPuzzleOutline,
  AddOutline,
  SettingsOutline,
  PlayCircleOutline,
  WarningOutline,
  CheckmarkCircleOutline
} from '@vicons/ionicons5'
</script>

<style scoped>
.tutorial-tools-view {
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
}

.tutorial-header {
  text-align: center;
  margin-bottom: 40px;
}

.tutorial-header h1 {
  font-size: 2.5rem;
  font-weight: 600;
  color: #333;
  margin-bottom: 8px;
}

.subtitle {
  font-size: 1.1rem;
  color: #666;
  margin: 0;
}

.tutorial-content {
  display: flex;
  flex-direction: column;
  gap: 40px;
}

.tutorial-section {
  background: white;
  border-radius: 12px;
  padding: 32px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.tutorial-section h2 {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 1.5rem;
  font-weight: 600;
  color: #333;
  margin-bottom: 20px;
}

.tutorial-section h3 {
  font-size: 1.2rem;
  font-weight: 600;
  color: #333;
  margin: 24px 0 16px 0;
}

.tutorial-section h4 {
  font-size: 1.1rem;
  font-weight: 600;
  color: #333;
  margin-bottom: 8px;
}

.section-content {
  color: #666;
  line-height: 1.6;
}

.section-content ul {
  margin: 16px 0;
  padding-left: 20px;
}

.section-content li {
  margin-bottom: 8px;
}

.step-guide {
  display: flex;
  flex-direction: column;
  gap: 24px;
  margin-top: 20px;
}

.step {
  display: flex;
  gap: 16px;
  align-items: flex-start;
}

.step-number {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #18a058;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  flex-shrink: 0;
}

.step-content {
  flex: 1;
}

.config-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 24px;
  margin-top: 20px;
}

.config-item {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 20px;
}

.status-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin: 20px 0;
}

.status-item {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 20px;
  text-align: center;
}

.status-item p {
  margin-top: 12px;
  color: #666;
}

.troubleshoot-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 24px;
  margin-top: 20px;
}

.troubleshoot-item {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 20px;
}

.best-practices {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-top: 20px;
}

.practice-item {
  background: #f0f9ff;
  border-radius: 8px;
  padding: 20px;
  border-left: 4px solid #18a058;
}

.practice-item h4 {
  color: #18a058;
  margin-bottom: 8px;
}

.practice-item p {
  color: #666;
  margin: 0;
}

@media (max-width: 768px) {
  .tutorial-tools-view {
    padding: 16px;
  }
  
  .tutorial-section {
    padding: 20px;
  }
  
  .config-grid,
  .status-grid,
  .troubleshoot-grid,
  .best-practices {
    grid-template-columns: 1fr;
  }
}
</style>