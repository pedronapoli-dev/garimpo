import { ScrollView, type ScrollViewProps } from 'react-native';

/**
 * A screen's scrolling content. iOS insets it below the navigation bar and
 * above the tab bar, like a UIScrollView with contentInsetAdjustmentBehavior
 * .automatic, and keeps focused fields above the keyboard.
 */
export function ScreenScrollView(props: ScrollViewProps) {
  return (
    <ScrollView
      contentInsetAdjustmentBehavior="automatic"
      automaticallyAdjustKeyboardInsets
      {...props}
    />
  );
}
