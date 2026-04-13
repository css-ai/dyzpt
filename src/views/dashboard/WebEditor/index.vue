<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import { VueDraggable, type DraggableEvent } from 'vue-draggable-plus'

import SchemaRenderer from './components/SchemaRenderer.vue'

type NodeType = 'content' | 'nav' | 'text'
type PreviewDevice = 'desktop' | 'mobile' | 'tablet'

type TextNodeProps = {
  align?: 'left' | 'center' | 'right'
  text?: string
}

type NavNodeProps = {
  align?: 'left' | 'center' | 'right'
  items?: string[]
}

type ContentNodeProps = {
  background?: string
  padding?: number
  title?: string
}

type BasePageNode = {
  children?: PageNode[]
  id: string
  name: string
}

type TextPageNode = BasePageNode & {
  props: TextNodeProps
  type: 'text'
}

type NavPageNode = BasePageNode & {
  props: NavNodeProps
  type: 'nav'
}

type ContentPageNode = BasePageNode & {
  props: ContentNodeProps
  type: 'content'
}

type PageNode = ContentPageNode | NavPageNode | TextPageNode

type PageSchema = {
  id: string
  root: {
    children: PageNode[]
    id: string
    type: 'page'
  }
  title: string
  version: 1
}

type PaletteItem = {
  defaultChildren?: PageNode[]
  defaultProps: ContentNodeProps | NavNodeProps | TextNodeProps
  name: string
  type: NodeType
}

const STORAGE_KEY = 'web-editor-page-schema'

const isTextBlock = (node: null | PageNode): node is TextPageNode => node?.type === 'text'
const isNavBlock = (node: null | PageNode): node is NavPageNode => node?.type === 'nav'
const isContentBlock = (node: null | PageNode): node is ContentPageNode => node?.type === 'content'

const previewDevices: Array<{ label: string; value: PreviewDevice }> = [
  { label: 'PC', value: 'desktop' },
  { label: '平板', value: 'tablet' },
  { label: '手机', value: 'mobile' },
]

const palette = ref<PaletteItem[]>([
  {
    type: 'content',
    name: '内容容器',
    defaultProps: { title: '内容区标题', padding: 24, background: '#ffffff' },
    defaultChildren: [
      {
        id: 'content-default-text',
        type: 'text',
        name: '文本',
        props: { text: '这里可以继续插入和编辑内容', align: 'left' },
      },
    ],
  },
  { type: 'text', name: '文本', defaultProps: { text: '双击修改文案', align: 'left' } },
  { type: 'nav', name: '导航', defaultProps: { items: ['首页', '产品', '关于', '联系'], align: 'left' } },
])

const pageSchema = ref<PageSchema>({
  id: 'page-home',
  title: '未命名页面',
  version: 1,
  root: {
    id: 'root',
    type: 'page',
    children: [],
  },
})

const canvas = computed<PageNode[]>({
  get: () => pageSchema.value.root.children,
  set: (value) => {
    pageSchema.value.root.children = value
  },
})

const selectedId = ref<null | string>(null)
const previewDevice = ref<PreviewDevice>('desktop')
const schemaText = ref('')
const exportCopied = ref(false)

const selectedBlock = computed<PageNode | null>(() => {
  if (!selectedId.value) return null
  return findNodeById(canvas.value, selectedId.value)
})

const nodeTypeSet = new Set<NodeType>(['content', 'text', 'nav'])

const previewWidth = computed(() => {
  if (previewDevice.value === 'mobile') return 390
  if (previewDevice.value === 'tablet') return 834
  return null
})

const previewWidthLabel = computed(() => (previewWidth.value ? `${previewWidth.value}px` : '自适应'))
const previewFrameStyle = computed(() => ({
  width: '100%',
  maxWidth: previewWidth.value ? `${previewWidth.value}px` : '100%',
}))

const makeId = () => `${Date.now()}-${Math.random().toString(16).slice(2)}`

