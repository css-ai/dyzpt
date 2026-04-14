<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, provide, ref } from 'vue'

import { AUTO_SAVE_DELAY, HISTORY_MAX, paletteCategories as paletteCategoriesSource, previewDevices, STORAGE_KEY } from './components/config'
import { renderEditorNode } from './components/render-node'
import { cloneNode, createEmptySchema, createNodeFromPalette, findNodeById, findParentNode, insertNodeAt, removeNodeById } from './components/schema'
import type { HistoryEntry, PageNode, PageSchema, PaletteItem, PreviewDevice } from './components/types'

const pageSchema = ref<PageSchema>(createEmptySchema())
const selectedId = ref<null | string>(null)
const previewDevice = ref<PreviewDevice>('desktop')
const schemaText = ref('')
const exportCopied = ref(false)
const showHistory = ref(false)
const sidebarTab = ref<'components' | 'layers' | 'settings'>('components')
const zoom = ref(1)
const isDragging = ref(false)
const searchKeyword = ref('')
const undoStack = ref<HistoryEntry[]>([])
const redoStack = ref<HistoryEntry[]>([])
const autoSaveTimer = ref<number | null>(null)
const paletteCategories = ref(paletteCategoriesSource)

const canvas = computed<PageNode[]>({
  get: () => pageSchema.value.root.children || [],
  set: (value) => {
    pageSchema.value.root.children = value
  },
})

const selectedNode = computed(() => {
  if (!selectedId.value) return null
  return findNodeById(pageSchema.value.root, selectedId.value)
})

const previewWidth = computed(() => previewDevices.find((device) => device.value === previewDevice.value)?.width)

const filteredCategories = computed(() => {
  if (!searchKeyword.value) return paletteCategories.value
  const keyword = searchKeyword.value.toLowerCase()
  return paletteCategories.value
    .map((category) => ({
      ...category,
      items: category.items.filter((item) => item.name.toLowerCase().includes(keyword) || item.description.toLowerCase().includes(keyword)),
    }))
    .filter((category) => category.items.length > 0)
})

function syncSchemaText() {
  schemaText.value = JSON.stringify(pageSchema.value, null, 2)
}

function saveToHistory(action: string) {
  undoStack.value.push({
    schema: JSON.parse(JSON.stringify(pageSchema.value)),
    timestamp: Date.now(),
    action,
  })

  if (undoStack.value.length > HISTORY_MAX) {
    undoStack.value.shift()
  }

  redoStack.value = []
}

function saveSchema() {
  pageSchema.value.updatedAt = Date.now()
  localStorage.setItem(STORAGE_KEY, JSON.stringify(pageSchema.value))
  syncSchemaText()

  if (autoSaveTimer.value) {
    clearTimeout(autoSaveTimer.value)
  }

  autoSaveTimer.value = window.setTimeout(() => {}, AUTO_SAVE_DELAY)
}

function loadSchema() {
  const stored = localStorage.getItem(STORAGE_KEY)
  if (!stored) {
    syncSchemaText()
    return
  }

  try {
    pageSchema.value = JSON.parse(stored) as PageSchema
    syncSchemaText()
  } catch (error) {
    console.error('Failed to load schema:', error)
  }
}

function addNode(node: PageNode, parentNode?: PageNode, index?: number) {
  const targetParent = parentNode || pageSchema.value.root
  insertNodeAt(targetParent, node, index)
  selectedId.value = node.id
  saveToHistory(`添加 ${node.name}`)
  saveSchema()
}

function updateNodeProps(nodeId: string, props: Record<string, any>) {
  const node = findNodeById(pageSchema.value.root, nodeId)
  if (!node) return

  node.props = { ...node.props, ...props }
  saveToHistory('更新属性')
  saveSchema()
}

function deleteNode(nodeId: string) {
  const node = findNodeById(pageSchema.value.root, nodeId)
  if (!node || nodeId === pageSchema.value.root.id) return

  removeNodeById(pageSchema.value.root, nodeId)
  if (selectedId.value === nodeId) {
    selectedId.value = null
  }
  saveToHistory(`删除 ${node.name || '节点'}`)
  saveSchema()
}

