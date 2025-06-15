<template>
  <div class="welcome-container">
    <div class="welcome-card">
      <!-- 酒店Logo和标题 -->
      <div class="hotel-header">
        <div class="hotel-logo">🏨</div>
        <h1 class="hotel-name">波特普大学快捷廉价酒店</h1>
        <p class="hotel-subtitle">BUTP super super cheap trash hotel</p>
      </div>

      <!-- 欢迎信息 -->
      <div class="welcome-content">
        <h2 class="welcome-title">欢迎入住！</h2>
        <p class="welcome-message">
          尊敬的客人，欢迎您下榻波特普大学快捷廉价酒店！<br>
          为了给您提供更舒适的住宿体验，我们为每个房间都配备了智能空调控制系统。<br>
          请输入您的房间号，即可进入房间的空调控制面板。
        </p>
      </div>

      <!-- 房间号输入区域 -->
      <div class="room-input-section">
        <div class="input-group">
          <label for="roomNumber" class="input-label">请输入您的房间号：</label>
          <div class="input-container">
            <input
              id="roomNumber"
              v-model="roomNumber"
              type="text"
              class="room-input"
              placeholder="例如：101, 102, 201..."
              maxlength="10"
              @keyup.enter="navigateToRoom"
              @input="validateRoomNumber"
              :class="{ 'error': hasError }"
            />
            <button 
              @click="navigateToRoom" 
              class="confirm-btn"
              :disabled="!isValidRoom || isNavigating"
            >
              <span v-if="isNavigating" class="loading-spinner">⏳</span>
              <span v-else>确认</span>
            </button>
          </div>
        </div>
        
        <!-- 错误提示 -->
        <div v-if="errorMessage" class="error-message">
          {{ errorMessage }}
        </div>
        
        <!-- 房间号提示 -->
        <div class="room-hints">
          <p class="hint-title">可用房间：</p>
          <div class="room-list">
            <span 
              v-for="room in availableRooms" 
              :key="room"
              class="room-tag"
              @click="selectRoom(room)"
            >
              {{ room }}
            </span>
          </div>
        </div>
      </div>

      <!-- 额外服务提示 -->
      <div class="service-info">
        <div class="service-item">
          <span class="service-icon">🌡️</span>
          <span class="service-text">智能温控</span>
        </div>
        <div class="service-item">
          <span class="service-icon">💨</span>
          <span class="service-text">多档风速</span>
        </div>
        <div class="service-item">
          <span class="service-icon">💰</span>
          <span class="service-text">实时计费</span>
        </div>
        <div class="service-item">
          <span class="service-icon">📱</span>
          <span class="service-text">远程控制</span>
        </div>
      </div>
    </div>

    <!-- 背景装饰 -->
    <div class="bg-decoration">
      <div class="floating-icon" style="--delay: 0s">❄️</div>
      <div class="floating-icon" style="--delay: 1s">🌡️</div>
      <div class="floating-icon" style="--delay: 2s">💨</div>
      <div class="floating-icon" style="--delay: 3s">⭐</div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'WelcomePage',
  data() {
    return {
      roomNumber: '',
      errorMessage: '',
      hasError: false,
      isNavigating: false,
      availableRooms: ['101', '102', '103', '201', '202'],
    };
  },
  computed: {
    isValidRoom() {
      return this.roomNumber.trim().length >= 3 && /^\d+$/.test(this.roomNumber.trim());
    }
  },
  methods: {
    validateRoomNumber() {
      const room = this.roomNumber.trim();
      this.hasError = false;
      this.errorMessage = '';
      
      if (room.length > 0) {
        if (!/^\d+$/.test(room)) {
          this.hasError = true;
          this.errorMessage = '房间号只能包含数字';
        } else if (room.length < 3) {
          this.hasError = true;
          this.errorMessage = '房间号至少需要3位数字';
        }
      }
    },
    
    selectRoom(room) {
      this.roomNumber = room;
      this.validateRoomNumber();
    },
    
    async navigateToRoom() {
      if (!this.isValidRoom) {
        this.hasError = true;
        this.errorMessage = '请输入有效的房间号';
        return;
      }
      
      this.isNavigating = true;
      this.errorMessage = '';
      
      try {
        // 模拟检查房间是否存在的API调用
        await this.checkRoomExists(this.roomNumber);
        
        // 跳转到对应的空调控制面板
        this.$router.push(`/aircon/${this.roomNumber}`);
        
      } catch (error) {
        this.hasError = true;
        this.errorMessage = error.message || '房间不存在或暂时无法访问';
      } finally {
        this.isNavigating = false;
      }
    },
    
    async checkRoomExists(roomNumber) {
      // 模拟API调用延迟
      await new Promise(resolve => setTimeout(resolve, 500));
      
      // 这里可以调用真实的API检查房间是否存在
      // 示例：检查房间号是否在可用房间列表中
      if (!this.availableRooms.includes(roomNumber)) {
        throw new Error(`房间 ${roomNumber} 不存在或暂未开放`);
      }
      
      return true;
    }
  },
  mounted() {
    // 页面加载时聚焦到输入框
    this.$nextTick(() => {
      const input = document.getElementById('roomNumber');
      if (input) {
        input.focus();
      }
    });
  }
};
</script>