function cloneNode(node: PageNode): PageNode {
  return {
    ...node,
    id: makeId(),
    props: JSON.parse(JSON.stringify(node.props || {})),
    children: node.children?.map(cloneNode),
  } as PageNode
}

function createNodeFromPalette(item: PaletteItem): PageNode {
  const id = makeId()

  if (item.type === 'text') {
    return {
      id,
      type: 'text',
      name: item.name,
      props: JSON.parse(JSON.stringify(item.defaultProps)) as TextNodeProps,
    }
  }

  if (item.type === 'nav') {
    return {
      id,
      type: 'nav',
      name: item.name,
      props: JSON.parse(JSON.stringify(item.defaultProps)) as NavNodeProps,
    }
  }

  return {
    id,
    type: 'content',
    name: item.name,
    props: JSON.parse(JSON.stringify(item.defaultProps)) as ContentNodeProps,
    children: item.defaultChildren?.map(cloneNode),
  }
}

function normalizeNode(node: Partial<PageNode>): PageNode {
  const nextType = nodeTypeSet.has(node.type as NodeType) ? (node.type as NodeType) : 'text'
  const base = {
    id: node.id || makeId(),
    name: node.name || (nextType === 'nav' ? '导航' : nextType === 'content' ? '内容容器' : '文本'),
  }

  if (nextType === 'nav') {
    return {
      ...base,
      type: 'nav',
      props: (node.props || {}) as NavNodeProps,
    }
  }

  if (nextType === 'content') {
    return {
      ...base,
      type: 'content',
      props: (node.props || {}) as ContentNodeProps,
      children: Array.isArray(node.children) ? node.children.map((child) => normalizeNode(child)) : [],
    }
  }

  return {
    ...base,
    type: 'text',
    props: (node.props || {}) as TextNodeProps,
  }
}

function findNodeById(nodes: PageNode[], id: string): PageNode | null {
  for (const node of nodes) {
    if (node.id === id) return node
    if (node.children?.length) {
      const found = findNodeById(node.children, id)
      if (found) return found
    }
  }
  return null
}

function removeNodeById(nodes: PageNode[], id: string): boolean {
  const index = nodes.findIndex((node) => node.id === id)
  if (index >= 0) {
    nodes.splice(index, 1)
    return true
  }

  for (const node of nodes) {
    if (node.children?.length && removeNodeById(node.children, id)) {
      return true
    }
  }

  return false
}

const exportSchema = computed<PageSchema>(() => pageSchema.value)

function syncSchemaText() {
  schemaText.value = JSON.stringify(exportSchema.value, null, 2)
}

function normalizePageSchema(data: Partial<PageSchema> | null | undefined): PageSchema {
  const children = Array.isArray(data?.root?.children) ? data.root.children : []

  return {
    id: data?.id || 'page-home',
    title: data?.title || '未命名页面',
    version: 1,
    root: {
      id: data?.root?.id || 'root',
      type: 'page',
      children: children.map((node) => normalizeNode(node)),
    },
  }
}

function loadSavedSchema() {
  const stored = localStorage.getItem(STORAGE_KEY)
  if (!stored) return

  try {
    const parsed = JSON.parse(stored) as Partial<PageSchema>
    pageSchema.value = normalizePageSchema(parsed)
  } catch (error) {
    console.error('Failed to restore web editor schema:', error)
  }
}

function saveSchema() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(exportSchema.value))
  syncSchemaText()
}

const selectNode = (id: null | string) => {
  selectedId.value = id
}

const onAddToCanvas = (e: DraggableEvent) => {
  const newIndex = (e as any).newIndex as number | undefined
  if (typeof newIndex !== 'number') return

  const inserted = canvas.value[newIndex] as PageNode | PaletteItem | undefined
  if (!inserted) return

  if (!('id' in inserted)) {
    const created = createNodeFromPalette(inserted)
    canvas.value.splice(newIndex, 1, created)
    selectNode(created.id)
    return
  }

  selectNode(inserted.id)
}

