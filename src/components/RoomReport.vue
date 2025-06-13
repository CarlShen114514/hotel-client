<template>
  <div class="room-report">
    <h2>按房间号查询调度记录</h2>
    <form @submit.prevent="fetchRoomRecords" class="query-form">
      <label for="roomId">房间号：</label>
      <input
        type="text"
        id="roomId"
        v-model="roomId"
        placeholder="输入房间号"
        required
      />
      
      <label for="reportType">查询类型：</label>
      <select id="reportType" v-model="reportType" required>
        <option value="detailed">详细记录</option>
        <option value="summary">统计汇总</option>
      </select>
      
      <button type="submit">查询</button>
    </form>

    <div v-if="error" class="error-message">{{ error }}</div>
    <div v-if="loading">加载中...</div>

    <!-- 详细记录表 -->
    <table
      v-if="reportType === 'detailed' && roomRecords.length > 0 && !loading"
      class="report-table"
    >
      <thead>
        <tr>
          <th>房间号</th>
          <th>开始时间</th>
          <th>结束时间</th>
          <th>持续时间（s）</th>
          <th>风速</th>
          <th>费用（￥）</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="record in roomRecords" :key="'room-' + record.id">
          <td>{{ record.roomId }}</td>
          <td>{{ formatDateTime(record.startTime) }}</td>
          <td>{{ formatDateTime(record.endTime) }}</td>
          <td>{{ record.durationSeconds ?? '-' }}</td>
          <td>{{ formatSpeed(record.speed) }}</td>
          <td>{{ record.cost != null ? record.cost.toFixed(2) : '-' }}</td>
        </tr>
      </tbody>
    </table>

    <!-- 统计汇总表 -->
    <table
      v-if="reportType === 'summary' && roomSummary && !loading"
      class="report-table summary-table"
    >
      <thead>
        <tr>
          <th>房间号</th>
          <th>总开启时间（s）</th>
          <th>总费用（￥）</th>
          <th>使用次数</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>{{ roomSummary.roomId }}</td>
          <td>{{ roomSummary.totalDuration }}</td>
          <td>{{ roomSummary.totalCost.toFixed(2) }}</td>
          <td>{{ roomSummary.usageCount }}</td>
        </tr>
      </tbody>
    </table>

    <div
      v-else-if="!loading && !error && roomRecordsQueried"
    >暂无{{ reportType === 'detailed' ? '详细记录' : '统计' }}数据</div>
  </div>
</template>

<script>
export default {
  name: "RoomReport",
  data() {
    return {
      roomId: "",
      reportType: "detailed", // 'detailed' 或 'summary'
      roomRecords: [],
      roomSummary: null,
      roomRecordsQueried: false,
      loading: false,
      error: null,
    };
  },
  methods: {
    async fetchRoomRecords() {
      this.error = null;
      this.roomRecordsQueried = false;

      if (!this.roomId) {
        this.error = "请输入房间号";
        return;
      }

      this.loading = true;
      this.roomRecords = [];
      this.roomSummary = null;

      try {
        // 始终调用详细记录接口
        const response = await fetch(
          `/api/reports/rooms/${encodeURIComponent(this.roomId)}`
        );

        if (!response.ok) {
          const data = await response.json();
          this.error = data.error || "查询失败";
          return;
        }

        const data = await response.json();
        this.roomRecords = data;
        
        // 如果选择统计汇总，在前端计算
        if (this.reportType === 'summary') {
          this.roomSummary = this.calculateSummary(data, this.roomId);
        }
        
        this.roomRecordsQueried = true;
      } catch (err) {
        this.error = "请求失败，请稍后重试";
      } finally {
        this.loading = false;
      }
    },

    // 前端计算汇总数据的方法
    calculateSummary(records, roomId) {
      console.log('=== calculateSummary 开始 ===');
      console.log('输入参数 records:', records);
      console.log('roomId:', roomId, '类型:', typeof roomId);
      
      // 确保 roomId 是字符串类型
      const normalizedRoomId = String(roomId);
      
      if (!records || records.length === 0) {
        console.log('records 为空，返回默认统计');
        return {
          roomId: normalizedRoomId,
          totalDuration: 0,
          totalCost: 0,
          usageCount: 0
        };
      }

      const totalDuration = records.reduce((sum, record) => {
        const duration = Number(record.durationSeconds) || 0;
        console.log(`累加持续时间: ${duration} (原始: ${record.durationSeconds})`);
        return sum + duration;
      }, 0);

      const totalCost = records.reduce((sum, record) => {
        const cost = Number(record.cost) || 0;
        console.log(`累加费用: ${cost} (原始: ${record.cost})`);
        return sum + cost;
      }, 0);

      const result = {
        roomId: normalizedRoomId,
        totalDuration: totalDuration,
        totalCost: totalCost,
        usageCount: records.length
      };
      
      console.log('计算结果:', result);
      console.log('=== calculateSummary 结束 ===');
      
      return result;
    },

    formatDateTime(dateStr) {
      if (!dateStr) return "-";
      const d = new Date(dateStr);
      const y = d.getFullYear();
      const m = String(d.getMonth() + 1).padStart(2, "0");
      const day = String(d.getDate()).padStart(2, "0");
      const h = String(d.getHours()).padStart(2, "0");
      const min = String(d.getMinutes()).padStart(2, "0");
      const s = String(d.getSeconds()).padStart(2, "0");
      return `${y}-${m}-${day} ${h}:${min}:${s}`;
    },

    formatSpeed(speed) {
      switch (speed) {
        case 1:
          return "低";
        case 2:
          return "中";
        case 3:
          return "高";
        default:
          return "-";
      }
    },
  },
};
</script>

<style scoped>
.room-report {
  max-width: 800px;
  margin: 0 auto;
  font-family: Arial, sans-serif;
}

.query-form {
  display: flex;
  gap: 10px;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

label {
  font-weight: bold;
}

input[type="text"], select {
  padding: 6px 8px;
  font-size: 1em;
  border: 1px solid #ccc;
  border-radius: 4px;
}

select {
  min-width: 120px;
}

button {
  padding: 6px 15px;
  background-color: #013fba;
  border: none;
  color: white;
  cursor: pointer;
  border-radius: 4px;
}

button:hover {
  background-color: #0253d2;
}

.error-message {
  color: red;
  margin-bottom: 10px;
}

.report-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 20px;
}

.report-table th,
.report-table td {
  border: 1px solid #ddd;
  padding: 8px;
  text-align: center;
}

.report-table th {
  background-color: #f1f1f1;
  font-weight: bold;
}

.summary-table {
  background-color: #f9f9f9;
}

.summary-table td {
  font-weight: 500;
}
</style>