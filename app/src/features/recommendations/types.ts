import type { components } from '@/api/schema';

export type Recommendation = components['schemas']['RecommendationOut'];
export type RecommendationPage = components['schemas']['RecommendationPage'];
export type RecommendationCreate = components['schemas']['RecommendationCreate'];
export type RecommendationUpdate = components['schemas']['RecommendationUpdate'];
export type RecommendationType = Recommendation['type'];
export type Tag = components['schemas']['TagOut'];
