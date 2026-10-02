import { create } from 'zustand';
import type { 
  Project, 
  Scene, 
  UserChannel, 
  TrackedChannel, 
  TopicSuggestion, 
  EngineSettings, 
  StudioMode 
} from '../types';

interface StudioState {
  // Navigation & Modes
  activeTab: 'channels' | 'analytics' | 'projects';
  studioMode: StudioMode;
  isEditorOpen: boolean;
  
  // Active Project in Studio
  activeProject: Project | null;
  activeSceneIdx: number;
  isInspectorFolded: boolean;
  activeInspectorTab: 'script' | 'still' | 'video' | 'subs' | 'hook';
  // CapCut Subtitle Properties
  captionColor: 'yellow' | 'cyan' | 'emerald' | 'white' | 'red';
  captionFont: 'Impact' | 'Montserrat' | 'Arial Black' | 'Anton';
  captionFontSize: number;
  captionStroke: number;
  captionUppercase: boolean;
  captionPacing: 'burst' | 'phrase' | 'single';
  captionY: number;
  isPlaying: boolean;

  // Channels
  activeChannel: UserChannel | null;
  userChannels: UserChannel[];
  trackedChannels: TrackedChannel[];

  // Topics & Analytics
  topics: TopicSuggestion[];
  topicHistory: TopicSuggestion[];
  projects: Project[];
  trashProjects: Project[];

  // Settings
  settings: EngineSettings;

  // Modals
  isSettingsOpen: boolean;
  isAddUserChannelOpen: boolean;
  isAddTrackedChannelOpen: boolean;
  isTrashModalOpen: boolean;
  isExportModalOpen: boolean;
  isRepurposeModalOpen: boolean;
  isTopicHistoryOpen: boolean;
  isNewDraftModalOpen: boolean;

  // Actions
  setActiveTab: (tab: 'channels' | 'analytics' | 'projects') => void;
  setStudioMode: (mode: StudioMode) => void;
  openEditor: (projectName: string) => Promise<void>;
  closeEditor: () => void;
  setActiveSceneIdx: (idx: number) => void;
  setInspectorFolded: (folded: boolean) => void;
  setActiveInspectorTab: (tab: 'script' | 'still' | 'video' | 'subs' | 'hook') => void;
  setCaptionColor: (color: 'yellow' | 'cyan' | 'emerald' | 'white' | 'red') => void;
  setCaptionSettings: (settings: Partial<{
    captionColor: 'yellow' | 'cyan' | 'emerald' | 'white' | 'red';
    captionFont: 'Impact' | 'Montserrat' | 'Arial Black' | 'Anton';
    captionFontSize: number;
    captionStroke: number;
    captionUppercase: boolean;
    captionPacing: 'burst' | 'phrase' | 'single';
    captionY: number;
  }>) => void;
  setIsPlaying: (playing: boolean) => void;

  // Fetch actions
  fetchChannels: () => Promise<void>;
  selectActiveChannel: (handle: string) => Promise<void>;
  fetchTopics: (refresh?: boolean) => Promise<void>;
  fetchProjects: () => Promise<void>;
  fetchTrash: () => Promise<void>;
  fetchSettings: () => Promise<void>;
  saveSettings: (settings: EngineSettings) => Promise<void>;

  // Modal actions
  setModal: (modalName: string, open: boolean) => void;
  updateActiveScene: (updates: Partial<Scene>) => void;
}

