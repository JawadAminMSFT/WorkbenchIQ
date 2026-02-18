'use client';

import React, { useState, useRef } from 'react';
import { Play, Pause, SkipBack, SkipForward, AlertTriangle, Clock, ChevronLeft, ChevronRight } from 'lucide-react';
import { Keyframe, DamageArea, getMediaUrl } from '@/lib/api';

interface VideoTimelineProps {
  videoUrl?: string;
  duration: number;
  keyframes: Keyframe[];
  onKeyframeSelect?: (keyframe: Keyframe) => void;
  selectedKeyframeId?: string;
}

interface KeyframeThumbnailProps {
  keyframe: Keyframe;
  isSelected: boolean;
  onClick: () => void;
  totalDuration: number;
}

const KeyframeThumbnail: React.FC<KeyframeThumbnailProps> = ({
  keyframe,
  isSelected,
  onClick,
  totalDuration,
}) => {
  return (
    <button
      onClick={onClick}
      className={`flex-shrink-0 w-32 rounded-lg overflow-hidden transition-all duration-200 ${
        isSelected
          ? 'ring-2 ring-red-500 ring-offset-2 scale-105'
          : 'hover:ring-2 hover:ring-gray-300 hover:ring-offset-1'
      }`}
    >
      {/* Thumbnail */}
      <div className="relative aspect-video bg-gray-100">
        {keyframe.thumbnail_url ? (
          <img
            src={getMediaUrl(keyframe.thumbnail_url)}
            alt={`Frame at ${keyframe.timestamp_formatted}`}
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center bg-gray-200">
            <Play className="w-6 h-6 text-gray-400" />
          </div>
        )}

        {/* Damage Indicator */}
        {keyframe.damage_detected && (
          <div className="absolute top-1 right-1">
            <div className="w-5 h-5 rounded-full bg-red-500 flex items-center justify-center">
              <AlertTriangle className="w-3 h-3 text-white" />
            </div>
          </div>
        )}

        {/* Timestamp Badge */}
        <div className="absolute bottom-1 left-1 bg-black/70 text-white text-xs px-1.5 py-0.5 rounded">
          {keyframe.timestamp_formatted}
        </div>

        {/* Confidence Indicator */}
        <div className="absolute bottom-1 right-1">
          <div
            className={`w-2 h-2 rounded-full ${
              keyframe.confidence > 0.8
                ? 'bg-green-500'
                : keyframe.confidence > 0.5
                ? 'bg-yellow-500'
                : 'bg-red-500'
            }`}
            title={`${(keyframe.confidence * 100).toFixed(0)}% confidence`}
          />
        </div>
      </div>

      {/* Description */}
      {keyframe.description && (
        <div className="p-2 bg-white border-t border-gray-100">
          <p className="text-xs text-gray-600 line-clamp-2">{keyframe.description}</p>
        </div>
      )}
    </button>
  );
};

interface TimelineBarProps {
  duration: number;
  keyframes: Keyframe[];
  currentTime: number;
  onSeek: (time: number) => void;
  onKeyframeClick: (keyframe: Keyframe) => void;
  selectedKeyframeId?: string;
}

