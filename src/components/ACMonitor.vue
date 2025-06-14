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

          <p v-if="room.guestName">
            <strong>当前客人:</strong> {{ room.guestName }}
          </p>
          <p v-else>
            <strong>房间状态:</strong> <span class="status-unoccupied">未入住</span>
          </p>

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
import api from '../../src/api';

export default {
  name: 'ACMonitor',
  data() {
    return {
      rooms: [],
      isLoading: false,
      isActionLoading: {},
      filterRoomNumber: '',
      filterStatus: '',
      autoRefreshEnabled: true,
      autoRefreshInterval: 1000,
      autoRefreshTimer: null,
    };
  },
  computed: {
    displayedRooms() {
      return this.rooms.filter(room => {
        const matchesRoomNumber = room.roomNumber.toLowerCase().includes(this.filterRoomNumber.toLowerCase());
        const matchesStatus = this.filterStatus ? room.status === this.filterStatus : true;
        return matchesRoomNumber && matchesStatus;
      }).sort((a, b) => a.roomNumber.localeCompare(b.roomNumber, undefined, { numeric: true }));
    }
  },
  methods: {
    async fetchRoomsData() {
      this.isLoading = true;
      try {
        const response = await api.getAllRoomsStatus();
        // 使用 transformRoomData 方法来处理每个从后端接收到的房间对象
        this.rooms = response.data.map(this.transformRoomData);
        console.log("AC data refreshed from server.");
      } catch (error) {
        console.error("获取空调数据失败:", error);
        alert('无法加载空调数据，请检查后端服务是否运行。');
      } finally {
        this.isLoading = false;
      }
    },

    /**
     * @description 将后端 RoomInfo 对象转换为前端UI所需的格式
     * @param {object} backendRoom - 从后端获取的 RoomInfo 对象
     */
    transformRoomData(backendRoom) {
      // 根据你最新的定义，从 acState (Integer) 映射到 status (String)
      const getStatus = (acState) => {
        switch (acState) {
          case 0: return 'off';       // 关机
          case 1: return 'on';        // 运行中
          case 2: return 'standby';   // 等待中/待机
          case 3: return 'error';     // 假设3是故障
          default: return 'off';      // 其他未知情况默认为关机
        }
      };
      
      // 根据温度判断空调模式 (因为 RoomInfo 中没有模式字段)
      const getMode = (target, current) => {
        if (target === null || current === null) return 'cool';
        return current > target ? 'cool' : 'heat';
      };

      return {
        // --- 核心字段映射 ---
        id: String(backendRoom.roomId),
        roomNumber: String(backendRoom.roomId),
        status: getStatus(backendRoom.acState),
        currentMode: getMode(backendRoom.targetTempera, backendRoom.currentTempera),
        targetTemperature: backendRoom.targetTempera,
        currentTemperature: backendRoom.currentTempera,
        fanSpeed: backendRoom.currentSpeed?.toLowerCase() || 'low',
        guestName: backendRoom.state === 0 ? null : backendRoom.clientName,

        // --- 不再需要的或默认的字段 ---
        errorMessage: null, // RoomInfo 中没有错误信息
        lastUpdateTime: Date.now(),
      };
    },

    async forceShutdown(roomNumber) {
      if (this.isActionLoading[roomNumber]) return;
      this.isActionLoading = { ...this.isActionLoading, [roomNumber]: 'shutdown' };
      try {
        await api.turnOffAC(roomNumber);
        // 短暂延迟后刷新数据，给后端一点处理时间
        setTimeout(() => this.fetchRoomsData(), 500);
      } catch (error) {
        console.error(`强制关机失败 (房间 ${roomNumber}):`, error);
        alert(`房间 ${roomNumber} 强制关机失败: ${error.response?.data?.error || '未知错误'}`);
      } finally {
        const newActionLoading = { ...this.isActionLoading };
        delete newActionLoading[roomNumber];
        this.isActionLoading = newActionLoading;
      }
    },

    // --- 以下方法保持不变 ---
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
      this.stopAutoRefresh();
      if (this.autoRefreshEnabled && this.autoRefreshInterval > 0) {
        this.autoRefreshTimer = setInterval(() => {
          if (!this.isLoading) {
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