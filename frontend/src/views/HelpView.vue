<template>
  <div class="help-view">
    <div class="help-header">
      <h1>MCPS.ONE 使用教程</h1>
      <p class="subtitle">Model Context Protocol 统一服务平台使用指南</p>
    </div>

    <div class="help-content">
      <!-- 快速开始 -->
      <section class="help-section">
        <h2><n-icon><RocketOutline /></n-icon> 快速开始</h2>
        <div class="section-content">
          <p>MCPS.ONE 是一个功能强大的 MCP (Model Context Protocol) 统一服务平台，支持多种运行模式和灵活的配置选项。</p>
          
          <div class="quick-steps">
            <div class="step">
              <div class="step-number">1</div>
              <div class="step-content">
                <h4>选择服务模式</h4>
                <p>在顶部导航栏选择合适的MCP服务模式</p>
              </div>
            </div>
            <div class="step">
              <div class="step-number">2</div>
              <div class="step-content">
                <h4>配置工具</h4>
                <p>在工具页面配置和管理MCP工具</p>
              </div>
            </div>
            <div class="step">
              <div class="step-number">3</div>
              <div class="step-content">
                <h4>开始使用</h4>
                <p>通过API或直接集成开始使用MCP服务</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- 服务模式详解 -->
      <section class="help-section">
        <h2><n-icon><SettingsOutline /></n-icon> 服务模式详解</h2>
        <div class="section-content">
          <div class="mode-cards">
            <div class="mode-card both">
              <div class="mode-header">
                <n-icon class="mode-icon"><ExtensionPuzzleOutline /></n-icon>
                <h3>双模式 (推荐)</h3>
                <n-tag type="success" size="small">默认模式</n-tag>
              </div>
              <div class="mode-description">
                <p><strong>功能：</strong>同时启用代理服务和MCP服务端</p>
                <p><strong>适用场景：</strong></p>
                <ul>
                  <li>开发和调试环境</li>
                  <li>需要完整功能的生产环境</li>
                  <li>同时支持HTTP API和MCP协议</li>
                </ul>
                <p><strong>优势：</strong>功能最完整，支持所有特性</p>
              </div>
            </div>

            <div class="mode-card proxy">
              <div class="mode-header">
                <n-icon class="mode-icon"><ServerOutline /></n-icon>
                <h3>代理模式</h3>
                <n-tag type="info" size="small">轻量级</n-tag>
              </div>
              <div class="mode-description">
                <p><strong>功能：</strong>仅启用HTTP代理服务</p>
                <p><strong>适用场景：</strong></p>
                <ul>
                  <li>作为MCP工具的HTTP网关</li>
                  <li>需要RESTful API接口</li>
                  <li>资源受限的环境</li>
                </ul>
                <p><strong>优势：</strong>资源占用少，启动快速</p>
              </div>
            </div>

            <div class="mode-card server">
              <div class="mode-header">
                <n-icon class="mode-icon"><TerminalOutline /></n-icon>
                <h3>MCP服务模式</h3>
                <n-tag type="warning" size="small">专业级</n-tag>
              </div>
              <div class="mode-description">
                <p><strong>功能：</strong>仅启用MCP服务端</p>
                <p><strong>适用场景：</strong></p>
                <ul>
                  <li>直接集成到IDE (如Cursor)</li>
                  <li>原生MCP协议通信</li>
                  <li>高性能要求的场景</li>
                </ul>
                <p><strong>优势：</strong>原生协议，性能最优</p>
              </div>
            </div>

            <div class="mode-card disabled">
              <div class="mode-header">
                <n-icon class="mode-icon"><StopCircleOutline /></n-icon>
                <h3>禁用服务</h3>
                <n-tag type="error" size="small">维护模式</n-tag>
              </div>
              <div class="mode-description">
                <p><strong>功能：</strong>关闭所有MCP服务</p>
                <p><strong>适用场景：</strong></p>
                <ul>
                  <li>系统维护期间</li>
                  <li>故障排查</li>
                  <li>资源释放</li>
                </ul>
                <p><strong>优势：</strong>完全停止服务，释放资源</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- 配置指南 -->
      <section class="help-section">
        <h2><n-icon><DocumentTextOutline /></n-icon> 配置指南</h2>
        <div class="section-content">
          <div class="config-tabs">
            <n-tabs type="line" animated>
              <n-tab-pane name="env" tab="环境变量">
                <div class="config-content">
                  <h4>主要配置项</h4>
                  <div class="config-table">
                    <table>
                      <thead>
                        <tr>
                          <th>配置项</th>
                          <th>说明</th>
                          <th>默认值</th>
                          <th>示例</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr>
                          <td><code>MCP_SERVICE_MODE</code></td>
                          <td>服务模式</td>
                          <td>both</td>
                          <td>proxy, server, both, disabled</td>
                        </tr>
                        <tr>
                          <td><code>ENABLE_MCP_SERVER</code></td>
                          <td>启用MCP服务端</td>
                          <td>true</td>
                          <td>true, false</td>
                        </tr>
                        <tr>
                          <td><code>MCP_SERVER_PORT</code></td>
                          <td>MCP服务端口</td>
                          <td>8001</td>
                          <td>8001, 8002</td>
                        </tr>
                        <tr>
                          <td><code>PROXY_PORT</code></td>
                          <td>代理服务端口</td>
                          <td>8000</td>
                          <td>8000, 9000</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </div>
              </n-tab-pane>
              
              <n-tab-pane name="tools" tab="工具配置">
                <div class="config-content">
                  <h4>MCP工具配置</h4>
                  <p>在 <code>mcp_client_config.json</code> 文件中配置MCP工具：</p>
                  <pre><code>{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["@modelcontextprotocol/server-filesystem", "./allowed-files"],
      "env": {}
    },
    "brave-search": {
      "command": "npx",
      "args": ["@modelcontextprotocol/server-brave-search"],
      "env": {
        "BRAVE_API_KEY": "your-api-key"
      }
    }
  }
}</code></pre>
                </div>
              </n-tab-pane>
              
              <n-tab-pane name="docker" tab="Docker部署">
                <div class="config-content">
                  <h4>Docker Compose 配置</h4>
                  <p>使用 Docker Compose 快速部署：</p>
                  <pre><code>version: '3.8'
