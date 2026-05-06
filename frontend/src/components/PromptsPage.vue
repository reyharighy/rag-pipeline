<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { fetchPromptTemplates, updatePromptTemplate, type PromptTemplateRow } from '../api/promptTemplates'
import AssistantPromptFlowDiagram from './AssistantPromptFlowDiagram.vue'
import { formatDisplayTimestamp } from '../lib/formatDisplayTimestamp'
import { pushToast } from '../lib/toast'

const NODE_TABS = ['refine', 'response'] as const

type NodeTabKey = (typeof NODE_TABS)[number]

type PanelKey = 'refine_system' | 'response_system' | 'response_user'

const TAB_CONFIG: Record<
  NodeTabKey,
  { label: string; description: string; diagramCaption: string; panels: readonly PanelKey[] }
> = {
  refine: {
    label: 'Finding documents',
    description:
      'The app turns what you wrote into a clear search against your uploads. You can edit the instructions here; how your question is packaged for that step is fixed so the search format stays reliable.',
    diagramCaption:
      'Only the blue “Instructions” block below is editable. Your chat and that wording feed the search phrase, which is matched against your uploaded documents.',
    panels: ['refine_system'],
  },
  response: {
    label: 'Writing the answer',
    description:
      'Then, the app writes the reply using snippets from your files. Use the left box for tone and rules, and the right box for how excerpts and your question are laid out.',
    diagramCaption:
      'The two editors below match the blue and green blocks here. Snippets from your uploads and your question are filled into the right-hand wording before the assistant writes what you see in chat.',
    panels: ['response_system', 'response_user'],
  },
}

const PANEL_META: Record<PanelKey, { columnTitle: string; hint: string }> = {
  refine_system: {
    columnTitle: 'Instructions',
    hint: 'Describe how the assistant should rewrite the conversation into a good search.',
  },
  response_system: {
    columnTitle: 'Instructions',
    hint: 'Describe tone, format (e.g. Markdown), and how to use the provided excerpts.',
  },
  response_user: {
    columnTitle: 'Answer wording',
    hint: 'Leave {{context}} for the excerpts and {{question}} for the question—the app fills both in.',
  },
}

const rows = ref<PromptTemplateRow[]>([])
const loading = ref(true)
const savingKey = ref<string | null>(null)
const drafts = ref<Record<string, string>>({})
const activeTab = ref<NodeTabKey>('refine')

async function load(options?: { silent?: boolean }) {
  const silent = options?.silent ?? false

  if (!silent) {
    loading.value = true
  }

  try {
    const list = await fetchPromptTemplates()
    rows.value = list
    const next: Record<string, string> = {}

    for (const r of list) {
      next[r.key] = r.body
    }

    drafts.value = next
  } catch (e) {
    pushToast(e instanceof Error ? e.message : 'Could not load these settings.', 'error')
  } finally {
    if (!silent) {
      loading.value = false
    }
  }
}

onMounted(() => {
  void load()
})

const orderedTabs = computed(() =>
  NODE_TABS.filter((tab) => TAB_CONFIG[tab].panels.every((k) => rows.value.some((r) => r.key === k))),
)

watch([rows, orderedTabs], () => {
  const tabs = orderedTabs.value

  if (!tabs.includes(activeTab.value) && tabs.length > 0) {
    activeTab.value = tabs[0]!
  }
})

const activePanels = computed(() => TAB_CONFIG[activeTab.value].panels)

function rowFor(key: string): PromptTemplateRow | undefined {
  return rows.value.find((r) => r.key === key)
}

async function save(key: string) {
  const body = drafts.value[key]?.trim() ?? ''

  if (!body) {
    pushToast('Add some text before saving.', 'error')

    return
  }

  savingKey.value = key

  try {
    await updatePromptTemplate(key, drafts.value[key] ?? '')
    pushToast('Saved.', 'success')
    await load({ silent: true })
  } catch (e) {
    pushToast(e instanceof Error ? e.message : 'Save failed', 'error')
  } finally {
    savingKey.value = null
  }
}
</script>

