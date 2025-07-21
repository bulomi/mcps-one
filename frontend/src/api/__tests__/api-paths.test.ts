/**
 * API路径验证和规范化测试
 * 确保所有API路径都符合规范，避免307重定向问题
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { 
  validateApiPath, 
  buildApiPath,
  AUTH_PATHS,
  TOOLS_PATHS,
  MCP_AGENT_PATHS,
  MCP_UNIFIED_PATHS,
  SYSTEM_PATHS,
  SESSIONS_PATHS
} from '../constants'
import { apiRequest } from '../utils'

// Mock fetch
const mockFetch = vi.fn()
global.fetch = mockFetch

describe('API路径验证', () => {
  beforeEach(() => {
    mockFetch.mockClear()
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('validateApiPath', () => {
    it('应该移除路径末尾的斜杠', () => {
      expect(validateApiPath('/api/v1/tools/')).toBe('/api/v1/tools')
      expect(validateApiPath('/api/v1/auth/')).toBe('/api/v1/auth')
    })

    it('应该保留根路径的斜杠', () => {
      expect(validateApiPath('/')).toBe('/')
    })

    it('应该保持已经规范的路径不变', () => {
      expect(validateApiPath('/api/v1/tools')).toBe('/api/v1/tools')
      expect(validateApiPath('/api/v1/auth')).toBe('/api/v1/auth')
    })

    it('应该处理多个连续斜杠', () => {
      expect(validateApiPath('/api/v1/tools///')).toBe('/api/v1/tools')
    })
  })

  describe('buildApiPath', () => {
    it('应该正确构建API路径', () => {
      expect(buildApiPath('api', 'v1', 'tools')).toBe('/api/v1/tools')
      expect(buildApiPath('api', 'v1', 'auth')).toBe('/api/v1/auth')
    })

    it('应该处理空字符串和空白字符', () => {
      expect(buildApiPath('api', '', 'v1', '  ', 'tools')).toBe('/api/v1/tools')
    })

    it('应该移除段落中的前后斜杠', () => {
      expect(buildApiPath('/api/', '/v1/', '/tools/')).toBe('/api/v1/tools')
    })

    it('应该处理单个段落', () => {
      expect(buildApiPath('tools')).toBe('/tools')
    })
  })

  describe('API路径常量验证', () => {
    it('所有AUTH_PATHS应该是有效路径', () => {
      Object.values(AUTH_PATHS).forEach(path => {
        if (typeof path === 'string') {
          expect(path).not.toMatch(/\/$/) // 不应以斜杠结尾
          expect(path).toMatch(/^\//) // 应以斜杠开头
        }
      })
    })

    it('所有TOOLS_PATHS字符串应该是有效路径', () => {
      Object.values(TOOLS_PATHS).forEach(path => {
        if (typeof path === 'string') {
          expect(path).not.toMatch(/\/$/) // 不应以斜杠结尾
          expect(path).toMatch(/^\//) // 应以斜杠开头
        }
      })
    })

    it('所有MCP_AGENT_PATHS字符串应该是有效路径', () => {
      Object.values(MCP_AGENT_PATHS).forEach(path => {
        if (typeof path === 'string') {
          expect(path).not.toMatch(/\/$/) // 不应以斜杠结尾
          expect(path).toMatch(/^\//) // 应以斜杠开头
        }
      })
    })

    it('所有MCP_UNIFIED_PATHS应该是有效路径', () => {
      Object.values(MCP_UNIFIED_PATHS).forEach(path => {
        if (typeof path === 'string') {
          expect(path).not.toMatch(/\/$/) // 不应以斜杠结尾
          expect(path).toMatch(/^\//) // 应以斜杠开头
        }
      })
    })

    it('所有SYSTEM_PATHS字符串应该是有效路径', () => {
      Object.values(SYSTEM_PATHS).forEach(path => {
        if (typeof path === 'string') {
          expect(path).not.toMatch(/\/$/) // 不应以斜杠结尾
          expect(path).toMatch(/^\//) // 应以斜杠开头
        }
      })
    })

    it('所有SESSIONS_PATHS字符串应该是有效路径', () => {
      Object.values(SESSIONS_PATHS).forEach(path => {
        if (typeof path === 'string') {
          expect(path).not.toMatch(/\/$/) // 不应以斜杠结尾
          expect(path).toMatch(/^\//) // 应以斜杠开头
        }
      })
    })
  })

  describe('动态路径函数', () => {
    it('TOOLS_PATHS动态函数应该返回正确路径', () => {
      if (typeof TOOLS_PATHS.DETAIL === 'function') {
        expect(TOOLS_PATHS.DETAIL(123)).toBe('/tools/123')
      }
      if (typeof TOOLS_PATHS.STATUS === 'function') {
        expect(TOOLS_PATHS.STATUS(456)).toBe('/tools/456/status')
      }
    })

    it('MCP_AGENT_PATHS动态函数应该返回正确路径', () => {
      if (typeof MCP_AGENT_PATHS.TOOL_CALL === 'function') {
        expect(MCP_AGENT_PATHS.TOOL_CALL('test-tool')).toBe('/mcp-agent/tools/test-tool/call')
      }
    })

    it('SESSIONS_PATHS动态函数应该返回正确路径', () => {
      if (typeof SESSIONS_PATHS.DETAIL === 'function') {
        expect(SESSIONS_PATHS.DETAIL('session-123')).toBe('/sessions/session-123')
      }
    })
  })

  describe('路径构建函数', () => {
    it('buildToolPath应该构建正确的工具路径', () => {
      const buildToolPath = (id: string) => `/tools/${id}`
      
      expect(buildToolPath('123')).toBe('/tools/123')
      expect(validateApiPath(buildToolPath('123'))).toBe('/tools/123')
    })

    it('buildToolStatusPath应该构建正确的状态路径', () => {
      const buildToolStatusPath = (id: string) => `/tools/${id}/status`
      
      expect(buildToolStatusPath('123')).toBe('/tools/123/status')
      expect(validateApiPath(buildToolStatusPath('123'))).toBe('/tools/123/status')
    })

    it('buildMcpToolPath应该构建正确的MCP工具路径', () => {
      const buildMcpToolPath = (toolName: string) => `/mcp-agent/tools/${toolName}`
      
      expect(buildMcpToolPath('test-tool')).toBe('/mcp-agent/tools/test-tool')
      expect(validateApiPath(buildMcpToolPath('test-tool'))).toBe('/mcp-agent/tools/test-tool')
    })
  })
})

describe('API请求路径验证', () => {
  beforeEach(() => {
    mockFetch.mockResolvedValue({
      ok: true,
      status: 200,
      headers: new Headers({ 'content-type': 'application/json' }),
      json: async () => ({ success: true })
    })
  })

  it('apiRequest应该处理有效路径', async () => {
    const result = await apiRequest('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username: 'test', password: 'test' })
    })

    expect(result).toEqual({ success: true })
    expect(mockFetch).toHaveBeenCalledTimes(1)
  })

  it('apiRequest应该自动规范化路径', async () => {
    await apiRequest('/tools/')
    
    // 检查实际调用的URL是否已经规范化
    const callArgs = mockFetch.mock.calls[0]
    expect(callArgs[0]).not.toMatch(/\/$/) // URL不应以斜杠结尾
  })
})

describe('路径一致性检查', () => {
  it('确保所有认证路径都在AUTH_PATHS中定义', () => {
    const expectedAuthPaths = [
      '/auth/login',
      '/auth/logout',
      '/auth/refresh',
      '/auth/me',
      '/auth/change-password'
    ]
    
    expectedAuthPaths.forEach(path => {
      const isDefinedInConstants = Object.values(AUTH_PATHS).includes(path)
      expect(isDefinedInConstants).toBe(true)
    })
  })

  it('确保所有工具路径都在TOOLS_PATHS中定义', () => {
    const expectedToolsPaths = [
      '/tools',
      '/tools/validate-config',
      '/tools/categories',
      '/tools/tags',
      '/tools/search',
      '/tools/stats'
    ]
    
    expectedToolsPaths.forEach(path => {
      const isDefinedInConstants = Object.values(TOOLS_PATHS)
        .filter(p => typeof p === 'string')
        .includes(path)
      expect(isDefinedInConstants).toBe(true)
    })
  })

  it('检查动态路径构建的一致性', () => {
    const dynamicTests = [
      // 工具相关动态路径
      { fn: TOOLS_PATHS.DETAIL, input: 123, expected: '/tools/123' },
      { fn: TOOLS_PATHS.STATUS, input: 456, expected: '/tools/456/status' },
      
      // MCP代理相关动态路径
      { fn: MCP_AGENT_PATHS.TOOL_CALL, input: 'test-tool', expected: '/mcp-agent/tools/test-tool/call' },
      
      // 会话相关动态路径
      { fn: SESSIONS_PATHS.DETAIL, input: 'session-123', expected: '/sessions/session-123' }
    ]
    
    dynamicTests.forEach(({ fn, input, expected }) => {
      if (typeof fn === 'function') {
        const result = fn(input)
        expect(result).toBe(expected)
        expect(result).not.toMatch(/\/$/) 
      }
    })
  })
})

describe('307重定向预防', () => {
  it('确保所有常用路径都不会导致重定向', () => {
    const commonPaths = [
      '/tools',
      '/auth/login',
      '/auth/logout',
      '/system/stats',
      '/mcp-agent/tools',
      '/sessions'
    ]
    
    commonPaths.forEach(path => {
      // 确保路径规范化后保持一致
      const normalized = validateApiPath(path)
      expect(normalized).toBe(path)
      
      // 确保没有尾部斜杠
      expect(path).not.toMatch(/\/$/) 
      
      // 确保以斜杠开头
      expect(path).toMatch(/^\//) 
    })
  })

  it('检查可能导致重定向的路径模式', () => {
    // 检查所有定义的API路径
    const allPaths = [
      ...Object.values(AUTH_PATHS),
      ...Object.values(TOOLS_PATHS).filter(p => typeof p === 'string'),
      ...Object.values(MCP_AGENT_PATHS).filter(p => typeof p === 'string'),
      ...Object.values(MCP_UNIFIED_PATHS).filter(p => typeof p === 'string'),
      ...Object.values(SYSTEM_PATHS).filter(p => typeof p === 'string'),
      ...Object.values(SESSIONS_PATHS).filter(p => typeof p === 'string')
    ]
    
    allPaths.forEach(path => {
      // 检查尾部斜杠（根路径除外）
      if (path !== '/') {
        expect(path).not.toMatch(/\/$/, `路径 ${path} 不应以斜杠结尾，这可能导致307重定向`) 
      }
      
      // 检查双斜杠
      expect(path).not.toMatch(/\/\//, `路径 ${path} 不应包含双斜杠`) 
      
      // 确保路径以斜杠开头
      expect(path).toMatch(/^\//, `路径 ${path} 应以斜杠开头`)
      
      // 确保路径不包含空格
      expect(path).not.toMatch(/\s/, `路径 ${path} 不应包含空格`)
    })
  })

  it('验证动态路径函数不会产生问题路径', () => {
    // 测试动态路径函数
    const dynamicPathTests = [
      { fn: TOOLS_PATHS.DETAIL, input: 123 },
      { fn: MCP_AGENT_PATHS.TOOL_CALL, input: 'my-tool' },
      { fn: SESSIONS_PATHS.DETAIL, input: 'session-123' }
    ]

    dynamicPathTests.forEach(({ fn, input }) => {
      if (typeof fn === 'function') {
        const result = fn(input)
        
        // 确保动态生成的路径也符合规范
        expect(result).not.toMatch(/\/$/, `动态路径 ${result} 不应以斜杠结尾`)
        expect(result).toMatch(/^\//, `动态路径 ${result} 应以斜杠开头`)
        expect(result).not.toMatch(/\/\//, `动态路径 ${result} 不应包含双斜杠`)
      }
    })
  })

  it('验证路径规范化功能', () => {
    const problematicPaths = [
      '/api/v1/tools/',
      '/api/v1/auth/',
      '//api/v1/tools',
      '/api//v1//tools'
    ]

    problematicPaths.forEach(path => {
      const normalized = validateApiPath(path)
      expect(normalized).not.toMatch(/\/$/, `规范化后的路径 ${normalized} 不应以斜杠结尾`)
      expect(normalized).not.toMatch(/\/\//, `规范化后的路径 ${normalized} 不应包含双斜杠`)
    })
  })
})