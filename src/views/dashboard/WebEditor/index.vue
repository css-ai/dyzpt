<script setup lang="ts">
import { computed, ref } from 'vue'
import { VueDraggable, type DraggableEvent } from 'vue-draggable-plus'

import ModuleText from '#/views/modules/Text/index.vue'
import ModuleNavigation from '#/views/modules/Navigation/index.vue'

type BlockType = 'text' | 'nav'

type Block = {
  id: string
  type: BlockType
  name: string
  props: Record<string, any>
}

type PaletteItem = {
  type: BlockType
  name: string
  defaultProps: Record<string, any>
}

const palette = ref<PaletteItem[]>([
  { type: 'text', name: '文本', defaultProps: { text: '双击修改文案', align: 'left' } },
  { type: 'nav', name: '导航', defaultProps: { items: ['首页', '产品', '关于', '联系'], align: 'left' } },
])

const canvas = ref<Block[]>([])
const selectedId = ref<string | null>(null)

const selectedBlock = computed(() => {
  if (!selectedId.value) return null
  return canvas.value.find((b) => b.id === selectedId.value) ?? null
})

const componentMap: Record<BlockType, any> = {
  text: ModuleText,
  nav: ModuleNavigation,
}

const makeId = () => `${Date.now()}-${Math.random().toString(16).slice(2)}`

const onAddToCanvas = (e: DraggableEvent) => {
  const newIndex = (e as any).newIndex as number | undefined
  if (typeof newIndex !== 'number') return

  const inserted = canvas.value[newIndex] as any

  // clone 来自 palette 时，这里把插入项规范化成 Block
  if (inserted && !inserted.id) {
    const item = inserted as PaletteItem
    canvas.value[newIndex] = {
      id: makeId(),
      type: item.type,
      name: item.name,
      props: JSON.parse(JSON.stringify(item.defaultProps || {})),
    }
  }

  selectedId.value = canvas.value[newIndex]?.id ?? null
}

const onUpdateCanvas = (_e: DraggableEvent) => {
  // 排序后保持 selectedId 不变即可
}

const handleSelect = (id: string) => {
  selectedId.value = id
}

const handleDeleteSelected = () => {
  if (!selectedId.value) return
  const idx = canvas.value.findIndex((b) => b.id === selectedId.value)
  if (idx === -1) return
  canvas.value.splice(idx, 1)
  selectedId.value = null
}

const updateSelectedProp = (key: string, value: any) => {
  if (!selectedBlock.value) return
  selectedBlock.value.props = { ...selectedBlock.value.props, [key]: value }
}
</script>

<template>
  <div class="web-editor-page">
    <div class="page-title">网页编辑</div>

    <div class="web-box">
      <!-- 左：模块库（拖到画布会克隆一份） -->
      <section class="panel left">
        <div class="panel-title">模块库</div>
        <VueDraggable
          v-model="palette"
          :group="{ name: 'blocks', pull: 'clone', put: false }"
          :sort="false"
          :clone="(item) => ({ ...item, defaultProps: JSON.parse(JSON.stringify(item.defaultProps || {})) })"
          item-key="name"
          class="palette-list"
        >
          <div v-for="item in palette" :key="item.type" class="palette-item">
            {{ item.name }}
          </div>
        </VueDraggable>
        <p class="hint">拖拽到中间画布生成模块</p>
      </section>

      <!-- 中：画布（可排序） -->
      <section class="panel center">
        <div class="panel-title">
          画布
          <button class="mini-btn" type="button" @click="handleDeleteSelected" :disabled="!selectedBlock">
            删除选中
          </button>
        </div>

        <VueDraggable
          v-model="canvas"
          :group="{ name: 'blocks', pull: true, put: true }"
          item-key="id"
          class="canvas"
          :animation="180"
          ghost-class="drag-ghost"
          chosen-class="drag-chosen"
          @add="onAddToCanvas"
          @update="onUpdateCanvas"
        >
          <div
            v-for="block in canvas"
            :key="block.id"
            class="canvas-block"
            :class="{ selected: selectedId === block.id }"
            @click.stop="handleSelect(block.id)"
          >
            <component
              :is="componentMap[block.type]"
              v-bind="block.props"
            />
          </div>

          <template #footer>
            <div v-if="canvas.length === 0" class="empty">把左侧模块拖进来开始搭建页面</div>
          </template>
        </VueDraggable>
      </section>

      <!-- 右：属性编辑 -->
      <section class="panel right">
        <div class="panel-title">属性</div>

        <div v-if="!selectedBlock" class="empty">选择一个画布模块以编辑属性</div>

        <div v-else class="prop-form">
          <div class="prop-row">
            <div class="prop-label">模块</div>
            <div class="prop-value">{{ selectedBlock.name }}</div>
          </div>

          <template v-if="selectedBlock.type === 'text'">
            <div class="prop-row">
              <label class="prop-label">文案</label>
              <textarea
                class="prop-input"
                rows="4"
                :value="selectedBlock.props.text"
                @input="updateSelectedProp('text', ($event.target as HTMLTextAreaElement).value)"
              />
            </div>

            <div class="prop-row">
              <label class="prop-label">对齐</label>
              <select
                class="prop-input"
                :value="selectedBlock.props.align"
                @change="updateSelectedProp('align', ($event.target as HTMLSelectElement).value)"
              >
                <option value="left">左</option>
                <option value="center">中</option>
                <option value="right">右</option>
              </select>
            </div>
          </template>

          <template v-else-if="selectedBlock.type === 'nav'">
            <div class="prop-row">
              <label class="prop-label">菜单（逗号分隔）</label>
              <input
                class="prop-input"
                type="text"
                :value="(selectedBlock.props.items || []).join(',')"
                @input="updateSelectedProp('items', (($event.target as HTMLInputElement).value || '').split(',').map((s) => s.trim()).filter(Boolean))"
              />
            </div>

            <div class="prop-row">
              <label class="prop-label">对齐</label>
              <select
                class="prop-input"
                :value="selectedBlock.props.align"
                @change="updateSelectedProp('align', ($event.target as HTMLSelectElement).value)"
              >
                <option value="left">左</option>
                <option value="center">中</option>
                <option value="right">右</option>
              </select>
            </div>
          </template>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.web-editor-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
  height: 100%;
  min-height: 0;
}

