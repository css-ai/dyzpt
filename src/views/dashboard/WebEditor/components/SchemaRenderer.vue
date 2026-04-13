<script setup lang="ts">
import ModuleText from '#/views/dashboard/WebEditor/components/Text/index.vue'
import ModuleNavigation from '#/views/dashboard/WebEditor/components/Navigation/index.vue'

export type SchemaRendererNodeType = 'content' | 'text' | 'nav'

export type SchemaRendererTextProps = {
  align?: 'left' | 'center' | 'right'
  text?: string
}

export type SchemaRendererNavProps = {
  align?: 'left' | 'center' | 'right'
  items?: string[]
}

export type SchemaRendererContentProps = {
  background?: string
  padding?: number
  title?: string
}

export type SchemaRendererNode = {
  children?: SchemaRendererNode[]
  id: string
  name: string
  props:
    | Record<string, any>
    | SchemaRendererContentProps
    | SchemaRendererNavProps
    | SchemaRendererTextProps
  type: SchemaRendererNodeType
}

const props = withDefaults(defineProps<{
  nodes: SchemaRendererNode[]
  selectedId?: null | string
}>(), {
  selectedId: null,
})

const emit = defineEmits<{
  nodeClick: [id: string]
}>()

const componentMap: Partial<Record<SchemaRendererNodeType, any>> = {
  text: ModuleText,
  nav: ModuleNavigation,
}

const handleNodeClick = (id: string) => {
  emit('nodeClick', id)
}
</script>

<template>
  <div class="schema-renderer">
    <div
      v-for="node in props.nodes"
      :key="node.id"
      class="schema-renderer-node"
      :class="[`is-${node.type}`, { 'is-selected': props.selectedId === node.id }]"
      :data-node-id="node.id"
      :data-node-type="node.type"
      @click.stop="handleNodeClick(node.id)"
    >
      <template v-if="node.type === 'content'">
        <section
          class="schema-content"
          :style="{
            background: (node.props as SchemaRendererContentProps).background || '#ffffff',
            padding: `${(node.props as SchemaRendererContentProps).padding ?? 24}px`,
          }"
        >
          <div v-if="(node.props as SchemaRendererContentProps).title" class="schema-content-title">
            {{ (node.props as SchemaRendererContentProps).title }}
          </div>
          <SchemaRenderer
            :nodes="node.children || []"
            :selected-id="props.selectedId"
            @node-click="handleNodeClick"
          />
        </section>
      </template>

      <template v-else>
        <component
          :is="componentMap[node.type]"
          v-bind="node.props"
        />
      </template>
    </div>
  </div>
</template>

<style scoped>
.schema-renderer {
  display: grid;
  gap: 12px;
  align-content: start;
}

.schema-renderer-node {
  min-width: 0;
  border: 1px dashed #000;
  cursor: pointer;
}

.schema-renderer-node.is-selected {
  border: 1px solid #0099ff;
}

.schema-content {
  border: none;
  min-height: 120px;
}

.schema-content-title {
  margin-bottom: 12px;
  color: #1f2937;
  font-size: 14px;
  font-weight: 600;
}
</style>
