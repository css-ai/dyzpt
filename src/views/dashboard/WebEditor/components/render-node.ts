import { h, type VNode } from 'vue'

import type {
  BoxPadding,
  ButtonProps,
  ContainerProps,
  FeaturesProps,
  FooterProps,
  HeroProps,
  ImageProps,
  NavProps,
  PageNode,
  SectionProps,
  TextProps,
} from './types'

export type RenderNodeContext = {
  handleDropToCanvas: (event: DragEvent, targetNode?: PageNode) => void
  selectedId: null | string
  selectNode: (id: string) => void
  updateNodeProps: (nodeId: string, props: Record<string, any>) => void
}

export function renderEditorNode(node: PageNode, context: RenderNodeContext): VNode | null {
  const isSelected = context.selectedId === node.id
  const props = node.props || {}
  const baseClass = `editor-node editor-node--${node.type}`
  const selectedClass = isSelected ? 'editor-node--selected' : ''

  const handleClick = (event: MouseEvent) => {
    event.stopPropagation()
    context.selectNode(node.id)
  }

  switch (node.type) {
    case 'text': {
      const textProps = props as TextProps
      return h('div', {
        key: node.id,
        class: `${baseClass} ${selectedClass}`,
        onClick: handleClick,
        onDblclick: () => {
          const newText = prompt('编辑文本内容', textProps.text || '')
          if (newText !== null) context.updateNodeProps(node.id, { text: newText })
        },
      }, [
        h('div', {
          class: 'text-content',
          style: {
            textAlign: textProps.align || 'left',
            fontSize: `${textProps.fontSize || 16}px`,
            fontWeight: textProps.fontWeight || 'normal',
            color: textProps.color || '#333333',
          },
        }, textProps.text || '文本内容'),
      ])
    }

    case 'image': {
      const imageProps = props as ImageProps
      return h('div', {
        key: node.id,
        class: `${baseClass} ${selectedClass}`,
        onClick: handleClick,
      }, [
        h('img', {
          src: imageProps.src || 'https://picsum.photos/300/200',
          alt: imageProps.alt || '图片',
          style: {
            width: imageProps.width || '100%',
            height: imageProps.height || 'auto',
            objectFit: imageProps.objectFit || 'cover',
          },
        }),
      ])
    }

    case 'button': {
      const buttonProps = props as ButtonProps
      return h('div', {
        key: node.id,
        class: `${baseClass} ${selectedClass}`,
        onClick: handleClick,
      }, [
        h('button', {
          class: `btn btn--${buttonProps.type || 'primary'} btn--${buttonProps.size || 'medium'}`,
        }, buttonProps.text || '按钮'),
      ])
    }

    case 'nav': {
      const navProps = props as NavProps
      return h('div', {
        key: node.id,
        class: `${baseClass} ${selectedClass} nav nav--${navProps.theme || 'light'}`,
        onClick: handleClick,
      }, [
        h('div', { class: 'nav-container' }, [
          h('div', { class: 'nav-logo' }, 'Logo'),
          h('div', {
            class: 'nav-items',
            style: { justifyContent: navProps.align || 'center' },
          }, (navProps.items || []).map((item, idx) => h('a', { key: idx, href: item.href, class: 'nav-link' }, item.label))),
        ]),
      ])
    }

    case 'hero': {
      const heroProps = props as HeroProps
      return h('div', {
        key: node.id,
        class: `${baseClass} ${selectedClass} hero`,
        style: {
          backgroundImage: heroProps.backgroundImage ? `url(${heroProps.backgroundImage})` : undefined,
          position: 'relative',
        },
        onClick: handleClick,
      }, [
        heroProps.overlay && h('div', { class: 'hero-overlay' }),
        h('div', { class: 'hero-content' }, [
          h('h1', { class: 'hero-title' }, heroProps.title || 'Hero 标题'),
          h('p', { class: 'hero-subtitle' }, heroProps.subtitle || '这是 Hero 区块的描述文字'),
          heroProps.buttonText && h('button', { class: 'hero-btn' }, heroProps.buttonText),
        ]),
      ])
    }

    case 'features': {
      const featuresProps = props as FeaturesProps
      return h('div', {
        key: node.id,
        class: `${baseClass} ${selectedClass} features`,
        onClick: handleClick,
      }, [
        featuresProps.title && h('h2', { class: 'features-title' }, featuresProps.title),
        h('div', {
          class: `features-grid features-grid--${featuresProps.columns || 3}`,
        }, (featuresProps.items || []).map((item, idx) => h('div', { key: idx, class: 'feature-card' }, [
          item.icon && h('div', { class: 'feature-icon' }, item.icon),
          h('h3', { class: 'feature-title' }, item.title),
          h('p', { class: 'feature-description' }, item.description),
        ]))),
      ])
    }

    case 'footer': {
      const footerProps = props as FooterProps
      return h('footer', {
        key: node.id,
        class: `${baseClass} ${selectedClass} footer footer--${footerProps.theme || 'light'}`,
        onClick: handleClick,
      }, [
        h('div', { class: 'footer-container' }, [
          h('div', { class: 'footer-links' }, (footerProps.links || []).map((link, idx) => h('a', { key: idx, href: link.href, class: 'footer-link' }, link.label))),
          h('div', { class: 'footer-copyright' }, footerProps.copyright || '© 2024 企业级编辑器'),
        ]),
      ])
    }

    case 'container':
    case 'section': {
      const isSection = node.type === 'section'
      const containerProps = props as ContainerProps & SectionProps
      const containerClass = `${baseClass} ${selectedClass} ${isSection ? 'section' : 'container'}`
      const padding: BoxPadding = containerProps.padding || { top: 16, right: 16, bottom: 16, left: 16 }
      const childrenNodes: any[] = []

      if (isSection && containerProps.title) {
        childrenNodes.push(
          h('div', { class: 'section-header' }, [
            h('h2', { class: 'section-title' }, containerProps.title),
            containerProps.subtitle && h('p', { class: 'section-subtitle' }, containerProps.subtitle),
          ]),
        )
      }

      childrenNodes.push(
        h('div', {
          class: 'container-children',
          style: {
            display: containerProps.layout === 'grid' ? 'grid' : 'flex',
            flexDirection: 'column',
            gap: `${containerProps.gap || 16}px`,
            gridTemplateColumns: containerProps.layout === 'grid' ? `repeat(${containerProps.columns || 1}, 1fr)` : undefined,
          },
        }, [
          ...(node.children?.map((child) => renderEditorNode(child, context)) || []),
          (!node.children || node.children.length === 0) && h('div', { class: 'container-placeholder' }, '拖拽组件到此区域'),
        ]),
      )

      return h('div', {
        key: node.id,
        class: containerClass,
        style: {
          backgroundColor: containerProps.background || 'transparent',
          padding: `${padding.top}px ${padding.right}px ${padding.bottom}px ${padding.left}px`,
          maxWidth: containerProps.maxWidth || '100%',
          margin: '0 auto',
        },
        onClick: handleClick,
        onDragover: (event: DragEvent) => event.preventDefault(),
        onDrop: (event: DragEvent) => context.handleDropToCanvas(event, node),
      }, childrenNodes)
    }

    default:
      return null
  }
}

