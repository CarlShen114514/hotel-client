<template>
  <div class="aircon-monitor-container">
    <h2>空调状态监控</h2>

    <div class="filters">
      <input type="text" v-model="filterRoomNumber" placeholder="筛选房间号">
      <select v-model="filterStatus">
        <option value="">所有状态</option>
        <option value="on">运行中</option>
        <option value="standby">待机/停风</option>
        <option value="off">关机</option>
        <option value="error">故障</option>
      </select>
      <button @click="fetchRoomsData" :disabled="isLoading">
        <span v-if="isLoading">刷新中...</span>
        <span v-else>刷新数据</span>
      </button>
      <div class="auto-refresh">
        <label for="autoRefreshToggle">自动刷新:</label>
        <input type="checkbox" id="autoRefreshToggle" v-model="autoRefreshEnabled" @change="toggleAutoRefresh">
        <span v-if="autoRefreshEnabled"> ({{ autoRefreshInterval / 1000 }}s)</span>
      </div>
    </div>

    <div v-if="isLoading && displayedRooms.length === 0" class="loading-data">
      正在加载房间空调数据...
    </div>
    <div v-else-if="!isLoading && displayedRooms.length === 0 && (filterRoomNumber || filterStatus)" class="no-data">
      没有符合筛选条件的房间。
    </div>
    <div v-else-if="!isLoading && rooms.length === 0" class="no-data">
      暂无房间空调数据。
    </div>

    <div class="room-cards-grid" v-else>
      <div v-for="room in displayedRooms" :key="room.id" :class="['room-card', getStatusClass(room.status)]">
        <div class="room-header">
          <h3>房间 {{ room.roomNumber }}</h3>
          <span :class="['status-badge', getStatusClass(room.status)]">{{ getStatusText(room.status) }}</span>
        </div>
        <div class="room-details">
          <p v-if="room.status !== 'off' && room.status !== 'error'">
            <strong>模式:</strong> {{ room.currentMode === 'cool' ? '制冷' : room.currentMode === 'heat' ? '制热' : 'N/A' }}
          </p>
          <p v-if="room.status !== 'off' && room.status !== 'error'">
            <strong>设定温度:</strong> {{ room.targetTemperature }}°C
          </p>
          <p><strong>当前室温:</strong> {{ room.currentTemperature.toFixed(1) }}°C</p>
          <p v-if="room.status !== 'off' && room.status !== 'error'">
            <strong>风速:</strong> {{ displayFanSpeed(room.fanSpeed) }}
          </p>
           <p v-if="room.status === 'on'">
            <strong>送风状态:</strong> {{ room.isSupplyingAir ? '送风中' : '已达目标，停风' }}
          </p>
          <p><strong>累计费用:</strong> {{ room.totalCost.toFixed(2) }}元</p>
          <p v-if="room.guestName"><strong>当前客人:</strong> {{ room.guestName }}</p>
          <p v-if="room.status === 'error' && room.errorMessage"><strong>故障信息:</strong> {{ room.errorMessage }}</p>
          <p class="last-updated">最后更新: {{ formatTime(room.lastUpdateTime) }}</p>
        </div>
        <!-- 可以添加更多操作，如强制关机、发送消息等 -->
         <div class="room-actions" v-if="room.status !== 'off'">
            <button @click="forceShutdown(room.id)" class="action-btn shutdown-btn" :disabled="isActionLoading[room.id]">
                {{ isActionLoading[room.id] === 'shutdown' ? '处理中...' : '强制关机' }}
            </button>
            <!-- <button @click="viewDetails(room.id)" class="action-btn details-btn">查看详单</button> -->
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ACMonitor',
  data() {
    return {
      rooms: [], // 存储所有房间的空调状态数据
      isLoading: false,
      isActionLoading: {}, // 用于跟踪特定房间操作的加载状态 e.g. { roomId: 'shutdown' }
      filterRoomNumber: '',
      filterStatus: '', // 'on', 'standby', 'off', 'error'
      autoRefreshEnabled: true,
      autoRefreshInterval: 10000, // 10秒自动刷新
      autoRefreshTimer: null,
    };
  },
  computed: {
    displayedRooms() {
      return this.rooms.filter(room => {
        const matchesRoomNumber = room.roomNumber.toLowerCase().includes(this.filterRoomNumber.toLowerCase());
        const matchesStatus = this.filterStatus ? room.status === this.filterStatus : true;
        return matchesRoomNumber && matchesStatus;
      }).sort((a, b) => a.roomNumber.localeCompare(b.roomNumber, undefined, { numeric: true })); // 按房间号排序
    }
  },
  methods: {
    async fetchRoomsData() {
      this.isLoading = true;
      // 模拟API调用
      console.log("Fetching AC data from server...");
      await new Promise(resolve => setTimeout(resolve, 800)); // 模拟网络延迟

      // 模拟从后端获取的数据
      const mockData = [
        { id: 'r101', roomNumber: '101', status: 'on', currentMode: 'cool', targetTemperature: 22, currentTemperature: 22.5, fanSpeed: 'medium', isSupplyingAir: true, totalCost: 12.50, guestName: '张三', lastUpdateTime: Date.now() - 5000 },
        { id: 'r102', roomNumber: '102', status: 'standby', currentMode: 'cool', targetTemperature: 24, currentTemperature: 23.8, fanSpeed: 'low', isSupplyingAir: false, totalCost: 8.75, guestName: '李四', lastUpdateTime: Date.now() - 10000 },
        { id: 'r103', roomNumber: '103', status: 'off', currentMode: null, targetTemperature: null, currentTemperature: 26.1, fanSpeed: null, isSupplyingAir: false, totalCost: 0.00, guestName: null, lastUpdateTime: Date.now() - 3600000 },
        { id: 'r201', roomNumber: '201', status: 'on', currentMode: 'heat', targetTemperature: 28, currentTemperature: 27.0, fanSpeed: 'high', isSupplyingAir: true, totalCost: 25.00, guestName: '王五', lastUpdateTime: Date.now() - 2000 },
        { id: 'r202', roomNumber: '202', status: 'error', currentMode: 'cool', targetTemperature: 20, currentTemperature: 29.5, fanSpeed: 'medium', isSupplyingAir: false, totalCost: 5.50, guestName: '赵六', errorMessage: '传感器故障', lastUpdateTime: Date.now() - 60000 },
        { id: 'r305A', roomNumber: '305A', status: 'standby', currentMode: 'heat', targetTemperature: 26, currentTemperature: 26.2, fanSpeed: 'medium', isSupplyingAir: false, totalCost: 3.20, guestName: '孙七', lastUpdateTime: Date.now() - 120000 },
      ];

      // 更新数据时，可以保留现有的一些状态或智能合并
      this.rooms = mockData.map(room => ({ ...room, lastUpdateTime: room.lastUpdateTime || Date.now() }));
      this.isLoading = false;
      console.log("AC data refreshed.");
    },
    getStatusClass(status) {
      switch (status) {
        case 'on': return 'status-on';
        case 'standby': return 'status-standby';
        case 'off': return 'status-off';
        case 'error': return 'status-error';
        default: return '';
      }
    },
    getStatusText(status) {
      switch (status) {
        case 'on': return '运行中';
        case 'standby': return '待机';
        case 'off': return '关机';
        case 'error': return '故障';
        default: return '未知';
      }
    },
    displayFanSpeed(speed) {
      if (!speed) return 'N/A';
      const map = { 'low': '低风', 'medium': '中风', 'high': '高风' };
      return map[speed] || speed;
    },
    formatTime(timestamp) {
      if (!timestamp) return 'N/A';
      return new Date(timestamp).toLocaleTimeString();
    },
    toggleAutoRefresh() {
      if (this.autoRefreshEnabled) {
        this.startAutoRefresh();
      } else {
        this.stopAutoRefresh();
      }
    },
    startAutoRefresh() {
      this.stopAutoRefresh(); // Clear existing timer
      if (this.autoRefreshEnabled && this.autoRefreshInterval > 0) {
        this.autoRefreshTimer = setInterval(() => {
          if (!this.isLoading) { // 避免在前一个请求未完成时再次请求
             this.fetchRoomsData();
          }
        }, this.autoRefreshInterval);
        console.log("Auto-refresh started.");
      }
    },
    stopAutoRefresh() {
      if (this.autoRefreshTimer) {
        clearInterval(this.autoRefreshTimer);
        this.autoRefreshTimer = null;
        console.log("Auto-refresh stopped.");
      }
    },
    async forceShutdown(roomId) {
        if (this.isActionLoading[roomId]) return;
        // this.$set(this.isActionLoading, roomId, 'shutdown'); // Vue 2
        this.isActionLoading = { ...this.isActionLoading, [roomId]: 'shutdown' }; // Vue 3 reactivity

        console.log(`Force shutting down AC for room ID: ${roomId}`);
        // 模拟API调用
        await new Promise(resolve => setTimeout(resolve, 1000));

        const roomIndex = this.rooms.findIndex(r => r.id === roomId);
        if (roomIndex !== -1) {
            // this.$set(this.rooms[roomIndex], 'status', 'off'); // Vue 2
            // this.$set(this.rooms[roomIndex], 'isSupplyingAir', false);
            // this.$set(this.rooms[roomIndex], 'lastUpdateTime', Date.now());
            this.rooms[roomIndex] = {
                ...this.rooms[roomIndex],
                status: 'off',
                isSupplyingAir: false,
                lastUpdateTime: Date.now()
            };
             // 强制关机后，可能需要重置一些其他字段
            this.rooms[roomIndex].currentMode = null;
            this.rooms[roomIndex].targetTemperature = null;
            this.rooms[roomIndex].fanSpeed = null;
        }
        // this.$delete(this.isActionLoading, roomId); // Vue 2
        const newActionLoading = { ...this.isActionLoading }; // Vue 3
        delete newActionLoading[roomId];
        this.isActionLoading = newActionLoading;

        console.log(`AC for room ID: ${roomId} shut down successfully.`);
    }
  },
  mounted() {
    this.fetchRoomsData();
    if (this.autoRefreshEnabled) {
      this.startAutoRefresh();
    }
  },
  beforeUnmount() {
    this.stopAutoRefresh();
  }
};
</script>

