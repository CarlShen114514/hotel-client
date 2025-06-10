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

// 耗电: 度/分钟
const POWER_CONSUMPTION_RATE = {
  [FAN_HIGH]: 1 / 1,    // 1度/1分钟
  [FAN_MEDIUM]: 1 / 2, // 1度/2分钟
  [FAN_LOW]: 1 / 3,    // 1度/3分钟
};
const COST_PER_KWH = 1; // 1元/度

// 温度变化: 度/分钟
const TEMP_CHANGE_RATE_MEDIUM = 0.5; // 中风基础变化率
const TEMP_CHANGE_RATES = {
    [FAN_HIGH]: TEMP_CHANGE_RATE_MEDIUM * 1.2,
    [FAN_MEDIUM]: TEMP_CHANGE_RATE_MEDIUM,
    [FAN_LOW]: TEMP_CHANGE_RATE_MEDIUM * 0.8,
};
const TEMP_CHANGE_OFF_RATE = 0.5; // 关机时温度变化率
const TEMP_RESTART_THRESHOLD = 1; // 超过目标1度重启

export default {
  name: 'ACPanel',
  data() {
    return {
      isOn: false,
      currentMode: MODE_COOL,
      targetTemperature: DEFAULT_TEMP,
      currentFanSpeed: FAN_MEDIUM,
      roomTemperature: DEFAULT_TEMP, // 初始房间温度等于默认温度
      cost: 0,

      // 内部状态
      isSupplyingAir: false, // 是否正在送风 (达到目标后会停止)
      lastTempRequestTime: 0,
      tempChangeTimeoutId: null,
      simulationIntervalId: null,
      costCalculationIntervalId: null,
      logMessages: [],
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
    }
  },
  methods: {
    logToServer(message) {
      const timestamp = new Date().toLocaleTimeString();
      this.logMessages.unshift(`[${timestamp}] ${message}`);
      if (this.logMessages.length > 10) { // Keep log short
        this.logMessages.pop();
      }
      console.log(`[TO SERVER] ${message}`); // 模拟发送到服务器
    },
    togglePower() {
      this.isOn = !this.isOn;
      if (this.isOn) {
        // 开机，恢复/设置默认状态
        this.currentMode = MODE_COOL; // 或者可以保存上次的状态
        this.targetTemperature = DEFAULT_TEMP;
        this.currentFanSpeed = FAN_MEDIUM;
        this.isSupplyingAir = true; // 开机默认送风
        this.logToServer(`开机。模式: ${this.displayMode}, 目标温度: ${this.targetTemperature}°C, 风速: ${this.displayFanSpeed}`);
        this.startSimulations();
      } else {
        // 关机
        this.isSupplyingAir = false;
        this.logToServer('关机。');
        this.stopSimulations();
        // 关机后室温会逐渐恢复到初始温度（这里简化为向DEFAULT_TEMP变化）
        // 成本计算也应停止
      }
    },
    setMode(mode) {
      if (!this.isOn || this.currentMode === mode) return;
      this.currentMode = mode;
      // 切换模式时，如果目标温度超出新模式范围，则调整
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
      this.checkAndRestartAirSupply(); // 风速改变可能需要重新开始送风
      this.logToServer(`设置风速: ${this.displayFanSpeed}`);
    },
    changeTemperature(direction) {
      if (!this.isOn) return;

      const now = Date.now();
      if (this.tempChangeTimeoutId) {
        clearTimeout(this.tempChangeTimeoutId);
      }

      // 更新目标温度的逻辑，先临时更新以反映到界面，实际发送以最后一次为准
      let tempTarget = this.targetTemperature;
      if (direction === 'increase' && this.canIncreaseTemp) {
        tempTarget++;
      } else if (direction === 'decrease' && this.canDecreaseTemp) {
        tempTarget--;
      }
      this.targetTemperature = tempTarget; // 立即更新UI显示

      // 防抖：1秒内连续操作，只发送最后一次
      this.tempChangeTimeoutId = setTimeout(() => {
        // 确保最终的 targetTemperature 在范围内
        this.targetTemperature = Math.max(this.currentTempRange.min, Math.min(this.targetTemperature, this.currentTempRange.max));
        this.checkAndRestartAirSupply();
        this.logToServer(`调节温度: ${this.targetTemperature}°C`);
        this.lastTempRequestTime = 0; // 重置以便下次立即发送
      }, 1000); // 1秒延迟发送

       if (now - this.lastTempRequestTime < 1000) {
         // 如果小于1秒，只更新UI，不立即发送（上面timeout会处理）
         this.logToServer(`温度指令 (${this.targetTemperature}°C) 已缓存，等待1秒后发送最终值`);
       } else {
         // 大于1秒，这次操作算是新的开始（虽然也会被上面的timeout覆盖，但逻辑上是这样）
         // 实际发送由上面的timeout统一处理
       }
       this.lastTempRequestTime = now;
    },

    startSimulations() {
      this.stopSimulations(); // Clear existing intervals

      // 房间温度变化模拟 (每5秒更新一次，实际传感器可能是实时的)
      this.simulationIntervalId = setInterval(() => {
        if (this.isOn) {
          if (this.isSupplyingAir) {
            const rate = TEMP_CHANGE_RATES[this.currentFanSpeed];
            if (this.currentMode === MODE_COOL && this.roomTemperature > this.targetTemperature) {
              this.roomTemperature -= rate / (60 / 5); // 每5秒变化
              if (this.roomTemperature <= this.targetTemperature) {
                this.roomTemperature = this.targetTemperature;
                this.isSupplyingAir = false;
                this.logToServer(`房间达到目标温度 ${this.targetTemperature}°C，停止送风。`);
              }
            } else if (this.currentMode === MODE_HEAT && this.roomTemperature < this.targetTemperature) {
              this.roomTemperature += rate / (60 / 5);
              if (this.roomTemperature >= this.targetTemperature) {
                this.roomTemperature = this.targetTemperature;
                this.isSupplyingAir = false;
                this.logToServer(`房间达到目标温度 ${this.targetTemperature}°C，停止送风。`);
              }
            } else if ( (this.currentMode === MODE_COOL && this.roomTemperature < this.targetTemperature) ||
                        (this.currentMode === MODE_HEAT && this.roomTemperature > this.targetTemperature) ) {
                // 目标温度改变，但房间温度在错误的一侧，或者已经相等，不需要主动改变，而是等待自然变化或送风
                // 如果已经相等，上面逻辑会停止送风
            }
          } else { // 不送风时，检查是否需要重启
            if (this.currentMode === MODE_COOL && this.roomTemperature > this.targetTemperature + TEMP_RESTART_THRESHOLD) {
              this.isSupplyingAir = true;
              this.logToServer(`室温 (${this.roomTemperature.toFixed(1)}°C) 高于目标+${TEMP_RESTART_THRESHOLD}°C，重新启动制冷。`);
            } else if (this.currentMode === MODE_HEAT && this.roomTemperature < this.targetTemperature - TEMP_RESTART_THRESHOLD) {
              this.isSupplyingAir = true;
              this.logToServer(`室温 (${this.roomTemperature.toFixed(1)}°C) 低于目标-${TEMP_RESTART_THRESHOLD}°C，重新启动制热。`);
            }
          }
        } else { // 关机状态
          const diffToDefault = DEFAULT_TEMP - this.roomTemperature;
          if (Math.abs(diffToDefault) > 0.1) { // 避免浮点数精度问题
             const change = TEMP_CHANGE_OFF_RATE / (60 / 5);
             this.roomTemperature += Math.sign(diffToDefault) * Math.min(Math.abs(diffToDefault), change);
          } else {
            this.roomTemperature = DEFAULT_TEMP; // 稳定在初始温度
          }
        }
        // 确保室温不会极端
        this.roomTemperature = Math.max(10, Math.min(this.roomTemperature, 40));

      }, 5000); // 每5秒模拟一次温度变化和空调逻辑

      // 费用计算模拟 (每分钟结算一次，简化模型)
      // 实际中应该是服务端根据送风时长和费率计算
      this.costCalculationIntervalId = setInterval(() => {
        if (this.isOn && this.isSupplyingAir) {
          const consumptionRate = POWER_CONSUMPTION_RATE[this.currentFanSpeed]; // 度/分钟
          this.cost += consumptionRate * COST_PER_KWH; // 每分钟增加的费用
        }
      }, 60000); // 每分钟计算一次费用
    },
    stopSimulations() {
      if (this.simulationIntervalId) clearInterval(this.simulationIntervalId);
      if (this.costCalculationIntervalId) clearInterval(this.costCalculationIntervalId);
      this.simulationIntervalId = null;
      this.costCalculationIntervalId = null;
    },
    checkAndRestartAirSupply() {
        // 当目标温度、模式或风速改变时，如果当前未送风，但条件允许，则开始送风
        if (this.isOn && !this.isSupplyingAir) {
            if ( (this.currentMode === MODE_COOL && this.roomTemperature > this.targetTemperature) ||
                 (this.currentMode === MODE_HEAT && this.roomTemperature < this.targetTemperature) ) {
                this.isSupplyingAir = true;
                this.logToServer(`设置改变，重新开始送风以达到目标 ${this.targetTemperature}°C。`);
            }
        } else if (this.isOn && this.isSupplyingAir) {
            // 如果正在送风，但目标已达到或超过，则应停止
             if ( (this.currentMode === MODE_COOL && this.roomTemperature <= this.targetTemperature) ||
                 (this.currentMode === MODE_HEAT && this.roomTemperature >= this.targetTemperature) ) {
                this.isSupplyingAir = false;
                this.logToServer(`设置改变，房间已达目标，停止送风。`);
            }
        }
    }
  },
  mounted() {
    // 初始时空调关闭，室温为默认值
    // 如果需要一打开页面就模拟，可以在这里调用 this.startSimulations()
    // 但根据面板逻辑，应该是用户点击开机后才开始模拟
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
  min-height: 80vh; /* 占据大部分视口高度 */
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
  align-items: stretch; /* 让子元素拉伸到容器宽度 */
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
  text-align: center; /* 确保文字居中 */
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