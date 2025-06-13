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
  [MODE_COOL]: { min: 18, max: 25 },
  [MODE_HEAT]: { min: 25, max: 30 },
};

// 耗电标准 (度/分钟) - 保持前端模拟逻辑
const POWER_CONSUMPTION_RATE = {
  [FAN_HIGH]: 1,
  [FAN_MEDIUM]: 0.5,
  [FAN_LOW]: 1 / 3
};
const COST_PER_KWH = 1;

// 温度变化基准值 - 保持前端模拟逻辑
const DEBUG_FACTOR = 10;
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

      // 新增：记录上次上报的温度
      lastReportedTemperature: DEFAULT_TEMP,
      // 新增：温度变化阈值（0.1度）
      temperatureReportThreshold: 0.1,
    };
  },
  computed: {
    displayMode() {
      if (!this.isOn) return '关机';
      return this.currentMode === MODE_COOL ? '制冷' : '制热';
    },
    displayFanSpeed() {
      if (!this.isOn || !this.isSupplyingAir) return '停风';
      if (this.currentFanSpeed === FAN_LOW) return '低风';
      if (this.currentFanSpeed === FAN_MEDIUM) return '中风';
      if (this.currentFanSpeed === FAN_HIGH) return '高风';
      return '未知';
    },
    currentTempRange() {
      return TEMP_RANGES[this.currentMode];
    },
    canDecreaseTemp() {
      if (!this.isOn) return false;
      return this.targetTemperature > this.currentTempRange.min;
    },
    canIncreaseTemp() {
      if (!this.isOn) return false;
      return this.targetTemperature < this.currentTempRange.max;
    },
    shouldCharge() {
      if (!this.isOn || !this.isSupplyingAir) return false;
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
        default:
          return '';
      }
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
      
      try {
        const roomNum = parseInt(this.currentRoomNumber);
        if (isNaN(roomNum)) {
          throw new Error('无效的房间号');
        }
        
        this.connectionStatus = 'connected';
        this.logToServer(`连接到房间 ${this.currentRoomNumber}`);
        
        // 初始化时上报当前温度
        await this.reportCurrentTemperature(this.roomTemperature);
      } catch (error) {
        this.connectionStatus = 'error';
        this.errorMessage = `连接房间 ${this.currentRoomNumber} 失败: ${error.message}`;
        console.error('房间初始化失败:', error);
      }
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

    // 新增：向后端通知送风状态变化
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
      if (this.logMessages.length > 10) {
        this.logMessages.pop();
      }
      console.log(`[TO SERVER] 房间${this.currentRoomNumber}: ${message}`);
    },

    async togglePower() {
      const willTurnOn = !this.isOn;
      
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
          this.currentMode = MODE_COOL;
          this.targetTemperature = DEFAULT_TEMP;
          this.currentFanSpeed = FAN_MEDIUM;

          if (this.isFirstStart || !this.isSupplyingAir) {
            this.isSupplyingAir = true;
            this.logToServer(`开机。模式: ${this.displayMode}, 目标温度: ${this.targetTemperature}°C, 风速: ${this.displayFanSpeed}`);
          }

          this.isFirstStart = false;
          this.startSimulations();
        } else {
          this.isSupplyingAir = false;
          this.logToServer('关机。');
          this.stopSimulations();
        }
      }
    },

    async setMode(mode) {
      if (!this.isOn || this.currentMode === mode) return;
      
      this.currentMode = mode;
      if (this.targetTemperature < this.currentTempRange.min) {
        this.targetTemperature = this.currentTempRange.min;
      } else if (this.targetTemperature > this.currentTempRange.max) {
        this.targetTemperature = this.currentTempRange.max;
      }
      this.checkAndRestartAirSupply();
      this.logToServer(`切换模式: ${this.displayMode}, 目标温度: ${this.targetTemperature}°C`);
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
        this.checkAndRestartAirSupply();
        this.logToServer(`设置风速: ${this.displayFanSpeed}`);
      }
    },

    async changeTemperature(direction) {
      if (!this.isOn) return;

      const now = Date.now();
      if (this.tempChangeTimeoutId) {
        clearTimeout(this.tempChangeTimeoutId);
      }

      let tempTarget = this.targetTemperature;
      if (direction === 'increase' && this.canIncreaseTemp) {
        tempTarget++;
      } else if (direction === 'decrease' && this.canDecreaseTemp) {
        tempTarget--;
      }
      this.targetTemperature = tempTarget;

      this.tempChangeTimeoutId = setTimeout(async () => {
        this.targetTemperature = Math.max(this.currentTempRange.min, Math.min(this.targetTemperature, this.currentTempRange.max));
        
        const success = await this.sendBackendRequest(
          async () => {
            console.log(`发送温度设置请求: roomNumber=${this.currentRoomNumber}, temperature=${this.targetTemperature}`);
            await api.setAcTargetTemperature(this.currentRoomNumber, this.targetTemperature);
          },
          null,
          '设置温度失败'
        );

        if (success) {
          this.checkAndRestartAirSupply();
          this.logToServer(`调节温度: ${this.targetTemperature}°C`);
        }
        
        this.lastTempRequestTime = 0;
      }, 1000);

      if (now - this.lastTempRequestTime < 1000) {
        this.logToServer(`温度指令 (${this.targetTemperature}°C) 已缓存，等待1秒后发送最终值`);
      }
      this.lastTempRequestTime = now;
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
      this.stopSimulations();

      this.simulationIntervalId = setInterval(async () => {
        if (this.isOn) {
          if (this.isSupplyingAir) {
            const rate = TEMP_CHANGE_RATES[this.currentFanSpeed] / 60;

            if (this.currentMode === MODE_COOL) {
              this.roomTemperature -= rate;
              if (this.roomTemperature <= this.targetTemperature) {
                this.roomTemperature = this.targetTemperature;
                const wasSupplying = this.isSupplyingAir;
                this.isSupplyingAir = false;
                this.logToServer(`房间达到目标温度 ${this.targetTemperature}°C，停止送风。`);
                
                // 新增：通知后端停止送风
                if (wasSupplying) {
                  await this.notifyAirSupplyChange(false, `达到目标温度 ${this.targetTemperature}°C`);
                }
              }
            } else {
              this.roomTemperature += rate;
              if (this.roomTemperature >= this.targetTemperature) {
                this.roomTemperature = this.targetTemperature;
                const wasSupplying = this.isSupplyingAir;
                this.isSupplyingAir = false;
                this.logToServer(`房间达到目标温度 ${this.targetTemperature}°C，停止送风。`);
                
                // 新增：通知后端停止送风
                if (wasSupplying) {
                  await this.notifyAirSupplyChange(false, `达到目标温度 ${this.targetTemperature}°C`);
                }
              }
            }
          } else {
            const naturalChange = NATURAL_TEMP_CHANGE_RATE;

            if (this.currentMode === MODE_COOL) {
              if (this.roomTemperature < DEFAULT_TEMP) {
                this.roomTemperature = Math.min(
                  this.roomTemperature + naturalChange,
                  DEFAULT_TEMP
                );
              }

              if (this.roomTemperature > this.targetTemperature + TEMP_RESTART_THRESHOLD) {
                const wasSupplying = this.isSupplyingAir;
                this.isSupplyingAir = true;
                this.logToServer(`室温 (${this.roomTemperature.toFixed(1)}°C) 高于目标+${TEMP_RESTART_THRESHOLD}°C，重新启动制冷。`);
                
                // 新增：通知后端开始送风
                if (!wasSupplying) {
                  await this.notifyAirSupplyChange(true, `室温过高，重新启动制冷`);
                }
              }
            } else {
              if (this.roomTemperature > DEFAULT_TEMP) {
                this.roomTemperature = Math.max(
                  this.roomTemperature - naturalChange,
                  DEFAULT_TEMP
                );
              }

              if (this.roomTemperature < this.targetTemperature - TEMP_RESTART_THRESHOLD) {
                const wasSupplying = this.isSupplyingAir;
                this.isSupplyingAir = true;
                this.logToServer(`室温 (${this.roomTemperature.toFixed(1)}°C) 低于目标-${TEMP_RESTART_THRESHOLD}°C，重新启动制热。`);
                
                // 新增：通知后端开始送风
                if (!wasSupplying) {
                  await this.notifyAirSupplyChange(true, `室温过低，重新启动制热`);
                }
              }
            }
          }
        } else {
          // 空调关闭时的自然温度变化
          const diffToDefault = DEFAULT_TEMP - this.roomTemperature;
          if (Math.abs(diffToDefault) > 0.05) {
            const change = Math.sign(diffToDefault) * NATURAL_TEMP_CHANGE_RATE;
            this.roomTemperature += change;

            if ((diffToDefault > 0 && this.roomTemperature > DEFAULT_TEMP) ||
              (diffToDefault < 0 && this.roomTemperature < DEFAULT_TEMP)) {
              this.roomTemperature = DEFAULT_TEMP;
            }
          } else {
            this.roomTemperature = DEFAULT_TEMP;
          }
        }

        // 限制温度范围
        this.roomTemperature = Math.max(10, Math.min(this.roomTemperature, 40));

        // 检查温度是否有显著变化，如果有则上报给后端
        const temperatureChange = Math.abs(this.roomTemperature - this.lastReportedTemperature);
        if (temperatureChange >= this.temperatureReportThreshold) {
          this.reportCurrentTemperature(this.roomTemperature);
        }
      }, 1000);

      this.costCalculationIntervalId = setInterval(() => {
        if (this.shouldCharge) {
          const consumptionPerSecond = POWER_CONSUMPTION_RATE[this.currentFanSpeed] / 60;
          this.cost += consumptionPerSecond * COST_PER_KWH;
        }
      }, 1000);
    },

    stopSimulations() {
      if (this.simulationIntervalId) clearInterval(this.simulationIntervalId);
      if (this.costCalculationIntervalId) clearInterval(this.costCalculationIntervalId);
      this.simulationIntervalId = null;
      this.costCalculationIntervalId = null;
    },

    async checkAndRestartAirSupply() {
      if (this.isOn && !this.isSupplyingAir) {
        if ((this.currentMode === MODE_COOL && this.roomTemperature > this.targetTemperature) ||
          (this.currentMode === MODE_HEAT && this.roomTemperature < this.targetTemperature)) {
          const wasSupplying = this.isSupplyingAir;
          this.isSupplyingAir = true;
          this.logToServer(`设置改变，重新开始送风以达到目标 ${this.targetTemperature}°C。`);
          
          // 新增：通知后端开始送风
          if (!wasSupplying) {
            await this.notifyAirSupplyChange(true, `设置改变，重新开始送风`);
          }
        }
      } else if (this.isOn && this.isSupplyingAir) {
        if ((this.currentMode === MODE_COOL && this.roomTemperature <= this.targetTemperature) ||
          (this.currentMode === MODE_HEAT && this.roomTemperature >= this.targetTemperature)) {
          const wasSupplying = this.isSupplyingAir;
          this.isSupplyingAir = false;
          this.logToServer(`设置改变，房间已达目标，停止送风。`);
          
          // 新增：通知后端停止送风
          if (wasSupplying) {
            await this.notifyAirSupplyChange(false, `设置改变，房间已达目标`);
          }
        }
      }
    }
  },

  mounted() {
    // 组件挂载时初始化房间
  },

  beforeUnmount() {
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