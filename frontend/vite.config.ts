import path from 'node:path'
import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'

const repoRoot = path.resolve(__dirname, '..')

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, repoRoot, ['VITE_', 'VECTOR_'])
  const vectorEmbeddingDimension = env.VECTOR_EMBEDDING_DIMENSION ?? ''

  return {
    envDir: repoRoot,
    define: {
      'import.meta.env.VITE_VECTOR_EMBEDDING_DIMENSION': JSON.stringify(vectorEmbeddingDimension),
    },
    plugins: [vue(), tailwindcss()],
  }
})