<template>
  <div class="flex h-full min-h-0 flex-col bg-zinc-100 dark:bg-zinc-950">
    <header
      class="shrink-0 border-b border-zinc-200 bg-white px-5 pb-0 pt-4 text-left dark:border-zinc-700 dark:bg-zinc-900"
    >
      <h1 class="text-xl font-semibold text-zinc-900 dark:text-zinc-50">Customize the assistant</h1>
      <p class="mt-1.5 max-w-3xl pb-3 text-sm text-zinc-600 dark:text-zinc-400">
        Adjust the wording the app uses when it searches your files and when it writes replies.
      </p>

      <nav
        class="-mb-px flex flex-wrap gap-1 border-t border-zinc-100 pt-3 dark:border-zinc-800"
        aria-label="Assistant steps"
      >
        <button
          v-for="tab in orderedTabs"
          :key="tab"
          type="button"
          role="tab"
          :aria-selected="activeTab === tab"
          class="cursor-pointer rounded-t-md border border-b-0 px-3 py-2 text-xs font-semibold transition-colors"
          :class="
            activeTab === tab
              ? 'relative z-1 border-zinc-200 bg-zinc-100 text-zinc-900 dark:border-zinc-600 dark:bg-zinc-950 dark:text-zinc-50'
              : 'border-transparent bg-transparent text-zinc-500 hover:bg-zinc-50 hover:text-zinc-800 dark:text-zinc-400 dark:hover:bg-zinc-800/60 dark:hover:text-zinc-200'
          "
          @click="activeTab = tab"
        >
          {{ TAB_CONFIG[tab].label }}
        </button>
      </nav>
    </header>

    <div class="min-h-0 flex-1 overflow-y-auto px-5 pb-6 pt-4">
      <p v-if="loading" class="mx-auto max-w-6xl text-sm text-zinc-500 dark:text-zinc-400">Loading…</p>

      <div v-else class="mx-auto flex max-w-6xl flex-col gap-3">
        <p class="m-0 text-sm text-zinc-600 dark:text-zinc-400">
          {{ TAB_CONFIG[activeTab].description }}
        </p>

        <section
          class="rounded-xl border border-zinc-200 bg-white p-4 shadow-sm dark:border-zinc-700 dark:bg-zinc-900 dark:shadow-none"
          aria-labelledby="prompt-flow-heading"
        >
          <h3 id="prompt-flow-heading" class="m-0 text-sm font-semibold text-zinc-900 dark:text-zinc-100">
            How this step works
          </h3>
          <p class="mt-1 text-xs text-zinc-500 dark:text-zinc-400">
            Read left to right: what happens in this step before you edit the boxes underneath.
          </p>
          <div class="mt-3">
            <AssistantPromptFlowDiagram :variant="activeTab" :caption="TAB_CONFIG[activeTab].diagramCaption" />
          </div>
        </section>

        <div
          class="rounded-xl border border-zinc-200 bg-white p-4 shadow-sm dark:border-zinc-700 dark:bg-zinc-900 dark:shadow-none"
        >
          <div
            class="grid grid-cols-1 gap-5"
            :class="activePanels.length > 1 ? 'lg:grid-cols-2 lg:gap-6' : ''"
            role="group"
            :aria-label="`${TAB_CONFIG[activeTab].label} wording`"
          >
            <template v-for="panelKey in activePanels" :key="panelKey">
              <div
                v-if="rowFor(panelKey)"
                class="flex min-h-0 min-w-0 flex-col rounded-lg border border-zinc-100 bg-zinc-50/50 p-3 dark:border-zinc-800 dark:bg-zinc-950/40"
              >
                <div class="mb-2 flex flex-wrap items-start justify-between gap-2 border-b border-zinc-200/80 pb-2 dark:border-zinc-700/80">
                  <div class="min-w-0">
                    <h2 class="text-sm font-semibold text-zinc-900 dark:text-zinc-100">
                      {{ PANEL_META[panelKey].columnTitle }}
                    </h2>
                    <p class="mt-0.5 text-xs leading-relaxed text-zinc-500 dark:text-zinc-400">
                      {{ PANEL_META[panelKey].hint }}
                    </p>
                  </div>
                  <p class="m-0 shrink-0 text-right text-xs text-zinc-500 dark:text-zinc-400">
                    Updated {{ formatDisplayTimestamp(rowFor(panelKey)!.updated_at) }}
                  </p>
                </div>

                <textarea
                  v-model="drafts[panelKey]"
                  class="min-h-[min(320px,calc(100vh-380px))] w-full flex-1 resize-y rounded-lg border border-zinc-200 bg-white px-3 py-2.5 font-mono text-[13px] leading-relaxed text-zinc-800 shadow-inner outline-none transition-[border-color,box-shadow] placeholder:text-zinc-400 focus:border-blue-400 focus:ring-2 focus:ring-blue-500/25 dark:border-zinc-600 dark:bg-zinc-900 dark:text-zinc-100 dark:placeholder:text-zinc-500 dark:focus:border-blue-500 dark:focus:ring-blue-400/20"
                  spellcheck="false"
                  :aria-label="`${TAB_CONFIG[activeTab].label}: ${PANEL_META[panelKey].columnTitle}`"
                />

                <div class="mt-2 flex justify-end">
                  <button
                    type="button"
                    class="rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-45 dark:bg-blue-600 dark:hover:bg-blue-500 cursor-pointer"
                    :disabled="
                      savingKey === panelKey || (drafts[panelKey] ?? '') === rowFor(panelKey)!.body
                    "
                    @click="save(panelKey)"
                  >
                    {{ savingKey === panelKey ? 'Saving…' : 'Save' }}
                  </button>
                </div>
              </div>
            </template>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
