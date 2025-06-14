<template>
  <div class="ac-panel-container">
    <div class="ACPanel">
      <!-- 房间信息显示 -->
      <div class="room-info">
        <h2>房间 {{ currentRoomNumber }} 空调控制面板</h2>
        <div v-if="connectionStatus" class="connection-status" :class="connectionStatus">
          {{ connectionStatusText }}
        </div>
      </div>

      <div class="display-area">
        <div class="temperature-display">
          <div class="current-temp">
            房间: <strong>{{ roomTemperature.toFixed(1) }}</strong> °C
          </div>
          <div class="target-temp">
            设定: <strong>{{ isOn ? targetTemperature : '--' }}</strong> °C
          </div>
        </div>
        <div class="status-display">
          <div>模式: <strong>{{ displayMode }}</strong></div>
          <div>风速: <strong>{{ isOn ? displayFanSpeed : '关闭' }}</strong></div>
        </div>
        <div class="cost-display">
          费用: <strong>{{ cost.toFixed(2) }}</strong> 元
        </div>
      </div>

      <div class="controls-area">
        <button @click="togglePower" :class="{ active: isOn }" class="power-btn" :disabled="isRequesting">
          {{ isRequesting ? '请求中...' : (isOn ? '关机' : '开机') }}
        </button>

        <div v-if="isOn" class="active-controls">
          <div class="control-group">
            <label>模式:</label>
            <button @click="setMode('cool')" :class="{ active: currentMode === 'cool' }" :disabled="isRequesting">制冷</button>
            <button @click="setMode('heat')" :class="{ active: currentMode === 'heat' }" :disabled="isRequesting">制热</button>
          </div>

          <div class="control-group">
            <label>温度调节:</label>
            <button @click="changeTemperature('decrease')" :disabled="!canDecreaseTemp || isRequesting">-</button>
            <span>{{ targetTemperature }} °C</span>
            <button @click="changeTemperature('increase')" :disabled="!canIncreaseTemp || isRequesting">+</button>
          </div>

          <div class="control-group">
            <label>风速:</label>
            <button @click="setFanSpeed('low')" :class="{ active: currentFanSpeed === 'low' }" :disabled="isRequesting">低</button>
            <button @click="setFanSpeed('medium')" :class="{ active: currentFanSpeed === 'medium' }" :disabled="isRequesting">中</button>
            <button @click="setFanSpeed('high')" :class="{ active: currentFanSpeed === 'high' }" :disabled="isRequesting">高</button>
          </div>
        </div>
      </div>

      <div v-if="logMessages.length" class="log-area">
        <strong>操作记录:</strong>
        <ul>
          <li v-for="(msg, index) in logMessages" :key="index">{{ msg }}</li>
        </ul>
      </div>

      <!-- 错误信息显示 -->
      <div v-if="errorMessage" class="error-message">
        {{ errorMessage }}
      </div>
    </div>
  </div>
</template>

<script>
import api from '../api.js';

const MODE_COOL = 'cool';
const MODE_HEAT = 'heat';
const FAN_LOW = 'low';
const FAN_MEDIUM = 'medium';
const FAN_HIGH = 'high';

const DEFAULT_TEMP = 25;
const TEMP_RANGES = {
  [MODE_COOL]: { min: 18, max: 25 }, // 制冷模式：18-25度
  [MODE_HEAT]: { min: 26, max: 30 },  // 制热模式：26-30度
};

const getModeByTargetTemperature = (targetTemp) => {
  if (targetTemp >= 26 && targetTemp <= 30) {
    return MODE_HEAT;
  } else if (targetTemp >= 18 && targetTemp <= 25) {
    return MODE_COOL;
  } else {
    // 超出范围时的默认处理
    return targetTemp > 25 ? MODE_HEAT : MODE_COOL;
  }
};

// 耗电标准 (度/分钟) - 保持前端模拟逻辑
const POWER_CONSUMPTION_RATE = {
  [FAN_HIGH]: 1,
  [FAN_MEDIUM]: 0.5,
  [FAN_LOW]: 1 / 3
};
const COST_PER_KWH = 1;

// 温度变化基准值 - 保持前端模拟逻辑
const DEBUG_FACTOR = 1;
const TEMP_CHANGE_RATE_MEDIUM = 0.5 * DEBUG_FACTOR;
const TEMP_CHANGE_RATES = {
  [FAN_HIGH]: TEMP_CHANGE_RATE_MEDIUM * 1.2,
  [FAN_MEDIUM]: TEMP_CHANGE_RATE_MEDIUM,
  [FAN_LOW]: TEMP_CHANGE_RATE_MEDIUM * 0.8
};

const NATURAL_TEMP_CHANGE_RATE = 0.3 * DEBUG_FACTOR / 60;
const TEMP_RESTART_THRESHOLD = 1;

