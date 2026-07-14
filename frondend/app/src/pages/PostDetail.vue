<template>
  <div>
    <button @click="$router.back()" class="mb-3 text-sm">← 뒤로</button>

    <div v-if="loading">로딩중...</div>
    <div v-else-if="error" class="text-red-600">{{ error }}</div>
    <article v-else>
      <h2 class="text-2xl font-bold mb-2">{{ post.title }}</h2>
      <p class="mb-4">{{ post.content }}</p>
      <div class="flex gap-2">
        <button @click="startAction('edit')" class="px-3 py-1 border rounded">수정</button>
        <button @click="startAction('delete')" class="px-3 py-1 border rounded text-red-600">삭제</button>
      </div>
    </article>

    <PasswordModal :show="showPw" title="비밀번호를 입력하세요" @update:show="showPw = $event" @confirm="onConfirmPassword" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { fetchPost, deletePost, verifyPostPassword } from '../services/postService';
import PasswordModal from '../components/PasswordModal.vue';

const route = useRoute();
const router = useRouter();
const id = String(route.params.id ?? '');
const post = ref<any>(null);
const loading = ref(true);
const error = ref('');
const showPw = ref(false);
let pendingAction: 'edit'|'delete'|null = null;

onMounted(async () => {
  try { post.value = await fetchPost(id); } catch (e) { error.value = (e as Error).message; }
  finally { loading.value = false; }
});

function startAction(action: 'edit'|'delete') {
  pendingAction = action;
  showPw.value = true;
}

async function onConfirmPassword(password: string) {
  if (!pendingAction) return;
  if (pendingAction === 'edit') {
    // 권장: 백엔드에 /posts/:id/verify 구현되어 있으면 사용
    try {
      const ok = await verifyPostPassword(id, password);
      if (!ok) throw new Error('비밀번호가 틀렸습니다');
      router.push({ name: 'PostEdit', params: { id } });
    } catch (e) {
      error.value = (e as Error).message;
    }
  } else if (pendingAction === 'delete') {
    try {
      await deletePost(id, password);
      router.push({ name: 'Home' });
    } catch (e) {
      error.value = (e as Error).message;
    }
  }
  pendingAction = null;
}
</script>