<style scoped>
.welcome-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  position: relative;
  overflow: hidden;
}

.welcome-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 20px;
  padding: 40px;
  max-width: 500px;
  width: 100%;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  text-align: center;
  position: relative;
  z-index: 1;
}

/* 酒店头部 */
.hotel-header {
  margin-bottom: 30px;
}

.hotel-logo {
  font-size: 4rem;
  margin-bottom: 10px;
}

.hotel-name {
  color: #2c3e50;
  font-size: 2.5rem;
  font-weight: 600;
  margin: 0 0 5px 0;
  background: linear-gradient(45deg, #667eea, #764ba2);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hotel-subtitle {
  color: #7f8c8d;
  font-size: 1rem;
  margin: 0;
  font-style: italic;
}

/* 欢迎内容 */
.welcome-content {
  margin-bottom: 30px;
}

.welcome-title {
  color: #2c3e50;
  font-size: 1.8rem;
  font-weight: 500;
  margin-bottom: 15px;
}

.welcome-message {
  color: #5a6c7d;
  font-size: 1rem;
  line-height: 1.6;
  margin: 0;
}

/* 房间输入区域 */
.room-input-section {
  margin-bottom: 30px;
}

.input-group {
  margin-bottom: 15px;
}

.input-label {
  display: block;
  color: #2c3e50;
  font-size: 1.1rem;
  font-weight: 500;
  margin-bottom: 15px;
}

.input-container {
  display: flex;
  gap: 10px;
  align-items: center;
}

.room-input {
  flex: 1;
  padding: 15px 20px;
  border: 2px solid #e1e8ed;
  border-radius: 12px;
  font-size: 1.1rem;
  transition: all 0.3s ease;
  background: #f8f9fa;
}

.room-input:focus {
  outline: none;
  border-color: #667eea;
  background: white;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.room-input.error {
  border-color: #e74c3c;
  background: #fdf2f2;
}

.confirm-btn {
  padding: 15px 25px;
  background: linear-gradient(45deg, #667eea, #764ba2);
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 1.1rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  min-width: 80px;
}

.confirm-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(102, 126, 234, 0.3);
}

.confirm-btn:disabled {
  background: #bdc3c7;
  cursor: not-allowed;
  transform: none;
}

.loading-spinner {
  display: inline-block;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* 错误信息 */
.error-message {
  color: #e74c3c;
  font-size: 0.9rem;
  margin-top: 8px;
  padding: 8px 12px;
  background: #fdf2f2;
  border-radius: 6px;
  border-left: 3px solid #e74c3c;
}

/* 房间提示 */
.room-hints {
  margin-top: 20px;
  text-align: left;
}

.hint-title {
  color: #5a6c7d;
  font-size: 0.9rem;
  margin-bottom: 10px;
}

.room-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.room-tag {
  background: #ecf0f1;
  color: #2c3e50;
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.room-tag:hover {
  background: #667eea;
  color: white;
  transform: translateY(-1px);
}

/* 服务信息 */
.service-info {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 15px;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #ecf0f1;
}

.service-item {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #5a6c7d;
  font-size: 0.9rem;
}

.service-icon {
  font-size: 1.2rem;
}

/* 背景装饰 */
.bg-decoration {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  overflow: hidden;
}

.floating-icon {
  position: absolute;
  font-size: 2rem;
  opacity: 0.1;
  animation: float 6s ease-in-out infinite;
  animation-delay: var(--delay);
}

.floating-icon:nth-child(1) { top: 20%; left: 10%; }
.floating-icon:nth-child(2) { top: 60%; right: 15%; }
.floating-icon:nth-child(3) { bottom: 30%; left: 20%; }
.floating-icon:nth-child(4) { top: 40%; right: 30%; }

@keyframes float {
  0%, 100% { transform: translateY(0px) rotate(0deg); }
  50% { transform: translateY(-20px) rotate(10deg); }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .welcome-card {
    padding: 30px 20px;
    margin: 10px;
  }
  
  .hotel-name {
    font-size: 2rem;
  }
  
  .welcome-title {
    font-size: 1.5rem;
  }
  
  .service-info {
    grid-template-columns: 1fr;
  }
  
  .input-container {
    flex-direction: column;
  }
  
  .confirm-btn {
    width: 100%;
  }
}
</style>