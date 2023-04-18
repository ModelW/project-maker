<script setup>
// import { toast } from 'vue3-toastify';

nextTick(() => {
  if (process.client) {
    useNuxtApp().$toast('notify after nextTick');
  }
});

const notify = () => {
  useNuxtApp().$toast.info('toastify success');
  // or
  // toast.info('toastify success');
};
</script>

<template>
  <button @click="notify">notify by click</button>
</template>