export default {
  name: 'ACPanel',
  props: {
    roomNumber: {
      type: String,
      default: '101'
    }
  },
  data() {
    return {
      isOn: false,
      currentMode: MODE_COOL,
      targetTemperature: DEFAULT_TEMP,
      currentFanSpeed: FAN_MEDIUM,
      roomTemperature: DEFAULT_TEMP,
      cost: 0,

      // 内部状态
      isSupplyingAir: false,
      lastTempRequestTime: 0,
      tempChangeTimeoutId: null,
      simulationIntervalId: null,
      costCalculationIntervalId: null,
      logMessages: [],
      isFirstStart: true,

      // 后端通信相关
      isRequesting: false,
      errorMessage: '',
      connectionStatus: 'connecting',
      currentRoomNumber: '101',

      // 记录上次上报的温度
      lastReportedTemperature: DEFAULT_TEMP,
      temperatureReportThreshold: 0.01,
      
      // 状态同步相关
      isLoadingStatus: false,
      hasLoadedInitialStatus: false,
      
      // 新增：后端实际状态跟踪
      backendAcState: 0, // 后端实际的空调状态 (0:关机, 1:运行中, 2:待机)
      lastBackendStateCheck: 0, // 上次检查后端状态的时间
      backendStateCheckInterval: 1000, // 检查间隔 (3秒)

      shouldSkipInitialTurnOn: false, // 是否应该跳过初始开机请求
      hasUserAdjustedTemperature: false, // 用户是否已调整过温度
    
    };
  },
  computed: {
    displayMode() {
      if (!this.isOn) return '关机';
      return this.currentMode === MODE_COOL ? '制冷' : '制热';
    },
    displayFanSpeed() {
      if (!this.isOn) return '关闭';
      
      // 新增：显示实际送风状态
      if (this.backendAcState === 1) {
        // 后端确认正在送风
        if (this.currentFanSpeed === FAN_LOW) return '低风';
        if (this.currentFanSpeed === FAN_MEDIUM) return '中风';
        if (this.currentFanSpeed === FAN_HIGH) return '高风';
        return '送风中';
      } else if (this.backendAcState === 2) {
        // 后端显示待机状态
        return '待机';
      } else {
        // 后端显示关机或其他状态
        return '停风';
      }
    },
    currentTempRange() {
      return TEMP_RANGES[this.currentMode];
    },
    canDecreaseTemp() {
      if (!this.isOn) return false;
      // 修改：制冷模式可以降到18度，制热模式可以降到26度
      return this.targetTemperature > this.currentTempRange.min;
    },
    canIncreaseTemp() {
      if (!this.isOn) return false;
      // 修改：制冷模式可以升到25度，制热模式可以升到30度
      return this.targetTemperature < this.currentTempRange.max;
    },
    shouldCharge() {
      // 新增：只有后端确认正在送风时才计费
      if (!this.isOn || this.backendAcState !== 1) return false;
      if (this.currentMode === MODE_COOL) {
        return this.roomTemperature > this.targetTemperature;
      } else {
        return this.roomTemperature < this.targetTemperature;
      }
    },
    connectionStatusText() {
      switch (this.connectionStatus) {
        case 'connecting':
          return '连接中...';
        case 'connected':
          return '已连接';
        case 'error':
          return '连接失败';
        case 'loading':
          return '加载状态中...';
        default:
          return '';
      }
    },
    // 新增：实际是否在送风的计算属性
    isActuallySupplyingAir() {
      return this.isOn && this.backendAcState === 1;
    }
  },
  watch: {
    roomNumber: {
      immediate: true,
      handler(newRoomNumber) {
        if (newRoomNumber) {
          this.currentRoomNumber = newRoomNumber;
          this.initializeRoom();
        }
      }
    }
  },
  methods: {
    async initializeRoom() {
      this.connectionStatus = 'connecting';
      this.errorMessage = '';
      this.hasLoadedInitialStatus = false;
      
      try {
        const roomNum = parseInt(this.currentRoomNumber);
        if (isNaN(roomNum)) {
          throw new Error('无效的房间号');
        }
        
        this.connectionStatus = 'connected';
        this.logToServer(`连接到房间 ${this.currentRoomNumber}`);
        
        // 加载数据库中保存的空调状态
        await this.loadRoomStatusFromDatabase();
        
        // 初始化时上报当前温度
        await this.reportCurrentTemperature(this.roomTemperature);
        await this.target
        
        // 初始化时启动温度模拟（无论空调是否开启）
        this.startSimulations();
        
        this.hasLoadedInitialStatus = true;
      } catch (error) {
        this.connectionStatus = 'error';
        this.errorMessage = `连接房间 ${this.currentRoomNumber} 失败: ${error.message}`;
        console.error('房间初始化失败:', error);
      }
    },

    // 新增：检查后端实际空调状态
    async checkBackendAcState() {
      try {
        const response = await api.getRoomStatus(this.currentRoomNumber);
        const roomData = response.data;
        
        const previousState = this.backendAcState;
        this.backendAcState = roomData.acState || 0;
        
        // 如果状态发生变化，记录日志
        if (previousState !== this.backendAcState) {
          const stateText = this.getAcStateText(this.backendAcState);
          const previousStateText = this.getAcStateText(previousState);
          this.logToServer(`🔄 后端状态变化: ${previousStateText} → ${stateText}`);
          
          // 如果从送风变为待机，可能是被调度暂停
          if (previousState === 1 && this.backendAcState === 2) {
            this.logToServer(`⏸️  送风服务被暂停 (可能因调度限制)`);
          }
          // 如果从待机变为送风，可能是重新获得服务
          else if (previousState === 2 && this.backendAcState === 1) {
            this.logToServer(`▶️  重新获得送风服务`);
          }
        }
        
        this.lastBackendStateCheck = Date.now();
        return this.backendAcState;
        
      } catch (error) {
        console.warn('检查后端空调状态失败:', error);
        // 检查失败时不改变当前状态
        return this.backendAcState;
      }
    },

    // 新增：获取空调状态文本描述
    getAcStateText(acState) {
      switch (acState) {
        case 0: return '关机';
        case 1: return '运行中';
        case 2: return '待机';
        default: return '未知';
      }
    },

    // 从数据库加载房间状态
    async loadRoomStatusFromDatabase() {
      this.isLoadingStatus = true;
      this.connectionStatus = 'loading';
      
      try {
        console.log(`📡 正在从数据库加载房间 ${this.currentRoomNumber} 的状态...`);
        
        const response = await api.getRoomStatus(this.currentRoomNumber);
        const roomData = response.data;
        
        console.log('🔍 从数据库获取的房间状态:', roomData);
        
        // 解析并应用状态
        this.applyRoomStatusFromDatabase(roomData);
        
        this.logToServer(`✅ 已加载数据库状态 - 空调: ${this.isOn ? '开启' : '关闭'}, 温度: ${this.targetTemperature}°C, 风速: ${this.currentFanSpeed}`);
        
      } catch (error) {
        console.warn('⚠️ 加载房间状态失败，使用默认状态:', error);
        this.logToServer(`⚠️ 无法加载数据库状态，使用默认设置: ${error.message}`);
        
        // 加载失败时使用默认状态
        this.resetToDefaultState();
      } finally {
        this.isLoadingStatus = false;
        this.connectionStatus = 'connected';
      }
    },

    // 应用从数据库获取的状态
    applyRoomStatusFromDatabase(roomData) {
      // 映射空调状态
      const mapAcState = (acState) => {
        switch (acState) {
          case 0: return false; // 关机
          case 1: return true;  // 运行中
          case 2: return true;  // 待机（前端视为开启但未送风）
          default: return false;
        }
      };

      // 映射风速
      const mapFanSpeed = (speed) => {
        if (!speed) return FAN_MEDIUM;
        const speedLower = speed.toLowerCase();
        if (['low', 'medium', 'high'].includes(speedLower)) {
          return speedLower;
        }
        return FAN_MEDIUM;
      };

      // 应用状态
      this.isOn = mapAcState(roomData.acState);
      this.targetTemperature = roomData.targetTempera || DEFAULT_TEMP;
      this.roomTemperature = roomData.currentTempera || DEFAULT_TEMP;
      this.currentFanSpeed = mapFanSpeed(roomData.currentSpeed);
      this.backendAcState = roomData.acState || 0;
      
      // 修改：根据目标温度确定模式
      this.currentMode = getModeByTargetTemperature(this.targetTemperature);
      
      // 新增：检查是否应该跳过初始开机请求
      if (this.isOn && Math.abs(this.roomTemperature - this.targetTemperature) <= 0.2) {
        this.shouldSkipInitialTurnOn = true;
        this.logToServer(`🎯 当前温度(${this.roomTemperature.toFixed(1)}°C)已接近目标温度(${this.targetTemperature}°C)，跳过开机请求`);
      }

      // 确保温度在有效范围内
      this.validateAndAdjustTemperature();

      // 根据后端状态和温度差设置前端送风状态
      if (this.isOn) {
        if (roomData.acState === 1) { // 运行中
          this.isSupplyingAir = true;
        } else if (roomData.acState === 2) { // 待机
          this.isSupplyingAir = false;
        } else {
          // 根据温度差和跳过标志判断
          this.isSupplyingAir = !this.shouldSkipInitialTurnOn && this.shouldStartAirSupply();
        }
      } else {
        this.isSupplyingAir = false;
      }

      console.log('✅ 状态应用完成:', {
        isOn: this.isOn,
        mode: this.currentMode,
        targetTemp: this.targetTemperature,
        currentTemp: this.roomTemperature,
        fanSpeed: this.currentFanSpeed,
        backendAcState: this.backendAcState,
        isSupplyingAir: this.isSupplyingAir,
        shouldSkipInitialTurnOn: this.shouldSkipInitialTurnOn
      });
    },

    // 验证并调整温度到有效范围
    validateAndAdjustTemperature() {
      const range = this.currentTempRange;
      let adjusted = false;
      
      if (this.targetTemperature < range.min) {
        console.warn(`目标温度 ${this.targetTemperature}°C 低于${this.currentMode}模式最小值，调整为 ${range.min}°C`);
        this.targetTemperature = range.min;
        adjusted = true;
      } else if (this.targetTemperature > range.max) {
        console.warn(`目标温度 ${this.targetTemperature}°C 高于${this.currentMode}模式最大值，调整为 ${range.max}°C`);
        this.targetTemperature = range.max;
        adjusted = true;
      }
      
      if (adjusted) {
        this.logToServer(`⚠️ 目标温度已调整至${this.currentMode}模式范围内: ${this.targetTemperature}°C`);
      }
    },

    // 判断是否应该开始送风
    shouldStartAirSupply() {
      if (!this.isOn) return false;
      
      if (this.currentMode === MODE_COOL) {
        return this.roomTemperature > this.targetTemperature + 0.5;
      } else {
        return this.roomTemperature < this.targetTemperature - 0.5;
      }
    },

    // 重置为默认状态
    resetToDefaultState() {
      this.isOn = false;
      this.targetTemperature = DEFAULT_TEMP;
      this.currentMode = getModeByTargetTemperature(DEFAULT_TEMP); // 根据默认温度确定模式
      this.currentFanSpeed = FAN_MEDIUM;
      this.roomTemperature = DEFAULT_TEMP;
      this.isSupplyingAir = false;
      this.backendAcState = 0;
      this.cost = 0;
    },

    async sendBackendRequest(requestFunc, successMessage, errorPrefix) {
      if (this.isRequesting) return false;
      
      this.isRequesting = true;
      this.errorMessage = '';
      
      try {
        await requestFunc();
        if (successMessage) {
          this.logToServer(successMessage);
        }
        return true;
      } catch (error) {
        const message = error.response?.data?.error || error.message || '请求失败';
        this.errorMessage = `${errorPrefix}: ${message}`;
        this.logToServer(`${errorPrefix}: ${message}`);
        console.error(`${errorPrefix}:`, error);
        return false;
      } finally {
        this.isRequesting = false;
      }
    },

    // 向后端通知送风状态变化
    async notifyAirSupplyChange(isSupplying, reason) {
      try {
        if (isSupplying) {
          console.log(`通知后端开始送风: roomNumber=${this.currentRoomNumber}, 原因: ${reason}`);
          await api.turnOnAC(this.currentRoomNumber);
          this.logToServer(`[后端通知] 开始送风 - ${reason}`);
        } else {
          console.log(`通知后端停止送风: roomNumber=${this.currentRoomNumber}, 原因: ${reason}`);
          await api.turnOffAC(this.currentRoomNumber);
          this.logToServer(`[后端通知] 停止送风 - ${reason}`);
        }
      } catch (error) {
        // 送风状态通知失败不影响主要功能，只记录错误
        console.error('送风状态通知失败:', error);
        this.logToServer(`[后端通知失败] ${isSupplying ? '开始' : '停止'}送风通知失败: ${error.message}`);
      }
    },

    logToServer(message) {
      const timestamp = new Date().toLocaleTimeString();
      this.logMessages.unshift(`[${timestamp}] ${message}`);
      if (this.logMessages.length > 15) { // 增加日志数量以便观察调度情况
        this.logMessages.pop();
      }
      console.log(`[TO SERVER] 房间${this.currentRoomNumber}: ${message}`);
    },

    async togglePower() {
      const willTurnOn = !this.isOn;
      
      // 如果是开机操作且还未加载过初始状态，先加载数据库状态
      if (willTurnOn && !this.hasLoadedInitialStatus) {
        try {
          await this.loadRoomStatusFromDatabase();
          
          // 如果数据库中空调本来就是开启状态，直接返回
          if (this.isOn) {
            this.logToServer('空调已在开启状态，无需重复开机');
            return;
          }
        } catch (error) {
          console.warn('开机前加载状态失败，继续执行开机操作:', error);
        }
      }
      
      // 新增：开机时检查温度是否相等
      if (willTurnOn) {
        const temperatureDiff = Math.abs(this.roomTemperature - this.targetTemperature);
        
        if (temperatureDiff <= 0.2) {
          // 温度已相等，跳过开机请求但设置状态
          this.isOn = true;
          this.shouldSkipInitialTurnOn = true;
          this.isSupplyingAir = false;
          
          this.logToServer(`⚡ 开机但跳过送风请求 - 当前温度(${this.roomTemperature.toFixed(1)}°C)已接近目标温度(${this.targetTemperature}°C)`);
          this.logToServer(`💡 空调已开启待机模式，调整目标温度后将自动开始送风`);
          
          // 开机时启动模拟
          this.startSimulations();
          return;
        }
      }
      
      const success = await this.sendBackendRequest(
        async () => {
          if (willTurnOn) {
            await api.turnOnAC(this.currentRoomNumber);
          } else {
            await api.turnOffAC(this.currentRoomNumber);
          }
        },
        null,
        willTurnOn ? '开机失败' : '关机失败'
      );

      if (success) {
        this.isOn = willTurnOn;
        
        if (this.isOn) {
          // 开机时如果还没有设置过，使用默认值
          if (!this.hasLoadedInitialStatus) {
            this.currentMode = MODE_COOL;
            this.targetTemperature = DEFAULT_TEMP;
            this.currentFanSpeed = FAN_MEDIUM;
          }

          if (this.isFirstStart || !this.isSupplyingAir) {
            this.isSupplyingAir = true;
            this.logToServer(`开机。模式: ${this.displayMode}, 目标温度: ${this.targetTemperature}°C, 风速: ${this.displayFanSpeed}`);
          }

          this.isFirstStart = false;
          // 开机时启动模拟
          this.startSimulations();
        } else {
          // 关机时停止送风，但不停止温度模拟
          this.isSupplyingAir = false;
          this.backendAcState = 0;
          this.shouldSkipInitialTurnOn = false; // 重置跳过标志
          this.hasUserAdjustedTemperature = false; // 重置用户调整标志
          this.logToServer('关机。温度将自然回升至室外温度。');
        }
      }
    },

  

    async setFanSpeed(speed) {
      if (!this.isOn || this.currentFanSpeed === speed) return;
      
      const success = await this.sendBackendRequest(
        async () => {
          console.log(`发送风速设置请求: roomNumber=${this.currentRoomNumber}, speed="${speed}"`);
          await api.setAcSpeed(this.currentRoomNumber, speed);
        },
        null,
        '设置风速失败'
      );

      if (success) {
        this.currentFanSpeed = speed;
        this.logToServer(`设置风速: ${speed} (等待调度器分配送风服务)`);
        
        // 风速变更会触发新的送风请求，可能需要等待调度
        // 立即检查一次后端状态
        setTimeout(() => this.checkBackendAcState(), 1000);
      }
    },

    async changeTemperature(direction) {
      if (!this.isOn) return;

      const now = Date.now();
      if (this.tempChangeTimeoutId) {
        clearTimeout(this.tempChangeTimeoutId);
      }

      const previousTemp = this.targetTemperature;
      const previousMode = this.currentMode;
      let tempTarget = this.targetTemperature;
      
      if (direction === 'increase' && this.canIncreaseTemp) {
        tempTarget++;
      } else if (direction === 'decrease' && this.canDecreaseTemp) {
        tempTarget--;
      }
      
      // 重构：根据新的目标温度重新确定模式
      const newMode = getModeByTargetTemperature(tempTarget);
      
      // 检查是否需要跨模式调节
      if (newMode !== this.currentMode) {
        // 跨模式调节，需要检查是否在新模式的有效范围内
        const newRange = TEMP_RANGES[newMode];
        
        if (tempTarget >= newRange.min && tempTarget <= newRange.max) {
          // 在新模式范围内，允许调节
          this.targetTemperature = tempTarget;
          this.currentMode = newMode;
          
          this.logToServer(`🔄 模式切换: ${previousMode === MODE_COOL ? '制冷' : '制热'} → ${newMode === MODE_COOL ? '制冷' : '制热'} (目标温度: ${tempTarget}°C)`);
        } else {
          // 不在新模式范围内，阻止调节
          this.logToServer(`❌ 无法调节至 ${tempTarget}°C - 超出${newMode === MODE_COOL ? '制冷' : '制热'}模式范围(${newRange.min}-${newRange.max}°C)`);
          return;
        }
      } else {
        // 同模式内调节
        this.targetTemperature = tempTarget;
      }

      // 标记用户已调整温度
      if (!this.hasUserAdjustedTemperature) {
        this.hasUserAdjustedTemperature = true;
        this.logToServer(`📝 用户首次调整目标温度: ${previousTemp}°C → ${this.targetTemperature}°C`);
      }

      this.tempChangeTimeoutId = setTimeout(async () => {
        // 再次验证温度范围
        this.validateAndAdjustTemperature();
        
        const success = await this.sendBackendRequest(
          async () => {
            console.log(`发送温度设置请求: roomNumber=${this.currentRoomNumber}, temperature=${this.targetTemperature}`);
            await api.setAcTargetTemperature(this.currentRoomNumber, this.targetTemperature);
          },
          null,
          '设置温度失败'
        );

        if (success) {
          // 检查是否需要发送开机请求
          await this.checkAndSendTurnOnRequestIfNeeded();
          
          const tempChange = this.targetTemperature - previousTemp;
          const modeText = this.currentMode === MODE_COOL ? '制冷' : '制热';
          this.logToServer(`调节温度: ${previousTemp}°C → ${this.targetTemperature}°C (${tempChange > 0 ? '+' : ''}${tempChange}°C) [${modeText}模式]`);
        }
        
        this.lastTempRequestTime = 0;
      }, 1000);

      if (now - this.lastTempRequestTime < 1000) {
        this.logToServer(`温度指令 (${this.targetTemperature}°C) 已缓存，等待1秒后发送最终值`);
      }
      this.lastTempRequestTime = now;
    },
    
    async checkAndSendTurnOnRequestIfNeeded() {
      // 只有在跳过了初始开机且用户已调整温度的情况下才检查
      if (!this.shouldSkipInitialTurnOn || !this.hasUserAdjustedTemperature) {
        return;
      }
      
      const temperatureDiff = Math.abs(this.roomTemperature - this.targetTemperature);
      
      // 如果温度差异超过阈值，发送开机请求
      if (temperatureDiff > 0.5) {
        try {
          this.logToServer(`🚀 温度差异(${temperatureDiff.toFixed(1)}°C)超过阈值，发送开机请求开始调温`);
          
          await api.turnOnAC(this.currentRoomNumber);
          
          // 重置跳过标志，表示已经正式开始工作
          this.shouldSkipInitialTurnOn = false;
          this.isSupplyingAir = true;
          
          this.logToServer(`✅ 开机请求已发送，开始调节至目标温度 ${this.targetTemperature}°C`);
          
          // 检查后端状态
          setTimeout(() => this.checkBackendAcState(), 1000);
          
        } catch (error) {
          console.error('发送开机请求失败:', error);
          this.logToServer(`❌ 开机请求失败: ${error.message}`);
        }
      } else {
        this.logToServer(`🎯 目标温度调整后仍接近当前温度(差异${temperatureDiff.toFixed(1)}°C)，继续待机`);
      }
    },

    // 新增：重置送风请求状态
    resetAirSupplyRequestState() {
      this.isWaitingForAirSupply = false;
      this.airSupplyRequestCount = 0;
      this.hasPendingAirSupplyRequest = false;
    },

    async reportCurrentTemperature(temperature) {
      try {
        console.log(`上报当前温度: roomNumber=${this.currentRoomNumber}, temperature=${temperature.toFixed(2)}`);
        await api.setAcCurrentTemperature(this.currentRoomNumber, temperature);
        this.lastReportedTemperature = temperature;
      } catch (error) {
        console.error('温度上报失败:', error);
      }
    },

    startSimulations() {
      // 如果已经在运行，不要重复启动
      if (this.simulationIntervalId) return;
      
      this.simulationIntervalId = setInterval(async () => {
        // 定期检查后端状态
        const now = Date.now();
        if (now - this.lastBackendStateCheck > this.backendStateCheckInterval) {
          await this.checkBackendAcState();
        }

        if (this.isOn) {
          // 根据后端实际状态决定温度变化逻辑
          if (this.isActuallySupplyingAir) {
            // 后端确认正在送风，重置请求计数
            this.resetAirSupplyRequestState();
            
            // 修复：正确的制冷制热逻辑
            this.simulateAirConditioningEffect();
          } else {
            // 空调开启但后端显示未送风（可能被调度暂停），执行自然温度变化
            this.simulateNaturalTemperatureChange();
            
            // 智能请求送风服务（带冷却时间和重试限制）
            if (this.shouldRequestAirSupply()) {
              await this.smartRequestAirSupplyService();
            }
          }
        } else {
          // 空调关闭，执行自然温度变化并重置请求状态
          this.simulateNaturalTemperatureChange();
          this.resetAirSupplyRequestState();
        }

        // 限制温度范围
        this.roomTemperature = Math.max(10, Math.min(this.roomTemperature, 40));

        // 检查温度是否有显著变化，如果有则上报给后端
        const temperatureChange = Math.abs(this.roomTemperature - this.lastReportedTemperature);
        if (temperatureChange >= this.temperatureReportThreshold) {
          this.reportCurrentTemperature(this.roomTemperature);
        }
      }, 1000);

      // 费用计算逻辑：只有实际送风时才计费
      if (!this.costCalculationIntervalId) {
        this.costCalculationIntervalId = setInterval(() => {
          if (this.shouldCharge) {
            const consumptionPerSecond = POWER_CONSUMPTION_RATE[this.currentFanSpeed] / 60;
            this.cost += consumptionPerSecond * COST_PER_KWH;
          }
        }, 1000);
      }
    },
    
    async smartRequestAirSupplyService() {
      const now = Date.now();
      
      // 再次检查温度偏离，确保确实需要送风
      const temperatureDeviation = Math.abs(this.roomTemperature - this.targetTemperature);
      if (temperatureDeviation <= TEMP_RESTART_THRESHOLD) {
        this.logToServer(`🚫 温度偏离不足(${temperatureDeviation.toFixed(1)}°C)，取消送风请求`);
        return;
      }
      
      // 设置防重复请求标志
      this.hasPendingAirSupplyRequest = true;
      this.isWaitingForAirSupply = true;
      this.lastAirSupplyRequest = now;
      this.airSupplyRequestCount++;
      
      try {
        console.log(`🔄 请求送风服务 (第${this.airSupplyRequestCount}次尝试)`);
        this.logToServer(`🔄 重新请求送风服务 (温度偏离${temperatureDeviation.toFixed(1)}°C, 第${this.airSupplyRequestCount}次)`);
        
        await api.turnOnAC(this.currentRoomNumber);
        
        // 请求发出后，等待一段时间让调度器处理
        setTimeout(async () => {
          await this.checkBackendAcState();
          
          // 检查请求是否成功
          if (this.isActuallySupplyingAir) {
            this.logToServer(`✅ 送风请求成功，已重新开始送风`);
            this.resetAirSupplyRequestState();
          } else {
            // 请求失败或仍在等待，清除待处理标志但保留其他状态
            this.hasPendingAirSupplyRequest = false;
            
            if (this.airSupplyRequestCount >= this.maxRequestAttempts) {
              this.logToServer(`⚠️ 达到最大重试次数(${this.maxRequestAttempts})，将等待${this.airSupplyRequestCooldown * 2 / 1000}秒后重试`);
            } else {
              this.logToServer(`⏳ 送风请求已发出，等待调度器分配 (${this.airSupplyRequestCooldown / 1000}秒冷却)`);
            }
          }
        }, 10000); // 等待3秒让调度器处理
        
      } catch (error) {
        console.error('请求送风服务失败:', error);
        this.logToServer(`❌ 送风请求失败: ${error.message}`);
        this.hasPendingAirSupplyRequest = false;
      }
    },

    async simulateAirConditioningEffect() {
      const rate = TEMP_CHANGE_RATES[this.currentFanSpeed] / 60;
      const currentTemp = this.roomTemperature;
      const targetTemp = this.targetTemperature;
      
      // 重构：温度变化方向总是向目标温度方向，不依赖模式
      if (Math.abs(currentTemp - targetTemp) < 0.01) {
        // 已经非常接近目标温度，不需要调整
        return;
      }
      
      if (currentTemp > targetTemp) {
        // 当前温度高于目标温度，降温
        this.roomTemperature = Math.max(currentTemp - rate, targetTemp);
        
        // 到达目标温度时停止送风
        if (this.roomTemperature <= targetTemp) {
          this.roomTemperature = targetTemp;
          this.logToServer(`降温达到目标温度 ${targetTemp}°C，停止送风`);
          await this.sendStopAirSupplyRequest('达到目标温度');
        }
      } else if (currentTemp < targetTemp) {
        // 当前温度低于目标温度，升温
        this.roomTemperature = Math.min(currentTemp + rate, targetTemp);
        
        // 到达目标温度时停止送风
        if (this.roomTemperature >= targetTemp) {
          this.roomTemperature = targetTemp;
          this.logToServer(`升温达到目标温度 ${targetTemp}°C，停止送风`);
          await this.sendStopAirSupplyRequest('达到目标温度');
        }
      }
    },

    async sendStopAirSupplyRequest(reason) {
      try {
        console.log(`🛑 向服务器发送停止送风请求: roomNumber=${this.currentRoomNumber}, 原因: ${reason}`);
        
        // 发送关机请求来停止送风
        await api.turnOffAC(this.currentRoomNumber);
        
        this.logToServer(`📤 已向服务器发送停止送风请求 - ${reason}`);
        
        // 稍后检查后端状态确认是否成功停止
        setTimeout(async () => {
          await this.checkBackendAcState();
          
          if (this.backendAcState === 2 || this.backendAcState === 0) {
            this.logToServer(`✅ 服务器确认停止送风成功`);
          } else {
            this.logToServer(`⚠️ 服务器可能未响应停止送风请求`);
          }
        }, 1000);
        
      } catch (error) {
        console.error('发送停止送风请求失败:', error);
        this.logToServer(`❌ 停止送风请求失败: ${error.message}`);
      }
    },

    // 新增：模拟自然温度变化
    simulateNaturalTemperatureChange() {
      const diffToDefault = DEFAULT_TEMP - this.roomTemperature;
      const naturalChangeRate = NATURAL_TEMP_CHANGE_RATE;
      
      if (Math.abs(diffToDefault) > 0.05) {
        // 温度向默认温度(25°C)缓慢变化
        if (diffToDefault > 0) {
          // 当前温度低于25°C，温度上升
          this.roomTemperature = Math.min(
            this.roomTemperature + naturalChangeRate,
            DEFAULT_TEMP
          );
        } else {
          // 当前温度高于25°C，温度下降
          this.roomTemperature = Math.max(
            this.roomTemperature - naturalChangeRate,
            DEFAULT_TEMP
          );
        }
      } else {
        // 温度已接近默认值，直接设为默认温度
        this.roomTemperature = DEFAULT_TEMP;
      }
    },

    async setMode(mode) {
      if (!this.isOn) return;
      
      const previousMode = this.currentMode;
      
      // 检查当前目标温度是否适合新模式
      const targetRange = TEMP_RANGES[mode];
      
      if (this.targetTemperature < targetRange.min || this.targetTemperature > targetRange.max) {
        // 目标温度不在新模式范围内，调整到新模式的合适温度
        const newTargetTemp = this.targetTemperature < targetRange.min ? targetRange.min : targetRange.max;
        
        this.logToServer(`🔄 切换${mode === MODE_COOL ? '制冷' : '制热'}模式，目标温度调整: ${this.targetTemperature}°C → ${newTargetTemp}°C`);
        
        this.currentMode = mode;
        this.targetTemperature = newTargetTemp;
        
        // 发送温度设置请求
        await this.sendBackendRequest(
          async () => {
            await api.setAcTargetTemperature(this.currentRoomNumber, this.targetTemperature);
          },
          null,
          '设置温度失败'
        );
      } else {
        // 目标温度在新模式范围内，直接切换
        this.currentMode = mode;
        this.logToServer(`🔄 切换模式: ${previousMode === MODE_COOL ? '制冷' : '制热'} → ${mode === MODE_COOL ? '制冷' : '制热'}`);
      }
      
      this.checkAndRestartAirSupply();
    },

    // 新增：判断是否需要重新请求送风服务
    shouldRequestAirSupply() {
      const now = Date.now();
      
      // 基本条件检查
      if (!this.isOn || this.isActuallySupplyingAir) return false;
      
      // 如果设置了跳过标志且用户未调整温度，不请求送风
      if (this.shouldSkipInitialTurnOn && !this.hasUserAdjustedTemperature) {
        return false;
      }
      
      // 如果有待处理的请求，不要重复请求
      if (this.hasPendingAirSupplyRequest) return false;
      
      // 检查冷却时间
      if (now - this.lastAirSupplyRequest < this.airSupplyRequestCooldown) {
        return false;
      }
      
      // 检查重试次数限制
      if (this.airSupplyRequestCount >= this.maxRequestAttempts) {
        if (now - this.lastAirSupplyRequest < this.airSupplyRequestCooldown * 2) {
          return false;
        } else {
          this.airSupplyRequestCount = 0;
        }
      }
      
      // 检查温度偏离程度
      const temperatureGap = Math.abs(this.roomTemperature - this.targetTemperature);
      
      
      return temperatureGap > TEMP_RESTART_THRESHOLD;
    },

    // 新增：请求送风服务
    async requestAirSupplyService() {
      try {
        await api.turnOnAC(this.currentRoomNumber);
        this.logToServer(`🔄 重新请求送风服务 (室温偏离目标${TEMP_RESTART_THRESHOLD}°C)`);
        
        // 请求后稍等片刻再检查状态
        setTimeout(() => this.checkBackendAcState(), 1000);
      } catch (error) {
        console.error('请求送风服务失败:', error);
      }
    },

    stopSimulations() {
      if (this.simulationIntervalId) clearInterval(this.simulationIntervalId);
      if (this.costCalculationIntervalId) clearInterval(this.costCalculationIntervalId);
      this.simulationIntervalId = null;
      this.costCalculationIntervalId = null;
    },

    async checkAndRestartAirSupply() {
      if (this.isOn && !this.isActuallySupplyingAir) {
        // 如果设置了跳过标志且用户未调整温度，不要自动请求送风
        if (this.shouldSkipInitialTurnOn && !this.hasUserAdjustedTemperature) {
          return;
        }
        
        // 根据实际温度差判断是否需要送风
        const temperatureGap = Math.abs(this.roomTemperature - this.targetTemperature);
        
        if (temperatureGap > 0.5) { // 温度差超过0.5度才请求送风
          if (this.shouldRequestAirSupply()) {
            await this.smartRequestAirSupplyService();
          }
        }
      }
    }

  },

  mounted() {
    // 组件挂载时会自动调用 initializeRoom
  },

  beforeUnmount() {
    // 组件卸载时才真正停止所有模拟
    this.stopSimulations();
    if (this.tempChangeTimeoutId) clearTimeout(this.tempChangeTimeoutId);
  }
};
</script>

