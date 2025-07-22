<template>
  <div class="tutorial-mcp-mode">
    <n-card title="MCP模式教程" :bordered="false">
      <template #header-extra>
        <n-tag type="success" size="small">
          <template #icon>
            <n-icon><server-outline /></n-icon>
          </template>
          MCP模式
        </n-tag>
      </template>

      <n-space vertical size="large">
        <!-- 概述 -->
        <n-card title="什么是MCP模式？" size="small">
          <n-text>
            MCP模式是 MCPS.ONE 的另一种核心运行模式，在此模式下，MCPS.ONE 直接作为 MCP 服务器运行，
            为客户端应用提供原生的 MCP 协议支持。这种模式适合需要直接集成 MCP 协议的应用场景。
          </n-text>
        </n-card>

        <!-- 工作原理 -->
        <n-card title="工作原理" size="small">
          <n-space vertical>
            <n-text>MCP模式的工作流程如下：</n-text>
            <n-ol>
              <n-li>MCPS.ONE 启动内置的 MCP 服务器</n-li>
              <n-li>客户端应用通过 MCP 协议连接到服务器</n-li>
              <n-li>客户端发送 MCP 标准请求（如工具调用、资源访问等）</n-li>
              <n-li>MCP 服务器处理请求并执行相应的工具或操作</n-li>
              <n-li>服务器返回符合 MCP 协议的响应</n-li>
            </n-ol>
          </n-space>
        </n-card>

        <!-- 优势 -->
        <n-card title="MCP模式的优势" size="small">
          <n-space vertical>
            <n-alert type="success" show-icon>
              <template #icon>
                <n-icon><checkmark-circle-outline /></n-icon>
              </template>
              MCP模式提供了原生协议支持的优势
            </n-alert>
            <n-ul>
              <n-li><strong>原生协议：</strong>完全符合 MCP 标准协议规范</n-li>
              <n-li><strong>高性能：</strong>直接通信，无代理层开销</n-li>
              <n-li><strong>标准兼容：</strong>与所有支持 MCP 的客户端兼容</n-li>
              <n-li><strong>实时通信：</strong>支持 WebSocket 等实时通信协议</n-li>
              <n-li><strong>资源管理：</strong>原生支持 MCP 资源和提示模板</n-li>
            </n-ul>
          </n-space>
        </n-card>

        <!-- 配置步骤 -->
        <n-card title="配置MCP模式" size="small">
          <n-space vertical>
            <n-steps vertical :current="1">
              <n-step title="启用MCP模式">
                <div>在系统设置中选择"MCP模式"或"双模式"</div>
              </n-step>
              <n-step title="配置MCP服务器">
                <div>设置 MCP 服务器的监听地址和端口</div>
                <pre><code>MCP服务器地址: localhost
端口: 3000
协议: stdio/websocket</code></pre>
              </n-step>
              <n-step title="配置工具和资源">
                <div>在工具管理页面配置可用的工具和资源</div>
              </n-step>
              <n-step title="测试连接">
                <div>使用 MCP 客户端测试连接和功能</div>
              </n-step>
            </n-steps>
          </n-space>
        </n-card>

        <!-- MCP协议特性 -->
        <n-card title="MCP协议特性" size="small">
          <n-space vertical>
            <n-descriptions :column="1" bordered>
              <n-descriptions-item label="工具调用">
                支持动态工具发现和调用，客户端可以查询可用工具并执行
              </n-descriptions-item>
              <n-descriptions-item label="资源访问">
                提供文件、数据库等资源的统一访问接口
              </n-descriptions-item>
              <n-descriptions-item label="提示模板">
                支持可重用的提示模板，提高 AI 交互效率
              </n-descriptions-item>
              <n-descriptions-item label="实时通信">
                支持 WebSocket 连接，实现实时双向通信
              </n-descriptions-item>
              <n-descriptions-item label="错误处理">
                标准化的错误响应格式，便于客户端处理
              </n-descriptions-item>
            </n-descriptions>
          </n-space>
        </n-card>

        <!-- 客户端集成 -->
        <n-card title="客户端集成示例" size="small">
          <n-space vertical>
            <n-text>以下是不同客户端集成 MCP 服务器的示例：</n-text>
            
            <n-tabs type="line">
              <n-tab-pane name="claude" tab="Claude Desktop">
                <n-text>在 Claude Desktop 配置文件中添加：</n-text>
                <pre><code>{
  "mcpServers": {
    "mcps-one": {
      "command": "node",
      "args": ["./mcp-client.js"],
      "env": {
        "MCPS_SERVER_URL": "http://localhost:3000"
      }
    }
  }
}</code></pre>
              </n-tab-pane>
              
              <n-tab-pane name="python" tab="Python客户端">
                <pre><code>from mcp import Client
import asyncio

async def main():
    # 连接到 MCP 服务器
    client = Client("ws://localhost:3000")
    await client.connect()
    
    # 获取可用工具
    tools = await client.list_tools()
    print(f"可用工具: {tools}")
    
    # 调用工具
    result = await client.call_tool(
        name="get_weather",
        arguments={"location": "北京"}
    )
    print(f"结果: {result}")
    
    await client.disconnect()

asyncio.run(main())</code></pre>
              </n-tab-pane>
              
              <n-tab-pane name="nodejs" tab="Node.js客户端">
                <pre><code>const { MCPClient } = require('@modelcontextprotocol/client');