const TimelineBar: React.FC<TimelineBarProps> = ({
  duration,
  keyframes,
  currentTime,
  onSeek,
  onKeyframeClick,
  selectedKeyframeId,
}) => {
  const barRef = useRef<HTMLDivElement>(null);

  const handleBarClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!barRef.current) return;
    const rect = barRef.current.getBoundingClientRect();
    const percentage = (e.clientX - rect.left) / rect.width;
    onSeek(percentage * duration);
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="space-y-2">
      {/* Time Labels */}
      <div className="flex justify-between text-xs text-gray-500">
        <span>{formatTime(currentTime)}</span>
        <span>{formatTime(duration)}</span>
      </div>

      {/* Timeline Bar */}
      <div
        ref={barRef}
        onClick={handleBarClick}
        className="relative h-8 bg-gray-200 rounded-lg cursor-pointer overflow-hidden"
      >
        {/* Progress */}
        <div
          className="absolute inset-y-0 left-0 bg-red-100"
          style={{ width: `${(currentTime / duration) * 100}%` }}
        />

        {/* Keyframe Markers */}
        {keyframes.map((kf) => {
          const position = (kf.timestamp / duration) * 100;
          const isSelected = kf.keyframe_id === selectedKeyframeId;
          return (
            <button
              key={kf.keyframe_id}
              onClick={(e) => {
                e.stopPropagation();
                onKeyframeClick(kf);
              }}
              className={`absolute top-1/2 -translate-y-1/2 -translate-x-1/2 transition-all duration-200 ${
                isSelected ? 'z-10' : ''
              }`}
              style={{ left: `${position}%` }}
              title={`${kf.timestamp_formatted}${kf.damage_detected ? ' - Damage detected' : ''}`}
            >
              <div
                className={`w-3 h-6 rounded-sm transition-all ${
                  kf.damage_detected
                    ? isSelected
                      ? 'bg-red-600 scale-125'
                      : 'bg-red-500 hover:scale-110'
                    : isSelected
                    ? 'bg-blue-600 scale-125'
                    : 'bg-blue-500 hover:scale-110'
                }`}
              />
            </button>
          );
        })}

        {/* Playhead */}
        <div
          className="absolute top-0 bottom-0 w-0.5 bg-red-600"
          style={{ left: `${(currentTime / duration) * 100}%` }}
        >
          <div className="absolute -top-1 -left-1.5 w-4 h-4 rounded-full bg-red-600 border-2 border-white shadow" />
        </div>
      </div>

      {/* Damage Segments Legend */}
      <div className="flex items-center gap-4 text-xs text-gray-500">
        <div className="flex items-center gap-1.5">
          <div className="w-2 h-4 rounded-sm bg-red-500" />
          <span>Damage detected</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-2 h-4 rounded-sm bg-blue-500" />
          <span>Key moment</span>
        </div>
      </div>
    </div>
  );
};

