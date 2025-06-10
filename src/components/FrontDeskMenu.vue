<template>
  <div class="front-desk-menu-container">
    <h1>波特普大学快捷廉价酒店</h1>
    <nav class="tabs">
      <button @click="activeTab = 'checkin'" :class="{ active: activeTab === 'checkin' }">
        办理入住
      </button>
      <button @click="activeTab = 'checkout'" :class="{ active: activeTab === 'checkout' }">
        办理结账
      </button>
    </nav>

    <div class="tab-content">
      <CheckInForm v-if="activeTab === 'checkin'" />
      <CheckOutForm v-if="activeTab === 'checkout'" />
    </div>
  </div>
</template>

<script>
import CheckInForm from './CheckInForm.vue'; // 确保路径正确
import CheckOutForm from './CheckOutForm.vue'; // 确保路径正确

export default {
  name: 'FrontDeskMenu',
  components: {
    CheckInForm,
    CheckOutForm
  },
  data() {
    return {
      activeTab: 'checkin' // 默认显示办理入住表单
    };
  }
};
</script>

<style scoped>
.front-desk-menu-container {
  max-width: 800px; /* 可以根据内容调整 */
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
  margin: 0 5px -2px 5px; /* -2px to overlap border */
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
  color: #007bff;
  border-color: #eee;
  border-bottom-color: #fff; /* Make bottom border invisible when active */
  font-weight: bold;
}

.tab-content {
  padding-top: 10px; /* Add some space if tabs overlap content */
}
</style>