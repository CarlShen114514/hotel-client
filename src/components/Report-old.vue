<template>
  <div class="report-usage">
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
      <button type="submit">查询</button>
    </form>

    <h2>按时间查询调度记录</h2>
    <form @submit.prevent="fetchReport" class="query-form">
      <label for="startDate">开始日期：</label>
      <input type="date" id="startDate" v-model="startDate" required />

      <label for="endDate">结束日期：</label>
      <input type="date" id="endDate" v-model="endDate" required />

      <button type="submit">查询</button>
    </form>

    <div v-if="error" class="error-message">{{ error }}</div>
    <div v-if="loading">加载中...</div>

    <!-- 房间号查询结果表 -->
    <table
      v-if="roomRecords.length > 0 && !loading"
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
    <div
      v-else-if="!loading && !error && roomRecordsQueried"
    >暂无房间记录数据</div>

    <!-- 时间范围查询结果表 -->
    <table
      v-if="records.length > 0 && !loading"
      class="report-table"
      style="margin-top: 40px;"
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
        <tr v-for="record in records" :key="'time-' + record.id">
          <td>{{ record.roomId }}</td>
          <td>{{ formatDateTime(record.startTime) }}</td>
          <td>{{ formatDateTime(record.endTime) }}</td>
          <td>{{ record.durationSeconds ?? '-' }}</td>
          <td>{{ formatSpeed(record.speed) }}</td>
          <td>{{ record.cost != null ? record.cost.toFixed(2) : '-' }}</td>
        </tr>
      </tbody>
    </table>
    <div
      v-else-if="!loading && !error && timeRangeQueried"
    >暂无时间范围记录数据</div>
  </div>
</template>

<script>
export default {
  name: "ReportUsage",
  data() {
    return {
      // 查询参数
      startDate: "",
      endDate: "",
      roomId: "",

      // 查询结果
      records: [],
      roomRecords: [],

      // 状态标记
      timeRangeQueried: false,
      roomRecordsQueried: false,
      loading: false,
      error: null,
    };
  },
  methods: {
    async fetchReport() {
      this.error = null;
      this.timeRangeQueried = false;

      // 清除房间记录
      this.roomRecords = [];
      this.roomRecordsQueried = false;

      if (!this.startDate || !this.endDate) {
        this.error = "请选择开始和结束日期";
        return;
      }
      if (this.startDate > this.endDate) {
        this.error = "开始日期不能晚于结束日期";
        return;
      }

      this.loading = true;
      this.records = [];

      const startTime = this.startDate + "T00:00:00";
      const endTime = this.endDate + "T23:59:59";

      try {
        const response = await fetch(
          `/api/reports/usage?startTime=${encodeURIComponent(
            startTime
          )}&endTime=${encodeURIComponent(endTime)}`
        );
        if (!response.ok) {
          const data = await response.json();
          this.error = data.error || "查询失败";
          return;
        }
        const data = await response.json();
        this.records = data;
        this.timeRangeQueried = true;
      } catch (err) {
        this.error = "请求失败，请稍后重试";
      } finally {
        this.loading = false;
      }
    },

    async fetchRoomRecords() {
      this.error = null;
      this.roomRecordsQueried = false;

      // 清除时间范围记录
      this.records = [];
      this.timeRangeQueried = false;

      if (!this.roomId) {
        this.error = "请输入房间号";
        return;
      }

      this.loading = true;
      this.roomRecords = [];

      try {
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
        this.roomRecordsQueried = true;
      } catch (err) {
        this.error = "请求失败，请稍后重试";
      } finally {
        this.loading = false;
      }
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
.report-usage {
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

input[type="date"],
input[type="text"] {
  padding: 6px 8px;
  font-size: 1em;
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
</style>
