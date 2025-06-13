<template>
  <div class="ac-panel-container">
    <div class="ACPanel">
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
        <button @click="togglePower" :class="{ active: isOn }" class="power-btn">
          {{ isOn ? '关机' : '开机' }}
        </button>

        <div v-if="isOn" class="active-controls">
          <div class="control-group">
            <label>模式:</label>
            <button @click="setMode('cool')" :class="{ active: currentMode === 'cool' }">制冷</button>
            <button @click="setMode('heat')" :class="{ active: currentMode === 'heat' }">制热</button>
          </div>

          <div class="control-group">
            <label>温度调节:</label>
            <button @click="changeTemperature('decrease')" :disabled="!canDecreaseTemp">-</button>
            <span>{{ targetTemperature }} °C</span>
            <button @click="changeTemperature('increase')" :disabled="!canIncreaseTemp">+</button>
          </div>

          <div class="control-group">
            <label>风速:</label>
            <button @click="setFanSpeed('low')" :class="{ active: currentFanSpeed === 'low' }">低</button>
            <button @click="setFanSpeed('medium')" :class="{ active: currentFanSpeed === 'medium' }">中</button>
            <button @click="setFanSpeed('high')" :class="{ active: currentFanSpeed === 'high' }">高</button>
          </div>
        </div>
      </div>
      
      <div v-if="logMessages.length" class="log-area">
        <strong>操作记录:</strong>
        <ul>
          <li v-for="(msg, index) in logMessages" :key="index">{{ msg }}</li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script>
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

// 耗电标准 (度/分钟)
const POWER_CONSUMPTION_RATE = {
  [FAN_HIGH]: 1,    // 1度/1分钟
  [FAN_MEDIUM]: 0.5, // 1度/2分钟
  [FAN_LOW]: 1/3     // 1度/3分钟
};
const COST_PER_KWH = 1; // 1元/度

// 温度变化基准值 (中风模式下每分钟变化0.5度)
const TEMP_CHANGE_RATE_MEDIUM = 0.5;
// 高风模式提高20%，低风模式降低20%
const TEMP_CHANGE_RATES = {
  [FAN_HIGH]: TEMP_CHANGE_RATE_MEDIUM * 1.2,   // 0.6度/分钟
  [FAN_MEDIUM]: TEMP_CHANGE_RATE_MEDIUM,       // 0.5度/分钟
  [FAN_LOW]: TEMP_CHANGE_RATE_MEDIUM * 0.8     // 0.4度/分钟
};

// 自然温度变化率 (停风后每分钟变化0.3度)
const NATURAL_TEMP_CHANGE_RATE = 0.3 / 60; // 转换为每秒变化量
// 温度重启阈值1度
const TEMP_RESTART_THRESHOLD = 1;

