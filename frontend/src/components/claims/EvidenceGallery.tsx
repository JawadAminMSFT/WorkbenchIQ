'use client';

import React, { useState } from 'react';
import { Image, Video, FileText, ZoomIn, X, ChevronLeft, ChevronRight } from 'lucide-react';
import { MediaItem, DamageArea, getMediaUrl } from '@/lib/api';

interface EvidenceGalleryProps {
  mediaItems: MediaItem[];
  damageAreas?: DamageArea[];
  onMediaSelect?: (media: MediaItem) => void;
  selectedMediaId?: string;
}

interface MediaThumbnailProps {
  media: MediaItem;
  isSelected: boolean;
  onClick: () => void;
  damageCount?: number;
}

const MediaThumbnail: React.FC<MediaThumbnailProps> = ({
  media,
  isSelected,
  onClick,
  damageCount,
}) => {
  const getMediaIcon = () => {
    switch (media.media_type) {
      case 'image':
        return <Image className="w-6 h-6 text-gray-400" />;
      case 'video':
        return <Video className="w-6 h-6 text-gray-400" />;
      default:
        return <FileText className="w-6 h-6 text-gray-400" />;
    }
  };

  return (
    <div
      className={`relative rounded-lg overflow-hidden cursor-pointer transition-all duration-200 ${
        isSelected
          ? 'ring-2 ring-red-500 ring-offset-2'
          : 'hover:ring-2 hover:ring-gray-300 hover:ring-offset-1'
      }`}
      onClick={onClick}
    >
      {/* Thumbnail or Placeholder */}
      <div className="aspect-video bg-gray-100 flex items-center justify-center">
        {media.thumbnail_url ? (
          <img
            src={getMediaUrl(media.thumbnail_url)}
            alt={media.filename}
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="flex flex-col items-center gap-2">
            {getMediaIcon()}
            <span className="text-xs text-gray-500 truncate max-w-[80%]">
              {media.filename}
            </span>
          </div>
        )}
      </div>

      {/* Media Type Badge */}
      <div className="absolute top-2 left-2">
        <span
          className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${
            media.media_type === 'image'
              ? 'bg-blue-100 text-blue-700'
              : media.media_type === 'video'
              ? 'bg-purple-100 text-purple-700'
              : 'bg-gray-100 text-gray-700'
          }`}
        >
          {media.media_type === 'image' && <Image className="w-3 h-3" />}
          {media.media_type === 'video' && <Video className="w-3 h-3" />}
          {media.media_type}
        </span>
      </div>

      {/* Damage Count Badge */}
      {damageCount !== undefined && damageCount > 0 && (
        <div className="absolute top-2 right-2">
          <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-red-500 text-white text-xs font-bold">
            {damageCount}
          </span>
        </div>
      )}

      {/* Processing Status */}
      {!media.processed && (
        <div className="absolute inset-0 bg-black/50 flex items-center justify-center">
          <div className="flex items-center gap-2 text-white text-sm">
            <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
            Processing...
          </div>
        </div>
      )}

      {/* Zoom Icon on Hover */}
      <div className="absolute inset-0 bg-black/0 hover:bg-black/20 transition-colors flex items-center justify-center opacity-0 hover:opacity-100">
        <ZoomIn className="w-8 h-8 text-white drop-shadow-lg" />
      </div>
    </div>
  );
};

interface MediaLightboxProps {
  media: MediaItem;
  damageAreas?: DamageArea[];
  onClose: () => void;
  onPrev?: () => void;
  onNext?: () => void;
  hasPrev: boolean;
  hasNext: boolean;
}

const MediaLightbox: React.FC<MediaLightboxProps> = ({
  media,
  damageAreas,
  onClose,
  onPrev,
  onNext,
  hasPrev,
  hasNext,
}) => {
  const [showDamageOverlay, setShowDamageOverlay] = useState(true);
  const mediaDamageAreas = damageAreas?.filter((d) => d.source_media_id === media.media_id) || [];

  return (
    <div className="fixed inset-0 z-50 bg-black/90 flex items-center justify-center">
      {/* Close Button */}
      <button
        onClick={onClose}
        className="absolute top-4 right-4 p-2 rounded-full bg-white/10 hover:bg-white/20 transition-colors"
      >
        <X className="w-6 h-6 text-white" />
      </button>

      {/* Navigation */}
      {hasPrev && onPrev && (
        <button
          onClick={onPrev}
          className="absolute left-4 top-1/2 -translate-y-1/2 p-2 rounded-full bg-white/10 hover:bg-white/20 transition-colors"
        >
          <ChevronLeft className="w-8 h-8 text-white" />
        </button>
      )}
      {hasNext && onNext && (
        <button
          onClick={onNext}
          className="absolute right-4 top-1/2 -translate-y-1/2 p-2 rounded-full bg-white/10 hover:bg-white/20 transition-colors"
        >
          <ChevronRight className="w-8 h-8 text-white" />
        </button>
      )}

      {/* Media Content */}
      <div className="relative max-w-5xl max-h-[80vh] mx-16">
        {media.media_type === 'image' ? (
          <div className="relative">
            <img
              src={getMediaUrl(media.url)}
              alt={media.filename}
              className="max-w-full max-h-[80vh] object-contain"
            />
            {/* Damage Overlay */}
            {showDamageOverlay &&
              mediaDamageAreas.map((damage) =>
                damage.bounding_box ? (
                  <div
                    key={damage.area_id}
                    className="absolute border-2 border-red-500 bg-red-500/20 rounded"
                    style={{
                      left: `${damage.bounding_box.x}%`,
                      top: `${damage.bounding_box.y}%`,
                      width: `${damage.bounding_box.width}%`,
                      height: `${damage.bounding_box.height}%`,
                    }}
                  >
                    <div className="absolute -top-6 left-0 bg-red-500 text-white text-xs px-2 py-1 rounded whitespace-nowrap">
                      {damage.location} - {damage.severity}
                    </div>
                  </div>
                ) : null
              )}
          </div>
        ) : media.media_type === 'video' ? (
          <video
            src={getMediaUrl(media.url)}
            controls
            className="max-w-full max-h-[80vh]"
            autoPlay
          />
        ) : (
          <div className="bg-white p-8 rounded-lg">
            <FileText className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <p className="text-center text-gray-600">{media.filename}</p>
            <a
              href={getMediaUrl(media.url)}
              target="_blank"
              rel="noopener noreferrer"
              className="mt-4 block text-center text-blue-600 hover:underline"
            >
              Open Document
            </a>
          </div>
        )}
      </div>

      {/* Info Panel */}
      <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-6">
        <div className="max-w-5xl mx-auto flex items-end justify-between">
          <div>
            <h3 className="text-white font-medium">{media.filename}</h3>
            <p className="text-white/70 text-sm">
              {media.media_type} • {(media.size / 1024 / 1024).toFixed(2)} MB
            </p>
            {media.analysis_summary && (
              <p className="text-white/80 text-sm mt-2 max-w-2xl">
                {media.analysis_summary}
              </p>
            )}
          </div>
          {mediaDamageAreas.length > 0 && (
            <button
              onClick={() => setShowDamageOverlay(!showDamageOverlay)}
              className={`px-4 py-2 rounded-lg transition-colors ${
                showDamageOverlay
                  ? 'bg-red-500 text-white'
                  : 'bg-white/20 text-white hover:bg-white/30'
              }`}
            >
              {showDamageOverlay ? 'Hide' : 'Show'} Damage Areas ({mediaDamageAreas.length})
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

const EvidenceGallery: React.FC<EvidenceGalleryProps> = ({
  mediaItems,
  damageAreas = [],
  onMediaSelect,
  selectedMediaId,
}) => {
  const [lightboxIndex, setLightboxIndex] = useState<number | null>(null);
  const [filter, setFilter] = useState<'all' | 'image' | 'video' | 'document'>('all');

  const filteredItems = mediaItems.filter(
    (item) => filter === 'all' || item.media_type === filter
  );

  const getDamageCountForMedia = (mediaId: string) => {
    return damageAreas.filter((d) => d.source_media_id === mediaId).length;
  };

  const handleThumbnailClick = (index: number) => {
    const media = filteredItems[index];
    if (onMediaSelect) {
      onMediaSelect(media);
    }
    setLightboxIndex(index);
  };

  const imageCount = mediaItems.filter((m) => m.media_type === 'image').length;
  const videoCount = mediaItems.filter((m) => m.media_type === 'video').length;
  const documentCount = mediaItems.filter((m) => m.media_type === 'document').length;

  return (
    <div className="space-y-4">
      {/* Filter Tabs */}
      <div className="flex gap-2 border-b border-gray-200 pb-2">
        <button
          onClick={() => setFilter('all')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            filter === 'all'
              ? 'bg-red-100 text-red-700'
              : 'text-gray-600 hover:bg-gray-100'
          }`}
        >
          All ({mediaItems.length})
        </button>
        <button
          onClick={() => setFilter('image')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-2 ${
            filter === 'image'
              ? 'bg-blue-100 text-blue-700'
              : 'text-gray-600 hover:bg-gray-100'
          }`}
        >
          <Image className="w-4 h-4" />
          Images ({imageCount})
        </button>
        <button
          onClick={() => setFilter('video')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-2 ${
            filter === 'video'
              ? 'bg-purple-100 text-purple-700'
              : 'text-gray-600 hover:bg-gray-100'
          }`}
        >
          <Video className="w-4 h-4" />
          Videos ({videoCount})
        </button>
        {documentCount > 0 && (
          <button
            onClick={() => setFilter('document')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-2 ${
              filter === 'document'
                ? 'bg-gray-200 text-gray-800'
                : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            <FileText className="w-4 h-4" />
            Documents ({documentCount})
          </button>
        )}
      </div>

      {/* Gallery Grid */}
      {filteredItems.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          <Image className="w-12 h-12 mx-auto mb-4 text-gray-300" />
          <p>No {filter === 'all' ? 'evidence' : filter + 's'} uploaded yet</p>
        </div>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {filteredItems.map((media, index) => (
            <MediaThumbnail
              key={media.media_id}
              media={media}
              isSelected={media.media_id === selectedMediaId}
              onClick={() => handleThumbnailClick(index)}
              damageCount={getDamageCountForMedia(media.media_id)}
            />
          ))}
        </div>
      )}

      {/* Lightbox */}
      {lightboxIndex !== null && filteredItems[lightboxIndex] && (
        <MediaLightbox
          media={filteredItems[lightboxIndex]}
          damageAreas={damageAreas}
          onClose={() => setLightboxIndex(null)}
          onPrev={
            lightboxIndex > 0 ? () => setLightboxIndex(lightboxIndex - 1) : undefined
          }
          onNext={
            lightboxIndex < filteredItems.length - 1
              ? () => setLightboxIndex(lightboxIndex + 1)
              : undefined
          }
          hasPrev={lightboxIndex > 0}
          hasNext={lightboxIndex < filteredItems.length - 1}
        />
      )}
    </div>
  );
};

export default EvidenceGallery;
