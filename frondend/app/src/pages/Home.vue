<template>
  <div class="lh-layout">
    <aside class="lh-left">
      <h2 class="text-lg font-semibold mb-2">게시판</h2>
      <BoardList filename="mock_posts.json" :page-size="3" />
    </aside>

    <main class="lh-right">
      <h2 class="text-lg font-semibold mb-2 md:hidden">지도</h2>
      <MapView />
    </main>
  </div>
</template>

<script setup lang="ts">
import BoardList from '../components/BoardList.vue';
import MapView from '../components/MapView.vue';
</script>

<style scoped>
.lh-layout {
  display: flex;
  gap: 1rem;
  align-items: flex-start;
  height: calc(100vh - 88px); /* 헤더 높이에 맞춰 필요시 조정 */
}

/* 3:7 비율 */
.lh-left {
  flex: 3 1 0%;
  min-width: 220px;
  max-width: 480px;
  overflow: auto;
}

.lh-right {
  flex: 7 1 0%;
  min-width: 240px;
  overflow: auto;
}

/* 화면 비율이 1:1(=5:5) 이하일 때 세로 스택 */
@media (max-aspect-ratio: 1/1) {
  .lh-layout {
    flex-direction: column;
    height: auto;
  }
  .lh-left,
  .lh-right {
    width: 100%;
    min-width: 0;
    max-width: none;
    height: auto;
  }
}
</style>