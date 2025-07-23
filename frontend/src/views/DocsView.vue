<template>
  <div class="docs-view">
    <!-- 文档导航栏 -->
    <div class="docs-nav">
      <div class="nav-container">
        <n-breadcrumb>
          <n-breadcrumb-item>文档</n-breadcrumb-item>
          <n-breadcrumb-item v-if="currentDocTitle">{{ currentDocTitle }}</n-breadcrumb-item>
        </n-breadcrumb>
        
        <div class="nav-actions">
          <n-select
            v-model:value="selectedDoc"
            :options="selectOptions"
            placeholder="选择文档"
            @update:value="handleDocSelect"
            style="width: 200px; margin-right: 12px"
          />
          <n-button
            text
            @click="toggleSidebar"
            :class="{ active: !sidebarCollapsed }"
          >
            <template #icon>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                <path d="M3 18h18v-2H3v2zm0-5h18v-2H3v2zm0-7v2h18V6H3z"/>
              </svg>
            </template>
          </n-button>
        </div>
      </div>
    </div>

    <div class="docs-layout">
      <!-- 左侧文档目录 -->
      <div class="docs-sidebar" :class="{ collapsed: sidebarCollapsed }">
        <div class="sidebar-header">
          <h3>文档目录</h3>
        </div>
        <div class="sidebar-content">
          <n-tree
            v-if="treeData.length > 0"
            :data="treeData"
            :selected-keys="selectedKeys"
            :expanded-keys="expandedKeys"
            block-line
            @update:selected-keys="handleTreeSelect"
            @update:expanded-keys="handleTreeExpand"
            :node-props="getNodeProps"
          />
          <div v-else-if="loading" class="sidebar-loading">
            <n-spin size="small" />
            <span>加载中...</span>
          </div>
          <div v-else class="sidebar-empty">
            <n-empty size="small" description="暂无文档" />
          </div>
        </div>
      </div>

      <!-- 主内容区 -->
      <div class="docs-content">
        <div v-if="loading" class="loading-container">
          <n-spin size="large" />
        </div>
        
        <div v-else-if="error" class="error-container">
          <n-result status="error" title="加载失败" :description="error">
            <template #footer>
              <n-button @click="loadDocs">重试</n-button>
            </template>
          </n-result>
        </div>

        <div v-else-if="selectedDoc && currentDocContent" class="doc-container">
          <article class="doc-article">
            <div class="doc-content" v-html="renderedContent"></div>
          </article>
        </div>

        <div v-else class="welcome-container">
          <n-empty description="请从左侧目录选择一个文档开始阅读">
            <template #extra>
              <n-button @click="toggleSidebar" v-if="sidebarCollapsed">
                显示文档目录
              </n-button>
            </template>
          </n-empty>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, watch, h } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { NSpin, NResult, NButton, NEmpty, NTree, NSelect, NBreadcrumb, NBreadcrumbItem } from 'naive-ui'
import { marked } from 'marked'
import { api } from '@/api/utils'

interface DocItem {
  name: string
  path: string
  title: string
}

interface TreeNode {
  key: string
  label: string
  children?: TreeNode[]
  isLeaf?: boolean
}

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const error = ref('')
const docs = ref<DocItem[]>([])
const selectedDoc = ref<string | null>(null)
const currentDocContent = ref('')
const currentDocTitle = ref('')
const sidebarCollapsed = ref(false)
const selectedKeys = ref<string[]>([])
    const expandedKeys = ref<string[]>([])
    const activeHeadingId = ref('')
    let scrollCleanup: (() => void) | null = null

// 选择器选项
const selectOptions = computed(() => {
  return docs.value.map(doc => ({
    label: doc.title,
    value: doc.path
  }))
})