const WebSocket = require('ws');

async function main() {
  // 创建 WebSocket 连接
  const ws = new WebSocket('ws://localhost:3000');
  const client = new MCPClient(ws);
  
  // 连接到服务器
  await client.connect();
  
  // 获取可用工具
  const tools = await client.listTools();
  console.log('可用工具:', tools);
  
  // 调用工具
  const result = await client.callTool({
    name: 'get_weather',
    arguments: { location: '北京' }
  });
  console.log('结果:', result);
  
  await client.disconnect();
}

main().catch(console.error);</code></pre>
              </n-tab-pane>
            </n-tabs>
          </n-space>
        </n-card>

        <!-- 工具开发 -->
        <n-card title="自定义工具开发" size="small">
          <n-space vertical>
            <n-alert type="info" show-icon>
              <template #icon>
                <n-icon><code-outline /></n-icon>
              </template>
              在 MCP 模式下，您可以开发自定义工具来扩展功能
            </n-alert>
            
            <n-text>工具开发步骤：</n-text>
            <n-ol>
              <n-li>定义工具的输入参数和输出格式</n-li>
              <n-li>实现工具的核心逻辑</n-li>
              <n-li>注册工具到 MCP 服务器</n-li>
              <n-li>测试工具功能</n-li>
            </n-ol>
            
            <n-text>示例工具代码：</n-text>
            <pre><code>// 天气查询工具示例
class WeatherTool {
  name = 'get_weather';
  description = '获取指定城市的天气信息';
  
  inputSchema = {
    type: 'object',
    properties: {
      location: {
        type: 'string',
        description: '城市名称'
      }
    },
    required: ['location']
  };
  
  async execute(args) {
    const { location } = args;
    // 实现天气查询逻辑
    const weather = await fetchWeather(location);
    return {
      location,
      temperature: weather.temp,
      description: weather.desc
    };
  }
}</code></pre>
          </n-space>
        </n-card>

        <!-- 监控和调试 -->
        <n-card title="监控和调试" size="small">
          <n-space vertical>
            <n-alert type="info" show-icon>
              <template #icon>
                <n-icon><analytics-outline /></n-icon>
              </template>
              MCP 模式提供了完整的监控和调试功能
            </n-alert>
            
            <n-descriptions :column="1" bordered>
              <n-descriptions-item label="服务器状态">
                实时监控 MCP 服务器的运行状态和连接数
              </n-descriptions-item>
              <n-descriptions-item label="请求日志">
                记录所有 MCP 协议请求和响应的详细日志
              </n-descriptions-item>
              <n-descriptions-item label="性能指标">
                监控工具调用的响应时间和成功率
              </n-descriptions-item>
              <n-descriptions-item label="错误追踪">
                自动捕获和记录工具执行中的错误
              </n-descriptions-item>
            </n-descriptions>
          </n-space>
        </n-card>

        <!-- 故障排除 -->
        <n-card title="常见问题和故障排除" size="small">
          <n-space vertical>
            <n-collapse>
              <n-collapse-item title="MCP服务器启动失败" name="1">
                <n-ul>
                  <n-li>检查端口是否被占用</n-li>
                  <n-li>确认 Node.js 版本兼容性</n-li>
                  <n-li>查看启动日志获取详细错误信息</n-li>
                </n-ul>
              </n-collapse-item>
              
              <n-collapse-item title="客户端连接失败" name="2">
                <n-ul>
                  <n-li>验证服务器地址和端口配置</n-li>
                  <n-li>检查防火墙和网络设置</n-li>
                  <n-li>确认 MCP 协议版本兼容性</n-li>
                </n-ul>
              </n-collapse-item>
              
              <n-collapse-item title="工具调用失败" name="3">
                <n-ul>
                  <n-li>检查工具参数格式是否正确</n-li>
                  <n-li>验证工具权限和依赖</n-li>
                  <n-li>查看工具执行日志</n-li>
                </n-ul>
              </n-collapse-item>
              
              <n-collapse-item title="性能问题" name="4">
                <n-ul>
                  <n-li>优化工具执行逻辑</n-li>
                  <n-li>调整并发连接数限制</n-li>
                  <n-li>监控系统资源使用情况</n-li>
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
              遵循最佳实践以获得最佳的 MCP 服务器性能
            </n-alert>
            
            <n-ul>
              <n-li><strong>工具设计：</strong>保持工具功能单一且明确，避免过于复杂的操作</n-li>
              <n-li><strong>错误处理：</strong>实现完善的错误处理和用户友好的错误消息</n-li>
              <n-li><strong>参数验证：</strong>严格验证输入参数，防止安全漏洞</n-li>
              <n-li><strong>性能优化：</strong>对耗时操作使用异步处理和缓存机制</n-li>
              <n-li><strong>文档维护：</strong>保持工具文档的准确性和完整性</n-li>
              <n-li><strong>版本管理：</strong>合理管理工具版本，保持向后兼容性</n-li>
              <n-li><strong>安全考虑：</strong>限制工具权限，避免执行危险操作</n-li>
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
  ServerOutline,
  CheckmarkCircleOutline,
  CodeOutline,
  AnalyticsOutline,
  BulbOutline
} from '@vicons/ionicons5'
</script>

<style scoped>
.tutorial-mcp-mode {
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