services:
  mcps-backend:
    build: ./backend
    ports:
      - "8000:8000"
      - "8001:8001"
    environment:
      - MCP_SERVICE_MODE=both
      - ENABLE_MCP_SERVER=true
    volumes:
      - ./backend/data:/app/data
      
  mcps-frontend:
    build: ./frontend
    ports:
      - "5173:5173"
    depends_on:
      - mcps-backend</code></pre>
                </div>
              </n-tab-pane>
            </n-tabs>
          </div>
        </div>
      </section>

      <!-- 使用示例 -->
      <section class="help-section">
        <h2><n-icon><CodeOutline /></n-icon> 使用示例</h2>
        <div class="section-content">
          <div class="example-tabs">
            <n-tabs type="line" animated>
              <n-tab-pane name="api" tab="HTTP API">
                <div class="example-content">
                  <h4>调用MCP工具</h4>
                  <pre><code>// 获取可用工具列表
GET /api/mcp-unified/tools

// 调用工具
POST /api/mcp-unified/tools/call
{
  "tool_name": "filesystem",
  "arguments": {
    "path": "./example-file.txt",
    "action": "read"
  }
}</code></pre>
                  
                  <h4>服务状态管理</h4>
                  <pre><code>// 获取服务状态
GET /api/mcp-unified/service/status

// 切换服务模式
POST /api/mcp-unified/service/switch-mode
{
  "enable_server": true,
  "enable_proxy": true
}</code></pre>
                </div>
              </n-tab-pane>
              
              <n-tab-pane name="cursor" tab="Cursor集成">
                <div class="example-content">
                  <h4>Cursor IDE 配置</h4>
                  <p>在 Cursor 的设置中添加 MCP 服务器配置：</p>
                  <pre><code>{
  "mcpServers": {
    "mcps-one": {
      "command": "python",
      "args": ["./backend/start_mcp_server.py"],
      "env": {
        "MCP_SERVICE_MODE": "server"
      }
    }
  }
}</code></pre>
                  
                  <h4>使用步骤</h4>
                  <ol>
                    <li>确保MCPS.ONE后端服务正在运行</li>
                    <li>将服务模式设置为"MCP服务模式"或"双模式"</li>
                    <li>在Cursor中配置MCP服务器</li>
                    <li>重启Cursor以加载配置</li>
                    <li>在聊天中使用 @mcps-one 调用工具</li>
                  </ol>
                </div>
              </n-tab-pane>
              
              <n-tab-pane name="python" tab="Python SDK">
                <div class="example-content">
                  <h4>Python 客户端示例</h4>
                  <pre><code>import requests