function duplicateNode(nodeId: string) {
  const node = findNodeById(pageSchema.value.root, nodeId)
  if (!node || nodeId === pageSchema.value.root.id) return

  const parent = findParentNode(pageSchema.value.root, nodeId)
  if (!parent) return

  const clone = cloneNode(node, true)
  clone.name = `${node.name} (副本)`
  const index = parent.children?.findIndex((child) => child.id === nodeId) ?? -1
  insertNodeAt(parent, clone, index + 1)
  selectedId.value = clone.id
  saveToHistory(`复制 ${node.name}`)
  saveSchema()
}

function undo() {
  if (undoStack.value.length === 0) return

  const previous = undoStack.value.pop()!
  redoStack.value.push({
    schema: JSON.parse(JSON.stringify(pageSchema.value)),
    timestamp: Date.now(),
    action: 'undo',
  })
  pageSchema.value = previous.schema
  selectedId.value = null
  saveSchema()
}

function redo() {
  if (redoStack.value.length === 0) return

  const next = redoStack.value.pop()!
  undoStack.value.push({
    schema: JSON.parse(JSON.stringify(pageSchema.value)),
    timestamp: Date.now(),
    action: 'redo',
  })
  pageSchema.value = next.schema
  selectedId.value = null
  saveSchema()
}

function handleDragStart(event: DragEvent, item: PaletteItem) {
  if (event.dataTransfer) {
    event.dataTransfer.setData('application/json', JSON.stringify(item))
    event.dataTransfer.effectAllowed = 'copy'
  }
  isDragging.value = true
}

function handleDragEnd() {
  isDragging.value = false
}

function handleDropToCanvas(event: DragEvent, targetNode?: PageNode) {
  event.preventDefault()
  event.stopPropagation()
  isDragging.value = false

  const rawData = event.dataTransfer?.getData('application/json')
  if (!rawData) return

  try {
    const item = JSON.parse(rawData) as PaletteItem
    const newNode = createNodeFromPalette(item)

    if (targetNode && (targetNode.type === 'container' || targetNode.type === 'section')) {
      addNode(newNode, targetNode)
      return
    }

    addNode(newNode)
  } catch (error) {
    console.error('Failed to drop item:', error)
  }
}

