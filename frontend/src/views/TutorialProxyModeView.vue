<template>
  <div class="tutorial-proxy-mode">
    <n-card title="代理模式教程" :bordered="false">
      <template #header-extra>
        <n-tag type="info" size="small">
          <template #icon>
            <n-icon><cloud-outline /></n-icon>
          </template>
          代理模式
        </n-tag>
      </template>

      <n-space vertical size="large">
        <!-- 概述 -->
        <n-card title="什么是代理模式？" size="small">
          <n-text>
            代理模式是 MCPS.ONE 的核心功能之一，它允许您的应用程序通过代理服务器与 MCP 服务器进行通信。
            在这种模式下，MCPS.ONE 充当中间代理，处理客户端请求并转发到相应的 MCP 服务器。
          </n-text>
        </n-card>

        <!-- 工作原理 -->
        <n-card title="工作原理" size="small">
          <n-space vertical>
            <n-text>代理模式的工作流程如下：</n-text>
            <n-ol>
              <n-li>客户端应用发送请求到 MCPS.ONE 代理服务器</n-li>
              <n-li>代理服务器解析请求并确定目标 MCP 服务器</n-li>
              <n-li>代理服务器将请求转发到相应的 MCP 服务器</n-li>
              <n-li>MCP 服务器处理请求并返回响应</n-li>
              <n-li>代理服务器将响应转发回客户端应用</n-li>
            </n-ol>
          </n-space>
        </n-card>

        <!-- 优势 -->
        <n-card title="代理模式的优势" size="small">
          <n-space vertical>
            <n-alert type="success" show-icon>
              <template #icon>
                <n-icon><checkmark-circle-outline /></n-icon>
              </template>
              代理模式提供了多项重要优势
            </n-alert>
            <n-ul>
              <n-li><strong>统一入口：</strong>所有 MCP 服务器通过单一代理端点访问</n-li>
              <n-li><strong>负载均衡：</strong>自动分发请求到多个 MCP 服务器实例</n-li>
              <n-li><strong>安全控制：</strong>集中管理认证和授权</n-li>
              <n-li><strong>监控日志：</strong>统一收集和分析所有请求日志</n-li>
              <n-li><strong>故障恢复：</strong>自动处理服务器故障和重试机制</n-li>
            </n-ul>
          </n-space>
        </n-card>

        <!-- 配置步骤 -->
        <n-card title="配置代理模式" size="small">
          <n-space vertical>
            <n-steps vertical :current="1">
              <n-step title="启用代理模式">
                <div>在系统设置中选择"代理模式"或"双模式"</div>
              </n-step>
              <n-step title="配置代理端点">
                <div>设置代理服务器的监听地址和端口</div>
                <pre><code>代理地址: http://localhost:8080
端口: 8080</code></pre>
              </n-step>
              <n-step title="添加 MCP 服务器">
                <div>在工具管理页面添加要代理的 MCP 服务器</div>
              </n-step>
              <n-step title="测试连接">
                <div>验证代理服务器与 MCP 服务器的连接状态</div>
              </n-step>
            </n-steps>
          </n-space>
        </n-card>

        <!-- 使用示例 -->
        <n-card title="使用示例" size="small">
          <n-space vertical>
            <n-text>以下是通过代理模式调用 MCP 服务器的示例：</n-text>
            
            <n-tabs type="line">
              <n-tab-pane name="curl" tab="cURL">
                <pre><code>curl -X POST http://localhost:8080/api/proxy/call \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "server_name": "example-mcp-server",
    "tool_name": "get_weather",
    "arguments": {
      "location": "北京"
    }
  }'</code></pre>
              </n-tab-pane>
              
              <n-tab-pane name="python" tab="Python">
                <pre><code>import requests

url = "http://localhost:8080/api/proxy/call"
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer YOUR_TOKEN"
}
data = {
    "server_name": "example-mcp-server",
    "tool_name": "get_weather",
    "arguments": {
        "location": "北京"
    }
}

response = requests.post(url, json=data, headers=headers)
print(response.json())</code></pre>
              </n-tab-pane>
              
              <n-tab-pane name="javascript" tab="JavaScript">
                <pre><code>const response = await fetch("http://localhost:8080/api/proxy/call", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    "Authorization": "Bearer YOUR_TOKEN"
  },
  body: JSON.stringify({
    server_name: "example-mcp-server",
    tool_name: "get_weather",
    arguments: {
      location: "北京"
    }
  })
});

