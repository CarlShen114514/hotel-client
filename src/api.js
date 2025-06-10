import axios from 'axios';

// 创建一个axios实例
// 你的 vue.config.js 文件已经配置了代理 '/api'，所以我们的基础URL可以直接写 '/api'
//
const apiClient = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// 导出所有后端API的调用函数
export default {
  // 认证 (AuthController)
  login(account, password) {
    return apiClient.post('/login', { account, password });
  },

  // 房间状态 (RoomController)
  getRoomStatus(roomId) {
    return apiClient.get(`/rooms/${roomId}/status`);
  },
  getBill(roomId) {
    return apiClient.get(`/rooms/${roomId}/detail_bill`); // 使用详细账单接口
  },

  // 入住退房 (CheckInOutController)
  checkIn(data) {
    return apiClient.post('/check-in', data);
  },
  checkOut(data) {
    return apiClient.post('/check-out', data);
  },

  // 空调控制 (AirConditionerController)
  turnOnAC(roomNumber) {
    return apiClient.post('/ac/turn-on', { roomNumber });
  },
  turnOffAC(roomNumber) {
    return apiClient.post('/ac/turn-off', { roomNumber });
  },
  setAcSpeed(roomNumber, speed) {
    return apiClient.post('/ac/set-speed', { roomNumber, speed });
  },
  setAcTemperature(roomNumber, temperature) {
    return apiClient.post('/ac/set-temperature', { roomNumber, temperature });
  },

  // 监控 (这个需要后端提供一个获取所有房间状态的接口，这里我们先假设有)
  getAllRoomsStatus() {
    // 注意：你的后端目前没有提供一个一次性获取所有房间状态的接口。
    // 你可能需要在后端 RoomController 中添加一个 @GetMapping("/rooms/all-status")
    // 这里我们暂时假设它存在
    return apiClient.get('/rooms/all-status');
  }
};