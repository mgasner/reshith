import type { ReactNode, CSSProperties } from 'react'

interface CommentaryFlowItemProps {
  /** The primary content (verse, passage, etc.) — floated to the left. */
  primary: ReactNode
  /** The commentary that flows to the right of and below the primary content. */
  commentary: ReactNode
  /** Width of the primary float. Default: '56%'. */
  primaryWidth?: string
  /** Gap between primary and commentary. Default: '1.75rem'. */
  gap?: string
  /** dir attribute on the commentary wrapper. Default: 'ltr'. */
  commentaryDir?: 'ltr' | 'rtl'
  /** Extra classes on the commentary wrapper. */
  commentaryClassName?: string
  /** Extra top padding on the commentary wrapper (to align with primary content). Default: '0'. */
  commentaryPaddingTop?: string
}

/** One primary+commentary pair. Primary floats left; commentary flows around it. */
export function CommentaryFlowItem({
  primary,
  commentary,
  primaryWidth = '56%',
  gap = '1.75rem',
  commentaryDir = 'ltr',
  commentaryClassName = '',
  commentaryPaddingTop = '0',
}: CommentaryFlowItemProps) {
  const floatStyle: CSSProperties = {
    float: 'left',
    width: primaryWidth,
    marginRight: gap,
  }
  const commentaryStyle: CSSProperties = {
    paddingTop: commentaryPaddingTop,
  }

  return (
    <div>
      <div style={floatStyle}>{primary}</div>
      <div
        dir={commentaryDir}
        className={commentaryClassName}
        style={commentaryStyle}
      >
        {commentary}
      </div>
      <div style={{ clear: 'both' }} />
    </div>
  )
}

interface CommentaryFlowProps {
  children: ReactNode
  /** Vertical gap between items. Default: '0.25rem'. */
  itemGap?: string
}

/** Container for a list of CommentaryFlowItem rows. */
export function CommentaryFlow({ children, itemGap = '0.25rem' }: CommentaryFlowProps) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: itemGap }}>
      {children}
    </div>
  )
}
