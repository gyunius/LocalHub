import {
  createRouter,
  createWebHistory,
} from 'vue-router'

import Home from '../pages/Home.vue'
import Place from '../pages/Place.vue'
import PostDetail from '../pages/PostDetail.vue'
import PostForm from '../pages/PostForm.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),

  routes: [
    {
      path: '/',
      name: 'Home',
      component: Home,

      meta: {
        title: '서울 관광 지도',
      },
    },

    {
      path: '/place/:id',
      name: 'Place',
      component: Place,
      props: true,

      meta: {
        title: '관광지 상세',
      },
    },

    {
      path: '/posts/new',
      name: 'PostNew',
      component: PostForm,

      meta: {
        title: '새 여행 이야기',
      },
    },

    {
      path: '/posts/:id',
      name: 'PostDetail',
      component: PostDetail,
      props: true,

      meta: {
        title: '여행 이야기',
      },
    },

    {
      path: '/posts/:id/edit',
      name: 'PostEdit',
      component: PostForm,
      props: true,

      meta: {
        title: '이야기 수정',
      },
    },
  ],

  scrollBehavior() {
    return {
      top: 0,
      behavior: 'smooth',
    }
  },
})

router.afterEach((to) => {
  const pageTitle =
    typeof to.meta.title === 'string'
      ? to.meta.title
      : ''

  document.title = pageTitle
    ? `${pageTitle} | LocalHub`
    : 'LocalHub'
})

export default router