# 初始化客户端
class MCPSClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
    
    def call_tool(self, tool_name, arguments):
        response = requests.post(
            f"{self.base_url}/api/mcp-unified/tools/call",
            json={
                "tool_name": tool_name,
                "arguments": arguments
            }
        )
        return response.json()
    
    def get_tools(self):
        response = requests.get(
            f"{self.base_url}/api/mcp-unified/tools"
        )
        return response.json()

# 使用示例
client = MCPSClient()
tools = client.get_tools()
result = client.call_tool("filesystem", {"path": "./data", "action": "list"})</code></pre>
                </div>
              </n-tab-pane>
            </n-tabs>
          </div>
        </div>
      </section>

      <!-- 故障排除 -->
      <section class="help-section">
        <h2><n-icon><WarningOutline /></n-icon> 故障排除</h2>
        <div class="section-content">
          <div class="troubleshooting">
            <div class="trouble-item">
              <h4>服务无法启动</h4>
              <div class="trouble-content">
                <p><strong>可能原因：</strong></p>
                <ul>
                  <li>端口被占用</li>
                  <li>配置文件错误</li>
                  <li>依赖缺失</li>
                </ul>
                <p><strong>解决方案：</strong></p>
                <ol>
                  <li>检查端口占用：<code>netstat -an | findstr :8000</code></li>
                  <li>验证配置文件格式</li>
                  <li>重新安装依赖：<code>pip install -r requirements.txt</code></li>
                </ol>
              </div>
            </div>
            
            <div class="trouble-item">
              <h4>工具调用失败</h4>
              <div class="trouble-content">
                <p><strong>可能原因：</strong></p>
                <ul>
                  <li>工具未正确配置</li>
                  <li>参数格式错误</li>
                  <li>权限不足</li>
                </ul>
                <p><strong>解决方案：</strong></p>
                <ol>
                  <li>检查工具配置文件</li>
                  <li>验证API调用参数</li>
                  <li>查看系统日志获取详细错误信息</li>
                </ol>
              </div>
            </div>
            
            <div class="trouble-item">
              <h4>Cursor集成问题</h4>
              <div class="trouble-content">
                <p><strong>可能原因：</strong></p>
                <ul>
                  <li>MCP服务器配置错误</li>
                  <li>服务模式不正确</li>
                  <li>网络连接问题</li>
                </ul>
                <p><strong>解决方案：</strong></p>
                <ol>
                  <li>确认服务模式为"server"或"both"</li>
                  <li>检查MCP服务器配置路径</li>
                  <li>重启Cursor和MCPS.ONE服务</li>
                </ol>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- 最佳实践 -->
      <section class="help-section">
        <h2><n-icon><CheckmarkCircleOutline /></n-icon> 最佳实践</h2>
        <div class="section-content">
          <div class="best-practices">
            <div class="practice-category">
              <h4>性能优化</h4>
              <ul>
                <li>根据实际需求选择合适的服务模式</li>
                <li>定期清理日志文件</li>
                <li>监控系统资源使用情况</li>
                <li>使用连接池优化数据库连接</li>
              </ul>
            </div>
            
            <div class="practice-category">
              <h4>安全建议</h4>
              <ul>
                <li>使用环境变量管理敏感配置</li>
                <li>定期更新依赖包</li>
                <li>限制文件系统访问权限</li>
                <li>启用API访问日志</li>
              </ul>
            </div>
            
            <div class="practice-category">
              <h4>运维建议</h4>
              <ul>
                <li>设置健康检查监控</li>
                <li>配置自动重启机制</li>
                <li>定期备份配置文件</li>
                <li>建立错误告警机制</li>
              </ul>
            </div>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { NIcon, NTag, NTabs, NTabPane } from 'naive-ui'
import {
  RocketOutline,
  SettingsOutline,
  ExtensionPuzzleOutline,
  ServerOutline,
  TerminalOutline,
  StopCircleOutline,
  DocumentTextOutline,
  CodeOutline,
  WarningOutline,
  CheckmarkCircleOutline
} from '@vicons/ionicons5'
</script>

<style scoped>
.help-view {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px;
}

.help-header {
  text-align: center;
  margin-bottom: 48px;
  padding: 48px 0;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 12px;
}

.help-header h1 {
  font-size: 48px;
  margin: 0 0 16px 0;
  font-weight: 700;
}

