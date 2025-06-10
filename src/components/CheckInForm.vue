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
          <label for="guestName">客户姓名:</label>
          <input type="text" id="guestName" v-model="guestName" required>
        </div>
        <div class="form-group">
          <label for="guestIdCard">身份证号:</label>
          <input type="text" id="guestIdCard" v-model="guestIdCard" required pattern="\d{17}[\dX]">
        </div>
        <div class="form-group">
          <label for="contactNumber">联系电话:</label>
          <input type="tel" id="contactNumber" v-model="contactNumber" required>
        </div>
        <div class="form-group">
          <label for="numberOfNights">入住天数:</label>
          <input type="number" id="numberOfNights" v-model.number="numberOfNights" min="1" required>
        </div>
        <div class="form-group">
          <label for="deposit">押金 (元):</label>
          <input type="number" id="deposit" v-model.number="deposit" min="0" required>
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
export default {
  name: 'CheckInForm',
  data() {
    return {
      roomNumber: '',
      guestName: '',
      guestIdCard: '',
      contactNumber: '',
      numberOfNights: 1,
      deposit: 200, // 默认押金
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
        this.guestName.trim() !== '' &&
        this.guestIdCard.trim() !== '' && // 可以添加更复杂的身份证校验
        this.contactNumber.trim() !== '' &&
        this.numberOfNights >= 1 &&
        this.deposit >= 0
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

      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 500));
      const roomData = this.availableRooms[this.roomNumber.toUpperCase()];
      if (roomData) {
        this.roomStatusInfo = roomData;
      } else {
        this.roomStatusInfo = { status: '房间不存在' };
      }
      this.isLoading = false;
    },
    async handleCheckIn() {
      if (!this.isFormValid) return;
      this.isLoading = true;
      this.feedbackMessage = '';

      // 模拟API调用
      console.log('办理入住信息:', {
        roomNumber: this.roomNumber,
        guestName: this.guestName,
        guestIdCard: this.guestIdCard,
        contactNumber: this.contactNumber,
        numberOfNights: this.numberOfNights,
        deposit: this.deposit,
      });

      await new Promise(resolve => setTimeout(resolve, 1000));

      // 模拟成功或失败
      const isSuccess = Math.random() > 0.2; // 80% 成功率
      if (isSuccess) {
        this.feedbackMessage = `房间 ${this.roomNumber} 办理入住成功！客户: ${this.guestName}`;
        this.feedbackType = 'success';
        // 实际应用中，这里会更新房间状态为“已入住”
        this.availableRooms[this.roomNumber.toUpperCase()] = {
            status: '已入住',
            occupant: this.guestName,
            checkInTime: new Date().toISOString(),
            // ... 其他入住信息
        };
        this.resetForm();
      } else {
        this.feedbackMessage = '办理入住失败，请检查信息或联系管理员。';
        this.feedbackType = 'error';
      }
      this.isLoading = false;
    },
    resetForm() {
      this.roomNumber = '';
      this.guestName = '';
      this.guestIdCard = '';
      this.contactNumber = '';
      this.numberOfNights = 1;
      this.deposit = 200;
      this.roomStatusInfo = null;
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