function exportSchema() {
  const dataStr = JSON.stringify(pageSchema.value, null, 2)
  const blob = new Blob([dataStr], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `${pageSchema.value.title || 'page'}.json`
  link.click()
  URL.revokeObjectURL(url)
}

function importSchema(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return

  const reader = new FileReader()
  reader.onload = (loadEvent) => {
    try {
      const content = loadEvent.target?.result as string
      pageSchema.value = JSON.parse(content) as PageSchema
      selectedId.value = null
      saveToHistory('导入 Schema')
      saveSchema()
    } catch (error) {
      console.error('Failed to import schema:', error)
      alert('导入失败：文件格式不正确')
    }
  }
  reader.readAsText(file)
  input.value = ''
}

function copySchemaToClipboard() {
  navigator.clipboard.writeText(schemaText.value)
  exportCopied.value = true
  window.setTimeout(() => {
    exportCopied.value = false
  }, 2000)
}

function resetSchema() {
  if (!confirm('确定要重置所有内容吗？此操作不可撤销。')) return

  pageSchema.value = createEmptySchema()
  selectedId.value = null
  undoStack.value = []
  redoStack.value = []
  saveToHistory('重置页面')
  saveSchema()
}

function selectNode(id: string) {
  selectedId.value = id
}

function handleKeydown(event: KeyboardEvent) {
  const isMac = navigator.platform.toUpperCase().includes('MAC')
  const cmdOrCtrl = isMac ? event.metaKey : event.ctrlKey

  if (cmdOrCtrl && event.key === 'z') {
    event.preventDefault()
    if (event.shiftKey) {
      redo()
    } else {
      undo()
    }
    return
  }

  if (cmdOrCtrl && event.key === 'y') {
    event.preventDefault()
    redo()
    return
  }

  if (event.key === 'Delete' && selectedId.value) {
    event.preventDefault()
    deleteNode(selectedId.value)
    return
  }

  if (cmdOrCtrl && event.key === 'd' && selectedId.value) {
    event.preventDefault()
    duplicateNode(selectedId.value)
    return
  }

  if (cmdOrCtrl && event.key === 's') {
    event.preventDefault()
    saveSchema()
  }
}

onMounted(() => {
  loadSchema()
  saveToHistory('初始化')
  window.addEventListener('keydown', handleKeydown)
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', handleKeydown)
  if (autoSaveTimer.value) {
    clearTimeout(autoSaveTimer.value)
  }
})

const renderNode = (node: PageNode) => renderEditorNode(node, {
  handleDropToCanvas,
  selectedId: selectedId.value,
  selectNode,
  updateNodeProps,
})

provide('renderNode', renderNode)
</script>

<template>
  <div class="enterprise-editor" @dragover.prevent>
    <header class="editor-header">
      <div class="header-left">
        <div class="logo">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="3" width="18" height="18" rx="2" />
            <path d="M3 9h18" />
            <path d="M9 21V9" />
          </svg>
          <span>企业级编辑器</span>
        </div>
        <div class="page-info">
          <input v-model="pageSchema.title" class="page-title-input" @blur="saveSchema" placeholder="页面标题" />
        </div>
      </div>

      <div class="header-center">
        <div class="device-switcher">
          <button v-for="device in previewDevices" :key="device.value" class="device-btn"
            :class="{ active: previewDevice === device.value }" @click="previewDevice = device.value">
            {{ device.label }}
          </button>
        </div>
        <div class="zoom-control">
          <button class="zoom-btn" @click="zoom = Math.max(0.5, zoom - 0.1)">-</button>
          <span class="zoom-value">{{ Math.round(zoom * 100) }}%</span>
          <button class="zoom-btn" @click="zoom = Math.min(2, zoom + 0.1)">+</button>
        </div>
      </div>

      <div class="header-right">
        <button class="tool-btn" @click="undo" :disabled="undoStack.length === 0" title="撤销 (Ctrl+Z)">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M3 7v6h6" />
            <path d="M21 17a9 9 0 0 0-9-9 9 9 0 0 0-6 2.3L3 13" />
          </svg>
        </button>
        <button class="tool-btn" @click="redo" :disabled="redoStack.length === 0" title="重做 (Ctrl+Y)">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 7v6h-6" />
            <path d="M3 17a9 9 0 0 1 9-9 9 9 0 0 1 6 2.3L21 13" />
          </svg>
        </button>
        <div class="divider"></div>
        <button class="tool-btn" @click="exportSchema" title="导出 JSON">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="7 10 12 15 17 10" />
            <line x1="12" y1="15" x2="12" y2="3" />
          </svg>
        </button>
        <button class="tool-btn tool-btn--primary" @click="copySchemaToClipboard">
          {{ exportCopied ? '已复制' : '复制 JSON' }}
        </button>
        <button class="tool-btn tool-btn--danger" @click="resetSchema" title="重置">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="3 6 5 6 21 6" />
            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
          </svg>
        </button>
      </div>
    </header>

    <div class="editor-main">
      <aside class="sidebar sidebar--left">
        <div class="sidebar-tabs">
          <button class="sidebar-tab" :class="{ active: sidebarTab === 'components' }" @click="sidebarTab = 'components'">📦 组件</button>
          <button class="sidebar-tab" :class="{ active: sidebarTab === 'layers' }" @click="sidebarTab = 'layers'">📋 图层</button>
          <button class="sidebar-tab" :class="{ active: sidebarTab === 'settings' }" @click="sidebarTab = 'settings'">⚙️ 设置</button>
        </div>

        <div class="sidebar-content">
          <div v-show="sidebarTab === 'components'" class="components-panel">
            <div class="search-box">
              <input v-model="searchKeyword" type="text" placeholder="搜索组件..." class="search-input" />
            </div>
            <div v-for="category in filteredCategories" :key="category.name" class="component-category">
              <div class="category-header">
                <span class="category-icon">{{ category.icon }}</span>
                <span class="category-name">{{ category.name }}</span>
              </div>
              <div class="component-grid">
                <div v-for="item in category.items" :key="`${category.name}-${item.type}`" class="component-card" draggable="true"
                  @dragstart="handleDragStart($event, item)" @dragend="handleDragEnd">
                  <div class="component-icon">{{ item.icon }}</div>
                  <div class="component-info">
                    <div class="component-name">{{ item.name }}</div>
                    <div class="component-desc">{{ item.description }}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div v-show="sidebarTab === 'layers'" class="layers-panel">
            <div class="layers-header">
              <span>页面结构</span>
              <button class="icon-btn" @click="showHistory = !showHistory">📜</button>
            </div>
            <div class="layers-tree">
              <div class="layer-node layer-node--root">
                <div class="layer-info" @click="selectedId = null">
                  <span class="layer-icon">📄</span>
                  <span class="layer-name">{{ pageSchema.title || '页面根节点' }}</span>
                </div>
                <div class="layer-children">
                  <template v-for="node in canvas" :key="node.id">
                    <div class="layer-node" :class="{ active: selectedId === node.id }">
                      <div class="layer-info" @click="selectedId = node.id">
                        <span class="layer-icon">{{
                          node.type === 'section' ? '📦' :
                            node.type === 'container' ? '🗃️' :
                              node.type === 'text' ? '📝' :
                                node.type === 'image' ? '🖼️' :
                                  node.type === 'button' ? '🔘' :
                                    node.type === 'nav' ? '🧭' :
                                      node.type === 'hero' ? '🌟' :
                                        node.type === 'features' ? '✨' : '📋'
                        }}</span>
                        <span class="layer-name">{{ node.name }}</span>
                      </div>
                      <div class="layer-actions">
                        <button class="layer-action" @click.stop="duplicateNode(node.id)" title="复制">📋</button>
                        <button class="layer-action layer-action--danger" @click.stop="deleteNode(node.id)" title="删除">🗑️</button>
                      </div>
                      <div v-if="node.children?.length" class="layer-children">
                        <div v-for="child in node.children" :key="child.id" class="layer-node" :class="{ active: selectedId === child.id }">
                          <div class="layer-info" @click="selectedId = child.id">
                            <span class="layer-icon">📄</span>
                            <span class="layer-name">{{ child.name }}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </template>
                </div>
              </div>
            </div>
          </div>

          <div v-show="sidebarTab === 'settings'" class="settings-panel">
            <div class="setting-group">
              <label class="setting-label">页面标题</label>
              <input v-model="pageSchema.title" class="setting-input" @blur="saveSchema" />
            </div>
            <div class="setting-group">
              <label class="setting-label">页面描述</label>
              <textarea v-model="pageSchema.description" class="setting-textarea" rows="3" @blur="saveSchema"></textarea>
            </div>
            <div class="setting-group">
              <label class="setting-label">导入配置</label>
              <input type="file" accept=".json" @change="importSchema" class="setting-file" />
            </div>
            <div class="setting-group">
              <label class="setting-label">快捷键</label>
              <div class="shortcuts-list">
                <div class="shortcut-item"><kbd>Ctrl+Z</kbd><span>撤销</span></div>
                <div class="shortcut-item"><kbd>Ctrl+Y</kbd><span>重做</span></div>
                <div class="shortcut-item"><kbd>Delete</kbd><span>删除选中</span></div>
                <div class="shortcut-item"><kbd>Ctrl+D</kbd><span>复制选中</span></div>
              </div>
            </div>
          </div>
        </div>
      </aside>

      <main class="canvas-area">
        <div class="canvas-container" :style="{ transform: `scale(${zoom})`, transformOrigin: 'top center' }">
          <div class="canvas-preview" :style="{ maxWidth: previewWidth ? `${previewWidth}px` : '100%', margin: '0 auto' }">
            <div class="canvas-surface" @dragover.prevent @drop="handleDropToCanvas($event)" @click="selectedId = null">
              <div v-if="canvas.length === 0" class="empty-canvas">
                <div class="empty-icon">🎨</div>
                <div class="empty-title">开始构建你的页面</div>
                <div class="empty-desc">从左侧组件库拖拽组件到此处，或点击组件添加</div>
              </div>
              <div v-else class="canvas-nodes">
                <component v-for="node in canvas" :key="node.id" :is="renderNode(node)" />
              </div>
            </div>
          </div>
        </div>
      </main>

      <aside class="sidebar sidebar--right">
        <div class="sidebar-header"><span>属性设置</span></div>
        <div class="sidebar-content">
          <div v-if="!selectedNode" class="empty-props">
            <div class="empty-icon">🔧</div>
            <div class="empty-text">选择一个组件以编辑属性</div>
          </div>
          <div v-else class="props-form">
            <div class="prop-group">
              <label class="prop-label">组件名称</label>
              <input v-model="selectedNode.name" class="prop-input" @blur="saveSchema" />
            </div>

            <template v-if="selectedNode.type === 'text'">
              <div class="prop-group">
                <label class="prop-label">文本内容</label>
                <textarea v-model="selectedNode.props.text" class="prop-textarea" rows="4" @blur="saveSchema"></textarea>
              </div>
              <div class="prop-group">
                <label class="prop-label">对齐方式</label>
                <select v-model="selectedNode.props.align" class="prop-select" @change="saveSchema">
                  <option value="left">左对齐</option>
                  <option value="center">居中</option>
                  <option value="right">右对齐</option>
                  <option value="justify">两端对齐</option>
                </select>
              </div>
              <div class="prop-group">
                <label class="prop-label">字号 (px)</label>
                <input type="number" v-model="selectedNode.props.fontSize" class="prop-input" @blur="saveSchema" />
              </div>
              <div class="prop-group">
                <label class="prop-label">文字颜色</label>
                <input type="color" v-model="selectedNode.props.color" class="prop-color" @change="saveSchema" />
              </div>
            </template>

            <template v-if="selectedNode.type === 'image'">
              <div class="prop-group">
                <label class="prop-label">图片地址</label>
                <input v-model="selectedNode.props.src" class="prop-input" @blur="saveSchema" />
              </div>
              <div class="prop-group">
                <label class="prop-label">替代文本</label>
                <input v-model="selectedNode.props.alt" class="prop-input" @blur="saveSchema" />
              </div>
            </template>

            <template v-if="selectedNode.type === 'button'">
              <div class="prop-group">
                <label class="prop-label">按钮文字</label>
                <input v-model="selectedNode.props.text" class="prop-input" @blur="saveSchema" />
              </div>
              <div class="prop-group">
                <label class="prop-label">按钮类型</label>
                <select v-model="selectedNode.props.type" class="prop-select" @change="saveSchema">
                  <option value="primary">主要按钮</option>
                  <option value="secondary">次要按钮</option>
                  <option value="outline">线框按钮</option>
                  <option value="text">文本按钮</option>
                </select>
              </div>
              <div class="prop-group">
                <label class="prop-label">链接地址</label>
                <input v-model="selectedNode.props.href" class="prop-input" @blur="saveSchema" />
              </div>
            </template>

            <template v-if="selectedNode.type === 'container' || selectedNode.type === 'section'">
              <div class="prop-group">
                <label class="prop-label">背景颜色</label>
                <input type="color" v-model="selectedNode.props.background" class="prop-color" @change="saveSchema" />
              </div>
              <div class="prop-group">
                <label class="prop-label">内边距</label>
                <div class="prop-padding">
                  <input type="number" placeholder="上" v-model="selectedNode.props.padding.top" class="prop-padding-input" @blur="saveSchema" />
                  <input type="number" placeholder="右" v-model="selectedNode.props.padding.right" class="prop-padding-input" @blur="saveSchema" />
                  <input type="number" placeholder="下" v-model="selectedNode.props.padding.bottom" class="prop-padding-input" @blur="saveSchema" />
                  <input type="number" placeholder="左" v-model="selectedNode.props.padding.left" class="prop-padding-input" @blur="saveSchema" />
                </div>
              </div>
              <div class="prop-group">
                <label class="prop-label">最大宽度</label>
                <input v-model="selectedNode.props.maxWidth" class="prop-input" placeholder="如: 1200px" @blur="saveSchema" />
              </div>
              <div class="prop-group">
                <label class="prop-label">布局方式</label>
                <select v-model="selectedNode.props.layout" class="prop-select" @change="saveSchema">
                  <option value="flex">Flex 布局</option>
                  <option value="grid">Grid 布局</option>
                </select>
              </div>
              <div v-if="selectedNode.props.layout === 'grid'" class="prop-group">
                <label class="prop-label">列数</label>
                <input type="number" v-model="selectedNode.props.columns" class="prop-input" @blur="saveSchema" />
              </div>
            </template>

            <template v-if="selectedNode.type === 'nav'">
              <div class="prop-group">
                <label class="prop-label">菜单项</label>
                <div v-for="(item, idx) in selectedNode.props.items" :key="idx" class="prop-menu-item">
                  <input v-model="item.label" class="prop-input" placeholder="菜单文字" @blur="saveSchema" />
                  <input v-model="item.href" class="prop-input" placeholder="链接" @blur="saveSchema" />
                  <button class="prop-remove-btn" @click="selectedNode.props.items.splice(idx, 1); saveSchema()">✕</button>
                </div>
                <button class="prop-add-btn" @click="(selectedNode.props.items ||= []).push({ label: '新菜单', href: '/' }); saveSchema()">
                  + 添加菜单项
                </button>
              </div>
            </template>

            <template v-if="selectedNode.type === 'hero'">
              <div class="prop-group">
                <label class="prop-label">主标题</label>
                <input v-model="selectedNode.props.title" class="prop-input" @blur="saveSchema" />
              </div>
              <div class="prop-group">
                <label class="prop-label">副标题</label>
                <textarea v-model="selectedNode.props.subtitle" class="prop-textarea" rows="2" @blur="saveSchema"></textarea>
              </div>
              <div class="prop-group">
                <label class="prop-label">按钮文字</label>
                <input v-model="selectedNode.props.buttonText" class="prop-input" @blur="saveSchema" />
              </div>
            </template>

            <div class="prop-actions">
              <button class="prop-action-btn" @click="duplicateNode(selectedNode.id)">复制组件</button>
              <button class="prop-action-btn prop-action-btn--danger" @click="deleteNode(selectedNode.id)">删除组件</button>
            </div>
          </div>
        </div>
      </aside>
    </div>

    <div v-if="showHistory" class="modal-overlay" @click="showHistory = false">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>历史记录</h3>
          <button class="modal-close" @click="showHistory = false">✕</button>
        </div>
        <div class="modal-body">
          <div v-for="entry in [...undoStack].reverse()" :key="entry.timestamp" class="history-item">
            <span class="history-action">{{ entry.action }}</span>
            <span class="history-time">{{ new Date(entry.timestamp).toLocaleString() }}</span>
          </div>
          <div v-if="undoStack.length === 0" class="history-empty">暂无历史记录</div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.enterprise-editor {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #f1f5f9;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

.editor-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 20px;
  background: #ffffff;
  border-bottom: 1px solid #e2e8f0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  z-index: 10;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 24px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 16px;
  color: #1e293b;
}

.page-title-input {
  padding: 6px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  background: #f8fafc;
  transition: all 0.2s;
}

.page-title-input:focus {
  outline: none;
  border-color: #3b82f6;
  background: #ffffff;
}

.header-center {
  display: flex;
  align-items: center;
  gap: 16px;
}

.device-switcher {
  display: flex;
  gap: 4px;
  padding: 4px;
  background: #f1f5f9;
  border-radius: 12px;
}

.device-btn {
  padding: 6px 16px;
  border: none;
  background: transparent;
  border-radius: 8px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.device-btn.active {
  background: #ffffff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  font-weight: 500;
}

.zoom-control {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #f1f5f9;
  padding: 4px 12px;
  border-radius: 20px;
}

.zoom-btn {
  width: 24px;
  height: 24px;
  border: none;
  background: transparent;
  border-radius: 50%;
  cursor: pointer;
  font-size: 16px;
}

.zoom-value {
  font-size: 13px;
  min-width: 45px;
  text-align: center;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.tool-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border: 1px solid #e2e8f0;
  background: #ffffff;
  border-radius: 8px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.tool-btn:hover {
  background: #f8fafc;
  border-color: #cbd5e1;
}

.tool-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.tool-btn--primary {
  background: #3b82f6;
  border-color: #3b82f6;
  color: #ffffff;
}

.tool-btn--primary:hover {
  background: #2563eb;
}

.tool-btn--danger:hover {
  border-color: #ef4444;
  color: #ef4444;
}

.divider {
  width: 1px;
  height: 24px;
  background: #e2e8f0;
  margin: 0 4px;
}

.editor-main {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.sidebar {
  width: 280px;
  background: #ffffff;
  border-right: 1px solid #e2e8f0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.sidebar--right {
  border-right: none;
  border-left: 1px solid #e2e8f0;
}

.sidebar-tabs {
  display: flex;
  border-bottom: 1px solid #e2e8f0;
  padding: 0 12px;
}

.sidebar-tab {
  padding: 12px 16px;
  border: none;
  background: transparent;
  font-size: 13px;
  cursor: pointer;
  color: #64748b;
  transition: all 0.2s;
}

.sidebar-tab.active {
  color: #3b82f6;
  border-bottom: 2px solid #3b82f6;
}

.sidebar-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.search-box {
  margin-bottom: 16px;
}

.search-input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 13px;
}

.component-category {
  margin-bottom: 20px;
}

.category-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  font-size: 13px;
  font-weight: 600;
  color: #1e293b;
}

.component-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 8px;
}

.component-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  cursor: grab;
  transition: all 0.2s;
}

