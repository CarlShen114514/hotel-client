<template>
  <div class="check-out-form-container">
    <h2>办理结账</h2>
    <form @submit.prevent="handleCheckOut">
      <div class="form-group">
        <label for="checkoutRoomNumber">房间号:</label>
        <input type="text" id="checkoutRoomNumber" v-model="roomNumber" required>
        <button type="button" @click="fetchBillingDetails" class="inline-btn" :disabled="!roomNumber">查询账单</button>
      </div>

      <div v-if="isLoadingDetails" class="loading-details">查询中...</div>

      <div v-if="billingDetails" class="billing-details-section">
        <h3>账单详情 - 房间 {{ billingDetails.roomNumber }}</h3>
        <p><strong>客户姓名:</strong> {{ billingDetails.guestName }}</p>
        <p><strong>入住时间:</strong> {{ formatDate(billingDetails.checkInTime) }}</p>
        <p><strong>离店时间:</strong> {{ formatDate(billingDetails.checkOutTime) }}</p>
        <p><strong>入住天数:</strong> {{ billingDetails.durationDays }} 天</p>
        <hr>
        <h4>费用明细:</h4>
        <ul>
          <li>房费 ({{ billingDetails.price_per_night }} 元/晚 x {{ billingDetails.durationDays }} 天): {{ billingDetails.roomCharge.toFixed(2) }} 元</li>
          <li>空调使用费: {{ billingDetails.airConCharge.toFixed(2) }} 元</li>
          <li v-if="billingDetails.otherCharges > 0">其他消费: {{ billingDetails.otherCharges.toFixed(2) }} 元</li>
        </ul>
        <p class="total-charge"><strong>总费用:</strong> {{ billingDetails.totalCharge.toFixed(2) }} 元</p>
        <p>已付押金: {{ billingDetails.depositPaid.toFixed(2) }} 元</p>
        <p :class="finalAmountClass">
          <strong>{{ finalAmountText }}:</strong> {{ Math.abs(billingDetails.finalAmount).toFixed(2) }} 元
        </p>
        <hr>
        <h4>空调使用详单:</h4>
        <div class="aircon-usage-details">
          <div v-if="billingDetails.airConUsage.length === 0">无空调使用记录。</div>
          <ul v-else>
            <li v-for="(item, index) in billingDetails.airConUsage" :key="index">
              {{ formatDate(item.startTime) }} - {{ formatDate(item.endTime) }} |
              模式: {{ item.mode }} | 风速: {{ item.fanSpeed }} |
              时长: {{ item.durationMinutes }} 分钟 | 费用: {{ item.cost.toFixed(2) }} 元
            </li>
          </ul>
        </div>
      </div>

      <button type="submit" class="submit-btn" :disabled="!canCheckout || isLoadingCheckout">
        {{ isLoadingCheckout ? '处理中...' : '确认结账' }}
      </button>

      <div v-if="checkoutFeedbackMessage" :class="['feedback', checkoutFeedbackType]">
        {{ checkoutFeedbackMessage }}
      </div>
    </form>
  </div>
</template>

