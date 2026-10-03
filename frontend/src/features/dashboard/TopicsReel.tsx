import React, { useRef, useState } from 'react';
import { useStudioStore } from '../../stores/useStudioStore';
import { KineticCard } from '../../components/ui/kinetic-card';
import { Clock, RefreshCw, ChevronLeft, ChevronRight, ArrowRight, Sparkles } from 'lucide-react';
import type { TopicSuggestion } from '../../types';

const DEFAULT_TOPICS: TopicSuggestion[] = [
  {
    title: "Why Astronauts Lose Their Fingernails",
    category: "Extreme Biology",
    hook: "When astronauts work outside the space station, their fingernails can literally pop off in their gloves."
  },
  {
    title: "What Happens If You Swallow a Fish Bone",
    category: "Body Horrors",
    hook: "Swallowing a tiny needle-sharp fish bone doesn't just hurt—it can migrate directly through your throat tissue."
  },
  {
    title: "Why Alcatraz Only Gave Burning Hot Showers",
    category: "Bizarre Realities",
    hook: "Alcatraz prison forced inmates to take steaming hot showers, and the reason was pure calculated warfare."
  },
  {
    title: "Why You Must Never Pop Danger Triangle Pimples",
    category: "Medical Anatomy",
    hook: "Popping a pimple inside this tiny facial zone can send lethal bacteria straight into your brain veins."
  },
  {
    title: "Why Deep Sea Divers Cannot Fly For 24 Hours",
    category: "Extreme Physics",
    hook: "If a commercial diver boards a flight too soon, the nitrogen gas inside their bloodstream will literally boil."
  },
  {
    title: "Why Bulletproof Glass Shatters From The Inside",
    category: "Material Breakdown",
    hook: "Bulletproof glass stops high-powered rifle rounds from outside, but shatters from the inside with a pocket hammer."
  }
];

export const TopicsReel: React.FC = () => {
  const { topics, fetchTopics, fetchProjects, setModal, settings, openEditor } = useStudioStore();
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [generatingTopic, setGeneratingTopic] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  const displayTopics = topics && topics.length > 0 ? topics : DEFAULT_TOPICS;

  const scroll = (direction: 'left' | 'right') => {
    if (scrollRef.current) {
      const offset = direction === 'left' ? -340 : 340;
      scrollRef.current.scrollBy({ left: offset, behavior: 'smooth' });
    }
  };

  const handleUseTopic = (topicTitle: string) => {
    window.sessionStorage.setItem('prefilledTopic', topicTitle);
    setModal('newDraft', true);
  };

  const handleQuickCreate = async (e: React.MouseEvent, topicTitle: string) => {
    e.stopPropagation();
    setGeneratingTopic(topicTitle);
    try {
      const res = await fetch('/api/project/create-draft', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          topic: topicTitle,
          aspect_ratio: '9:16',
          art_style: settings.art_style || 'photo_35mm',
          tts_voice: settings.tts_voice || 'Charon'
        })
      });
      if (res.ok) {
        const data = await res.json();
        await fetchProjects();
        await openEditor(data.project_name);
      }
    } catch (err) {
      console.error('Quick Studio failed:', err);
    } finally {
      setGeneratingTopic(null);
    }
  };

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await fetchTopics(true);
    setIsRefreshing(false);
  };

  return (
    <div className="flex flex-col gap-2.5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">
            AI Viral Topic Suggestions
          </h3>
          <button
            onClick={() => setModal('topicHistory', true)}
            title="View Topic History"
            className="p-1 rounded-md bg-[#0d111a] hover:bg-[#161b26] border border-[#1f2736] text-slate-300 hover:text-cyan-400 transition flex items-center gap-1 px-2 text-[11px] cursor-pointer"
          >
            <Clock className="w-3.5 h-3.5 text-cyan-400" />
            <span>History</span>
          </button>
        </div>

        <div className="flex items-center gap-1.5">
          <button
            onClick={() => scroll('left')}
            className="w-6 h-6 rounded-lg bg-[#0d111a] hover:bg-[#161b26] border border-[#1f2736] text-slate-300 hover:text-white flex items-center justify-center text-xs transition active:scale-95 cursor-pointer"
          >
            <ChevronLeft className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => scroll('right')}
            className="w-6 h-6 rounded-lg bg-[#0d111a] hover:bg-[#161b26] border border-[#1f2736] text-slate-300 hover:text-white flex items-center justify-center text-xs transition active:scale-95 cursor-pointer"
          >
            <ChevronRight className="w-3.5 h-3.5" />
          </button>
          <button
            disabled={isRefreshing}
            onClick={handleRefresh}
            className="text-xs text-cyan-400 hover:underline flex items-center gap-1 font-semibold ml-1 cursor-pointer disabled:opacity-50"
          >
            <RefreshCw className={`w-3 h-3 ${isRefreshing ? 'animate-spin' : ''}`} />
            <span>{isRefreshing ? 'Generating...' : 'Refresh'}</span>
          </button>
        </div>
      </div>

      {/* Horizontal Snap Scroll Container (Saves screen space!) */}
      <div
        ref={scrollRef}
        className="flex items-stretch gap-3 overflow-x-auto pb-2 scrollbar-none snap-x snap-mandatory scroll-smooth"
      >
        {displayTopics.map((t, idx) => (
          <KineticCard
            key={idx}
            onClick={() => handleUseTopic(t.title)}
            className="min-w-[280px] sm:min-w-[320px] max-w-[340px] shrink-0 snap-start p-4 flex flex-col justify-between group cursor-pointer"
          >
            <div>
              <div className="flex items-center justify-between text-[10px] text-slate-400 uppercase tracking-wider mb-2">
                <span className="text-cyan-400 font-semibold flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-cyan-400" />
                  {t.category || 'Science'}
                </span>
                <div className="flex items-center gap-1.5">
                  <button
                    disabled={generatingTopic === t.title}
                    onClick={(e) => handleQuickCreate(e, t.title)}
                    className="bg-cyan-400/20 hover:bg-cyan-400/35 border border-cyan-400/50 text-cyan-300 px-2 py-0.5 rounded-md text-[10px] font-bold flex items-center gap-1 transition cursor-pointer disabled:opacity-50"
                    title="Generate screenplay and enter Studio immediately"
                  >
                    {generatingTopic === t.title ? (
                      <>
                        <RefreshCw className="w-2.5 h-2.5 animate-spin" />
                        <span>Creating...</span>
                      </>
                    ) : (
                      <>
                        <Sparkles className="w-2.5 h-2.5 text-cyan-400" />
                        <span>Quick Studio</span>
                      </>
                    )}
                  </button>
                  <span className="text-slate-400 hover:text-white text-[10px] font-semibold flex items-center gap-0.5">
                    Customize <ArrowRight className="w-2.5 h-2.5" />
                  </span>
                </div>
              </div>
              <div className="font-bold text-xs sm:text-sm text-slate-100 group-hover:text-cyan-400 leading-snug line-clamp-2">
                {t.title}
              </div>
            </div>
            <div className="text-[11px] text-slate-400 italic mt-3 line-clamp-2 bg-[#07090e]/60 p-2.5 rounded-xl border border-[#1f2736]/60">
              "{t.hook || ''}"
            </div>
          </KineticCard>
        ))}
      </div>
    </div>
  );
};