export default {
  name: 'ACPanel',
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
      isFirstStart: true
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
    }
  },
  methods: {
    logToServer(message) {
      const timestamp = new Date().toLocaleTimeString();
      this.logMessages.unshift(`[${timestamp}] ${message}`);
      if (this.logMessages.length > 10) {
        this.logMessages.pop();
      }
      console.log(`[TO SERVER] ${message}`);
    },
    togglePower() {
      this.isOn = !this.isOn;
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
    },
    setMode(mode) {
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
    setFanSpeed(speed) {
      if (!this.isOn || this.currentFanSpeed === speed) return;
      this.currentFanSpeed = speed;
      this.checkAndRestartAirSupply();
      this.logToServer(`设置风速: ${this.displayFanSpeed}`);
    },
    changeTemperature(direction) {
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

      this.tempChangeTimeoutId = setTimeout(() => {
        this.targetTemperature = Math.max(this.currentTempRange.min, Math.min(this.targetTemperature, this.currentTempRange.max));
        this.checkAndRestartAirSupply();
        this.logToServer(`调节温度: ${this.targetTemperature}°C`);
        this.lastTempRequestTime = 0;
      }, 1000);

      if (now - this.lastTempRequestTime < 1000) {
        this.logToServer(`温度指令 (${this.targetTemperature}°C) 已缓存，等待1秒后发送最终值`);
      }
      this.lastTempRequestTime = now;
    },
    startSimulations() {
      this.stopSimulations();

      // 房间温度变化模拟 (每秒更新一次)
      this.simulationIntervalId = setInterval(() => {
        if (this.isOn) {
          if (this.isSupplyingAir) {
            // 正在送风 - 按设定速率改变温度
            const rate = TEMP_CHANGE_RATES[this.currentFanSpeed] / 60;
            
            if (this.currentMode === MODE_COOL) {
              this.roomTemperature -= rate;
              if (this.roomTemperature <= this.targetTemperature) {
                this.roomTemperature = this.targetTemperature;
                this.isSupplyingAir = false;
                this.logToServer(`房间达到目标温度 ${this.targetTemperature}°C，停止送风。`);
              }
            } else {
              this.roomTemperature += rate;
              if (this.roomTemperature >= this.targetTemperature) {
                this.roomTemperature = this.targetTemperature;
                this.isSupplyingAir = false;
                this.logToServer(`房间达到目标温度 ${this.targetTemperature}°C，停止送风。`);
              }
            }
          } else {
            // 停风状态 - 温度自然变化
            const naturalChange = NATURAL_TEMP_CHANGE_RATE;
            
            if (this.currentMode === MODE_COOL) {
              // 制冷模式下，停风后温度会自然上升，但不超过默认温度
              if (this.roomTemperature < DEFAULT_TEMP) {
                this.roomTemperature = Math.min(
                  this.roomTemperature + naturalChange,
                  DEFAULT_TEMP
                );
              }
              
              // 当温度超过目标温度1度时重新启动
              if (this.roomTemperature > this.targetTemperature + TEMP_RESTART_THRESHOLD) {
                this.isSupplyingAir = true;
                this.logToServer(`室温 (${this.roomTemperature.toFixed(1)}°C) 高于目标+${TEMP_RESTART_THRESHOLD}°C，重新启动制冷。`);
              }
            } else {
              // 制热模式下，停风后温度会自然下降，但不低于默认温度
              if (this.roomTemperature > DEFAULT_TEMP) {
                this.roomTemperature = Math.max(
                  this.roomTemperature - naturalChange,
                  DEFAULT_TEMP
                );
              }
              
              // 当温度低于目标温度1度时重新启动
              if (this.roomTemperature < this.targetTemperature - TEMP_RESTART_THRESHOLD) {
                this.isSupplyingAir = true;
                this.logToServer(`室温 (${this.roomTemperature.toFixed(1)}°C) 低于目标-${TEMP_RESTART_THRESHOLD}°C，重新启动制热。`);
              }
            }
          }
        } else {
          // 关机状态 - 温度回归到默认温度
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

        // 确保室温在合理范围内
        this.roomTemperature = Math.max(10, Math.min(this.roomTemperature, 40));
      }, 1000);

      // 费用计算模拟 (每秒结算一次)
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
    checkAndRestartAirSupply() {
      if (this.isOn && !this.isSupplyingAir) {
        if ((this.currentMode === MODE_COOL && this.roomTemperature > this.targetTemperature) ||
            (this.currentMode === MODE_HEAT && this.roomTemperature < this.targetTemperature)) {
          this.isSupplyingAir = true;
          this.logToServer(`设置改变，重新开始送风以达到目标 ${this.targetTemperature}°C。`);
        }
      } else if (this.isOn && this.isSupplyingAir) {
        if ((this.currentMode === MODE_COOL && this.roomTemperature <= this.targetTemperature) ||
            (this.currentMode === MODE_HEAT && this.roomTemperature >= this.targetTemperature)) {
          this.isSupplyingAir = false;
          this.logToServer(`设置改变，房间已达目标，停止送风。`);
        }
      }
    }
  },
  mounted() {
    // 初始时空调关闭，室温为默认值
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
  box-shadow: 0 4px 8px rgba(0,0,0,0.1);
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
.current-temp strong, .target-temp strong {
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

.controls-area button:hover {
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
</style>