// 构建当前文档的目录结构
const treeData = computed(() => {
  if (!currentDocContent.value) {
    return []
  }
  
  const lines = currentDocContent.value.split('\n')
  const headings: { level: number; text: string; id: string; lineIndex: number }[] = []
  
  // 跟踪是否在代码块中
  let inCodeBlock = false
  
  // 提取所有标题，过滤掉代码块中的内容
  lines.forEach((line, index) => {
    // 检查是否进入或退出代码块
    if (line.trim().startsWith('```')) {
      inCodeBlock = !inCodeBlock
      return
    }
    
    // 如果在代码块中，跳过这一行
    if (inCodeBlock) {
      return
    }
    
    // 检查是否为标题行
    const match = line.match(/^(#{1,6})\s+(.+)$/)
    if (match) {
      const level = match[1].length
      const text = match[2].trim()
      const id = `heading-${index}-${text.replace(/[^a-zA-Z0-9\u4e00-\u9fa5]/g, '-').toLowerCase()}`
      headings.push({ level, text, id, lineIndex: index })
    }
  })
  
  // 过滤重复标题，保留第一个出现的
  const uniqueHeadings = []
  const seenTitles = new Set()
  
  for (const heading of headings) {
    const titleKey = `${heading.level}-${heading.text}`
    if (!seenTitles.has(titleKey)) {
      seenTitles.add(titleKey)
      uniqueHeadings.push(heading)
    }
  }
  
  // 构建树形结构
  const result: TreeNode[] = []
  const stack: { node: TreeNode; level: number }[] = []
  
  for (const heading of uniqueHeadings) {
    const node: TreeNode = {
      key: heading.id,
      label: heading.text,
      children: [],
      isLeaf: true
    }
    
    // 找到正确的父节点
    while (stack.length > 0 && stack[stack.length - 1].level >= heading.level) {
      stack.pop()
    }
    
    if (stack.length === 0) {
      // 顶级节点
      result.push(node)
    } else {
      // 添加到父节点的children中
      const parent = stack[stack.length - 1].node
      if (!parent.children) {
        parent.children = []
      }
      parent.children.push(node)
      parent.isLeaf = false
    }
    
    stack.push({ node, level: heading.level })
  }
  
  return result
})

// 渲染的Markdown内容
const renderedContent = computed(() => {
  if (!currentDocContent.value) return ''
  
  // 先渲染Markdown
  let html = marked(currentDocContent.value)
  
  // 获取原始文档的行信息，用于生成一致的ID
  const lines = currentDocContent.value.split('\n')
  let inCodeBlock = false
  const headingLines: { lineIndex: number; text: string }[] = []
  
  lines.forEach((line, index) => {
    if (line.trim().startsWith('```')) {
      inCodeBlock = !inCodeBlock
      return
    }
    if (inCodeBlock) return
    
    const match = line.match(/^(#{1,6})\s+(.+)$/)
    if (match) {
      const text = match[2].trim()
      headingLines.push({ lineIndex: index, text })
    }
  })
  
  // 为标题添加ID属性，使用与目录生成相同的逻辑
  let headingIndex = 0
  html = html.replace(/<h([1-6])>([^<]+)<\/h[1-6]>/g, (match, level, text) => {
    const cleanText = text.trim()
    if (headingIndex < headingLines.length) {
      const headingInfo = headingLines[headingIndex]
      const id = `heading-${headingInfo.lineIndex}-${headingInfo.text.replace(/[^a-zA-Z0-9\u4e00-\u9fa5]/g, '-').toLowerCase()}`
      headingIndex++
      return `<h${level} data-heading-id="${id}">${cleanText}</h${level}>`
    }
    return match
  })
  
  return html
})

// 加载文档列表
const loadDocs = async () => {
  try {
    loading.value = true
    error.value = ''
    const response = await api.get('/docs/')
    docs.value = response.data.items || []
  } catch (err: any) {
    error.value = err.response?.data?.message || '加载文档列表失败'
    console.error('加载文档列表失败:', err)
  } finally {
    loading.value = false
  }
}

// 加载文档内容
const loadDocContent = async (docPath: string) => {
  try {
    loading.value = true
    error.value = ''
    const response = await api.get('/docs/content', {
      params: { path: docPath }
    })
    currentDocContent.value = response.data.content
    currentDocTitle.value = response.data.title || docPath
  } catch (err: any) {
    error.value = err.response?.data?.message || '加载文档内容失败'
    console.error('加载文档内容失败:', err)
  } finally {
    loading.value = false
  }
}

// 切换侧边栏
const toggleSidebar = () => {
  sidebarCollapsed.value = !sidebarCollapsed.value
}

// 处理树节点选择
const handleTreeSelect = (keys: string[]) => {
  if (keys.length > 0) {
    const selectedKey = keys[0]
    selectedKeys.value = keys
    activeHeadingId.value = selectedKey
    
    // 滚动到对应的标题位置
    setTimeout(() => {
      const headingElement = document.querySelector(`.docs-content [data-heading-id="${selectedKey}"]`)
      if (headingElement) {
        const docContent = document.querySelector('.docs-content')
        if (docContent) {
          // 获取标题元素相对于滚动容器的位置
          const docContentRect = docContent.getBoundingClientRect()
          const headingRect = headingElement.getBoundingClientRect()
          const relativeTop = headingRect.top - docContentRect.top + docContent.scrollTop
          
          docContent.scrollTo({
            top: relativeTop - 100,
            behavior: 'smooth'
          })
        }
      }
    }, 100)
  }
}

// 处理树节点展开
const handleTreeExpand = (keys: string[]) => {
  expandedKeys.value = keys
}

// 获取节点属性，用于高亮当前激活的标题
const getNodeProps = ({ option }: { option: TreeNode }) => {
  return {
    class: {
      'active-heading': option.key === activeHeadingId.value
    }
  }
}

// 处理文档选择（保留兼容性）
const handleDocSelect = (docPath: string) => {
  selectedDoc.value = docPath
  selectedKeys.value = [docPath]
  // 更新URL查询参数
  router.push({ path: '/docs', query: { doc: docPath } })
  loadDocContent(docPath)
}

// 监听选中的文档变化
watch(selectedDoc, (newDoc) => {
  if (newDoc) {
    loadDocContent(newDoc)
  }
})

// 监听文档内容变化，自动展开所有目录节点
watch(currentDocContent, () => {
  if (currentDocContent.value) {
    // 自动展开所有节点
    const getAllKeys = (nodes: TreeNode[]): string[] => {
      const keys: string[] = []
      nodes.forEach(node => {
        keys.push(node.key)
        if (node.children) {
          keys.push(...getAllKeys(node.children))
        }
      })
      return keys
    }
    
    setTimeout(() => {
      expandedKeys.value = getAllKeys(treeData.value)
      setupScrollListener()
    }, 100)
  }
})

// 设置滚动监听器
const setupScrollListener = () => {
  const docContent = document.querySelector('.docs-content')
  if (!docContent) return
  
  // 移除之前的监听器
  if (scrollCleanup) {
    scrollCleanup()
  }
  
  const handleScroll = () => {
    const headings = document.querySelectorAll('.docs-content [data-heading-id]')
    let currentHeading = ''
    
    // 找到当前可见的标题（从上到下第一个在视口上方或内部的标题）
    for (let i = headings.length - 1; i >= 0; i--) {
      const heading = headings[i]
      const rect = heading.getBoundingClientRect()
      const docRect = docContent.getBoundingClientRect()
      
      // 如果标题在文档容器的可视区域内或上方
      if (rect.top <= docRect.top + 150) {
        const headingId = heading.getAttribute('data-heading-id')
        if (headingId) {
          currentHeading = headingId
          break
        }
      }
    }
    
    if (currentHeading && currentHeading !== activeHeadingId.value) {
      activeHeadingId.value = currentHeading
      selectedKeys.value = [currentHeading]
    }
  }
  
  docContent.addEventListener('scroll', handleScroll, { passive: true })
  
  // 初始检查
  setTimeout(handleScroll, 100)
  
  // 返回清理函数
  scrollCleanup = () => {
    docContent.removeEventListener('scroll', handleScroll)
  }
}

// 组件挂载时加载文档列表
onMounted(async () => {
  await loadDocs()
  
  // 检查URL查询参数，如果有doc参数则自动选择对应文档
  const docParam = route.query.doc as string
  if (docParam && docs.value.some(doc => doc.path === docParam)) {
    selectedDoc.value = docParam
    await loadDocContent(docParam)
  }
})

// 监听路由查询参数变化
watch(() => route.query.doc, async (newDoc) => {
  if (newDoc && typeof newDoc === 'string' && docs.value.some(doc => doc.path === newDoc)) {
    selectedDoc.value = newDoc
    await loadDocContent(newDoc)
  }
})

// 组件卸载时清理
onUnmounted(() => {
  if (scrollCleanup) {
    scrollCleanup()
    scrollCleanup = null
  }
})
</script>

<style scoped>
.docs-view {
  min-height: 100vh;
  background: var(--n-color-base);
  display: flex;
  flex-direction: column;
}

.docs-nav {
  background: var(--n-color-base);
  border-bottom: 1px solid var(--n-border-color);
  padding: 16px 0;
  position: sticky;
  top: 0;
  z-index: 100;
  backdrop-filter: blur(8px);
}

.nav-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.nav-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.nav-actions .n-button.active {
  color: var(--n-primary-color);
}

.docs-layout {
  flex: 1;
  display: flex;
  min-height: 0;
}

.docs-sidebar {
  width: 280px;
  background: var(--n-color-base);
  border-right: 1px solid var(--n-border-color);
  display: flex;
  flex-direction: column;
  transition: all 0.3s ease;
  overflow: hidden;
}

.docs-sidebar.collapsed {
  width: 0;
  border-right: none;
}

.sidebar-header {
  padding: 20px;
  border-bottom: 1px solid var(--n-border-color);
  background: var(--n-color-base-hover);
}

.sidebar-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--n-text-color-base);
}

.sidebar-content {
  flex: 1;
  padding: 16px;
  overflow-y: auto;
}

.sidebar-loading,
.sidebar-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 40px 20px;
  color: var(--n-text-color-depth-3);
  font-size: 14px;
}

.docs-content {
  flex: 1;
  overflow-y: auto;
  min-width: 0;
  max-height: calc(100vh - 120px);
}

.loading-container,
.error-container,
.welcome-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 60vh;
  padding: 40px 24px;
}

