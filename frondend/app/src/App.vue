<template>
  <div class="app-shell">
    <header class="app-header">
      <div class="header-inner">
        <router-link to="/" class="brand-link" aria-label="LocalHub 홈">
          <span class="brand-mark" aria-hidden="true">
            <svg viewBox="0 0 24 24" width="23" height="23" fill="none">
              <path
                d="M12 21s7-5.07 7-12A7 7 0 1 0 5 9c0 6.93 7 12 7 12Z"
                stroke="currentColor"
                stroke-width="1.9"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
              <path
                d="M9.1 9.2a2.9 2.9 0 1 0 5.8 0 2.9 2.9 0 0 0-5.8 0Z"
                fill="currentColor"
              />
            </svg>
          </span>

          <span class="brand-copy">
            <span class="brand-name">LocalHub</span>
            <span class="brand-tagline">
              서울을 더 가깝게 발견하는 방법
            </span>
          </span>
        </router-link>

        <nav class="header-nav" aria-label="주요 메뉴">
          <router-link to="/" class="nav-link">
            <svg
              viewBox="0 0 24 24"
              width="18"
              height="18"
              fill="none"
              aria-hidden="true"
            >
              <path
                d="m4 10 8-6 8 6v9a1 1 0 0 1-1 1h-5v-6h-4v6H5a1 1 0 0 1-1-1v-9Z"
                stroke="currentColor"
                stroke-width="1.8"
                stroke-linejoin="round"
              />
            </svg>

            <span class="nav-home-label">홈</span>
          </router-link>

          <router-link to="/posts/new" class="btn btn-primary">
            <svg
              viewBox="0 0 24 24"
              width="17"
              height="17"
              fill="none"
              aria-hidden="true"
            >
              <path
                d="M12 5v14M5 12h14"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
              />
            </svg>

            여행 이야기 쓰기
          </router-link>
        </nav>
      </div>
    </header>

    <main class="app-main">
      <router-view v-slot="{ Component }">
        <transition name="page" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
  </div>
</template>

<script setup lang="ts" />