<script>
export default {
  name: 'CheckOutForm',
  data() {
    return {
      roomNumber: '',
      isLoadingDetails: false,
      isLoadingCheckout: false,
      billingDetails: null, // 存储从后端获取的账单详情
      checkoutFeedbackMessage: '',
      checkoutFeedbackType: '',

      // 模拟已入住房间的账单数据 (实际应从后端获取)
      occupiedRoomsBilling: {
        '101': {
          roomNumber: '101',
          guestName: '李四',
          checkInTime: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(), // 2天前
          checkOutTime: new Date().toISOString(),
          durationDays: 2,
          price_per_night: 299,
          airConCharge: 15.50,
          otherCharges: 0,
          depositPaid: 500,
          airConUsage: [
            { startTime: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000 + 10 * 60 * 1000).toISOString(), endTime: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000 + 70 * 60 * 1000).toISOString(), mode: '制冷', fanSpeed: '中', durationMinutes: 60, cost: 5.00 },
            { startTime: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000 + 30 * 60 * 1000).toISOString(), endTime: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000 + 150 * 60 * 1000).toISOString(), mode: '制热', fanSpeed: '高', durationMinutes: 120, cost: 10.50 },
          ]
        },
         '203A': {
          roomNumber: '203A',
          guestName: '王五',
          checkInTime: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(), // 1天前
          checkOutTime: new Date().toISOString(),
          durationDays: 1,
          price_per_night: 199,
          airConCharge: 8.75,
          otherCharges: 25.00, // 假设有其他消费
          depositPaid: 200,
          airConUsage: [
             { startTime: new Date(Date.now() - 20 * 60 * 60 * 1000).toISOString(), endTime: new Date(Date.now() - 18 * 60 * 60 * 1000).toISOString(), mode: '制冷', fanSpeed: '低', durationMinutes: 120, cost: 8.75 },
          ]
        }
      }
    };
  },
  computed: {
    canCheckout() {
      return this.billingDetails !== null;
    },
    finalAmountText() {
      if (!this.billingDetails) return '';
      return this.billingDetails.finalAmount >= 0 ? '应补交' : '应退还';
    },
    finalAmountClass() {
      if (!this.billingDetails) return '';
      return this.billingDetails.finalAmount >= 0 ? 'amount-due' : 'amount-refund';
    }
  },
  methods: {
    formatDate(dateString) {
      if (!dateString) return 'N/A';
      const options = { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' };
      return new Date(dateString).toLocaleDateString(undefined, options);
    },
    async fetchBillingDetails() {
      if (!this.roomNumber) return;
      this.isLoadingDetails = true;
      this.billingDetails = null;
      this.checkoutFeedbackMessage = '';

      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 700));
      const roomBill = this.occupiedRoomsBilling[this.roomNumber.toUpperCase()];

      if (roomBill) {
        // 动态计算总费用和最终金额
        const roomCharge = roomBill.price_per_night * roomBill.durationDays;
        const totalCharge = roomCharge + roomBill.airConCharge + (roomBill.otherCharges || 0);
        const finalAmount = totalCharge - roomBill.depositPaid;
        this.billingDetails = {
          ...roomBill,
          roomCharge,
          totalCharge,
          finalAmount
        };
      } else {
        this.checkoutFeedbackMessage = `房间 ${this.roomNumber} 未找到入住信息或账单。`;
        this.checkoutFeedbackType = 'error';
      }
      this.isLoadingDetails = false;
    },
    async handleCheckOut() {
      if (!this.canCheckout) return;
      this.isLoadingCheckout = true;
      this.checkoutFeedbackMessage = '';

      // 模拟API调用
      console.log('办理结账, 房间:', this.billingDetails.roomNumber, '最终金额:', this.billingDetails.finalAmount);
      await new Promise(resolve => setTimeout(resolve, 1000));

      // 模拟成功
      this.checkoutFeedbackMessage = `房间 ${this.billingDetails.roomNumber} 结账成功！`;
      this.checkoutFeedbackType = 'success';
      // 实际应用中，这里会更新房间状态为“可用”或“待清扫”，并清除账单信息
      delete this.occupiedRoomsBilling[this.roomNumber.toUpperCase()];
      // this.$parent.updateRoomStatus(this.roomNumber, '可用'); // 通过父组件更新
      this.resetForm();
      this.isLoadingCheckout = false;
    },
    resetForm() {
      this.roomNumber = '';
      this.billingDetails = null;
    }
  }
};
</script>

<style scoped>
.check-out-form-container {
  max-width: 650px;
  margin: 20px auto;
  padding: 25px;
  border: 1px solid #ddd;
  border-radius: 8px;
  background-color: #f9f9f9;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}
h2, h3, h4 {
  text-align: center;
  color: #333;
  margin-bottom: 15px;
}
h3 { text-align: center; }
.form-group {
  margin-bottom: 18px;
}
.form-group label {
  display: block;
  margin-bottom: 6px;
  font-weight: bold;
  color: #555;
}
.form-group input[type="text"] {
  width: calc(70% - 22px); /* 调整宽度以便按钮能放旁边 */
  padding: 10px;
  border: 1px solid #ccc;
  border-radius: 4px;
  box-sizing: border-box;
}
.inline-btn {
  padding: 10px 15px;
  margin-left: 10px;
  background-color: #337ab7;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  vertical-align: middle; /* 对齐输入框 */
}
.inline-btn:disabled {
  background-color: #aaa;
}
.loading-details {
  text-align: center;
  padding: 20px;
  color: #555;
}
.billing-details-section {
  margin-top: 20px;
  padding: 15px;
  border: 1px solid #e0e0e0;
  border-radius: 5px;
  background-color: #fff;
}
.billing-details-section p {
  margin: 8px 0;
  line-height: 1.6;
}
.billing-details-section ul {
  list-style-type: none;
  padding-left: 0;
}
.billing-details-section li {
  margin-bottom: 5px;
}
.total-charge strong {
  font-size: 1.2em;
}
.amount-due {
  color: red;
  font-weight: bold;
}
.amount-refund {
  color: green;
  font-weight: bold;
}
hr {
  margin: 15px 0;
  border: 0;
  border-top: 1px solid #eee;
}
.aircon-usage-details {
  max-height: 200px;
  overflow-y: auto;
  padding: 10px;
  background-color: #f8f8f8;
  border: 1px solid #efefef;
  border-radius: 4px;
  font-size: 0.9em;
}
.aircon-usage-details li {
  padding: 3px 0;
  border-bottom: 1px dotted #ddd;
}
.aircon-usage-details li:last-child {
  border-bottom: none;
}
.submit-btn {
  width: 100%;
  padding: 12px;
  background-color: #d9534f;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 1.1em;
  cursor: pointer;
  margin-top: 20px;
  transition: background-color 0.2s;
}
.submit-btn:hover {
  background-color: #c9302c;
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