<template>
  <div class="check-in-form-container">
    <h2>办理入住</h2>
    <form @submit.prevent="handleCheckIn">
      <div class="form-group">
        <label for="roomNumber">房间号:</label>
        <input type="text" id="roomNumber" v-model="roomNumber" required placeholder="例如: 101, 203A">
        <button type="button" @click="fetchRoomStatus" class="inline-btn" :disabled="!roomNumber">查询</button>
      </div>
      <div v-if="roomStatusInfo" class="room-status-info">
        <p>状态: <span :class="roomStatusClass">{{ roomStatusInfo.status }}</span></p>
        <p v-if="roomStatusInfo.type">类型: {{ roomStatusInfo.type }}</p>
        <p v-if="roomStatusInfo.price_per_night">价格: {{ roomStatusInfo.price_per_night }} 元/晚</p>
      </div>

      <div v-if="canProceedToGuestInfo" class="guest-info-section">
        <hr>
        <h3>客户信息</h3>
        <div class="form-group">
          <label for="clientName">客户姓名:</label>
          <input type="text" id="clientName" v-model="clientName" required>
        </div>
        <div class="form-group">
          <label for="clientID">身份证号:</label>
          <input type="text" id="clientID" v-model="clientID" required pattern="\d{17}[\dX]">
        </div>
      </div>

      <button type="submit" class="submit-btn" :disabled="!isFormValid || isLoading">
        {{ isLoading ? '处理中...' : '确认入住' }}
      </button>

      <div v-if="feedbackMessage" :class="['feedback', feedbackType]">
        {{ feedbackMessage }}
      </div>
    </form>
  </div>
</template>

<script>
import api from '../../src/api'; 
export default {
  name: 'CheckInForm',
  data() {
    return {
      roomNumber: '',
      clientName: '',
      clientID: '',
      isLoading: false,
      feedbackMessage: '',
      feedbackType: '', // 'success' or 'error'

      // 模拟房间状态
      roomStatusInfo: null, // { status: '可用', type: '大床房', price_per_night: 299 }
      availableRooms: { // 模拟后端数据
        '101': { status: '可用', type: '大床房', price_per_night: 299 },
        '102': { status: '已入住', occupant: '张三' },
        '201': { status: '维修中' },
        '203A': { status: '可用', type: '标准间', price_per_night: 199 },
      }
    };
  },
  computed: {
    canProceedToGuestInfo() {
      return this.roomStatusInfo && this.roomStatusInfo.status === '可用';
    },
    isFormValid() {
      if (!this.canProceedToGuestInfo) return false;
      return (
        this.clientName.trim() !== '' &&
        this.clientID.trim() !== ''  // 可以添加更复杂的身份证校验
      );
    },
    roomStatusClass() {
        if (!this.roomStatusInfo) return '';
        if (this.roomStatusInfo.status === '可用') return 'status-available';
        if (this.roomStatusInfo.status === '已入住') return 'status-occupied';
        return 'status-other';
    }
  },
  methods: {
    async fetchRoomStatus() {
      if (!this.roomNumber) return;
      this.isLoading = true;
      this.feedbackMessage = '';
      this.roomStatusInfo = null; // 重置

      
      try {
        // 2. 调用api服务中的 getRoomStatus 方法，该方法会发送 GET /api/rooms/{roomId}/status 请求
        const response = await api.getRoomStatus(this.roomNumber);
    
        const data = response.data; // 后端返回的原始数据

        if (data.occupancyState === 0) {
          this.roomStatusInfo = { status: '可用'};
        } else if (data.occupancyState === 1) {
          this.roomStatusInfo = { status: '已占用'};
        } 
      } catch (error) {
        this.roomStatusInfo = { status: '查询失败' }; // 在UI上显示查询失败
        // 从后端响应中提取错误信息，如果提取不到则显示通用错误提示
        this.feedbackMessage = error.response?.data?.error || `房间 ${this.roomNumber} 不存在或网络错误。`;
        this.feedbackType = 'error';
      } finally {
        this.isLoading = false; // 无论成功或失败，都结束加载状态
      }
    },
    async handleCheckIn() {
      if (!this.isFormValid) return;
      this.isLoading = true;
      this.feedbackMessage = '';

      // 模拟API调用
      console.log('办理入住信息:', {
        roomNumber: this.roomNumber,
        clientName: this.clientName,
        clientID: this.clientID,
      });

      await new Promise(resolve => setTimeout(resolve, 1000));


      const checkInData = {
        roomNumber: this.roomNumber,
        clientName: this.clientName,
        clientID: this.clientID,
      };

      try {
        // 4. 调用api服务中的 checkIn 方法，发送 POST /api/check-in 请求
        const response = await api.checkIn(checkInData);
        
        // 使用后端返回的成功信息来提示用户
        this.feedbackMessage = response.data.message || `房间 ${this.roomNumber} 办理入住成功！`;
        this.feedbackType = 'success';
        this.resetForm(); // 入住成功后，清空表单以便下次使用

      } catch (error) {
        // 使用后端返回的错误信息来提示用户
        this.feedbackMessage = error.response?.data?.error || '办理入住失败，请检查信息或联系管理员。';
        this.feedbackType = 'error';
      } finally {
        this.isLoading = false;
      }
    },
    resetForm() {
      this.roomNumber = '';
      this.clientName = '';
      this.clientID = '';
    }
  }
};
</script>

<style scoped>
.check-in-form-container {
  max-width: 500px;
  margin: 20px auto;
  padding: 25px;
  border: 1px solid #ddd;
  border-radius: 8px;
  background-color: #f9f9f9;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}
h2, h3 {
  text-align: center;
  color: #333;
  margin-bottom: 20px;
}
.form-group {
  margin-bottom: 18px;
}
.form-group label {
  display: block;
  margin-bottom: 6px;
  font-weight: bold;
  color: #555;
}
.form-group input[type="text"],
.form-group input[type="tel"],
.form-group input[type="number"] {
  width: calc(80% - 11px);
  padding: 10px;
  border: 1px solid #ccc;
  border-radius: 4px;
  box-sizing: border-box;
}
.inline-btn {
  padding: 10px 15px;
  margin-left: 10px;
  background-color: #5cb85c;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  display: inline-block; /* 确保按钮也是行内块元素 */
  vertical-align: middle; /* 垂直居中对齐 */
  width: calc(20% - 15px); /* 设置按钮宽度 */
}
.inline-btn:disabled {
  background-color: #aaa;
}
.room-status-info {
  padding: 10px;
  margin-top: 10px;
  border: 1px dashed #ccc;
  border-radius: 4px;
  background-color: #f0f0f0;
}
.room-status-info p {
  margin: 5px 0;
}
.status-available { color: green; font-weight: bold; }
.status-occupied { color: red; font-weight: bold; }
.status-other { color: orange; font-weight: bold; }

.guest-info-section hr {
    margin: 20px 0;
    border: 0;
    border-top: 1px solid #eee;
}

.submit-btn {
  width: calc(92% + 25px);
  padding: 12px;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 1.1em;
  cursor: pointer;
  transition: background-color 0.2s;
}
.submit-btn:hover {
  background-color: #006bde;
}
.submit-btn:disabled {
  background-color: #aaa;
  cursor: not-allowed;
}
.feedback {
  margin-top: 15px;
  padding: 10px;
  border-radius: 4px;
  text-align: center;
}
.feedback.success {
  background-color: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}
.feedback.error {
  background-color: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}
</style>