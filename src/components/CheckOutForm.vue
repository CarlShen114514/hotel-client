<template>
  <div class="check-out-form-container">
    <h2>办理结账</h2>

    <div v-if="step === 1">
      <form @submit.prevent="handleInitialCheckOut">
        <div class="form-group">
          <label for="checkoutRoomNumber">请输入要结账的房间号:</label>
          <input type="text" id="checkoutRoomNumber" v-model.trim="roomNumber" required>
        </div>
        <button type="submit" class="submit-btn" :disabled="!roomNumber || isLoading">
          {{ isLoading ? '处理中...' : '退房并生成账单' }}
        </button>
      </form>
    </div>

    <div v-if="step >= 2 && bill" class="billing-details-section">
      <h3>账单详情 - 房间 {{ bill.roomId }}</h3>
      <p><strong>客户姓名:</strong> {{ bill.clientName }}</p>
      <p><strong>入住时间:</strong> {{ formatDate(bill.checkinTime) }}</p>
      <p><strong>离店时间:</strong> {{ formatDate(bill.checkoutTime) }}</p>
      <hr>
      <h4>费用明细 (粗略):</h4>
      <ul>
        <li>房费: {{ bill.roomFee.toFixed(2) }} 元</li>
        <li>空调使用费: {{ bill.totalAcCost.toFixed(2) }} 元</li>
      </ul>
      <p class="total-charge"><strong>总费用:</strong> {{ bill.totalBill.toFixed(2) }} 元</p>
      <hr>

      <div v-if="step === 3">
        <h4>空调使用详单:</h4>
        <div class="aircon-usage-details">
          <div v-if="!bill.details || bill.details.length === 0">无空调使用记录。</div>
          <ul v-else>
      <li v-for="(item, index) in bill.details" :key="index">
        {{ formatDate(item.startTime) }} - {{ formatDate(item.endTime) }} |
        风速: {{ formatFanSpeed(item.speed) }} |
        时长: {{ item.durationSeconds }} 秒 |
        费用: {{ item.cost.toFixed(2) }} 元
        </li>
    </ul>
        </div>
        <hr>
      </div>
      
      <div class="actions">
        <button 
          v-if="step === 2" 
          @click="showDetailedBill" 
          class="action-btn details-btn" 
          :disabled="isLoading"
        >
          {{ isLoading ? '加载中...' : '查看详细账单' }}
        </button>

        <button @click="settleBill" class="action-btn settle-btn">结账</button>
      </div>
    </div>
    
    <div v-if="feedbackMessage" :class="['feedback', feedbackType]">
        {{ feedbackMessage }}
    </div>
  </div>
</template>

<script>
import api from '../../src/api.js';

