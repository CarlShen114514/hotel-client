import { createRouter, createWebHistory } from 'vue-router';
import ACPanel from '../components/ACPanel.vue';
import FrontDeskMenu from '../components/FrontDeskMenu.vue';
import ACMonitor from '../components/ACMonitor.vue'; // 确保路径正确
import Report from '../components/Report.vue';
import DataOverview from '../components/DataOverview.vue';
import WelcomePage from '@/components/WelcomePage.vue';

const routes = [
  {
    path: '/',
    name: 'Home',
    redirect: '/overview'
  },
  {
    path: '/aircon/:roomNumber',
    name: 'ACPanelRoom',
    component: ACPanel,
    props: true // 将路由参数作为props传递给组件
  },
  {
    path: '/frontdesk',
    name: 'FrontDesk',
    component: FrontDeskMenu
  },
  {
    path: '/welcome',
    name: 'Welcome',
    component: WelcomePage
  },
  {
    path: '/monitor',
    name: 'ACMonitor',
    component: ACMonitor
  },
  {
    path: '/report-usage',
    name: 'Report',
    component: Report
  },
  {
    path: '/overview',
    name: 'DataOverview',
    component: DataOverview
  }
];

const router = createRouter({
  history: createWebHistory('/'),
  routes
});

export default router;