<style scoped>
.ac-panel-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 80vh;
  width: 100%;
}

.ACPanel {
  width: 350px;
  border: 2px solid #ccc;
  border-radius: 10px;
  padding: 20px;
  font-family: Arial, sans-serif;
  background-color: #f9f9f9;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.room-info {
  text-align: center;
  margin-bottom: 15px;
}

.room-info h2 {
  color: #333;
  margin: 0 0 10px 0;
  font-size: 1.3em;
}

.connection-status {
  padding: 5px 10px;
  border-radius: 15px;
  font-size: 0.8em;
  font-weight: bold;
}

.connection-status.connecting {
  background-color: #fff3cd;
  color: #856404;
}

.connection-status.connected {
  background-color: #d4edda;
  color: #155724;
}

.connection-status.error {
  background-color: #f8d7da;
  color: #721c24;
}

.display-area {
  background-color: #e0e0e0;
  padding: 15px;
  border-radius: 8px;
  margin-bottom: 20px;
  text-align: center;
}

.temperature-display {
  display: flex;
  justify-content: space-around;
  margin-bottom: 10px;
  font-size: 1.2em;
}

.current-temp strong,
.target-temp strong {
  font-size: 1.5em;
  color: #333;
}

.status-display {
  display: flex;
  justify-content: space-around;
  font-size: 0.9em;
  color: #555;
  margin-bottom: 10px;
}

