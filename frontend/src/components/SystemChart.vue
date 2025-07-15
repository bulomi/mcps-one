<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js'
import { Line } from 'vue-chartjs'

// 注册Chart.js组件
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
)

// Props定义
interface DataPoint {
  time: Date
  value: number
}

interface Props {
  data: DataPoint[]
  type: 'cpu' | 'memory' | 'disk' | 'network'
  timeRange: string
}

const props = defineProps<Props>()

// 图表配置
const chartData = computed(() => {
  const labels = props.data.map(point => {
    const time = new Date(point.time)
    if (props.timeRange === '1h') {
      return time.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
    } else if (props.timeRange === '6h' || props.timeRange === '24h') {
      return time.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
    } else {
      return time.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' })
    }
  })
  
  const values = props.data.map(point => point.value)
  
  // 根据图表类型设置颜色
  const getChartColor = () => {
    switch (props.type) {
      case 'cpu':
        return {
          border: 'rgb(102, 126, 234)',
          background: 'rgba(102, 126, 234, 0.1)'
        }
      case 'memory':
        return {
          border: 'rgb(240, 147, 251)',
          background: 'rgba(240, 147, 251, 0.1)'
        }
      case 'disk':
        return {
          border: 'rgb(79, 172, 254)',
          background: 'rgba(79, 172, 254, 0.1)'
        }
      case 'network':
        return {
          border: 'rgb(67, 233, 123)',
          background: 'rgba(67, 233, 123, 0.1)'
        }
      default:
        return {
          border: 'rgb(102, 126, 234)',
          background: 'rgba(102, 126, 234, 0.1)'
        }
    }
  }
  
  const colors = getChartColor()
  
  return {
    labels,
    datasets: [
      {
        label: getChartLabel(),
        data: values,
        borderColor: colors.border,
        backgroundColor: colors.background,
        borderWidth: 2,
        fill: true,
        tension: 0.4,
        pointRadius: 3,
        pointHoverRadius: 6,
        pointBackgroundColor: colors.border,
        pointBorderColor: '#fff',
        pointBorderWidth: 2
      }
    ]
  }
})

// 获取图表标签
const getChartLabel = () => {
  switch (props.type) {
    case 'cpu': return 'CPU使用率 (%)'
    case 'memory': return '内存使用率 (%)'
    case 'disk': return '磁盘使用率 (%)'
    case 'network': return '网络流量 (MB/s)'
    default: return '使用率 (%)'
  }
}

// 图表选项
const chartOptions = computed(() => {
  const isPercentage = props.type !== 'network'
  
  return {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      intersect: false,
      mode: 'index' as const
    },
    plugins: {
      legend: {
        display: true,
        position: 'top' as const,
        labels: {
          usePointStyle: true,
          padding: 20,
          font: {
            size: 12
          }
        }
      },
      tooltip: {
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        titleColor: '#fff',
        bodyColor: '#fff',
        borderColor: 'rgba(255, 255, 255, 0.1)',
        borderWidth: 1,
        cornerRadius: 8,
        displayColors: true,
        callbacks: {
          label: function(context: any) {
            const value = context.parsed.y
            if (props.type === 'network') {
              return `${context.dataset.label}: ${value.toFixed(2)} MB/s`
            } else {
              return `${context.dataset.label}: ${value.toFixed(1)}%`
            }
          }
        }
      }
    },
    scales: {
      x: {
        display: true,
        title: {
          display: true,
          text: '时间',
          font: {
            size: 12,
            weight: 'bold'
          }
        },
        grid: {
          color: 'rgba(0, 0, 0, 0.1)',
          drawBorder: false
        },
        ticks: {
          maxTicksLimit: 10,
          font: {
            size: 11
          }
        }
      },
      y: {
        display: true,
        title: {
          display: true,
          text: isPercentage ? '使用率 (%)' : '流量 (MB/s)',
          font: {
            size: 12,
            weight: 'bold'
          }
        },
        min: 0,
        max: isPercentage ? 100 : undefined,
        grid: {
          color: 'rgba(0, 0, 0, 0.1)',
          drawBorder: false
        },
        ticks: {
          callback: function(value: any) {
            if (isPercentage) {
              return value + '%'
            } else {
              return value.toFixed(1) + ' MB/s'
            }
          },
          font: {
            size: 11
          }
        }
      }
    },
    elements: {
      point: {
        hoverRadius: 8
      }
    },
    animation: {
      duration: 750,
      easing: 'easeInOutQuart'
    }
  }
})

// 图表实例引用
const chartRef = ref()

// 监听数据变化，更新图表
watch(
  () => [props.data, props.type, props.timeRange],
  () => {
    if (chartRef.value?.chart) {
      chartRef.value.chart.update('active')
    }
  },
  { deep: true }
)
</script>

<template>
  <div class="chart-wrapper">
    <div v-if="!data || data.length === 0" class="chart-empty">
      <p>暂无数据</p>
    </div>
    <div v-else class="chart-container">
      <Line
        ref="chartRef"
        :data="chartData"
        :options="chartOptions"
      />
    </div>
  </div>
</template>

<style scoped>
.chart-wrapper {
  width: 100%;
  height: 100%;
  position: relative;
}

.chart-container {
  width: 100%;
  height: 100%;
  position: relative;
}

.chart-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #909399;
  font-size: 14px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .chart-container {
    height: 300px;
  }
}
</style>