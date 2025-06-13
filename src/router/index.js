import { createRouter, createWebHistory } from 'vue-router';
import ACPanel from '../components/ACPanel.vue';
import FrontDeskMenu from '../components/FrontDeskMenu.vue';
import ACMonitor from '../components/ACMonitor.vue'; // 确保路径正确
import Report from '../components/Report.vue';
import DataOverview from '../components/DataOverview.vue';

const routes = [
  {
    path: '/',
    name: 'Home',
    redirect: '/aircon'
  },
  {
    path: '/aircon',
    name: 'ACPanel',
    component: ACPanel
  },
  {
    path: '/frontdesk',
    name: 'FrontDesk',
    component: FrontDeskMenu
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