const result = await response.json();
// 处理响应结果</code></pre>
              </n-tab-pane>
            </n-tabs>
          </n-space>
        </n-card>

        <!-- 监控和调试 -->
        <n-card title="监控和调试" size="small">
          <n-space vertical>
            <n-alert type="info" show-icon>
              <template #icon>
                <n-icon><information-circle-outline /></n-icon>
              </template>
              代理模式提供了丰富的监控和调试功能
            </n-alert>
            
            <n-descriptions :column="1" bordered>
              <n-descriptions-item label="代理状态">
                在"代理状态"页面查看当前代理服务器的运行状态
              </n-descriptions-item>
              <n-descriptions-item label="会话管理">
                在"代理会话"页面查看和管理活跃的代理会话
              </n-descriptions-item>
              <n-descriptions-item label="日志查看">
                在"日志"页面查看详细的代理请求和响应日志
              </n-descriptions-item>
              <n-descriptions-item label="性能监控">
                监控代理服务器的性能指标和资源使用情况
              </n-descriptions-item>
            </n-descriptions>
          </n-space>
        </n-card>

        <!-- 故障排除 -->
        <n-card title="常见问题和故障排除" size="small">
          <n-space vertical>
            <n-collapse>
              <n-collapse-item title="代理服务器无法启动" name="1">
                <n-ul>
                  <n-li>检查端口是否被占用</n-li>
                  <n-li>确认配置文件格式正确</n-li>
                  <n-li>查看系统日志获取详细错误信息</n-li>
                </n-ul>
              </n-collapse-item>
              
              <n-collapse-item title="MCP 服务器连接失败" name="2">
                <n-ul>
                  <n-li>验证 MCP 服务器地址和端口</n-li>
                  <n-li>检查网络连接和防火墙设置</n-li>
                  <n-li>确认 MCP 服务器正在运行</n-li>
                </n-ul>
              </n-collapse-item>
              
              <n-collapse-item title="请求超时" name="3">
                <n-ul>
                  <n-li>调整代理超时设置</n-li>
                  <n-li>检查 MCP 服务器响应时间</n-li>
                  <n-li>优化网络配置</n-li>
                </n-ul>
              </n-collapse-item>
            </n-collapse>
          </n-space>
        </n-card>

        <!-- 最佳实践 -->
        <n-card title="最佳实践" size="small">
          <n-space vertical>
            <n-alert type="warning" show-icon>
              <template #icon>
                <n-icon><bulb-outline /></n-icon>
              </template>
              遵循最佳实践以获得最佳性能和稳定性
            </n-alert>
            
            <n-ul>
              <n-li><strong>合理配置超时：</strong>根据 MCP 服务器的响应时间设置合适的超时值</n-li>
              <n-li><strong>监控资源使用：</strong>定期检查代理服务器的 CPU 和内存使用情况</n-li>
              <n-li><strong>日志管理：</strong>定期清理和归档日志文件，避免磁盘空间不足</n-li>
              <n-li><strong>安全配置：</strong>使用强密码和 HTTPS 连接保护代理服务器</n-li>
              <n-li><strong>备份配置：</strong>定期备份代理服务器配置文件</n-li>
              <n-li><strong>版本管理：</strong>保持 MCPS.ONE 和 MCP 服务器版本的兼容性</n-li>
            </n-ul>
          </n-space>
        </n-card>
      </n-space>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import {
  NCard,
  NSpace,
  NText,
  NTag,
  NIcon,
  NAlert,
  NSteps,
  NStep,
  NTabs,
  NTabPane,
  NDescriptions,
  NDescriptionsItem,
  NCollapse,
  NCollapseItem,
  NOl,
  NLi,
  NUl
} from 'naive-ui'
import {
  CloudOutline,
  CheckmarkCircleOutline,
  InformationCircleOutline,
  BulbOutline
} from '@vicons/ionicons5'
</script>

<style scoped>
.tutorial-proxy-mode {
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
}

pre {
  background-color: #f5f5f5;
  padding: 12px;
  border-radius: 6px;
  overflow-x: auto;
  font-family: 'Courier New', monospace;
  font-size: 14px;
  line-height: 1.4;
}

code {
  font-family: 'Courier New', monospace;
  font-size: 14px;
  background-color: #f5f5f5;
  padding: 2px 4px;
  border-radius: 3px;
}

.n-steps {
  margin-top: 16px;
}

.n-collapse {
  margin-top: 16px;
}
</style>