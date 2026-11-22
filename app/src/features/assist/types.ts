import type { components } from '@/api/schema';

export type AssistIn = components['schemas']['AssistIn'];
export type AssistResult = components['schemas']['AssistResult'];
export type FeedbackDelta = components['schemas']['FeedbackDelta'];
export type AssistDone = components['schemas']['AssistDone'];
export type AssistFailed = components['schemas']['AssistFailed'];
export type AssistEvent = FeedbackDelta | AssistDone | AssistFailed;
export type AssistStatus = components['schemas']['AssistStatusOut'];
