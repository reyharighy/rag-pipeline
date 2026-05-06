<script setup lang="ts">
defineProps<{
  variant: 'refine' | 'response'
  caption: string
}>()
</script>

<template>
  <figure class="m-0">
    <figcaption class="sr-only">
      <template v-if="variant === 'refine'">
        Flow: your chat and fixed in-app wording combine with editable instructions to produce a search phrase compared
        against your uploaded documents.
      </template>
      <template v-else>
        Flow: passages from your files and your question feed two editable texts—instructions and answer wording—which
        together produce the reply shown in chat.
      </template>
    </figcaption>

    <div
      class="overflow-x-auto rounded-lg border border-zinc-200 bg-linear-to-r from-zinc-50 to-white px-3 py-4 dark:border-zinc-700 dark:from-zinc-900/80 dark:to-zinc-900"
    >
      <!-- Horizontal: chat → instructions → search phrase → uploads (search wording is fixed in app, not shown) -->
      <svg
        v-if="variant === 'refine'"
        class="mx-auto block h-auto w-full min-w-[380px] max-w-[560px] text-zinc-600 dark:text-zinc-400"
        viewBox="0 0 412 76"
        xmlns="http://www.w3.org/2000/svg"
        aria-hidden="true"
      >
        <defs>
          <marker
            id="flow-arrow-refine"
            markerWidth="7"
            markerHeight="7"
            refX="6"
            refY="3.5"
            orient="auto"
            markerUnits="strokeWidth"
          >
            <path d="M0,0 L7,3.5 L0,7 Z" class="fill-zinc-500 dark:fill-zinc-400" />
          </marker>
        </defs>

        <g font-family="system-ui, sans-serif">
          <rect
            x="4"
            y="14"
            width="72"
            height="48"
            rx="8"
            class="fill-white stroke-zinc-300 stroke-[1.5] dark:fill-zinc-950 dark:stroke-zinc-600"
          />
          <text x="40" y="36" text-anchor="middle" class="fill-zinc-800 text-[10px] font-semibold dark:fill-zinc-100">
            Your chat
          </text>
          <text x="40" y="50" text-anchor="middle" class="fill-zinc-500 text-[8px] dark:fill-zinc-400">+ history</text>

          <line x1="76" y1="38" x2="86" y2="38" class="stroke-current stroke-[1.5]" marker-end="url(#flow-arrow-refine)" />

          <rect
            x="86"
            y="14"
            width="100"
            height="48"
            rx="8"
            class="fill-blue-50 stroke-blue-200 stroke-[1.5] dark:fill-blue-950/40 dark:stroke-blue-800"
          />
          <text x="136" y="36" text-anchor="middle" class="fill-zinc-800 text-[10px] font-semibold dark:fill-zinc-100">
            Instructions
          </text>
          <text x="136" y="50" text-anchor="middle" class="fill-zinc-500 text-[8px] dark:fill-zinc-400">you can edit</text>

          <line x1="186" y1="38" x2="196" y2="38" class="stroke-current stroke-[1.5]" marker-end="url(#flow-arrow-refine)" />

          <rect
            x="196"
            y="14"
            width="104"
            height="48"
            rx="8"
            class="fill-white stroke-zinc-300 stroke-[1.5] dark:fill-zinc-950 dark:stroke-zinc-600"
          />
          <text x="248" y="38" text-anchor="middle" class="fill-zinc-800 text-[10px] font-medium dark:fill-zinc-100">
            Search phrase
          </text>

          <line x1="300" y1="38" x2="310" y2="38" class="stroke-current stroke-[1.5]" marker-end="url(#flow-arrow-refine)" />

          <rect
            x="310"
            y="14"
            width="98"
            height="48"
            rx="8"
            class="fill-zinc-100 stroke-zinc-300 stroke-[1.5] dark:fill-zinc-800/60 dark:stroke-zinc-600"
          />
          <text x="359" y="38" text-anchor="middle" class="fill-zinc-800 text-[10px] font-medium dark:fill-zinc-100">
            Your uploads
          </text>
        </g>
      </svg>

      <!-- Horizontal: excerpts → question → instructions → answer wording → draft → chat -->
      <svg
        v-else
        class="mx-auto block h-auto w-full min-w-[560px] max-w-[800px] text-zinc-600 dark:text-zinc-400"
        viewBox="0 0 636 76"
        xmlns="http://www.w3.org/2000/svg"
        aria-hidden="true"
      >
        <defs>
          <marker
            id="flow-arrow-response"
            markerWidth="7"
            markerHeight="7"
            refX="6"
            refY="3.5"
            orient="auto"
            markerUnits="strokeWidth"
          >
            <path d="M0,0 L7,3.5 L0,7 Z" class="fill-zinc-500 dark:fill-zinc-400" />
          </marker>
        </defs>

        <g font-family="system-ui, sans-serif">
          <rect
            x="4"
            y="14"
            width="88"
            height="48"
            rx="8"
            class="fill-amber-50 stroke-amber-200 stroke-[1.5] dark:fill-amber-950/30 dark:stroke-amber-800"
          />
          <text x="48" y="36" text-anchor="middle" class="fill-zinc-800 text-[10px] font-semibold dark:fill-zinc-100">
            File excerpts
          </text>
          <text x="48" y="50" text-anchor="middle" class="fill-zinc-500 text-[8px] dark:fill-zinc-400">from uploads</text>

          <line x1="92" y1="38" x2="104" y2="38" class="stroke-current stroke-[1.5]" marker-end="url(#flow-arrow-response)" />

          <rect
            x="104"
            y="14"
            width="82"
            height="48"
            rx="8"
            class="fill-violet-50 stroke-violet-200 stroke-[1.5] dark:fill-violet-950/30 dark:stroke-violet-800"
          />
          <text x="145" y="38" text-anchor="middle" class="fill-zinc-800 text-[10px] font-semibold dark:fill-zinc-100">
            Your question
          </text>

          <line x1="186" y1="38" x2="198" y2="38" class="stroke-current stroke-[1.5]" marker-end="url(#flow-arrow-response)" />

          <rect
            x="198"
            y="14"
            width="86"
            height="48"
            rx="8"
            class="fill-blue-50 stroke-blue-200 stroke-[1.5] dark:fill-blue-950/40 dark:stroke-blue-800"
          />
          <text x="241" y="36" text-anchor="middle" class="fill-zinc-800 text-[10px] font-semibold dark:fill-zinc-100">
            Instructions
          </text>
          <text x="241" y="50" text-anchor="middle" class="fill-zinc-500 text-[8px] dark:fill-zinc-400">left column</text>

          <line x1="284" y1="38" x2="296" y2="38" class="stroke-current stroke-[1.5]" marker-end="url(#flow-arrow-response)" />

          <rect
            x="296"
            y="14"
            width="92"
            height="48"
            rx="8"
            class="fill-emerald-50 stroke-emerald-200 stroke-[1.5] dark:fill-emerald-950/35 dark:stroke-emerald-800"
          />
          <text x="342" y="36" text-anchor="middle" class="fill-zinc-800 text-[10px] font-semibold dark:fill-zinc-100">
            Answer wording
          </text>
          <text x="342" y="50" text-anchor="middle" class="fill-zinc-500 text-[8px] dark:fill-zinc-400">right column</text>

          <line x1="388" y1="38" x2="400" y2="38" class="stroke-current stroke-[1.5]" marker-end="url(#flow-arrow-response)" />

          <rect
            x="400"
            y="14"
            width="108"
            height="48"
            rx="8"
            class="fill-white stroke-zinc-300 stroke-[1.5] dark:fill-zinc-950 dark:stroke-zinc-600"
          />
          <text x="454" y="38" text-anchor="middle" class="fill-zinc-800 text-[10px] font-medium dark:fill-zinc-100">
            Draft reply
          </text>

          <line x1="508" y1="38" x2="520" y2="38" class="stroke-current stroke-[1.5]" marker-end="url(#flow-arrow-response)" />

          <rect
            x="520"
            y="14"
            width="112"
            height="48"
            rx="8"
            class="fill-zinc-100 stroke-zinc-300 stroke-[1.5] dark:fill-zinc-800/60 dark:stroke-zinc-600"
          />
          <text x="576" y="38" text-anchor="middle" class="fill-zinc-800 text-[10px] font-medium dark:fill-zinc-100">
            In chat
          </text>
        </g>
      </svg>
    </div>

    <p class="mt-2 text-center text-xs leading-relaxed text-zinc-500 dark:text-zinc-400">
      {{ caption }}
    </p>
  </figure>
</template>