.cost-display {
  font-size: 1.1em;
  color: #27ae60;
  font-weight: bold;
}

.controls-area {
  display: flex;
  flex-direction: column;
  align-items: stretch;
}

.controls-area button {
  padding: 10px 15px;
  margin: 5px;
  border: 1px solid #bbb;
  border-radius: 5px;
  background-color: #fff;
  cursor: pointer;
  transition: background-color 0.2s;
}

.controls-area button:hover:not(:disabled) {
  background-color: #3a8a3d;
}

.controls-area button.active {
  background-color: #4CAF50;
  color: white;
  border-color: #4CAF50;
}

.controls-area button:disabled {
  background-color: #eee;
  color: #aaa;
  cursor: not-allowed;
}

.power-btn {
  padding: 12px;
  font-size: 1.1em;
  margin-bottom: 15px;
  background-color: #f8f0ef;
  color: rgb(15, 14, 14);
  border: 1px solid #e74c3c;
  border-radius: 5px;
  box-sizing: border-box;
  cursor: pointer;
  transition: background-color 0.2s;
  text-align: center;
}

.power-btn.active {
  background-color: #2ecc71;
  border-color: #2ecc71;
}

.active-controls .control-group {
  margin-bottom: 15px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.active-controls .control-group label {
  margin-right: 10px;
  font-weight: bold;
  flex-shrink: 0;
}

.active-controls .control-group span {
  font-size: 1.1em;
  min-width: 50px;
  text-align: center;
}

.log-area {
  margin-top: 20px;
  padding: 10px;
  border: 1px dashed #ccc;
  border-radius: 5px;
  font-size: 0.8em;
  max-height: 150px;
  overflow-y: auto;
  background-color: #fdfdfd;
}

.log-area ul {
  list-style-type: none;
  padding: 0;
  margin: 0;
}

.log-area li {
  padding: 2px 0;
  border-bottom: 1px solid #eee;
}

.log-area li:last-child {
  border-bottom: none;
}

.error-message {
  background-color: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
  border-radius: 4px;
  padding: 10px;
  margin-top: 15px;
  font-size: 0.9em;
}
</style>