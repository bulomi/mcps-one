/**
 * API监控面板组件
 * 提供实时API性能监控和调试功能
 */

import React, { useState, useEffect, useCallback } from 'react';
import { apiMonitor, ApiPerformanceStats, performanceAnalyzer } from '../api/monitor';

interface ApiMonitorPanelProps {
  isVisible: boolean;
  onClose: () => void;
}

const ApiMonitorPanel: React.FC<ApiMonitorPanelProps> = ({ isVisible, onClose }) => {
  const [stats, setStats] = useState<ApiPerformanceStats | null>(null);
  const [realTimeMetrics, setRealTimeMetrics] = useState({
    activeRequests: 0,
    requestsPerMinute: 0,
    averageResponseTime: 0,
    errorRate: 0,
  });
  const [selectedTimeRange, setSelectedTimeRange] = useState(60000); // 1分钟
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [showDetails, setShowDetails] = useState(false);

  const refreshStats = useCallback(() => {
    const newStats = apiMonitor.getPerformanceStats(selectedTimeRange);
    const newRealTimeMetrics = apiMonitor.getRealTimeMetrics();
    setStats(newStats);
    setRealTimeMetrics(newRealTimeMetrics);
  }, [selectedTimeRange]);

  useEffect(() => {
    if (!isVisible) return;

    refreshStats();

    if (autoRefresh) {
      const interval = setInterval(refreshStats, 1000);
      return () => clearInterval(interval);
    }
  }, [isVisible, autoRefresh, refreshStats]);

  const handleClearMetrics = () => {
    apiMonitor.clearMetrics();
    refreshStats();
  };

  const handleExportMetrics = () => {
    const metrics = apiMonitor.exportMetrics();
    const blob = new Blob([JSON.stringify(metrics, null, 2)], {
      type: 'application/json',
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `api-metrics-${new Date().toISOString()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleGenerateReport = () => {
    const report = performanceAnalyzer.generateReport();
    const blob = new Blob([report], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `api-performance-report-${new Date().toISOString()}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const getStatusColor = (value: number, thresholds: { good: number; warning: number }) => {
    if (value <= thresholds.good) return 'text-green-600';
    if (value <= thresholds.warning) return 'text-yellow-600';
    return 'text-red-600';
  };

  if (!isVisible) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center">
      <div className="bg-white rounded-lg shadow-xl w-11/12 h-5/6 max-w-6xl overflow-hidden">
        {/* 头部 */}
        <div className="bg-gray-800 text-white p-4 flex justify-between items-center">
          <h2 className="text-xl font-bold">API 监控面板</h2>
          <div className="flex items-center space-x-4">
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
                className="rounded"
              />
              <span className="text-sm">自动刷新</span>
            </label>
            <select
              value={selectedTimeRange}
              onChange={(e) => setSelectedTimeRange(Number(e.target.value))}
              className="bg-gray-700 text-white rounded px-2 py-1 text-sm"
            >
              <option value={60000}>最近1分钟</option>
              <option value={300000}>最近5分钟</option>
              <option value={900000}>最近15分钟</option>
              <option value={3600000}>最近1小时</option>
              <option value={0}>全部时间</option>
            </select>
            <button
              onClick={onClose}
              className="text-gray-300 hover:text-white"
            >
              ✕
            </button>
          </div>
        </div>

        <div className="p-6 h-full overflow-y-auto">
          {/* 实时指标 */}
          <div className="grid grid-cols-4 gap-4 mb-6">
            <div className="bg-blue-50 p-4 rounded-lg">
              <h3 className="text-sm font-medium text-gray-600">每分钟请求数</h3>
              <p className="text-2xl font-bold text-blue-600">
                {realTimeMetrics.requestsPerMinute}
              </p>
            </div>
            <div className="bg-green-50 p-4 rounded-lg">
              <h3 className="text-sm font-medium text-gray-600">平均响应时间</h3>
              <p className={`text-2xl font-bold ${
                getStatusColor(realTimeMetrics.averageResponseTime, { good: 500, warning: 1000 })
              }`}>
                {realTimeMetrics.averageResponseTime.toFixed(0)}ms
              </p>
            </div>
            <div className="bg-yellow-50 p-4 rounded-lg">
              <h3 className="text-sm font-medium text-gray-600">错误率</h3>
              <p className={`text-2xl font-bold ${
                getStatusColor(realTimeMetrics.errorRate, { good: 1, warning: 5 })
              }`}>
                {realTimeMetrics.errorRate.toFixed(1)}%
              </p>
            </div>
            <div className="bg-purple-50 p-4 rounded-lg">
              <h3 className="text-sm font-medium text-gray-600">活跃请求</h3>
              <p className="text-2xl font-bold text-purple-600">
                {realTimeMetrics.activeRequests}
              </p>
            </div>
          </div>

          {/* 操作按钮 */}
          <div className="flex space-x-4 mb-6">
            <button
              onClick={refreshStats}
              className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
            >
              刷新数据
            </button>
            <button
              onClick={handleClearMetrics}
              className="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600"
            >
              清除数据
            </button>
            <button
              onClick={handleExportMetrics}
              className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600"
            >
              导出数据
            </button>
            <button
              onClick={handleGenerateReport}
              className="bg-purple-500 text-white px-4 py-2 rounded hover:bg-purple-600"
            >
              生成报告
            </button>
            <button
              onClick={() => setShowDetails(!showDetails)}
              className="bg-gray-500 text-white px-4 py-2 rounded hover:bg-gray-600"
            >
              {showDetails ? '隐藏详情' : '显示详情'}
            </button>
          </div>

          {stats && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* 总体统计 */}
              <div className="bg-gray-50 p-4 rounded-lg">
                <h3 className="text-lg font-semibold mb-4">总体统计</h3>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span>总请求数:</span>
                    <span className="font-medium">{stats.totalCalls}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>成功率:</span>
                    <span className={`font-medium ${
                      getStatusColor(100 - stats.successRate, { good: 1, warning: 5 })
                    }`}>
                      {stats.successRate.toFixed(2)}%
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>平均响应时间:</span>
                    <span className={`font-medium ${
                      getStatusColor(stats.averageResponseTime, { good: 500, warning: 1000 })
                    }`}>
                      {stats.averageResponseTime.toFixed(2)}ms
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>错误率:</span>
                    <span className={`font-medium ${
                      getStatusColor(stats.errorRate, { good: 1, warning: 5 })
                    }`}>
                      {stats.errorRate.toFixed(2)}%
                    </span>
                  </div>
                </div>
              </div>

              {/* 最慢端点 */}
              <div className="bg-gray-50 p-4 rounded-lg">
                <h3 className="text-lg font-semibold mb-4">最慢端点</h3>
                <div className="space-y-2 max-h-48 overflow-y-auto">
                  {stats.slowestEndpoints.slice(0, 5).map((endpoint, index) => (
                    <div key={index} className="flex justify-between items-center text-sm">
                      <span className="truncate flex-1 mr-2" title={endpoint.url}>
                        {endpoint.url}
                      </span>
                      <span className={`font-medium ${
                        getStatusColor(endpoint.averageTime, { good: 500, warning: 1000 })
                      }`}>
                        {endpoint.averageTime.toFixed(0)}ms
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* 错误统计 */}
              <div className="bg-gray-50 p-4 rounded-lg">
                <h3 className="text-lg font-semibold mb-4">错误统计</h3>
                <div className="space-y-2">
                  {Object.entries(stats.errorsByType).map(([type, count]) => (
                    <div key={type} className="flex justify-between">
                      <span className="text-sm">{type}:</span>
                      <span className="font-medium text-red-600">{count}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* 最近错误 */}
              <div className="bg-gray-50 p-4 rounded-lg">
                <h3 className="text-lg font-semibold mb-4">最近错误</h3>
                <div className="space-y-2 max-h-48 overflow-y-auto">
                  {stats.recentErrors.slice(0, 5).map((error, index) => (
                    <div key={index} className="text-sm">
                      <div className="font-medium text-red-600 truncate" title={error.url}>
                        {error.url}
                      </div>
                      <div className="text-gray-600 truncate" title={error.error}>
                        {error.error}
                      </div>
                      <div className="text-xs text-gray-500">
                        {new Date(error.timestamp).toLocaleTimeString()}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* 详细信息 */}
          {showDetails && stats && (
            <div className="mt-6 bg-gray-50 p-4 rounded-lg">
              <h3 className="text-lg font-semibold mb-4">详细信息</h3>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* 所有端点 */}
                <div>
                  <h4 className="font-medium mb-2">所有端点性能</h4>
                  <div className="max-h-64 overflow-y-auto">
                    {stats.slowestEndpoints.map((endpoint, index) => (
                      <div key={index} className="text-sm py-1 border-b border-gray-200">
                        <div className="flex justify-between">
                          <span className="truncate flex-1 mr-2" title={endpoint.url}>
                            {endpoint.url}
                          </span>
                          <span className="font-medium">
                            {endpoint.averageTime.toFixed(0)}ms
                          </span>
                        </div>
                        <div className="text-xs text-gray-500">
                          {endpoint.callCount} 次调用
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* 所有错误 */}
                <div>
                  <h4 className="font-medium mb-2">所有错误记录</h4>
                  <div className="max-h-64 overflow-y-auto">
                    {stats.recentErrors.map((error, index) => (
                      <div key={index} className="text-sm py-1 border-b border-gray-200">
                        <div className="font-medium text-red-600 truncate" title={error.url}>
                          {error.url}
                        </div>
                        <div className="text-gray-600 truncate" title={error.error}>
                          {error.error}
                        </div>
                        <div className="text-xs text-gray-500">
                          {new Date(error.timestamp).toLocaleString()}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ApiMonitorPanel;