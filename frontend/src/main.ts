import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import { createPinia } from 'pinia'
import { createApp } from 'vue'

import App from './App.vue'
import { setupHttpInterceptors } from './api/interceptors'
import { createAppRouter } from './router'
import './style.css'

const app = createApp(App)

const pinia = createPinia()
app.use(pinia)
app.use(ElementPlus)

setupHttpInterceptors(pinia)

const router = createAppRouter(pinia)
app.use(router)

app.mount('#app')
