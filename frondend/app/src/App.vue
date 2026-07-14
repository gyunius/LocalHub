<template>
  <div id="app" class="min-h-screen bg-white text-slate-900">
    <header class="p-4 bg-slate-800 text-white">
      <div class="container mx-auto">
        <h1 class="text-xl font-semibold">LocalHub</h1>
      </div>
    </header>

    <main class="container mx-auto p-4">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts" />