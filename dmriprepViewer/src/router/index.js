import Vue from 'vue';
import Router from 'vue-router';
import HelloWorld from '@/components/HelloWorld';
import Report from '@/components/Report';
import Bucket from '@/components/Bucket';

Vue.use(Router);

export default new Router({
  routes: [
    {
      path: '/',
      name: 'HelloWorld',
      component: HelloWorld,
    },
    {
      path: '/report',
      name: 'Report',
      component: Report,
    },
    {
      path: '/bucket/:bucket',
      name: 'Bucket',
      component: Bucket,
    },
  ],
});
