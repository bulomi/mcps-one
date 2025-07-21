/**
 * 日志管理相关API接口
 */
import api from './index'

/**
 * 获取日志统计信息
 * @param {Object} params - 查询参数
 * @param {string} params.period - 统计周期 (1h, 24h, 7d, 30d)
 * @param {string} params.log_type - 日志类型
 * @returns {Promise}
 */
export const getLogStats = (params = {}) => {
  return api.get('/logs/stats/', { params })
}

/**
 * 获取日志汇总统计
 * @returns {Promise}
 */
export const getLogSummary = () => {
  return api.get('/logs/stats/summary/')
}

/**
 * 获取系统日志
 * @param {Object} params - 查询参数
 * @param {number} params.page - 页码
 * @param {number} params.size - 每页大小
 * @param {string} params.level - 日志级别
 * @param {string} params.category - 日志分类
 * @param {string} params.start_time - 开始时间
 * @param {string} params.end_time - 结束时间
 * @param {string} params.search - 搜索关键词
 * @returns {Promise}
 */
export const getSystemLogs = (params = {}) => {
  return api.get('/logs/system/', { params })
}

/**
 * 获取系统日志详情
 * @param {number} logId - 日志ID
 * @returns {Promise}
 */
export const getSystemLog = (logId) => {
  return api.get(`/logs/system/${logId}/`)
}

/**
 * 获取操作日志
 * @param {Object} params - 查询参数
 * @param {number} params.page - 页码
 * @param {number} params.size - 每页大小
 * @param {string} params.action - 操作类型
 * @param {string} params.status - 操作状态
 * @param {string} params.resource_type - 资源类型
 * @param {string} params.resource_id - 资源ID
 * @param {string} params.user_id - 用户ID
 * @param {string} params.start_time - 开始时间
 * @param {string} params.end_time - 结束时间
 * @param {string} params.search - 搜索关键词
 * @returns {Promise}
 */
export const getOperationLogs = (params = {}) => {
  return api.get('/logs/operations/', { params })
}

/**
 * 获取操作日志详情
 * @param {number} logId - 日志ID
 * @returns {Promise}
 */
export const getOperationLog = (logId) => {
  return api.get(`/logs/operations/${logId}/`)
}

/**
 * 获取MCP协议日志
 * @param {Object} params - 查询参数
 * @param {number} params.page - 页码
 * @param {number} params.size - 每页大小
 * @param {number} params.tool_id - 工具ID
 * @param {string} params.direction - 消息方向
 * @param {string} params.method - 方法名
 * @param {string} params.start_time - 开始时间
 * @param {string} params.end_time - 结束时间
 * @param {string} params.search - 搜索关键词
 * @returns {Promise}
 */
export const getMcpLogs = (params = {}) => {
  return api.get('/logs/mcp/', { params })
}

/**
 * 获取MCP协议日志详情
 * @param {number} logId - 日志ID
 * @returns {Promise}
 */
export const getMcpLog = (logId) => {
  return api.get(`/logs/mcp/${logId}/`)
}

/**
 * 搜索日志
 * @param {Object} params - 搜索参数
 * @param {string} params.query - 搜索查询
 * @param {string} params.log_type - 日志类型
 * @param {number} params.page - 页码
 * @param {number} params.size - 每页大小
 * @param {string} params.start_time - 开始时间
 * @param {string} params.end_time - 结束时间
 * @returns {Promise}
 */
export const searchLogs = (params = {}) => {
  return api.get('/logs/search/', { params })
}

/**
 * 获取实时日志
 * @param {Object} params - 查询参数
 * @param {string} params.log_type - 日志类型
 * @param {string} params.level - 日志级别
 * @param {number} params.limit - 限制数量
 * @returns {Promise}
 */
export const getRealtimeLogs = (params = {}) => {
  return api.get('/logs/realtime/', { params })
}

/**
 * 清理日志
 * @param {Object} data - 清理参数
 * @param {number} data.retention_days - 保留天数
 * @param {Array} data.levels - 要清理的日志级别
 * @param {Array} data.categories - 要清理的日志分类
 * @param {Array} data.log_types - 要清理的日志类型
 * @returns {Promise}
 */
export const cleanupLogs = (data) => {
  return api.post('/logs/cleanup/', data)
}

/**
 * 导出日志
 * @param {Object} params - 导出参数
 * @param {string} params.log_type - 日志类型
 * @param {string} params.format - 导出格式 (csv, json)
 * @param {string} params.start_time - 开始时间
 * @param {string} params.end_time - 结束时间
 * @param {string} params.level - 日志级别
 * @param {string} params.category - 日志分类
 * @returns {Promise}
 */
export const exportLogs = (params = {}) => {
  return api.get('/logs/export/', { params, responseType: 'blob' })
}

/**
 * 获取所有日志（统一接口）
 * @param {Object} params - 查询参数
 * @param {number} params.page - 页码
 * @param {number} params.size - 每页大小
 * @param {string} params.logType - 日志类型 (system, operation, mcp)
 * @param {string} params.level - 日志级别
 * @param {string} params.source - 来源
 * @param {string} params.search - 搜索关键词
 * @param {Array} params.dateRange - 时间范围 [start, end]
 * @returns {Promise}
 */
export const getAllLogs = (params = {}) => {
  const { logType, dateRange, ...otherParams } = params
  
  // 处理时间范围
  if (dateRange && dateRange.length === 2) {
    otherParams.start_time = new Date(dateRange[0]).toISOString()
    otherParams.end_time = new Date(dateRange[1]).toISOString()
  }
  
  // 根据日志类型调用不同的API
  switch (logType) {
    case 'system':
      return getSystemLogs(otherParams)
    case 'operation':
      return getOperationLogs(otherParams)
    case 'mcp':
      return getMcpLogs(otherParams)
    default:
      // 默认获取系统日志
      return getSystemLogs(otherParams)
  }
}

export default {
  getLogStats,
  getLogSummary,
  getSystemLogs,
  getSystemLog,
  getOperationLogs,
  getOperationLog,
  getMcpLogs,
  getMcpLog,
  searchLogs,
  getRealtimeLogs,
  cleanupLogs,
  exportLogs,
  getAllLogs
}