export const useStudioStore = create<StudioState>((set, get) => ({
  activeTab: 'channels',
  studioMode: 'create',
  isEditorOpen: false,

  activeProject: null,
  activeSceneIdx: 0,
  isInspectorFolded: false,
  activeInspectorTab: 'still',
  
  // CapCut Subtitle Defaults
  captionColor: 'yellow',
  captionFont: 'Impact',
  captionFontSize: 24,
  captionStroke: 4,
  captionUppercase: true,
  captionPacing: 'burst',
  captionY: 72,
  isPlaying: false,

  activeChannel: {
    name: 'Newyr',
    handle: '@Newyrr',
    subscribers: '8',
    videos: 3,
    niche: 'Shorts science. How and what if moments.'
  },
  userChannels: [],
  trackedChannels: [],

  topics: [],
  topicHistory: [],
  projects: [],
  trashProjects: [],

  settings: {
    llm_model: 'openai/gpt-4o-mini',
    image_model: 'krea/krea-2-medium-turbo',
    video_provider: 'bytedance/seedance-2.0-mini',
    tts_model: 'google/gemini-3.8-flash-lite-tts',
    tts_voice: 'Charon',
    art_style: 'Hyper-Realistic Cinematic Film'
  },

  isSettingsOpen: false,
  isAddUserChannelOpen: false,
  isAddTrackedChannelOpen: false,
  isTrashModalOpen: false,
  isExportModalOpen: false,
  isRepurposeModalOpen: false,
  isTopicHistoryOpen: false,
  isNewDraftModalOpen: false,

  setActiveTab: (tab) => set({ activeTab: tab }),
  setStudioMode: (mode) => set({ studioMode: mode }),
  
  openEditor: async (projectName: string) => {
    try {
      let res = await fetch(`/api/project/load?project_name=${encodeURIComponent(projectName)}`);
      if (!res.ok) {
        res = await fetch(`/api/project/${encodeURIComponent(projectName)}`);
      }
      if (res.ok) {
        const project = await res.json();
        set({ activeProject: project, activeSceneIdx: 0, isEditorOpen: true });
      } else {
        console.error('Failed to load project:', await res.text());
      }
    } catch (e) {
      console.error('Failed to load project:', e);
    }
  },

  closeEditor: () => set({ isEditorOpen: false, isPlaying: false }),
  setActiveSceneIdx: (idx) => set({ activeSceneIdx: idx }),
  setInspectorFolded: (folded) => set({ isInspectorFolded: folded }),
  setActiveInspectorTab: (tab) => set({ activeInspectorTab: tab }),
  setCaptionColor: (color) => set({ captionColor: color }),
  setCaptionSettings: (settings) => set((state) => ({ ...state, ...settings })),
  setIsPlaying: (playing) => set({ isPlaying: playing }),

  fetchChannels: async () => {
    try {
      const res = await fetch('/api/channels');
      if (res.ok) {
        const data = await res.json();
        set({
          activeChannel: data.active_channel || null,
          userChannels: data.user_channels || [],
          trackedChannels: data.tracked_channels || []
        });
      }
    } catch (e) {
      console.error(e);
    }
  },

  selectActiveChannel: async (handle: string) => {
    try {
      await fetch('/api/channels/select-active', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ handle })
      });
      await get().fetchChannels();
      await get().fetchTopics();
    } catch (e) {
      console.error(e);
    }
  },

  fetchTopics: async (refresh = false) => {
    try {
      const url = refresh ? '/api/topics/suggest?refresh=true' : '/api/topics';
      const res = await fetch(url);
      if (res.ok) {
        const data = await res.json();
        if (Array.isArray(data) && data.length > 0) {
          set({ topics: data });
        }
      }
    } catch (e) {
      console.error(e);
    }
  },

  fetchProjects: async () => {
    try {
      const res = await fetch('/api/projects');
      if (res.ok) {
        const data = await res.json();
        set({ projects: data });
      }
      await get().fetchTrash();
    } catch (e) {
      console.error(e);
    }
  },

  fetchTrash: async () => {
    try {
      const res = await fetch('/api/projects/trash');
      if (res.ok) {
        const data = await res.json();
        set({ trashProjects: data });
      }
    } catch (e) {
      console.error(e);
    }
  },

  fetchSettings: async () => {
    try {
      const res = await fetch('/api/settings');
      if (res.ok) {
        const data = await res.json();
        set({ settings: data });
      }
    } catch (e) {
      console.error(e);
    }
  },

  saveSettings: async (settings) => {
    try {
      const res = await fetch('/api/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings)
      });
      if (res.ok) {
        set({ settings });
      }
    } catch (e) {
      console.error(e);
    }
  },

  setModal: (modalName, open) => {
    const raw = modalName.replace(/Modal$/, '');
    const capitalized = raw.charAt(0).toUpperCase() + raw.slice(1);
    const key1 = `is${capitalized}Open` as keyof StudioState;
    const key2 = `is${capitalized}ModalOpen` as keyof StudioState;
    const updates: Partial<StudioState> = {};
    if (key1 in get()) (updates as any)[key1] = open;
    if (key2 in get()) (updates as any)[key2] = open;
    set(updates);
  },

  updateActiveScene: (updates) => {
    const { activeProject, activeSceneIdx } = get();
    if (!activeProject || !activeProject.scenes[activeSceneIdx]) return;
    const newScenes = [...activeProject.scenes];
    newScenes[activeSceneIdx] = { ...newScenes[activeSceneIdx], ...updates };
    set({ activeProject: { ...activeProject, scenes: newScenes } });
  }
}));
