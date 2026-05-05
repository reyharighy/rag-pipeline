<script setup lang="ts">
import { toastCurrent, dismissToast } from '../lib/toast'
</script>

<template>
  <Teleport to="body">
    <Transition
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="translate-y-2 opacity-0"
      enter-to-class="translate-y-0 opacity-100"
      leave-active-class="transition duration-150 ease-in"
      leave-from-class="translate-y-0 opacity-100"
      leave-to-class="translate-y-1 opacity-0"
    >
      <div
        v-if="toastCurrent"
        :key="toastCurrent.id"
        class="pointer-events-auto fixed bottom-5 right-5 z-100 max-w-sm cursor-pointer rounded-lg border px-4 py-3 text-sm shadow-lg"
        :class="
          toastCurrent.variant === 'success'
            ? 'border-emerald-200 bg-white text-emerald-950 dark:border-emerald-800 dark:bg-zinc-900 dark:text-emerald-100'
            : 'border-red-200 bg-white text-red-950 dark:border-red-800 dark:bg-zinc-900 dark:text-red-100'
        "
        :role="toastCurrent.variant === 'error' ? 'alert' : 'status'"
        :aria-live="toastCurrent.variant === 'error' ? 'assertive' : 'polite'"
        @click="dismissToast"
      >
        <p class="m-0 font-medium leading-snug">{{ toastCurrent.message }}</p>
        <p class="mt-1.5 m-0 text-xs opacity-80">Click to dismiss</p>
      </div>
    </Transition>
  </Teleport>
</template>