.component-card:hover {
  background: #f1f5f9;
  border-color: #cbd5e1;
  transform: translateY(-1px);
}

.component-icon {
  font-size: 20px;
}

.component-info {
  flex: 1;
}

.component-name {
  font-size: 13px;
  font-weight: 500;
  color: #1e293b;
}

.component-desc {
  font-size: 11px;
  color: #64748b;
}

.layers-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  font-size: 13px;
  font-weight: 500;
}

.layers-tree {
  font-size: 13px;
}

.layer-node {
  margin-left: 16px;
  padding: 4px 0;
}

.layer-node--root {
  margin-left: 0;
}

.layer-info {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.2s;
}

.layer-info:hover {
  background: #f1f5f9;
}

.layer-node.active .layer-info {
  background: #eff6ff;
  color: #3b82f6;
}

.layer-icon {
  font-size: 14px;
}

.layer-name {
  font-size: 12px;
}

.layer-actions {
  display: flex;
  gap: 4px;
  margin-left: auto;
}

.layer-action {
  padding: 2px 6px;
  border: none;
  background: transparent;
  cursor: pointer;
  opacity: 0.6;
}

.layer-action:hover {
  opacity: 1;
}

.layer-action--danger:hover {
  color: #ef4444;
}

.layer-children {
  margin-left: 20px;
}