<style scoped>
.aircon-monitor-container {
  padding: 20px;
  font-family: Arial, sans-serif;
}
h2 {
  text-align: center;
  margin-bottom: 25px;
  color: #333;
}
.filters {
  display: flex;
  gap: 15px;
  align-items: center;
  margin-bottom: 25px;
  padding: 15px;
  background-color: #f8f9fa;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}
.filters input[type="text"],
.filters select {
  padding: 8px 12px;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 0.95em;
}
.filters button {
  padding: 8px 15px;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.2s;
}
.filters button:hover {
  background-color: #0056b3;
}
.filters button:disabled {
  background-color: #6c757d;
  cursor: not-allowed;
}
.auto-refresh {
    display: flex;
    align-items: center;
    gap: 5px;
    font-size: 0.9em;
    color: #555;
}
.auto-refresh input[type="checkbox"] {
    transform: scale(0.9); /* 使复选框小一点 */
}
.loading-data, .no-data {
  text-align: center;
  padding: 40px;
  font-size: 1.2em;
  color: #6c757d;
}
.room-cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 25px; /* 可以稍微增大间距，让毛玻璃效果更突出 */
  padding: 10px; /* 给网格一些内边距，防止卡片贴边 */
}

.room-card {
  border-radius: 12px; /* 圆角更大一些，配合毛玻璃更好看 */
  padding: 20px; /* 增加内边距 */
  position: relative; /* 为了伪元素定位 */
  overflow: hidden; /* 关键：确保伪元素的模糊效果不会溢出卡片边界 */
  box-shadow: 0 4px 15px rgba(0,0,0,0.1); /* 可以调整阴影 */
  transition: transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out;
  /* 移除之前的 border 和 background-color，将在伪元素上设置 */
}

