<template>
  <div v-if="show" class="fixed inset-0 z-50 flex items-center justify-center">
    <div class="absolute inset-0 bg-black/40" @click="close"></div>
    <div class="bg-white rounded p-4 w-[320px] z-10">
      <h3 class="font-semibold mb-2">{{ title }}</h3>
      <input v-model="password" type="password" placeholder="비밀번호" class="w-full border rounded p-2 mb-3" />
      <div class="flex justify-end gap-2">
        <button @click="close" class="px-3 py-1">취소</button>
        <button @click="confirm" class="px-3 py-1 bg-blue-600 text-white rounded">확인</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
const props = defineProps<{ show: boolean; title?: string }>();
const emit = defineEmits(['confirm','close','update:show']);
const password = ref('');
watch(() => props.show, (v) => { if (!v) password.value = ''; });
function confirm() { emit('confirm', password.value); emit('update:show', false); password.value = ''; }
function close() { emit('close'); emit('update:show', false); password.value = ''; }
</script>