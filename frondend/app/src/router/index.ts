import { createRouter, createWebHistory } from 'vue-router';
import Home from '../pages/Home.vue';
import Place from '../pages/Place.vue';
import PostForm from '../pages/PostForm.vue';
import PostDetail from '../pages/PostDetail.vue';

const routes = [
  { path: '/', name: 'Home', component: Home },
  { path: '/place/:id', name: 'Place', component: Place, props: true },
  { path: '/posts/new', name: 'PostNew', component: PostForm },
  { path: '/posts/:id', name: 'PostDetail', component: PostDetail, props: true },
  { path: '/posts/:id/edit', name: 'PostEdit', component: PostForm, props: true }
];

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
});

export default router;