.doc-container {
  margin: 0 auto;
  padding: 40px 24px;
}

.doc-article {
  width: 90%;
  background: var(--n-color-base);
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  overflow: hidden;
}

.doc-header {
  background: linear-gradient(135deg, var(--n-primary-color-hover), var(--n-primary-color));
  color: white;
  padding: 40px;
  text-align: center;
}

.doc-title {
  margin: 0;
  font-size: 32px;
  font-weight: 700;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.doc-content {
  padding: 48px;
  line-height: 1.8;
  color: var(--n-text-color-base);
  font-size: 16px;
  background: var(--n-color-base);
}

/* Markdown 样式 */
.doc-content :deep(h1),
.doc-content :deep(h2),
.doc-content :deep(h3),
.doc-content :deep(h4),
.doc-content :deep(h5),
.doc-content :deep(h6) {
  margin: 32px 0 20px;
  font-weight: 600;
  color: var(--n-text-color-base);
  line-height: 1.3;
}

.doc-content :deep(h1) {
  font-size: 28px;
  border-bottom: 2px solid var(--n-primary-color);
  padding-bottom: 12px;
  margin-top: 0;
}

.doc-content :deep(h2) {
  font-size: 24px;
  border-bottom: 1px solid var(--n-border-color);
  padding-bottom: 8px;
}

.doc-content :deep(h3) {
  font-size: 20px;
  color: var(--n-primary-color);
}

.doc-content :deep(h4) {
  font-size: 18px;
}

.doc-content :deep(p) {
  margin: 20px 0;
  text-align: justify;
}

.doc-content :deep(ul),
.doc-content :deep(ol) {
  margin: 20px 0;
  padding-left: 28px;
}

.doc-content :deep(li) {
  margin: 10px 0;
  line-height: 1.6;
}

.doc-content :deep(li strong) {
  color: var(--n-primary-color);
}

/* 内联代码样式 */
.doc-content :deep(code) {
  background: linear-gradient(135deg, #f8f9fa, #e9ecef);
  color: #d63384;
  padding: 3px 8px;
  border-radius: 6px;
  font-family: 'JetBrains Mono', 'Fira Code', 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 14px;
  font-weight: 500;
  border: 1px solid rgba(0, 0, 0, 0.08);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

/* 代码块样式 */
.doc-content :deep(pre) {
  background: linear-gradient(135deg, #1e1e1e, #2d2d2d);
  color: #f8f8f2;
  padding: 24px;
  border-radius: 12px;
  overflow-x: auto;
  margin: 24px 40px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  position: relative;
}

.doc-content :deep(pre code) {
  background: none;
  color: inherit;
  padding: 0;
  border: none;
  box-shadow: none;
  font-size: 14px;
  line-height: 1.6;
}

/* 代码块语言标识 */
.doc-content :deep(pre[class*="language-"]:before) {
  content: attr(class);
  position: absolute;
  top: 8px;
  right: 12px;
  background: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.7);
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  text-transform: uppercase;
  font-weight: 500;
}

/* HTTP 方法样式 */
.doc-content :deep(pre code:contains("GET")) {
  color: #28a745;
}

.doc-content :deep(pre code:contains("POST")) {
  color: #007bff;
}

.doc-content :deep(pre code:contains("PUT")) {
  color: #ffc107;
}

.doc-content :deep(pre code:contains("DELETE")) {
  color: #dc3545;
}

.doc-content :deep(blockquote) {
  border-left: 4px solid var(--n-primary-color);
  background: var(--n-color-base-hover);
  padding: 16px 20px;
  margin: 24px 0;
  border-radius: 0 8px 8px 0;
  color: var(--n-text-color-depth-2);
  font-style: italic;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.doc-content :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 24px 0;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.doc-content :deep(th),
.doc-content :deep(td) {
  border: 1px solid var(--n-border-color);
  padding: 12px 16px;
  text-align: left;
}

.doc-content :deep(th) {
  background: linear-gradient(135deg, var(--n-primary-color-hover), var(--n-primary-color));
  color: white;
  font-weight: 600;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.doc-content :deep(tr:nth-child(even)) {
  background: var(--n-color-base-hover);
}

.doc-content :deep(a) {
  color: var(--n-primary-color);
  text-decoration: none;
  font-weight: 500;
  transition: all 0.2s ease;
}

.doc-content :deep(a:hover) {
  text-decoration: underline;
  color: var(--n-primary-color-hover);
}

/* 激活的标题样式 */
.docs-sidebar :deep(.n-tree-node.active-heading .n-tree-node-content) {
  background: var(--n-primary-color-hover) !important;
  color: white !important;
  font-weight: 600;
}

.docs-sidebar :deep(.n-tree-node.active-heading .n-tree-node-content::before) {
  background: var(--n-primary-color) !important;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .doc-content {
    padding: 24px;
    font-size: 15px;
  }
  
  .doc-content :deep(pre) {
    padding: 16px;
    margin: 16px -8px;
    border-radius: 8px;
  }
  
  .nav-container {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }
  
  .nav-actions {
    flex-direction: column;
    width: 100%;
  }
  
  .nav-actions .n-select {
    width: 100% !important;
    margin-right: 0 !important;
    margin-bottom: 12px;
  }
  
  .docs-sidebar {
    position: fixed;
    top: 120px;
    left: 0;
    height: calc(100vh - 120px);
    z-index: 200;
    box-shadow: 2px 0 8px rgba(0, 0, 0, 0.1);
  }
  
  .docs-sidebar.collapsed {
    transform: translateX(-100%);
    width: 280px;
  }
  
  .docs-content {
    width: 100%;
  }
}
</style>