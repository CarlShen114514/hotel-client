import { createApp } from 'vue'
import App from './App.vue'
import router from './router' 


const app = createApp(App)

// 注册Element Plus
// app.use(ElementPlus)
app.use(router); // 使用路由



app.mount('#app')