.setting-group {
  margin-bottom: 20px;
}

.setting-label {
  display: block;
  font-size: 12px;
  font-weight: 500;
  color: #64748b;
  margin-bottom: 6px;
}

.setting-input,
.setting-textarea,
.setting-file {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 13px;
}

.setting-textarea {
  resize: vertical;
}

.shortcuts-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.shortcut-item {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
}

kbd {
  padding: 2px 6px;
  background: #f1f5f9;
  border-radius: 4px;
  font-family: monospace;
  font-size: 11px;
}

.canvas-area {
  flex: 1;
  overflow: auto;
  padding: 20px;
}

.canvas-container {
  transition: transform 0.2s ease;
}

.canvas-preview {
  transition: max-width 0.3s ease;
}

.canvas-surface {
  min-height: calc(100vh - 120px);
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
}

.empty-canvas {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 500px;
  text-align: center;
  padding: 60px 20px;
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 20px;
  opacity: 0.5;
}

.empty-title {
  font-size: 18px;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 8px;
}

.empty-desc {
  font-size: 14px;
  color: #64748b;
}

.canvas-nodes {
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  padding: 12px 16px;
  border-bottom: 1px solid #e2e8f0;
  font-weight: 600;
  font-size: 14px;
}

.empty-props {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
}

.empty-text {
  font-size: 13px;
  color: #64748b;
  margin-top: 12px;
}