const onUpdateCanvas = () => {
  if (selectedId.value && !findNodeById(canvas.value, selectedId.value)) {
    selectNode(null)
  }
}

const handleNodeClick = (id: string) => {
  selectNode(id)
}

const handleCanvasBackgroundClick = () => {
  selectNode(null)
}

const handleDeleteSelected = () => {
  if (!selectedId.value) return
  if (!removeNodeById(canvas.value, selectedId.value)) return
  selectNode(null)
}

const handleClearCanvas = () => {
  canvas.value = []
  selectNode(null)
}

const handleCopySchema = async () => {
  syncSchemaText()
  try {
    await navigator.clipboard.writeText(schemaText.value)
    exportCopied.value = true
    window.setTimeout(() => {
      exportCopied.value = false
    }, 1500)
  } catch (error) {
    console.error('Failed to copy schema:', error)
  }
}

const handleDropToCanvas = (event: DragEvent) => {
  event.preventDefault()
  event.stopPropagation()
  const raw = event.dataTransfer?.getData('application/json') || event.dataTransfer?.getData('text/plain')
  if (!raw) return

  try {
    const item = JSON.parse(raw) as PaletteItem
    if (!item?.type || !nodeTypeSet.has(item.type as NodeType)) return

    const block = createNodeFromPalette(item)
    canvas.value.push(block)
    selectNode(block.id)
  } catch (error) {
    console.error('Failed to drop palette item to canvas:', error)
  }
}

const handlePaletteDragStart = (event: DragEvent, item: PaletteItem) => {
  const payload = JSON.stringify(item)
  event.dataTransfer?.setData('application/json', payload)
  event.dataTransfer?.setData('text/plain', payload)
  if (event.dataTransfer) {
    event.dataTransfer.effectAllowed = 'copy'
  }
}

const updateSelectedProp = (key: string, value: unknown) => {
  if (!selectedBlock.value) return
  selectedBlock.value.props = { ...selectedBlock.value.props, [key]: value } as any
}

watch(
  pageSchema,
  () => {
    saveSchema()
  },
  { deep: true },
)

watch(selectedId, (id) => {
  if (id && !findNodeById(canvas.value, id)) {
    selectNode(null)
  }
})

watch(previewDevice, async () => {
  await nextTick()
})

loadSavedSchema()
syncSchemaText()
</script>

