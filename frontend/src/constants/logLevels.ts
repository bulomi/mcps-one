// 日志级别常量定义
export const LOG_LEVELS = {
  DEBUG: 'DEBUG',
  INFO: 'INFO',
  WARNING: 'WARNING',
  ERROR: 'ERROR',
  CRITICAL: 'CRITICAL'
} as const;

// 日志级别类型（大写）
export type LogLevel = typeof LOG_LEVELS[keyof typeof LOG_LEVELS];

// 日志级别类型（小写，兼容system.ts）
export type LogLevelLowercase = 'debug' | 'info' | 'warning' | 'error' | 'critical';

// 日志级别选项（用于下拉选择）
export const logLevelOptions = [
  { label: 'DEBUG', value: 'DEBUG' },
  { label: 'INFO', value: 'INFO' },
  { label: 'WARNING', value: 'WARNING' },
  { label: 'ERROR', value: 'ERROR' },
  { label: 'CRITICAL', value: 'CRITICAL' }
];

// 日志级别颜色映射
export const logLevelColors = {
  DEBUG: '#909399',
  INFO: '#409EFF',
  WARNING: '#E6A23C',
  ERROR: '#F56C6C',
  CRITICAL: '#F56C6C'
} as const;