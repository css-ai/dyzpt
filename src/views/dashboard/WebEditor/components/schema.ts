import type { PageNode, PageSchema, PaletteItem } from './types'

export function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).substring(2, 11)}`
}

export function createEmptySchema(): PageSchema {
  return {
    id: generateId(),
    title: '未命名页面',
    description: '',
    version: 1,
    createdAt: Date.now(),
    updatedAt: Date.now(),
    root: {
      id: generateId(),
      name: '根节点',
      type: 'container',
      props: {},
      children: [],
    },
  }
}

export function findNodeById(node: PageNode, id: string): PageNode | null {
  if (node.id === id) return node
  if (!node.children) return null

  for (const child of node.children) {
    const found = findNodeById(child, id)
    if (found) return found
  }
  return null
}

export function findParentNode(root: PageNode, targetId: string): PageNode | null {
  if (!root.children) return null

  for (const child of root.children) {
    if (child.id === targetId) return root
    const found = findParentNode(child, targetId)
    if (found) return found
  }

  return null
}

export function removeNodeById(node: PageNode, id: string): boolean {
  if (!node.children) return false

  const index = node.children.findIndex((child) => child.id === id)
  if (index !== -1) {
    node.children.splice(index, 1)
    return true
  }

  for (const child of node.children) {
    if (removeNodeById(child, id)) return true
  }

  return false
}

export function insertNodeAt(parentNode: PageNode, newNode: PageNode, index?: number) {
  if (!parentNode.children) parentNode.children = []

  if (index !== undefined && index >= 0 && index <= parentNode.children.length) {
    parentNode.children.splice(index, 0, newNode)
  } else {
    parentNode.children.push(newNode)
  }

  newNode.parentId = parentNode.id
}

export function cloneNode(node: PageNode, deep = true): PageNode {
  const clone: PageNode = {
    ...node,
    id: generateId(),
    props: JSON.parse(JSON.stringify(node.props || {})),
  }

  if (deep && node.children) {
    clone.children = node.children.map((child) => cloneNode(child, true))
  }

  return clone
}

export function createNodeFromPalette(item: PaletteItem): PageNode {
  const node: PageNode = {
    id: generateId(),
    name: item.name,
    type: item.type,
    props: JSON.parse(JSON.stringify(item.defaultProps)),
  }

  if (item.defaultChildren) {
    node.children = item.defaultChildren.map((child) => cloneNode(child, true))
  }

  return node
}