<template>
  <div class="web-editor-page">
    <div class="page-title">网页编辑</div>

    <div class="web-box">
      <!-- 左侧：模块库 -->
      <!-- 提供可拖拽的模块模板，拖到中间画布后会生成真正的模块实例 -->
      <section class="panel left">
        <div class="panel-title">模块库</div>
        <VueDraggable
          v-model="palette"
          :group="{ name: 'blocks', pull: 'clone', put: false }"
          :sort="false"
          :clone="(item) => ({
            ...item,
            defaultProps: JSON.parse(JSON.stringify(item.defaultProps || {})),
            defaultChildren: item.defaultChildren?.map(cloneNode),
          })"
          item-key="name"
          class="palette-list"
        >
          <div
            v-for="item in palette"
            :key="item.type"
            class="palette-item"
            draggable="true"
            @dragstart="handlePaletteDragStart($event, item)"
          >
            {{ item.name }}
          </div>
        </VueDraggable>
        <p class="hint">拖拽到中间画布生成模块</p>
        <div class="editor-status">
          <span>模块数：{{ canvas.length }}</span>
          <span>状态：本地自动保存</span>
        </div>
      </section>

      <!-- 中间：画布与预览区 -->
      <!-- 画布实际渲染在 iframe 内部，以获得更接近真实页面的隔离预览环境 -->
      <section class="panel center">
        <div class="panel-title panel-title--canvas">
          <div class="title-left">
            <span>画布</span>
            <span class="preview-size">{{ previewWidthLabel }}</span>
          </div>
          <div class="toolbar-actions">
            <!-- 设备切换：只影响预览宽度，不影响 schema 数据本身 -->
            <div class="device-switcher" role="tablist" aria-label="预览设备切换">
              <button
                v-for="device in previewDevices"
                :key="device.value"
                type="button"
                class="device-btn"
                :class="{ active: previewDevice === device.value }"
                @click="previewDevice = device.value"
              >
                {{ device.label }}
              </button>
            </div>
            <button class="mini-btn mini-btn--ghost" type="button" @click="handleClearCanvas" :disabled="canvas.length === 0">
              清空画布
            </button>
            <button class="mini-btn" type="button" @click="handleDeleteSelected" :disabled="!selectedBlock">
              删除选中
            </button>
          </div>
        </div>

        <div class="canvas-shell">
            <div class="pure-canvas-stage" :class="`is-${previewDevice}`">
              <div
                class="pure-canvas-surface"
                :style="previewFrameStyle"
                @dragover.prevent
                @drop="handleDropToCanvas"
                @click="handleCanvasBackgroundClick"
              >
                <VueDraggable
                  v-model="canvas"
                  :group="{ name: 'canvas-blocks', pull: false, put: false }"
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
                  >
                    <SchemaRenderer :nodes="[block]" :selected-id="selectedId" @node-click="handleNodeClick" />
                  </div>

                  <template #footer>
                    <div v-if="canvas.length === 0" class="empty empty-canvas">
                      <div class="empty-title">开始搭建页面</div>
                      <div class="empty-desc">把左侧模块拖进这个画布区域，系统会自动保存当前画布</div>
                    </div>
                  </template>
                </VueDraggable>
              </div>
            </div>
        </div>
      </section>

      <!-- 右侧：属性编辑与 schema 导出 -->
      <section class="panel right">
        <div class="panel-title">属性</div>

        <!-- 未选中模块时，只展示提示 -->
        <div v-if="!selectedBlock" class="empty">选择一个画布模块以编辑属性</div>

        <!-- 已选中模块时，根据模块类型展示不同的属性表单 -->
        <div v-else class="prop-form">
          <div class="prop-row">
            <div class="prop-label">模块</div>
            <div class="prop-value">{{ selectedBlock.name }}</div>
          </div>

          <!-- 文本模块属性 -->
          <template v-if="isTextBlock(selectedBlock)">
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

          <!-- 导航模块属性 -->
          <template v-else-if="isNavBlock(selectedBlock)">
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

          <!-- 内容容器属性 -->
          <template v-else-if="isContentBlock(selectedBlock)">
            <div class="prop-row">
              <label class="prop-label">标题</label>
              <input
                class="prop-input"
                type="text"
                :value="selectedBlock.props.title"
                @input="updateSelectedProp('title', ($event.target as HTMLInputElement).value)"
              />
            </div>

            <div class="prop-row">
              <label class="prop-label">背景色</label>
              <input
                class="prop-input"
                type="color"
                :value="selectedBlock.props.background || '#ffffff'"
                @input="updateSelectedProp('background', ($event.target as HTMLInputElement).value)"
              />
            </div>

            <div class="prop-row">
              <label class="prop-label">内边距</label>
              <input
                class="prop-input"
                type="number"
                min="0"
                :value="selectedBlock.props.padding ?? 24"
                @input="updateSelectedProp('padding', Number(($event.target as HTMLInputElement).value || 0))"
              />
            </div>

            <div class="prop-row">
              <div class="prop-label">子模块数</div>
              <div class="prop-value">{{ selectedBlock.children?.length || 0 }}</div>
            </div>
          </template>
        </div>

        <!-- schema 导出区：用于复制当前页面结构 JSON -->
        <div class="schema-panel">
          <div class="schema-head">
            <span>Schema 导出</span>
            <button class="mini-btn" type="button" @click="handleCopySchema">
              {{ exportCopied ? '已复制' : '复制 JSON' }}
            </button>
          </div>
          <textarea
            class="schema-output"
            :value="schemaText"
            readonly
            spellcheck="false"
          />
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