export default {
  name: 'CheckOutForm',
  data() {
    return {
      step: 1, // 1: 初始输入, 2: 显示粗略账单, 3: 显示详细账单
      roomNumber: '',
      bill: null,
      isLoading: false,
      feedbackMessage: '',
      feedbackType: '',
    };
  },
  methods: {
    formatDate(dateString) {
      if (!dateString) return 'N/A';
      const options = { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' };
      return new Date(dateString).toLocaleDateString(undefined, options);
    },
    formatFanSpeed(speedValue) {
      switch (speedValue) {
        case 1:
          return '低速';
        case 2:
          return '中速';
        case 3:
          return '高速';
        default:
          return '未知';
      }
    },
    /**
     * 步骤一触发：退房并获取粗略账单
     */
    async handleInitialCheckOut() {
      this.isLoading = true;
      this.feedbackMessage = '';
      try {
        await api.checkOut({ roomNumber: this.roomNumber }); //
        // 注意：这里调用的是获取粗略账单的接口
        const response = await api.getBill(this.roomNumber); //
        this.bill = response.data;
        this.step = 2; // 进入步骤二，显示粗略账单
      } catch (error) {
        this.feedbackMessage = error.response?.data?.error || '操作失败，请检查房间号。';
        this.feedbackType = 'error';
      } finally {
        this.isLoading = false;
      }
    },
    
    /**
     * 步骤二触发：获取并展示详细账单
     */
    async showDetailedBill() {
      this.isLoading = true;
      this.feedbackMessage = '';
      try {
        // 调用获取详细账单的接口
        const response = await api.getDetailedBill(this.roomNumber); //
        this.bill = response.data;
        this.step = 3; // 进入步骤三，展开详细信息
      } catch (error) {
        this.feedbackMessage = error.response?.data?.error || '获取详细账单失败。';
        this.feedbackType = 'error';
      } finally {
        this.isLoading = false;
      }
    },

    /**
     * 结账按钮触发：显示提示框并重置页面
     */
    settleBill() {
      // 显示一个简单的成功提示框
      alert(`房间 ${this.roomNumber} 已成功结账！`);
      // 清除页面内容，返回初始状态
      this.resetForm();
    },

    /**
     * 重置组件状态
     */
    resetForm() {
      this.step = 1;
      this.roomNumber = '';
      this.bill = null;
      this.feedbackMessage = '';
    }
  },
  // computed 和 style 部分保持不变
  computed: {
    finalAmountText() {
      if (!this.bill) return '';
      // 假设您的后端返回体中没有 finalAmount，我们可以在前端计算
      const finalAmount = this.bill.totalBill - (this.bill.depositPaid || 0);
      return finalAmount >= 0 ? '应补交' : '应退还';
    },
    finalAmountClass() {
      if (!this.bill) return '';
      const finalAmount = this.bill.totalBill - (this.bill.depositPaid || 0);
      return finalAmount >= 0 ? 'amount-due' : 'amount-refund';
    }
  },
};
</script>

<style scoped>
.check-out-form-container { max-width: 650px; margin: 20px auto; padding: 25px; border: 1px solid #ddd; border-radius: 8px; background-color: #f9f9f9; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
h2, h3, h4 { text-align: center; color: #333; margin-bottom: 15px; }
.form-group { margin-bottom: 18px; }
.form-group label { display: block; margin-bottom: 6px; font-weight: bold; color: #555; }
.form-group input[type="text"] { width: 100%; padding: 10px; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }
.billing-details-section { margin-top: 20px; padding: 15px; border: 1px solid #e0e0e0; border-radius: 5px; background-color: #fff; }
p { margin: 8px 0; line-height: 1.6; }
ul { list-style-type: none; padding-left: 0; }
li { margin-bottom: 5px; }
hr { margin: 15px 0; border: 0; border-top: 1px solid #eee; }
.total-charge strong { font-size: 1.2em; }
.amount-due { color: red; font-weight: bold; }
.amount-refund { color: green; font-weight: bold; }
.submit-btn { width: 100%; padding: 12px; font-size: 1.1em; cursor: pointer; border: none; border-radius: 4px; background-color: #d9534f; color: white; transition: background-color 0.2s; }
.submit-btn:hover { background-color: #c9302c; }
.submit-btn:disabled { background-color: #aaa; cursor: not-allowed; }
.actions { display: flex; justify-content: space-around; margin-top: 20px; }
.action-btn { padding: 10px 25px; border-radius: 5px; border: none; color: white; cursor: pointer; font-size: 1em; transition: background-color 0.2s; }
.action-btn:disabled { background-color: #aaa; cursor: not-allowed; }
.settle-btn { background-color: #5cb85c; }
.settle-btn:hover { background-color: #4cae4c; }
.details-btn { background-color: #337ab7; }
.details-btn:hover { background-color: #286090; }
.feedback { margin-top: 15px; padding: 10px; border-radius: 4px; text-align: center; }
.feedback.success { background-color: #d4edda; color: #155724; }
.feedback.error { background-color: #f8d7da; color: #721c24; }
.aircon-usage-details { margin-top: 10px; max-height: 200px; overflow-y: auto; padding: 10px; background-color: #f8f8f8; border: 1px solid #efefef; border-radius: 4px; font-size: 0.9em; }
</style>