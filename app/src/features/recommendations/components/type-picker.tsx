import { StyleSheet, View } from 'react-native';

import { Chip } from '@/components/chip';
import { Spacing } from '@/constants/theme';

import { TYPE_LABELS } from '../format';
import type { RecommendationType } from '../types';

const TYPES: RecommendationType[] = ['album', 'track', 'artist'];

type TypePickerProps = { value: RecommendationType; onChange: (type: RecommendationType) => void };

export function TypePicker({ value, onChange }: TypePickerProps) {
  return (
    <View style={styles.row} accessibilityRole="radiogroup">
      {TYPES.map((type) => (
        <Chip
          key={type}
          label={TYPE_LABELS[type]}
          selected={value === type}
          onPress={() => onChange(type)}
        />
      ))}
    </View>
  );
}

const styles = StyleSheet.create({ row: { flexDirection: 'row', gap: Spacing.two } });