.page-title {
  font-size: 18px;
  font-weight: 600;
}

.web-box {
  display: grid;
  grid-template-columns: 280px minmax(0, 1fr) 320px;
  gap: 12px;
  flex: 1;
  min-height: 0;
}

.panel {
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 10px;
  background: #fff;
  padding: 12px;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.panel-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-weight: 600;
  font-size: 14px;
}

.palette-list {
  display: grid;
  gap: 8px;
}

.palette-item {
  padding: 10px 12px;
  border-radius: 8px;
  background: #f6f7f9;
  border: 1px solid rgba(0, 0, 0, 0.06);
  cursor: grab;
  user-select: none;
}

.hint {
  margin: 0;
  color: #666;
  font-size: 12px;
}

.canvas {
  flex: 1;
  min-height: 0;
  padding: 12px;
  border-radius: 10px;
  background: #fafafa;
  border: 1px dashed rgba(0, 0, 0, 0.14);
  display: grid;
  gap: 10px;
  align-content: start;
}

.canvas-block {
  background: #fff;
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 10px;
  padding: 10px;
  cursor: pointer;
}

.canvas-block.selected {
  border-color: #1677ff;
  box-shadow: 0 0 0 3px rgba(22, 119, 255, 0.15);
}

.drag-ghost {
  opacity: 0.35;
}

.drag-chosen {
  opacity: 0.9;
}

.empty {
  color: #888;
  font-size: 13px;
  padding: 12px;
}

.mini-btn {
  border: 1px solid rgba(0, 0, 0, 0.12);
  background: #fff;
  border-radius: 8px;
  padding: 6px 10px;
  cursor: pointer;
  font-size: 12px;
}

.mini-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.prop-form {
  display: grid;
  gap: 10px;
}

.prop-row {
  display: grid;
  gap: 6px;
}

.prop-label {
  font-size: 12px;
  color: #666;
}

.prop-value {
  font-size: 13px;
}

.prop-input {
  width: 100%;
  padding: 8px 10px;
  border-radius: 8px;
  border: 1px solid rgba(0, 0, 0, 0.14);
  font-size: 13px;
  background: #fff;
}

/* 画布区域：完全无样式（无 padding / margin / border / background） */
.canvas {
  flex: 1;
  min-height: 0;
  padding: 0;
  margin: 0;
  border: none;
  border-radius: 0;
  background: transparent;
  display: block;
}

.canvas-block {
  padding: 0;
  margin: 0;
  border: none;
  border-radius: 0;
  background: transparent;
}

.canvas-block.selected {
  outline: 2px solid #1677ff;
  outline-offset: 0;
  box-shadow: none;
}
</style>
