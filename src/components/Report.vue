<template>
  <div class="report-menu-container">
    <h1>调度报表</h1>
    <nav class="tabs">
      <button @click="activeTab = 'room'" :class="{ active: activeTab === 'room' }">
        按房间查询
      </button>
      <button @click="activeTab = 'time'" :class="{ active: activeTab === 'time' }">
        按时间查询
      </button>
    </nav>

    <div class="tab-content">
      <RoomReport v-if="activeTab === 'room'" />
      <TimeReport v-if="activeTab === 'time'" />
    </div>
  </div>
</template>

<script>
import RoomReport from './RoomReport.vue';
import TimeReport from './TimeReport.vue';

export default {
  name: "ReportUsage",
  components: {
    RoomReport,
    TimeReport
  },
  data() {
    return {
      activeTab: 'room' // 默认显示按房间查询
    };
  }
};
</script>

<style scoped>
.report-menu-container {
  max-width: 900px;
  margin: 20px auto;
  padding: 20px;
}

h1 {
  text-align: center;
  color: #333;
  margin-bottom: 25px;
}

.tabs {
  display: flex;
  justify-content: center;
  margin-bottom: 20px;
  border-bottom: 2px solid #eee;
}

.tabs button {
  padding: 10px 20px;
  margin: 0 5px -2px 5px;
  border: 2px solid transparent;
  border-bottom: none;
  background-color: #f0f0f0;
  color: #555;
  cursor: pointer;
  font-size: 1em;
  border-top-left-radius: 5px;
  border-top-right-radius: 5px;
  transition: background-color 0.2s, color 0.2s, border-color 0.2s;
}

.tabs button:hover {
  background-color: #e0e0e0;
}

.tabs button.active {
  background-color: #fff;
  color: #013fba;
  border-color: #eee;
  border-bottom-color: #fff;
  font-weight: bold;
}

.tab-content {
  padding-top: 10px;
}
</style>