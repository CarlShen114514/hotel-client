<template>
  <div id="app-container">
    <header class="app-header">
      <img alt="Hotel Logo" src="./assets/bupt.png" class="logo" v-if="showLogo"> <!-- 假设你有logo.png -->
      <nav class="main-nav">
        <router-link to="/aircon">空调控制面板</router-link>
        <router-link to="/frontdesk">前台操作</router-link>
        <router-link to="/monitor">空调监控</router-link>
        <router-link to="/overview">数据总览</router-link>
        <router-link to="/report-usage">调度报表</router-link>
      </nav>
    </header>

    <main class="app-main-content">
      <router-view /> <!-- 路由匹配的组件将在这里渲染 -->
    </main>

    <footer class="app-footer">
      <p>© {{ currentYear }} 波特普大学快捷廉价酒店</p>
    </footer>
  </div>
</template>

<script>
export default {
  name: 'App',
  data() {
    return {
      currentYear: new Date().getFullYear(),
      showLogo: true // 控制logo显示，可以根据需要调整
    };
  },
  // 如果需要，可以在这里添加一些全局逻辑
};
</script>

<style>
/* 全局样式，也可以放在一个单独的 CSS 文件中引入 */
body {
  margin: 0;
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #2c3e50;
  background-color: #f4f6f8;
}

#app-container {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.app-header {
  background-color: #013fba; /* 酒店主题色 */
  padding: 15px 30px;
  color: white;
  display: flex;
  align-items: center;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.logo {
  height: 40px;
  margin-right: 20px;
}

.main-nav a {
  font-weight: bold;
  color: #ecf0f1;
  margin: 0 15px;
  text-decoration: none;
  padding: 8px 0;
  border-bottom: 2px solid transparent;
  transition: color 0.3s, border-bottom-color 0.3s;
}

.main-nav a:hover {
  color: #ffffff;
}

.main-nav a.router-link-exact-active { /* Vue Router 激活链接的类名 */
  color: #ffffff;
  border-bottom-color: #f1c40f; /* 激活链接的下划线颜色 */
}

.app-main-content {
  flex-grow: 1; /* 让主内容区域占据剩余空间 */
  padding: 20px;
}

.app-footer {
  background-color: #2c3e50;
  color: #bdc3c7;
  text-align: center;
  padding: 15px 0;
  font-size: 0.9em;
}

body {
  margin: 0;
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #2c3e50;
  background-color: #f4f6f8;
}

#app-container {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.app-header {
  background-color: #013fba;
  padding: 15px 30px;
  color: white;
  display: flex;
  align-items: center;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.logo {
  height: 40px;
  margin-right: 20px;
}

.main-nav {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}

.main-nav a {
  font-weight: bold;
  color: #ecf0f1;
  margin: 0 10px;
  text-decoration: none;
  padding: 8px 12px;
  border-radius: 4px;
  border-bottom: 2px solid transparent;
  transition: all 0.3s;
  white-space: nowrap;
}

.main-nav a:hover {
  color: #ffffff;
  background-color: rgba(255,255,255,0.1);
}

.main-nav a.router-link-exact-active {
  color: #ffffff;
  background-color: rgba(255,255,255,0.2);
  border-bottom-color: #f1c40f;
}

.app-main-content {
  flex-grow: 1;
  padding: 20px;
}

.app-footer {
  background-color: #2c3e50;
  color: #bdc3c7;
  text-align: center;
  padding: 15px 0;
  font-size: 0.9em;
}

/* 响应式导航 */
@media (max-width: 768px) {
  .app-header {
    flex-direction: column;
    text-align: center;
  }
  
  .logo {
    margin: 0 0 10px 0;
  }
  
  .main-nav {
    justify-content: center;
  }
  
  .main-nav a {
    margin: 2px 5px;
    font-size: 0.9em;
  }
}
</style>