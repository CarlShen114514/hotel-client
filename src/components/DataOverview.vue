<template>
  <div class="data-overview">
    <h1>数据总览</h1>
    
    <div class="charts-container">
      <!-- 左侧饼图 -->
      <div class="chart-section">
        <h2>今日空调花费分布</h2>
        <div class="chart-wrapper">
          <canvas ref="pieChart" id="pieChart"></canvas>
        </div>
        <div v-if="!pieChartData.length && !loading" class="no-data">
          今日暂无空调使用数据
        </div>
      </div>

      <!-- 右侧柱状图 -->
      <div class="chart-section">
        <h2>近七天空调消费趋势</h2>
        <div class="chart-wrapper">
          <canvas ref="barChart" id="barChart"></canvas>
        </div>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading">
      正在加载数据...
    </div>

    <!-- 错误信息 -->
    <div v-if="error" class="error-message">
      {{ error }}
    </div>

    <!-- 数据统计摘要 -->
    <div v-if="!loading && !error" class="summary-section">
      <h3>数据摘要</h3>
      <div class="summary-grid">
        <div class="summary-item">
          <span class="label">今日总消费：</span>
          <span class="value">￥{{ todayTotalCost.toFixed(2) }}</span>
        </div>
        <div class="summary-item">
          <span class="label">近七天总消费：</span>
          <span class="value">￥{{ weekTotalCost.toFixed(2) }}</span>
        </div>
        <div class="summary-item">
          <span class="label">活跃房间数：</span>
          <span class="value">{{ activeRoomsCount }} 间</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import Chart from 'chart.js/auto';
import api from '../api.js';

// 在组件顶部添加全局Chart.js配置
Chart.defaults.animation = false; // 全局禁用动画

