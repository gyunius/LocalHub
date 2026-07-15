<template>
  <div class="home-page">
    <section class="home-intro" aria-labelledby="home-title">
      <div>
        <div class="eyebrow">
          <span class="eyebrow-dot"></span>
          Seoul local discovery
        </div>

        <h1 id="home-title" class="page-title">
          서울을 발견하고,<br />
          <span>나만의 코스로 연결하세요.</span>
        </h1>

        <p class="page-description home-copy">
          지도에서 새로운 장소를 찾고, 다른 여행자의 생생한 이야기를
          참고해보세요.
        </p>
      </div>

      <div class="intro-guide" aria-label="서비스 이용 안내">
        <div class="guide-icon">
          <svg
            viewBox="0 0 24 24"
            width="20"
            height="20"
            fill="none"
            aria-hidden="true"
          >
            <path
              d="M9 18 3.8 20.6A.55.55 0 0 1 3 20.1V6.8a1 1 0 0 1 .55-.9L9 3.2m0 14.8 6 3m-6-3V3.2m6 17.8 5.45-2.7a1 1 0 0 0 .55-.9V4.1a.55.55 0 0 0-.8-.5L15 6.2m0 14.8V6.2M9 3.2l6 3"
              stroke="currentColor"
              stroke-width="1.7"
              stroke-linecap="round"
              stroke-linejoin="round"
            />
          </svg>
        </div>

        <div>
          <strong>지도 핀을 눌러보세요</strong>
          <span>관광지 상세 정보로 바로 이동할 수 있어요.</span>
        </div>
      </div>
    </section>

    <section class="workspace" aria-label="서울 관광 지도와 커뮤니티">
      <aside class="feed-panel surface-card">
        <div class="panel-header">
          <div>
            <div class="eyebrow">Community</div>
            <h2 class="panel-title">지금 서울 이야기</h2>
            <p class="panel-description">
              여행자들이 방금 공유한 장소와 팁
            </p>
          </div>

          <router-link
            to="/posts/new"
            class="icon-button"
            aria-label="새 글 쓰기"
            title="새 글 쓰기"
          >
            <svg
              viewBox="0 0 24 24"
              width="18"
              height="18"
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
          </router-link>
        </div>

        <div class="soft-divider"></div>

        <BoardList filename="mock_posts.json" :page-size="3" />
      </aside>

      <section class="map-panel surface-card">
        <div class="map-panel-header">
          <div>
            <div class="eyebrow">Explore map</div>
            <h2 class="panel-title">서울 관광 지도</h2>
          </div>

          <div class="status-chip">
            <span class="status-dot"></span>
            관광지 데이터 연결됨
          </div>
        </div>

        <MapView />
      </section>
    </section>
  </div>
</template>

<script setup lang="ts">
import BoardList from '../components/BoardList.vue'
import MapView from '../components/MapView.vue'
</script>

<style scoped>
.home-page {
  display: grid;
  gap: 26px;
}

.home-intro {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 36px;
  padding: 16px 6px 6px;
}

.eyebrow-dot {
  width: 8px;
  height: 8px;

  border-radius: 999px;

  background: linear-gradient(135deg, #9b6ee5, #6032ad);
  box-shadow: 0 0 0 5px rgba(139, 91, 221, 0.1);
}

.page-title {
  margin-top: 11px;
}

.page-title span {
  color: transparent;

  background: linear-gradient(
    100deg,
    #4b278f 0%,
    #8050cf 58%,
    #4b65bf 100%
  );

  background-clip: text;
  -webkit-background-clip: text;
}

.home-copy {
  max-width: 620px;
  margin-top: 16px;
}

.intro-guide {
  width: min(360px, 100%);
  padding: 14px 16px;
  flex: 0 0 auto;

  display: flex;
  align-items: center;
  gap: 13px;

  border: 1px solid rgba(226, 229, 238, 0.95);
  border-radius: 17px;

  background: rgba(255, 255, 255, 0.72);
  box-shadow: 0 8px 26px rgba(39, 28, 70, 0.05);

  backdrop-filter: blur(12px);
}

.guide-icon {
  width: 40px;
  height: 40px;
  flex: 0 0 auto;

  display: grid;
  place-items: center;

  border-radius: 13px;

  color: #6b3bb4;
  background: #f1ecfa;
}

.intro-guide strong,
.intro-guide span {
  display: block;
}

.intro-guide strong {
  color: #2a3040;
  font-size: 13px;
  font-weight: 800;
}

.intro-guide span {
  margin-top: 3px;

  color: #8a92a3;
  font-size: 11px;
  line-height: 1.5;
}

.workspace {
  min-height: 640px;

  display: grid;
  grid-template-columns: minmax(300px, 355px) minmax(0, 1fr);
  gap: 18px;
}

.feed-panel,
.map-panel {
  min-width: 0;
  overflow: hidden;
}

.feed-panel {
  display: flex;
  flex-direction: column;
}

.map-panel {
  padding: 8px;

  display: grid;
  grid-template-rows: auto minmax(0, 1fr);
}

.map-panel-header {
  padding: 12px 12px 16px;

  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
}

.map-panel-header .panel-title {
  margin-top: 3px;
}

@media (max-width: 960px) {
  .home-intro {
    align-items: flex-start;
    flex-direction: column;
    gap: 18px;
  }

  .intro-guide {
    width: 100%;
  }

  .workspace {
    grid-template-columns: 1fr;
  }

  .feed-panel {
    max-height: none;
  }
}

@media (max-width: 640px) {
  .home-page {
    gap: 20px;
  }

  .home-intro {
    padding-inline: 2px;
  }

  .workspace {
    gap: 14px;
  }

  .status-chip {
    display: none;
  }

  .map-panel-header {
    padding: 10px 10px 14px;
  }
}
</style>