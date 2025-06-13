<template>
  <div class="time-report">
    <h2>按时间查询调度记录</h2>
    <form @submit.prevent="fetchReport" class="query-form">
      <label for="startDate">开始日期：</label>
      <input type="date" id="startDate" v-model="startDate" required />

      <label for="endDate">结束日期：</label>
      <input type="date" id="endDate" v-model="endDate" required />

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
      v-if="reportType === 'detailed' && records.length > 0 && !loading"
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

    <!-- 统计汇总表 -->
    <table
      v-if="reportType === 'summary' && summaryData.length > 0 && !loading"
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
        <tr v-for="summary in summaryData" :key="'summary-' + summary.roomId">
          <td>{{ summary.roomId }}</td>
          <td>{{ summary.totalDuration }}</td>
          <td>{{ summary.totalCost.toFixed(2) }}</td>
          <td>{{ summary.usageCount }}</td>
        </tr>
      </tbody>
    </table>

    <div
      v-else-if="!loading && !error && timeRangeQueried"
    >暂无{{ reportType === 'detailed' ? '详细记录' : '统计' }}数据</div>
  </div>
</template>

<script>
export default {
  name: "TimeReport",
  data() {
    return {
      startDate: "",
      endDate: "",
      reportType: "detailed", // 'detailed' 或 'summary'
      records: [],
      summaryData: [],
      timeRangeQueried: false,
      loading: false,
      error: null,
    };
  },
  methods: {
    async fetchReport() {
      this.error = null;
      this.timeRangeQueried = false;

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
      this.summaryData = [];

      const startTime = this.startDate + "T00:00:00";
      const endTime = this.endDate + "T23:59:59";

      try {
        const url = `/api/reports/usage?startTime=${encodeURIComponent(
          startTime
        )}&endTime=${encodeURIComponent(endTime)}`;
        
        console.log('=== 时间查询调试信息 ===');
        console.log('查询类型:', this.reportType);
        console.log('请求URL:', url);
        
        const response = await fetch(url);
        console.log('HTTP状态:', response.status);

        if (!response.ok) {
          const errorText = await response.text();
          console.error('HTTP错误响应:', errorText);
          this.error = `HTTP错误: ${response.status} ${response.statusText}`;
          return;
        }

        const data = await response.json();
        console.log('后端返回的原始数据:', data);
        console.log('数据类型:', typeof data);
        console.log('是否为数组:', Array.isArray(data));
        console.log('数据长度:', data ? data.length : 'null');
        
        // 检查数据结构
        if (data && data.length > 0) {
          console.log('第一条记录样例:', data[0]);
          console.log('第一条记录的字段:', Object.keys(data[0]));
        }
        
        this.records = data;
        
        // 如果选择统计汇总，在前端计算按房间分组的统计
        if (this.reportType === 'summary') {
          console.log('=== 开始计算统计汇总 ===');
          try {
            this.summaryData = this.calculateGroupedSummary(data);
            console.log('统计汇总计算成功:', this.summaryData);
          } catch (summaryError) {
            console.error('统计汇总计算失败:', summaryError);
            this.error = `统计计算失败: ${summaryError.message}`;
            return;
          }
        }
        
        this.timeRangeQueried = true;
        console.log('=== 查询完成 ===');
        
      } catch (err) {
        console.error('网络请求异常详情:', err);
        console.error('错误堆栈:', err.stack);
        this.error = `请求失败: ${err.message}`;
      } finally {
        this.loading = false;
      }
    },

    // 前端计算按房间分组的汇总数据
    calculateGroupedSummary(records) {
      console.log('=== calculateGroupedSummary 开始 ===');
      console.log('输入参数 records:', records);
      console.log('records 类型:', typeof records);
      console.log('records 是否为数组:', Array.isArray(records));
      
      if (!records) {
        console.log('records 为 null 或 undefined');
        return [];
      }
      
      if (!Array.isArray(records)) {
        console.error('records 不是数组，实际类型:', typeof records);
        throw new Error('后端返回的数据格式不正确，期望数组');
      }
      
      if (records.length === 0) {
        console.log('records 数组为空');
        return [];
      }

      const roomGroups = {};
      
      records.forEach((record, index) => {
        console.log(`处理第 ${index + 1} 条记录:`, record);
        
        // 检查记录的必要字段
        if (!record) {
          console.warn(`第 ${index + 1} 条记录为空`);
          return;
        }
        
        if (!record.roomId && record.roomId !== 0) {
          console.warn(`第 ${index + 1} 条记录缺少 roomId:`, record);
          return;
        }
        
        // 确保 roomId 是字符串类型
        const roomId = String(record.roomId);
        console.log(`处理房间ID: ${roomId} (原始值: ${record.roomId}, 类型: ${typeof record.roomId})`);
        
        if (!roomGroups[roomId]) {
          roomGroups[roomId] = {
            roomId: roomId,
            totalDuration: 0,
            totalCost: 0,
            usageCount: 0
          };
        }
        
        // 安全地处理数值字段，确保转换为数字
        const duration = Number(record.durationSeconds) || 0;
        const cost = Number(record.cost) || 0;
        
        console.log(`房间 ${roomId}: duration=${duration} (原始: ${record.durationSeconds}), cost=${cost} (原始: ${record.cost})`);
        
        roomGroups[roomId].totalDuration += duration;
        roomGroups[roomId].totalCost += cost;
        roomGroups[roomId].usageCount += 1;
      });

      console.log('分组后的 roomGroups:', roomGroups);
      
      const result = Object.values(roomGroups).sort((a, b) => {
        // 确保 roomId 存在且可比较，并转换为字符串
        const aId = String(a.roomId || '');
        const bId = String(b.roomId || '');
        console.log(`排序比较: ${aId} vs ${bId}`);
        return aId.localeCompare(bId, undefined, { numeric: true });
      });
      
      console.log('最终统计结果:', result);
      console.log('=== calculateGroupedSummary 结束 ===');
      
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
.time-report {
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

input[type="date"], select {
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