.props-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.prop-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.prop-label {
  font-size: 12px;
  font-weight: 500;
  color: #64748b;
}

.prop-input,
.prop-select,
.prop-textarea,
.prop-color {
  padding: 8px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 13px;
}

.prop-textarea {
  resize: vertical;
}

.prop-color {
  width: 60px;
  height: 36px;
  padding: 2px;
}

.prop-padding {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.prop-padding-input {
  min-width: 0;
  width: 100%;
  padding: 8px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 12px;
  text-align: center;
  box-sizing: border-box;
}

.prop-menu-item {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr) auto;
  gap: 6px;
  margin-bottom: 8px;
  align-items: center;
}

.prop-menu-item .prop-input {
  min-width: 0;
}

.prop-remove-btn {
  padding: 0 8px;
  border: 1px solid #e2e8f0;
  background: #ffffff;
  border-radius: 6px;
  cursor: pointer;
  flex-shrink: 0;
}

.prop-add-btn {
  width: 100%;
  margin-top: 4px;
  padding: 8px;
  border: 1px dashed #cbd5e1;
  background: #f8fafc;
  border-radius: 8px;
  cursor: pointer;
  font-size: 12px;
  color: #3b82f6;
}

.prop-actions {
  display: flex;
  gap: 8px;
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid #e2e8f0;
}