.room-card::before {
  content: "";
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  /* 毛玻璃效果的关键 */
  background-color: rgba(255, 255, 255, 0.6); /* 半透明背景色 - 可调整透明度和颜色 */
  backdrop-filter: blur(10px) saturate(180%); /* 模糊效果和饱和度增强 */
  -webkit-backdrop-filter: blur(10px) saturate(180%); /* Safari 兼容 */
  z-index: -1; /* 将伪元素置于内容下方 */
  border-radius: inherit; /* 继承父元素的圆角 */
  /* 可以添加一个细微的边框在毛玻璃层上，如果需要的话 */
  /* border: 1px solid rgba(255, 255, 255, 0.18); */
}

.room-card:hover {
  transform: translateY(-5px) scale(1.02);
  box-shadow: 0 8px 25px rgba(0,0,0,0.15);
}

.room-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px; /* 调整间距 */
  padding-bottom: 12px;
  /* border-bottom: 1px solid rgba(255, 255, 255, 0.2); /* 分割线用半透明白色 */
  border-bottom: 1px solid rgba(0, 0, 0, 0.08); /* 或者用深色半透明 */
  position: relative; /* 确保内容在伪元素之上 */
  z-index: 1;
}
.room-header h3 {
  margin: 0;
  font-size: 1.3em;
  color: #2c3e50; /* 文字颜色需要确保在毛玻璃背景下清晰 */
}
.status-badge {
  padding: 5px 10px;
  border-radius: 15px;
  font-size: 0.8em;
  font-weight: bold;
  color: white;
  text-shadow: 0 1px 1px rgba(0,0,0,0.2); /* 给文字加一点阴影提高对比度 */
  position: relative;
  z-index: 1;
}
.status-on .status-badge { background-color: #28a745; } /* 保持徽章本身的颜色 */
.status-standby .status-badge { background-color: #ffc107; color: #333; }
.status-off .status-badge { background-color: #6c757d; }
.status-error .status-badge { background-color: #dc3545; }

.room-card.status-on { border-left: 7px solid #28a745; }
.room-card.status-standby { border-left: 7px solid #ffc107; }
.room-card.status-off { border-left: 7px solid #6c757d; }
.room-card.status-error { border-left: 7px solid #dc3545; }

/* Apply left border color to room-card as well */


.room-details {
    position: relative; /* 确保内容在伪元素之上 */
    z-index: 1;
}
.room-details p {
  margin: 8px 0; /* 调整间距 */
  font-size: 0.95em;
  color: #34495e; /* 调整文字颜色以保证可读性 */
  line-height: 1.6;
}
.room-details p strong {
  color: #2c3e50;
  min-width: 85px;
  display: inline-block;
}

.last-updated {
  font-size: 0.8em;
  color: #7f8c8d; /* 调整颜色 */
  text-align: right;
  margin-top: 12px;
  position: relative;
  z-index: 1;
}

.room-actions {
    margin-top: 15px;
    padding-top: 10px;
    border-top: 1px solid #f0f0f0;
    display: flex;
    gap: 10px;
}
.room-actions {
    margin-top: 18px;
    padding-top: 12px;
    /* border-top: 1px solid rgba(255, 255, 255, 0.2); */
    border-top: 1px solid rgba(0, 0, 0, 0.08);
    display: flex;
    gap: 10px;
    position: relative;
    z-index: 1;
}
.action-btn {
    padding: 7px 14px; /* 调整按钮大小 */
    border: none;
    border-radius: 5px; /* 调整圆角 */
    cursor: pointer;
    font-size: 0.9em;
    transition: background-color 0.2s, transform 0.1s;
}
.action-btn:hover {
    transform: translateY(-1px);
}
.action-btn.shutdown-btn {
    background-color: #e74c3c;
    color: white;
}
.action-btn.shutdown-btn:hover {
    background-color: #c0392b;
}
.action-btn:disabled {
    background-color: #bdc3c7; /* 调整禁用颜色 */
    color: #7f8c8d;
    cursor: not-allowed;
    transform: none;
}


</style>