<template>
  <div>
    <button @click="$router.back()" class="mb-3 text-sm">← 뒤로</button>
    <form @submit.prevent="onSubmit" class="max-w-xl">
      <div class="mb-2">
        <label class="block text-sm">제목</label>
        <input v-model="form.title" class="w-full border rounded p-2" />
      </div>
      <div class="mb-2">
        <label class="block text-sm">내용</label>
        <textarea v-model="form.content" class="w-full border rounded p-2 h-40"></textarea>
      </div>
      <div class="mb-4">
        <label class="block text-sm">수정용 비밀번호</label>
        <input v-model="form.password" type="password" class="w-full border rounded p-2" />
      </div>

      <div v-if="error" class="text-red-600 mb-2">{{ error }}</div>
      <div class="flex gap-2">
        <button type="button" @click="$router.back()" class="px-3 py-1">취소</button>
        <button type="submit" class="px-3 py-1 bg-blue-600 text-white rounded">
          {{ isEdit ? '저장' : '등록' }}
        </button>
      </div>
    </form>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { createPost, fetchPost, updatePost } from '../services/postService';

const route = useRoute();
const router = useRouter();
const id = String(route.params.id ?? '');
const isEdit = !!id;

const form = reactive({ title: '', content: '', password: '' });
const loading = ref(false);
const error = ref('');

onMounted(async () => {
  if (isEdit) {
    loading.value = true;
    try {
      const p = await fetchPost(id);
      form.title = p.title;
      form.content = p.content;
    } catch (e) {
      error.value = (e as Error).message;
    } finally {
      loading.value = false;
    }
  }
});

async function onSubmit() {
  error.value = '';
  if (!form.title.trim() || !form.content.trim() || !form.password) { error.value = '모든 항목을 입력하세요.'; return; }
  loading.value = true;
  try {
    if (isEdit) {
      await updatePost(id, { title: form.title, content: form.content, password: form.password });
      router.push({ name: 'PostDetail', params: { id } });
    } else {
      const created = await createPost({ title: form.title, content: form.content, password: form.password });
      router.push({ name: 'PostDetail', params: { id: (created as any).id } });
    }
  } catch (e) {
    error.value = (e as Error).message;
  } finally { loading.value = false; }
}
</script>