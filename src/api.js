import axios from 'axios';


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
    return apiClient.get(`/rooms/${roomId}/bill`); // 使用详细账单接口
  },
  getDetailedBill(roomId) {
    return apiClient.get(`/rooms/${roomId}/detail_bill`); // 使用详细账单接口
  },
  getAllRoomsStatus() {
    return apiClient.get('/rooms/status');
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
    // 修正：后端需要的是路径变量
    return apiClient.post(`/ac/${roomNumber}/turn-on`);
  },
  turnOffAC(roomNumber) {
    // 修正：后端需要的是路径变量
    return apiClient.post(`/ac/${roomNumber}/turn-off`);
  },
  setAcSpeed(roomNumber, speed) {
    // 修正：后端需要路径变量和请求体
    return apiClient.post(`/ac/${roomNumber}/set-speed`, { speed });
  },
  setAcTemperature(roomNumber, temperature) {
    // 修正：后端需要路径变量和请求体
    return apiClient.post(`/ac/${roomNumber}/set-temperature`, { temperature });
  },

  // 报表相关API
  getUsageReport(startTime, endTime) {
    return apiClient.get('/reports/usage', {
      params: { startTime, endTime }
    });
  },
  
  getRoomReport(roomId) {
    return apiClient.get(`/reports/rooms/${roomId}`);
  }
};