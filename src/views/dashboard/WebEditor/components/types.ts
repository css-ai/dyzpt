export type NodeType =
  | 'section'
  | 'container'
  | 'text'
  | 'image'
  | 'button'
  | 'nav'
  | 'hero'
  | 'features'
  | 'footer'

export type PreviewDevice = 'desktop' | 'tablet' | 'mobile'

export type BaseProps = {
  animation?: string
  customClass?: string
  customStyle?: Record<string, string>
}

export type TextProps = BaseProps & {
  align?: 'left' | 'center' | 'right' | 'justify'
  color?: string
  fontSize?: number
  fontWeight?: string
  text?: string
}

export type ImageProps = BaseProps & {
  alt?: string
  height?: string
  objectFit?: 'cover' | 'contain' | 'fill' | 'none'
  src?: string
  width?: string
}

export type ButtonProps = BaseProps & {
  href?: string
  size?: 'small' | 'medium' | 'large'
  target?: '_blank' | '_self'
  text?: string
  type?: 'primary' | 'secondary' | 'outline' | 'text'
}

export type NavItem = { href: string; label: string }

export type NavProps = BaseProps & {
  align?: 'left' | 'center' | 'right'
  items?: NavItem[]
  theme?: 'light' | 'dark'
}

export type BoxPadding = {
  bottom: number
  left: number
  right: number
  top: number
}

export type ContainerProps = BaseProps & {
  background?: string
  columns?: number
  gap?: number
  layout?: 'flex' | 'grid'
  maxWidth?: string
  padding?: BoxPadding
}

export type SectionProps = ContainerProps & {
  fullWidth?: boolean
  subtitle?: string
  title?: string
}

export type HeroProps = BaseProps & {
  backgroundImage?: string
  buttonText?: string
  overlay?: boolean
  subtitle?: string
  title?: string
}

export type FeatureItem = { description: string; icon?: string; title: string }

export type FeaturesProps = BaseProps & {
  columns?: 2 | 3 | 4
  items?: FeatureItem[]
  title?: string
}

export type FooterProps = BaseProps & {
  copyright?: string
  links?: NavItem[]
  theme?: 'light' | 'dark'
}

export type NodeProps =
  | ButtonProps
  | ContainerProps
  | FeaturesProps
  | FooterProps
  | HeroProps
  | ImageProps
  | NavProps
  | SectionProps
  | TextProps

export type PageNode = {
  children?: PageNode[]
  id: string
  name: string
  parentId?: string
  props: Record<string, any>
  type: NodeType
}

export type PageSchema = {
  createdAt: number
  description?: string
  id: string
  root: PageNode
  title: string
  updatedAt: number
  version: number
}

export type PaletteItem = {
  defaultChildren?: PageNode[]
  defaultProps: NodeProps
  description: string
  icon: string
  name: string
  type: NodeType
}

export type PaletteCategory = {
  icon: string
  items: PaletteItem[]
  name: string
}

export type HistoryEntry = {
  action: string
  schema: PageSchema
  timestamp: number
}