.prop-action-btn {
  flex: 1;
  padding: 8px;
  border: 1px solid #e2e8f0;
  background: #ffffff;
  border-radius: 8px;
  cursor: pointer;
  font-size: 12px;
}

.prop-action-btn--danger:hover {
  border-color: #ef4444;
  color: #ef4444;
}

.editor-node {
  position: relative;
  transition: all 0.2s ease;
}

.editor-node--selected {
  outline: 2px solid #3b82f6;
  outline-offset: 2px;
}

.container {
  background: transparent;
}

.container-placeholder {
  padding: 40px;
  text-align: center;
  color: #94a3b8;
  font-size: 14px;
  border: 2px dashed #e2e8f0;
  border-radius: 8px;
  background: #f8fafc;
}

.section-header {
  text-align: center;
  margin-bottom: 32px;
}

.section-title {
  font-size: 28px;
  font-weight: 700;
  margin-bottom: 12px;
}

.section-subtitle {
  font-size: 16px;
  color: #64748b;
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s;
}

.btn--primary {
  background: #3b82f6;
  color: #ffffff;
}

.btn--secondary {
  background: #64748b;
  color: #ffffff;
}

.btn--outline {
  background: transparent;
  border: 1px solid #3b82f6;
  color: #3b82f6;
}

.btn--text {
  background: transparent;
  color: #3b82f6;
}

