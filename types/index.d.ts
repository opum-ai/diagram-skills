/** What the diagram pane is showing. */
export type View = {
  /** The pane's heading: the file path, or the title the tool call gave. */
  title: string
  /** The tool call's one-sentence text equivalent, when it gave one. */
  alt?: string | undefined
  /** The diagram sources of the document, at most 8. */
  sources: string[]
  /** How many more fences the document had than the pane draws. */
  hidden: number
  /** Which source is drawn now. */
  index: number
}

declare module 'claude-code' {
  interface PluginState {
    'diagram-skills': { view: View | null }
  }
}