.panel-title--canvas {
  gap: 12px;
  flex-wrap: wrap;
}

.title-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.preview-size {
  padding: 2px 8px;
  border-radius: 999px;
  background: rgba(22, 119, 255, 0.1);
  color: #1677ff;
  font-size: 12px;
  font-weight: 500;
}

.toolbar-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
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

.editor-status {
  margin-top: auto;
  display: grid;
  gap: 6px;
  padding-top: 8px;
  font-size: 12px;
  color: #5b6475;
}

.device-switcher {
  display: inline-flex;
  padding: 3px;
  border-radius: 999px;
  background: #f2f4f7;
  border: 1px solid rgba(0, 0, 0, 0.06);
}

.device-btn {
  border: none;
  background: transparent;
  border-radius: 999px;
  padding: 6px 12px;
  font-size: 12px;
  color: #4b5565;
  cursor: pointer;
}

.device-btn.active {
  background: #1677ff;
  color: #fff;
}

.canvas-shell {
  position: relative;
  flex: 1;
  min-height: 0;
  overflow: auto;
  border-radius: 14px;
  background:
    radial-gradient(circle at top, rgba(129, 140, 248, 0.14), transparent 28%),
    linear-gradient(180deg, #eef2ff 0%, #e2e8f0 100%);
}

.pure-canvas-stage {
  display: flex;
  min-height: 100%;
}

.pure-canvas-stage.is-desktop {
  justify-content: stretch;
}

.pure-canvas-stage.is-tablet,
.pure-canvas-stage.is-mobile {
  justify-content: center;
}

.pure-canvas-surface {
  min-height: 100%;
  padding: 24px;
}

.canvas {
  min-height: 640px;
  display: grid;
  gap: 12px;
  align-content: start;
}

.canvas-block {
  position: relative;
  padding: 0;
  margin: 0;
  border: 1px dashed #000;
  border-radius: 0;
  background: transparent;
  cursor: pointer;
  transition: border-color 0.15s ease;
}

.canvas-block:hover {
  border-color: #000;
  box-shadow: none;
}

.canvas-block.selected {
  border: 1px solid #0099ff;
  box-shadow: none;
}

.drag-ghost {
  opacity: 0.45;
}

.drag-chosen {
  opacity: 0.92;
}

.empty {
  color: #888;
  font-size: 13px;
  padding: 12px;
  border: 1px dashed rgba(0, 0, 0, 0.14);
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.9);
}

.empty-canvas {
  min-height: 280px;
  display: grid;
  place-content: center;
  gap: 8px;
  text-align: center;
  border-style: dashed;
  border-color: rgba(22, 119, 255, 0.2);
  background: rgba(255, 255, 255, 0.75);
}

.empty-title {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.empty-desc {
  max-width: 320px;
  line-height: 1.6;
  color: #667085;
}

.mini-btn {
  border: 1px solid rgba(0, 0, 0, 0.12);
  background: #fff;
  border-radius: 8px;
  padding: 6px 10px;
  cursor: pointer;
  font-size: 12px;
}

.mini-btn--ghost {
  background: rgba(255, 255, 255, 0.7);
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

.schema-panel {
  margin-top: auto;
  display: grid;
  gap: 8px;
  padding-top: 8px;
  border-top: 1px solid rgba(0, 0, 0, 0.06);
}

.schema-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 13px;
  font-weight: 600;
}

.schema-output {
  width: 100%;
  min-height: 220px;
  resize: vertical;
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid rgba(0, 0, 0, 0.12);
  background: #0f172a;
  color: #dbeafe;
  font-size: 12px;
  line-height: 1.6;
  font-family: Consolas, "Courier New", monospace;
}
</style>
