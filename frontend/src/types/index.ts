export type StudioMode = 'create' | 'repurpose';

export interface Scene {
  scene_number: number;
  narration: string;
  flux_image_prompt?: string;
  minimax_motion_prompt?: string;
  image_file?: string;
  image_url?: string;
  video_file?: string;
  video_url?: string;
  audio_file?: string;
  audio_url?: string;
  actual_audio_duration?: number;
  sfx_cue?: string;
}

export interface Project {
  project_name: string;
  title: string;
  topic?: string;
  hook?: string;
  aspect_ratio: '9:16' | '16:9';
  scenes: Scene[];
  status?: string;
  art_style?: string;
  caption_y_percent?: number;
  thumbnail_url?: string;
  final_video_url?: string;
  deleted_at?: number;
  days_left?: number;
}

export interface UserChannel {
  id?: string;
  name: string;
  handle: string;
  subscribers?: string;
  videos?: number;
  niche?: string;
  top_video?: string;
  avatar_url?: string;
}

export interface TrackedChannel {
  name: string;
  handle: string;
  focus: string;
}

export interface TopicSuggestion {
  title: string;
  category: string;
  hook: string;
  created_at?: string;
}

export interface EngineSettings {
  llm_model: string;
  image_model: string;
  video_provider: string;
  tts_model: string;
  tts_voice: string;
  art_style: string;
}