.btn--small {
  padding: 6px 16px;
  font-size: 12px;
}

.btn--medium {
  padding: 8px 20px;
  font-size: 14px;
}

.btn--large {
  padding: 12px 28px;
  font-size: 16px;
}

.nav {
  background: #ffffff;
  border-bottom: 1px solid #e2e8f0;
}

.nav--dark {
  background: #1e293b;
  color: #ffffff;
}

.nav-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 1200px;
  margin: 0 auto;
  padding: 16px 24px;
}

.nav-logo {
  font-size: 20px;
  font-weight: 700;
}

.nav-items {
  display: flex;
  gap: 32px;
}

.nav-link {
  text-decoration: none;
  color: inherit;
  font-size: 14px;
}

.hero {
  position: relative;
  background-size: cover;
  background-position: center;
  min-height: 500px;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
}

.hero-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
}

.hero-content {
  position: relative;
  z-index: 1;
  color: #ffffff;
  max-width: 800px;
  padding: 40px;
}

.hero-title {
  font-size: 48px;
  font-weight: 800;
  margin-bottom: 20px;
}

.hero-subtitle {
  font-size: 20px;
  margin-bottom: 32px;
  opacity: 0.9;
}

.hero-btn {
  padding: 12px 32px;
  background: #3b82f6;
  border: none;
  border-radius: 8px;
  color: #ffffff;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
}

.features {
  padding: 60px 24px;
}

.features-title {
  text-align: center;
  font-size: 32px;
  font-weight: 700;
  margin-bottom: 40px;
}

.features-grid {
  display: grid;
  gap: 32px;
  max-width: 1200px;
  margin: 0 auto;
}

.features-grid--2 {
  grid-template-columns: repeat(2, 1fr);
}

.features-grid--3 {
  grid-template-columns: repeat(3, 1fr);
}

.features-grid--4 {
  grid-template-columns: repeat(4, 1fr);
}

.feature-card {
  text-align: center;
  padding: 24px;
}

.feature-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.feature-title {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 12px;
}

.feature-description {
  color: #64748b;
  font-size: 14px;
  line-height: 1.6;
}

.footer {
  background: #f8fafc;
  border-top: 1px solid #e2e8f0;
  padding: 40px 24px;
}

.footer--dark {
  background: #1e293b;
  color: #ffffff;
}

.footer-container {
  max-width: 1200px;
  margin: 0 auto;
  text-align: center;
}

.footer-links {
  display: flex;
  justify-content: center;
  gap: 32px;
  margin-bottom: 24px;
  flex-wrap: wrap;
}

.footer-link {
  text-decoration: none;
  color: inherit;
  font-size: 14px;
}

.footer-copyright {
  font-size: 12px;
  color: #64748b;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: #ffffff;
  border-radius: 12px;
  width: 400px;
  max-height: 80vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #e2e8f0;
}

.modal-close {
  border: none;
  background: transparent;
  font-size: 20px;
  cursor: pointer;
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 16px 20px;
}

.history-item {
  display: flex;
  justify-content: space-between;
  padding: 10px 0;
  border-bottom: 1px solid #f1f5f9;
  font-size: 13px;
}

.history-empty {
  text-align: center;
  color: #94a3b8;
  padding: 40px;
}

@media (max-width: 1024px) {
  .sidebar {
    width: 240px;
  }

  .features-grid--3,
  .features-grid--4 {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .editor-header {
    flex-wrap: wrap;
    gap: 12px;
  }

  .sidebar {
    width: 200px;
  }

  .hero-title {
    font-size: 32px;
  }

  .features-grid--2,
  .features-grid--3,
  .features-grid--4 {
    grid-template-columns: 1fr;
  }
}
</style>
