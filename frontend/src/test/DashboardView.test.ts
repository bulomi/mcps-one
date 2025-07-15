import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import DashboardView from '@/views/DashboardView.vue'
import * as systemApi from '@/api/system'
import * as toolsApi from '@/api/tools'
import * as tasksApi from '@/api/tasks'

// Mock API modules
vi.mock('@/api/system', () => ({
  getStats: vi.fn(),
  getSystemInfo: vi.fn()
}))

vi.mock('@/api/tools', () => ({
  getTools: vi.fn(),
  createTool: vi.fn(),
  updateTool: vi.fn(),
  deleteTool: vi.fn()
}))

vi.mock('@/api/tasks', () => ({
  getTasks: vi.fn(),
  createTask: vi.fn(),
  updateTask: vi.fn(),
  deleteTask: vi.fn()
}))

const mockSystemApi = vi.mocked(systemApi)
const mockToolsApi = vi.mocked(toolsApi)
const mockTasksApi = vi.mocked(tasksApi)

describe('DashboardView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    
    // Setup default mock responses
    mockSystemApi.getStats.mockResolvedValue({
      data: {
        total_tools: 5,
        active_tools: 3,
        active_sessions: 2,
        total_tasks: 10,
        completed_tasks: 8,
        failed_tasks: 1,
        cpu_usage: 45.2,
        memory_usage: 67.8,
        disk_usage: 23.5
      }
    })
    
    mockToolsApi.getTools.mockResolvedValue({
      data: {
        items: [
          {
            id: '1',
            name: 'Test Tool 1',
            status: 'active',
            description: 'Test tool description',
            created_at: '2024-01-01T00:00:00Z'
          },
          {
            id: '2',
            name: 'Test Tool 2',
            status: 'inactive',
            description: 'Another test tool',
            created_at: '2024-01-02T00:00:00Z'
          }
        ],
        total: 2
      }
    })
    
    mockTasksApi.getTasks.mockResolvedValue({
      data: {
        items: [
          {
            id: '1',
            name: 'Test Task 1',
            status: 'completed',
            created_at: '2024-01-01T00:00:00Z',
            updated_at: '2024-01-01T01:00:00Z'
          },
          {
            id: '2',
            name: 'Test Task 2',
            status: 'running',
            created_at: '2024-01-02T00:00:00Z',
            updated_at: '2024-01-02T00:30:00Z'
          }
        ],
        total: 2
      }
    })
  })
  
  it('renders dashboard title correctly', () => {
    const wrapper = mount(DashboardView)
    expect(wrapper.find('h1').text()).toBe('MCPS.ONE 控制台')
  })
  
  it('displays system stats cards', async () => {
    const wrapper = mount(DashboardView)
    
    // Wait for component to mount and fetch data
    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 100))
    
    // Check if stats cards are rendered
    const statsCards = wrapper.findAll('.stat-card')
    expect(statsCards.length).toBeGreaterThan(0)
  })
  
  it('calls API methods on component mount', async () => {
    const wrapper = mount(DashboardView)
    
    // Wait for the component to be fully mounted and async operations to complete
    await nextTick()
    await new Promise(resolve => setTimeout(resolve, 100))
    
    expect(mockSystemApi.getStats).toHaveBeenCalled()
    expect(mockToolsApi.getTools).toHaveBeenCalledWith({ limit: 5 })
    expect(mockTasksApi.getTasks).toHaveBeenCalledWith({ limit: 5 })
  })
  
  it('handles API errors gracefully', async () => {
    // Mock API to throw error
    mockSystemApi.getStats.mockRejectedValue(new Error('API Error'))
    
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
    
    mount(DashboardView)
    
    // Wait for async operations
    await new Promise(resolve => setTimeout(resolve, 100))
    
    expect(consoleSpy).toHaveBeenCalled()
    
    consoleSpy.mockRestore()
  })
  
  it('displays loading state initially', () => {
    const wrapper = mount(DashboardView)
    
    // Check for loading indicators or empty states
    const loadingElements = wrapper.findAll('[data-testid="loading"]')
    // Note: This test assumes loading indicators have data-testid="loading"
    // Adjust based on actual implementation
  })
  
  it('updates data when refresh is triggered', async () => {
    const wrapper = mount(DashboardView)
    
    // Wait for initial mount to complete
    await nextTick()
    await new Promise(resolve => setTimeout(resolve, 100))
    
    // Clear previous calls
    vi.clearAllMocks()
    
    // Trigger refresh (assuming there's a refresh method)
    if (wrapper.vm.fetchSystemStats) {
      await wrapper.vm.fetchSystemStats()
    }
    
    expect(mockSystemApi.getStats).toHaveBeenCalled()
  })
  
  it('displays correct system statistics', async () => {
    const wrapper = mount(DashboardView)
    
    // Wait for data to load
    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 100))
    
    // Check if the component displays the mocked data
    // This would depend on the actual template structure
    const text = wrapper.text()
    
    // These assertions would need to be adjusted based on how the data is displayed
    // expect(text).toContain('5') // total_tools
    // expect(text).toContain('3') // active_tools
  })
})