.subtitle {
  font-size: 20px;
  margin: 0;
  opacity: 0.9;
}

.help-content {
  display: flex;
  flex-direction: column;
  gap: 48px;
}

.help-section {
  background: white;
  border-radius: 12px;
  padding: 32px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.help-section h2 {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 28px;
  margin: 0 0 24px 0;
  color: #333;
  border-bottom: 2px solid #f0f0f0;
  padding-bottom: 16px;
}

.section-content {
  font-size: 16px;
  line-height: 1.6;
  color: #555;
}

/* 快速开始步骤 */
.quick-steps {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 24px;
  margin-top: 32px;
}

.step {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding: 24px;
  background: #f8f9fa;
  border-radius: 8px;
  border-left: 4px solid #667eea;
}

.step-number {
  width: 32px;
  height: 32px;
  background: #667eea;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  flex-shrink: 0;
}

.step-content h4 {
  margin: 0 0 8px 0;
  color: #333;
}

.step-content p {
  margin: 0;
  color: #666;
}

/* 服务模式卡片 */
.mode-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 24px;
  margin-top: 24px;
}

.mode-card {
  border: 2px solid #e0e0e0;
  border-radius: 12px;
  padding: 24px;
  transition: all 0.3s ease;
}

.mode-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

.mode-card.both {
  border-color: #52c41a;
  background: linear-gradient(135deg, #f6ffed 0%, #f0f9ff 100%);
}

.mode-card.proxy {
  border-color: #1890ff;
  background: linear-gradient(135deg, #e6f7ff 0%, #f0f5ff 100%);
}

.mode-card.server {
  border-color: #fa8c16;
  background: linear-gradient(135deg, #fff7e6 0%, #fffbf0 100%);
}

.mode-card.disabled {
  border-color: #ff4d4f;
  background: linear-gradient(135deg, #fff1f0 0%, #fff2f0 100%);
}

.mode-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.mode-icon {
  font-size: 24px;
}

.mode-header h3 {
  margin: 0;
  flex: 1;
}

.mode-description p {
  margin: 8px 0;
}

.mode-description ul {
  margin: 8px 0;
  padding-left: 20px;
}

.mode-description li {
  margin: 4px 0;
}

/* 配置表格 */
.config-table {
  margin-top: 16px;
  overflow-x: auto;
}

.config-table table {
  width: 100%;
  border-collapse: collapse;
  background: white;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.config-table th,
.config-table td {
  padding: 12px 16px;
  text-align: left;
  border-bottom: 1px solid #f0f0f0;
}

.config-table th {
  background: #fafafa;
  font-weight: 600;
  color: #333;
}

.config-table code {
  background: #f5f5f5;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 14px;
}

/* 代码块 */
pre {
  background: #f8f8f8;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 16px;
  overflow-x: auto;
  margin: 16px 0;
}

pre code {
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 14px;
  line-height: 1.5;
  color: #333;
}

/* 故障排除 */
.troubleshooting {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.trouble-item {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 20px;
  background: #fafafa;
}

.trouble-item h4 {
  margin: 0 0 12px 0;
  color: #d32f2f;
  font-size: 18px;
}

.trouble-content p {
  margin: 8px 0;
}

.trouble-content strong {
  color: #333;
}

.trouble-content ul,
.trouble-content ol {
  margin: 8px 0;
  padding-left: 20px;
}

.trouble-content li {
  margin: 4px 0;
}

/* 最佳实践 */
.best-practices {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 24px;
}

.practice-category {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 20px;
  border-left: 4px solid #52c41a;
}

.practice-category h4 {
  margin: 0 0 12px 0;
  color: #333;
  font-size: 18px;
}

.practice-category ul {
  margin: 0;
  padding-left: 20px;
}

.practice-category li {
  margin: 6px 0;
  color: #555;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .help-view {
    padding: 0 16px;
  }
  
  .help-header {
    padding: 32px 16px;
  }
  
  .help-header h1 {
    font-size: 36px;
  }
  
  .subtitle {
    font-size: 18px;
  }
  
  .help-section {
    padding: 24px 16px;
  }
  
  .help-section h2 {
    font-size: 24px;
  }
  
  .mode-cards {
    grid-template-columns: 1fr;
  }
  
  .quick-steps {
    grid-template-columns: 1fr;
  }
  
  .best-practices {
    grid-template-columns: 1fr;
  }
}
</style>