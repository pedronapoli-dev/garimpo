type Node = { type: unknown; props: Record<string, unknown>; parent: Node | null };

/**
 * Whether a screen's content sits in a scroll view that iOS insets below the
 * navigation bar and above the tab bar.
 */
export function isInsideInsetScrollView(element: unknown): boolean {
  let node = element as Node | null;
  while (node !== null) {
    if (node.props?.contentInsetAdjustmentBehavior === 'automatic') return true;
    node = node.parent;
  }
  return false;
}