const VideoTimeline: React.FC<VideoTimelineProps> = ({
  videoUrl,
  duration,
  keyframes,
  onKeyframeSelect,
  selectedKeyframeId,
}) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);

  const damageKeyframes = keyframes.filter((kf) => kf.damage_detected);
  const nonDamageKeyframes = keyframes.filter((kf) => !kf.damage_detected);

  const handlePlayPause = () => {
    if (videoRef.current) {
      if (isPlaying) {
        videoRef.current.pause();
      } else {
        videoRef.current.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  const handleSeek = (time: number) => {
    if (videoRef.current) {
      videoRef.current.currentTime = time;
      setCurrentTime(time);
    }
  };

  const handleTimeUpdate = () => {
    if (videoRef.current) {
      setCurrentTime(videoRef.current.currentTime);
    }
  };

  const handleKeyframeClick = (keyframe: Keyframe) => {
    handleSeek(keyframe.timestamp);
    onKeyframeSelect?.(keyframe);
  };

  const skipToKeyframe = (direction: 'prev' | 'next') => {
    const sortedKeyframes = [...keyframes].sort((a, b) => a.timestamp - b.timestamp);
    const currentIndex = sortedKeyframes.findIndex(
      (kf) => kf.timestamp > currentTime - 0.5
    );

    let targetKeyframe: Keyframe | undefined;
    if (direction === 'next') {
      targetKeyframe = sortedKeyframes[currentIndex] || sortedKeyframes[0];
    } else {
      targetKeyframe = sortedKeyframes[currentIndex - 1] || sortedKeyframes[sortedKeyframes.length - 1];
    }

    if (targetKeyframe) {
      handleKeyframeClick(targetKeyframe);
    }
  };

  const scrollKeyframes = (direction: 'left' | 'right') => {
    if (scrollRef.current) {
      const scrollAmount = 300;
      scrollRef.current.scrollBy({
        left: direction === 'left' ? -scrollAmount : scrollAmount,
        behavior: 'smooth',
      });
    }
  };

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="space-y-6">
      {/* Video Player */}
      {videoUrl && (
        <div className="relative bg-black rounded-xl overflow-hidden">
          <video
            ref={videoRef}
            src={getMediaUrl(videoUrl || '')}
            className="w-full aspect-video"
            onTimeUpdate={handleTimeUpdate}
            onPlay={() => setIsPlaying(true)}
            onPause={() => setIsPlaying(false)}
          />

          {/* Video Controls Overlay */}
          <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-4">
            <div className="flex items-center gap-4">
              <button
                onClick={() => skipToKeyframe('prev')}
                className="p-2 rounded-full bg-white/20 hover:bg-white/30 transition-colors"
              >
                <SkipBack className="w-5 h-5 text-white" />
              </button>
              <button
                onClick={handlePlayPause}
                className="p-3 rounded-full bg-white/20 hover:bg-white/30 transition-colors"
              >
                {isPlaying ? (
                  <Pause className="w-6 h-6 text-white" />
                ) : (
                  <Play className="w-6 h-6 text-white" />
                )}
              </button>
              <button
                onClick={() => skipToKeyframe('next')}
                className="p-2 rounded-full bg-white/20 hover:bg-white/30 transition-colors"
              >
                <SkipForward className="w-5 h-5 text-white" />
              </button>
              <span className="text-white text-sm">
                {formatDuration(currentTime)} / {formatDuration(duration)}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Timeline Bar */}
      <TimelineBar
        duration={duration}
        keyframes={keyframes}
        currentTime={currentTime}
        onSeek={handleSeek}
        onKeyframeClick={handleKeyframeClick}
        selectedKeyframeId={selectedKeyframeId}
      />

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="flex items-center gap-2 text-gray-600 text-sm">
            <Clock className="w-4 h-4" />
            Duration
          </div>
          <div className="text-xl font-semibold text-gray-900 mt-1">
            {formatDuration(duration)}
          </div>
        </div>
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="flex items-center gap-2 text-gray-600 text-sm">
            <Play className="w-4 h-4" />
            Keyframes
          </div>
          <div className="text-xl font-semibold text-gray-900 mt-1">
            {keyframes.length}
          </div>
        </div>
        <div className="bg-red-50 rounded-lg p-4">
          <div className="flex items-center gap-2 text-red-600 text-sm">
            <AlertTriangle className="w-4 h-4" />
            Damage Detected
          </div>
          <div className="text-xl font-semibold text-red-700 mt-1">
            {damageKeyframes.length}
          </div>
        </div>
      </div>

      {/* Keyframes Section */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">
            Extracted Keyframes
          </h3>
          <div className="flex gap-2">
            <button
              onClick={() => scrollKeyframes('left')}
              className="p-2 rounded-lg border border-gray-200 hover:bg-gray-50 transition-colors"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button
              onClick={() => scrollKeyframes('right')}
              className="p-2 rounded-lg border border-gray-200 hover:bg-gray-50 transition-colors"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Damage Keyframes */}
        {damageKeyframes.length > 0 && (
          <div className="mb-6">
            <h4 className="text-sm font-medium text-red-700 mb-3 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4" />
              Frames with Damage ({damageKeyframes.length})
            </h4>
            <div
              ref={scrollRef}
              className="flex gap-3 overflow-x-auto pb-2 scrollbar-thin scrollbar-thumb-gray-300"
            >
              {damageKeyframes.map((kf) => (
                <KeyframeThumbnail
                  key={kf.keyframe_id}
                  keyframe={kf}
                  isSelected={kf.keyframe_id === selectedKeyframeId}
                  onClick={() => handleKeyframeClick(kf)}
                  totalDuration={duration}
                />
              ))}
            </div>
          </div>
        )}

        {/* Other Keyframes */}
        {nonDamageKeyframes.length > 0 && (
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-3">
              Other Key Moments ({nonDamageKeyframes.length})
            </h4>
            <div className="flex gap-3 overflow-x-auto pb-2 scrollbar-thin scrollbar-thumb-gray-300">
              {nonDamageKeyframes.map((kf) => (
                <KeyframeThumbnail
                  key={kf.keyframe_id}
                  keyframe={kf}
                  isSelected={kf.keyframe_id === selectedKeyframeId}
                  onClick={() => handleKeyframeClick(kf)}
                  totalDuration={duration}
                />
              ))}
            </div>
          </div>
        )}

        {keyframes.length === 0 && (
          <div className="text-center py-12 bg-gray-50 rounded-xl">
            <Play className="w-12 h-12 mx-auto mb-4 text-gray-300" />
            <p className="text-gray-500">No keyframes extracted</p>
            <p className="text-sm text-gray-400 mt-1">
              Upload a video to analyze key moments
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default VideoTimeline;