export default {
  name: 'DataOverview',
  data() {
    return {
      loading: false,
      error: null,
      pieChart: null,
      barChart: null,
      pieChartData: [],
      barChartData: [],
      todayTotalCost: 0,
      weekTotalCost: 0,
      activeRoomsCount: 0,
      roomColors: {},
      // 新增：用于跟踪组件是否已卸载
      isDestroyed: false,
    };
  },
  mounted() {
    this.loadData();
  },
  beforeUnmount() {
    // 标记组件即将销毁
    this.isDestroyed = true;
    
    // 立即销毁图表实例
    this.destroyCharts();
  },
  // 新增：使用 unmounted 钩子确保彻底清理
  unmounted() {
    this.destroyCharts();
  },
  methods: {
    // 改进：更彻底的图表销毁方法
    destroyCharts() {
      // 销毁饼图
      if (this.pieChart) {
        try {
          // 停止所有动画
          this.pieChart.stop();
          // 清除画布内容
          if (this.pieChart.canvas && this.pieChart.ctx) {
            this.pieChart.ctx.clearRect(0, 0, this.pieChart.canvas.width, this.pieChart.canvas.height);
          }
          // 销毁图表实例
          this.pieChart.destroy();
        } catch (error) {
          console.warn('饼图销毁失败:', error);
        } finally {
          this.pieChart = null;
        }
      }
      
      // 销毁柱状图
      if (this.barChart) {
        try {
          // 停止所有动画
          this.barChart.stop();
          // 清除画布内容
          if (this.barChart.canvas && this.barChart.ctx) {
            this.barChart.ctx.clearRect(0, 0, this.barChart.canvas.width, this.barChart.canvas.height);
          }
          // 销毁图表实例
          this.barChart.destroy();
        } catch (error) {
          console.warn('柱状图销毁失败:', error);
        } finally {
          this.barChart = null;
        }
      }
    },

    async loadData() {
      // 检查组件是否已销毁
      if (this.isDestroyed) return;
      
      this.loading = true;
      this.error = null;

      try {
        const [todayData, weekData] = await Promise.all([
          this.fetchTodayData(),
          this.fetchWeekData()
        ]);

        // 再次检查组件状态
        if (this.isDestroyed) return;

        this.processPieChartData(todayData);
        this.processBarChartData(weekData);
        this.calculateSummary(todayData, weekData);

        // 使用 nextTick 并再次检查组件状态
        this.$nextTick(() => {
          if (!this.isDestroyed) {
            this.renderPieChart();
            this.renderBarChart();
          }
        });

      } catch (err) {
        if (!this.isDestroyed) {
          console.error('数据加载失败:', err);
          this.error = err.response?.data?.error || err.message || '数据加载失败，请稍后重试';
        }
      } finally {
        if (!this.isDestroyed) {
          this.loading = false;
        }
      }
    },

    async fetchTodayData() {
      if (this.isDestroyed) throw new Error('Component destroyed');
      
      const today = new Date();
      const startTime = new Date(today.getFullYear(), today.getMonth(), today.getDate()).toISOString();
      const endTime = new Date(today.getFullYear(), today.getMonth(), today.getDate(), 23, 59, 59).toISOString();

      try {
        const response = await api.getUsageReport(startTime, endTime);
        return response.data;
      } catch (error) {
        console.error('今日数据获取失败:', error);
        throw new Error(error.response?.data?.error || '今日数据获取失败');
      }
    },

    async fetchWeekData() {
      if (this.isDestroyed) throw new Error('Component destroyed');
      
      const today = new Date();
      const sevenDaysAgo = new Date(today.getTime() - 6 * 24 * 60 * 60 * 1000);
      
      const startTime = new Date(sevenDaysAgo.getFullYear(), sevenDaysAgo.getMonth(), sevenDaysAgo.getDate()).toISOString();
      const endTime = new Date(today.getFullYear(), today.getMonth(), today.getDate(), 23, 59, 59).toISOString();

      try {
        const response = await api.getUsageReport(startTime, endTime);
        return response.data;
      } catch (error) {
        console.error('近七天数据获取失败:', error);
        throw new Error(error.response?.data?.error || '近七天数据获取失败');
      }
    },

    processPieChartData(data) {
      if (!data || data.length === 0) {
        this.pieChartData = [];
        return;
      }

      // 按房间分组计算总费用
      const roomCosts = {};
      data.forEach(record => {
        const roomId = String(record.roomId);
        const cost = Number(record.cost) || 0;
        roomCosts[roomId] = (roomCosts[roomId] || 0) + cost;
      });

      // 转换为图表数据格式
      this.pieChartData = Object.entries(roomCosts)
        .filter(([, cost]) => cost > 0)
        .map(([roomId, cost]) => ({
          roomId,
          cost,
          percentage: 0 // 稍后计算
        }));

      // 计算百分比
      const totalCost = this.pieChartData.reduce((sum, item) => sum + item.cost, 0);
      this.pieChartData.forEach(item => {
        item.percentage = totalCost > 0 ? (item.cost / totalCost * 100) : 0;
      });

      // 按费用降序排列
      this.pieChartData.sort((a, b) => b.cost - a.cost);
    },

    processBarChartData(data) {
      if (!data || data.length === 0) {
        this.barChartData = [];
        return;
      }

      // 生成近七天的日期列表
      const dates = [];
      const today = new Date();
      for (let i = 6; i >= 0; i--) {
        const date = new Date(today.getTime() - i * 24 * 60 * 60 * 1000);
        dates.push(this.formatDate(date));
      }

      // 按日期和房间分组计算费用
      const dailyData = {};
      dates.forEach(date => {
        dailyData[date] = {};
      });

      data.forEach(record => {
        const recordDate = this.formatDate(new Date(record.startTime));
        const roomId = String(record.roomId);
        const cost = Number(record.cost) || 0;

        if (dailyData[recordDate]) {
          dailyData[recordDate][roomId] = (dailyData[recordDate][roomId] || 0) + cost;
        }
      });

      // 获取所有房间ID并分配颜色
      const allRooms = new Set();
      Object.values(dailyData).forEach(dayData => {
        Object.keys(dayData).forEach(roomId => allRooms.add(roomId));
      });

      this.assignRoomColors(Array.from(allRooms));

      this.barChartData = {
        dates,
        dailyData,
        rooms: Array.from(allRooms).sort()
      };
    },

    assignRoomColors(rooms) {
      const colors = [
        '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0',
        '#9966FF', '#FF9F40', '#FF6384', '#C9CBCF',
        '#4BC0C0', '#FF6384', '#36A2EB', '#FFCE56'
      ];

      rooms.forEach((roomId, index) => {
        this.roomColors[roomId] = colors[index % colors.length];
      });
    },

    calculateSummary(todayData, weekData) {
      // 今日总消费
      this.todayTotalCost = todayData.reduce((sum, record) => {
        return sum + (Number(record.cost) || 0);
      }, 0);

      // 近七天总消费
      this.weekTotalCost = weekData.reduce((sum, record) => {
        return sum + (Number(record.cost) || 0);
      }, 0);

      // 活跃房间数（有消费记录的房间）
      const activeRooms = new Set();
      weekData.forEach(record => {
        if (Number(record.cost) > 0) {
          activeRooms.add(String(record.roomId));
        }
      });
      this.activeRoomsCount = activeRooms.size;
    },

    renderPieChart() {
      // 检查组件状态和DOM元素
      if (this.isDestroyed || !this.$refs.pieChart || !this.pieChartData.length) return;

      try {
        const canvas = this.$refs.pieChart;
        const ctx = canvas.getContext('2d');
        
        // 检查DOM元素是否仍然有效
        if (!ctx || !canvas.offsetParent) {
          return;
        }
        
        // 销毁现有图表
        if (this.pieChart) {
          this.pieChart.stop();
          this.pieChart.destroy();
          this.pieChart = null;
        }

        // 再次检查组件状态
        if (this.isDestroyed) return;

        this.pieChart = new Chart(ctx, {
          type: 'pie',
          data: {
            labels: this.pieChartData.map(item => `房间 ${item.roomId}`),
            datasets: [{
              data: this.pieChartData.map(item => item.cost),
              backgroundColor: this.pieChartData.map(item => 
                this.roomColors[item.roomId] || '#CCCCCC'
              ),
              borderWidth: 2,
              borderColor: '#fff'
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            // 明确禁用所有动画
            animation: false,
            transitions: {
              active: {
                animation: {
                  duration: 0
                }
              }
            },
            plugins: {
              legend: {
                position: 'bottom',
                labels: {
                  padding: 20,
                  usePointStyle: true
                }
              },
              tooltip: {
                callbacks: {
                  label: (context) => {
                    const item = this.pieChartData[context.dataIndex];
                    return `房间 ${item.roomId}: ￥${item.cost.toFixed(2)} (${item.percentage.toFixed(1)}%)`;
                  }
                }
              }
            }
          }
        });

        // 如果组件已销毁，立即停止
        if (this.isDestroyed) {
          this.pieChart.stop();
          this.pieChart.destroy();
          this.pieChart = null;
        }

      } catch (error) {
        console.error('饼图渲染失败:', error);
        if (!this.isDestroyed) {
          this.error = '饼图渲染失败';
        }
      }
    },

    renderBarChart() {
      // 检查组件状态和DOM元素
      if (this.isDestroyed || !this.$refs.barChart || !this.barChartData.dates) return;

      try {
        const canvas = this.$refs.barChart;
        const ctx = canvas.getContext('2d');
        
        // 检查DOM元素是否仍然有效
        if (!ctx || !canvas.offsetParent) {
          return;
        }
        
        // 销毁现有图表
        if (this.barChart) {
          this.barChart.stop();
          this.barChart.destroy();
          this.barChart = null;
        }

        // 再次检查组件状态
        if (this.isDestroyed) return;

        // 准备数据集
        const datasets = this.barChartData.rooms.map(roomId => ({
          label: `房间 ${roomId}`,
          data: this.barChartData.dates.map(date => 
            this.barChartData.dailyData[date][roomId] || 0
          ),
          backgroundColor: this.roomColors[roomId] || '#CCCCCC',
          borderColor: this.roomColors[roomId] || '#CCCCCC',
          borderWidth: 1
        }));

        this.barChart = new Chart(ctx, {
          type: 'bar',
          data: {
            labels: this.barChartData.dates.map(date => this.formatDateForDisplay(date)),
            datasets: datasets
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            // 明确禁用所有动画
            animation: false,
            transitions: {
              active: {
                animation: {
                  duration: 0
                }
              }
            },
            scales: {
              x: {
                stacked: true,
                title: {
                  display: true,
                  text: '日期'
                }
              },
              y: {
                stacked: true,
                beginAtZero: true,
                title: {
                  display: true,
                  text: '消费金额 (￥)'
                },
                ticks: {
                  callback: function(value) {
                    return '￥' + value.toFixed(2);
                  }
                }
              }
            },
            plugins: {
              legend: {
                position: 'top'
              },
              tooltip: {
                callbacks: {
                  label: (context) => {
                    return `${context.dataset.label}: ￥${context.raw.toFixed(2)}`;
                  }
                }
              }
            }
          }
        });

        // 如果组件已销毁，立即停止
        if (this.isDestroyed) {
          this.barChart.stop();
          this.barChart.destroy();
          this.barChart = null;
        }

      } catch (error) {
        console.error('柱状图渲染失败:', error);
        if (!this.isDestroyed) {
          this.error = '柱状图渲染失败';
        }
      }
    },

    formatDate(date) {
      return date.toISOString().split('T')[0];
    },

    formatDateForDisplay(dateStr) {
      const date = new Date(dateStr);
      return `${date.getMonth() + 1}/${date.getDate()}`;
    }
  }
};
</script>

<style scoped>
.data-overview {
  max-width: 1200px;
  margin: 20px auto;
  padding: 20px;
  font-family: Arial, sans-serif;
}

h1 {
  text-align: center;
  color: #333;
  margin-bottom: 30px;
}

.charts-container {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 30px;
  margin-bottom: 30px;
}

.chart-section {
  background: #fff;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

.chart-section h2 {
  text-align: center;
  color: #333;
  margin-bottom: 20px;
  font-size: 1.2em;
}

.chart-wrapper {
  position: relative;
  height: 400px;
}

.no-data {
  text-align: center;
  color: #999;
  padding: 50px 0;
  font-style: italic;
}

.loading {
  text-align: center;
  padding: 50px 0;
  color: #666;
  font-size: 1.1em;
}

.error-message {
  background-color: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
  border-radius: 4px;
  padding: 15px;
  margin: 20px 0;
  text-align: center;
}

.summary-section {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 20px;
  margin-top: 20px;
}

.summary-section h3 {
  color: #333;
  margin-bottom: 15px;
  text-align: center;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 15px;
}

.summary-item {
  background: #fff;
  padding: 15px;
  border-radius: 6px;
  border: 1px solid #dee2e6;
  text-align: center;
}

.summary-item .label {
  display: block;
  color: #666;
  font-size: 0.9em;
  margin-bottom: 5px;
}

.summary-item .value {
  display: block;
  color: #013fba;
  font-size: 1.4em;
  font-weight: bold;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .charts-container {
    grid-template-columns: 1fr;
  }
  
  .chart-wrapper {
    height: 300px;
  }
}
</style>