/**
 * 开发工具组件
 * 提供开发环境下的调试和监控功能
 */

import React, { useState, useEffect } from 'react';
import ApiMonitorPanel from './ApiMonitorPanel';
import { apiMonitor } from '../api/monitor';

interface DevToolsProps {
  enabled?: boolean;
}

const DevTools: React.FC<DevToolsProps> = ({ enabled = process.env.NODE_ENV === 'development' }) => {
  const [isVisible, setIsVisible] = useState(false);
  const [showMonitorPanel, setShowMonitorPanel] = useState(false);
  const [realTimeStats, setRealTimeStats] = useState({
    requestsPerMinute: 0,
    averageResponseTime: 0,
    errorRate: 0,
  });
  const [keySequence, setKeySequence] = useState<string[]>([]);

  // 快捷键序列：Ctrl+Shift+D
  useEffect(() => {
    if (!enabled) return;

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.ctrlKey && event.shiftKey && event.key === 'D') {
        event.preventDefault();
        setIsVisible(prev => !prev);
      }

      // 隐藏快捷键：Escape
      if (event.key === 'Escape') {
        setIsVisible(false);
        setShowMonitorPanel(false);
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [enabled]);

  // 实时更新统计信息
  useEffect(() => {
    if (!enabled || !isVisible) return;

    const updateStats = () => {
      const metrics = apiMonitor.getRealTimeMetrics();
      setRealTimeStats(metrics);
    };

    updateStats();
    const interval = setInterval(updateStats, 1000);
    return () => clearInterval(interval);
  }, [enabled, isVisible]);

  const handleClearCache = () => {
    // 清除所有缓存
    if ('caches' in window) {
      caches.keys().then(names => {
        names.forEach(name => {
          caches.delete(name);
        });
      });
    }
    
    // 清除localStorage中的缓存
    Object.keys(localStorage).forEach(key => {
      if (key.startsWith('api_cache_')) {
        localStorage.removeItem(key);
      }
    });
    
    alert('缓存已清除');
  };

  const handleReloadApp = () => {
    window.location.reload();
  };

  const handleToggleMonitoring = () => {
    const isEnabled = apiMonitor.config?.enabled ?? true;
    apiMonitor.setEnabled(!isEnabled);
    alert(`API监控已${!isEnabled ? '启用' : '禁用'}`);
  };

  const getStatusIndicator = () => {
    if (realTimeStats.errorRate > 5) return '🔴';
    if (realTimeStats.averageResponseTime > 1000) return '🟡';
    return '🟢';
  };

  if (!enabled) return null;

  return (
    <>
      {/* 浮动工具栏 */}
      {isVisible && (
        <div className="fixed bottom-4 right-4 z-50">
          <div className="bg-gray-800 text-white rounded-lg shadow-xl p-4 min-w-80">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold">开发工具</h3>
              <button
                onClick={() => setIsVisible(false)}
                className="text-gray-300 hover:text-white"
              >
                ✕
              </button>
            </div>

            {/* 实时状态 */}
            <div className="mb-4 p-3 bg-gray-700 rounded">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium">API状态</span>
                <span className="text-lg">{getStatusIndicator()}</span>
              </div>
              <div className="grid grid-cols-3 gap-2 text-xs">
                <div>
                  <div className="text-gray-300">请求/分钟</div>
                  <div className="font-medium">{realTimeStats.requestsPerMinute}</div>
                </div>
                <div>
                  <div className="text-gray-300">平均响应</div>
                  <div className="font-medium">{realTimeStats.averageResponseTime.toFixed(0)}ms</div>
                </div>
                <div>
                  <div className="text-gray-300">错误率</div>
                  <div className="font-medium">{realTimeStats.errorRate.toFixed(1)}%</div>
                </div>
              </div>
            </div>

            {/* 工具按钮 */}
            <div className="space-y-2">
              <button
                onClick={() => setShowMonitorPanel(true)}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white py-2 px-4 rounded text-sm"
              >
                📊 API监控面板
              </button>
              
              <button
                onClick={handleToggleMonitoring}
                className="w-full bg-purple-600 hover:bg-purple-700 text-white py-2 px-4 rounded text-sm"
              >
                🔍 切换API监控
              </button>
              
              <button
                onClick={handleClearCache}
                className="w-full bg-yellow-600 hover:bg-yellow-700 text-white py-2 px-4 rounded text-sm"
              >
                🗑️ 清除缓存
              </button>
              
              <button
                onClick={handleReloadApp}
                className="w-full bg-green-600 hover:bg-green-700 text-white py-2 px-4 rounded text-sm"
              >
                🔄 重新加载
              </button>
              
              <div className="pt-2 border-t border-gray-600">
                <div className="text-xs text-gray-300 space-y-1">
                  <div>快捷键:</div>
                  <div>• Ctrl+Shift+D: 切换工具栏</div>
                  <div>• Escape: 关闭面板</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 状态指示器（当工具栏隐藏时显示） */}
      {!isVisible && (
        <div 
          className="fixed bottom-4 right-4 z-40 cursor-pointer"
          onClick={() => setIsVisible(true)}
          title="点击打开开发工具 (Ctrl+Shift+D)"
        >
          <div className="bg-gray-800 text-white rounded-full w-12 h-12 flex items-center justify-center shadow-lg hover:bg-gray-700 transition-colors">
            <span className="text-lg">{getStatusIndicator()}</span>
          </div>
        </div>
      )}

      {/* API监控面板 */}
      <ApiMonitorPanel
        isVisible={showMonitorPanel}
        onClose={() => setShowMonitorPanel(false)}
      />
    </>
  );
};

export default DevTools;