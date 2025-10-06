<template>
  <div class="gallery-container">
    <!-- Gallery Header -->
    <div class="gallery-header">
      <div class="gallery-info">
        <h2>Gallery</h2>
        <p>{{ pagination.totalCount || 0 }} image{{ (pagination.totalCount || 0) !== 1 ? 's' : '' }} found</p>
      </div>
      <div class="gallery-controls">
        <div class="view-mode-toggle">
          <button
            :class="['view-btn', viewMode === 'grid' ? 'active' : '']"
            @click="viewMode = 'grid'"
            title="Grid View"
          >
            ⊞
          </button>
          <button
            :class="['view-btn', viewMode === 'list' ? 'active' : '']"
            @click="viewMode = 'list'"
            title="List View"
          >
            ☰
          </button>
        </div>
      </div>
    </div>

    <!-- Gallery Content -->
    <div :class="['gallery-content', viewMode]">
      <div 
        v-for="image in images" 
        :key="image.id" 
        class="gallery-item"
        @click="handleImageClick(image)"
      >
        <div class="image-card">
          <div class="image-container">
            <img
              :src="getImageUrl(image)"
              :alt="getDisplayName(image)"
              class="gallery-image"
              loading="lazy"
              @error="handleImageError"
              @load="handleImageLoad"
            />
            <div v-if="image.needs_manual_metadata" class="metadata-badge">
              <span>⚠️ Needs Metadata</span>
            </div>
            <div v-if="image.is_manually_edited" class="edited-badge">
              <span>✏️ Edited</span>
            </div>
          </div>
          
          <div class="image-info">
            <h4 class="image-title">{{ getDisplayName(image) }}</h4>
            <p class="image-category">{{ getCategoryName(image) }}</p>
            
            <div v-if="viewMode === 'list'" class="image-details">
              <p class="image-description">{{ getDisplayDescription(image) }}</p>
              <div v-if="getDisplayTags(image).length > 0" class="image-tags">
                <span 
                  v-for="(tag, index) in getDisplayTags(image).slice(0, 3)" 
                  :key="index" 
                  class="image-tag"
                >
                  {{ tag }}
                </span>
                <span v-if="getDisplayTags(image).length > 3" class="tag-more">
                  +{{ getDisplayTags(image).length - 3 }} more
                </span>
              </div>
              <div class="image-meta">
                <span>{{ formatFileSize(image.file_size) }}</span>
                <span>{{ formatDate(image.created_at) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Load More Button -->
    <div v-if="pagination.hasMore" class="load-more-section">
      <button 
        @click="$emit('load-more')"
        class="load-more-btn"
        :disabled="loading"
      >
        {{ loading ? 'Loading...' : 'Load More Images' }}
      </button>
    </div>

    <!-- Error State -->
    <div v-if="error" class="error-state">
      <div class="error-content">
        <h3>Error Loading Images</h3>
        <p>{{ error }}</p>
        <button @click="$emit('retry')" class="retry-button">
          Try Again
        </button>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading && images.length === 0" class="gallery-loading">
      <div class="loading-spinner"></div>
      <p>Loading images...</p>
    </div>

    <!-- Empty State -->
    <div v-if="images.length === 0 && !loading" class="gallery-empty">
      <div class="empty-icon">📷</div>
      <h3>No images found</h3>
      <p>Try adjusting your search criteria or upload some images.</p>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'

export default {
  name: 'Gallery',
  props: {
    images: {
      type: Array,
      default: () => []
    },
    loading: {
      type: Boolean,
      default: false
    },
    error: {
      type: String,
      default: null
    },
    pagination: {
      type: Object,
      default: () => ({})
    }
  },
  emits: ['image-click', 'load-more', 'retry'],
  setup(props, { emit }) {
    const viewMode = ref('grid')

    const handleImageClick = (image) => {
      console.log('🎯 VUE GALLERY CLICK:', image.original_filename)
      emit('image-click', image)
    }

    const getImageUrl = (image) => {
      return `http://localhost:8002/${image.file_path}`
    }

    const getDisplayName = (image) => {
      return image.user_name || image.ai_name || image.original_filename
    }

    const getDisplayDescription = (image) => {
      return image.user_description || image.ai_description || 'No description available'
    }

    const getDisplayTags = (image) => {
      const userTags = image.user_tags || []
      const aiTags = image.ai_tags || []
      return userTags.length > 0 ? userTags : aiTags
    }

    const getCategoryName = (image) => {
      if (image.ai_processing_status === 'pending') return '🤖 AI Analyzing...'
      if (image.ai_processing_status === 'processing') return '⏳ Processing...'
      if (image.ai_processing_status === 'failed') return '❌ AI Failed'
      
      return image.user_category_name || image.ai_category_name || 'Uncategorized'
    }

    const formatFileSize = (bytes) => {
      if (bytes === 0) return '0 Bytes'
      const k = 1024
      const sizes = ['Bytes', 'KB', 'MB', 'GB']
      const i = Math.floor(Math.log(bytes) / Math.log(k))
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
    }

    const formatDate = (dateString) => {
      return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })
    }

    const handleImageError = (event) => {
      console.error('Image failed to load:', event.target.src)
      // You could set a fallback image here
      event.target.style.display = 'none'
    }

    const handleImageLoad = (event) => {
      console.log('Image loaded successfully:', event.target.src)
    }

    return {
      viewMode,
      handleImageClick,
      getImageUrl,
      getDisplayName,
      getDisplayDescription,
      getDisplayTags,
      getCategoryName,
      formatFileSize,
      formatDate,
      handleImageError,
      handleImageLoad
    }
  }
}
</script>

<style scoped>
.gallery-container {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 1.5rem;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.gallery-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.gallery-info h2 {
  color: white;
  font-size: 1.5rem;
  margin-bottom: 0.5rem;
}

.gallery-info p {
  color: rgba(255, 255, 255, 0.8);
  font-size: 0.9rem;
}

.gallery-controls {
  display: flex;
  gap: 1rem;
}

.view-mode-toggle {
  display: flex;
  gap: 0.5rem;
}

.view-btn {
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: white;
  padding: 0.5rem;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.view-btn:hover {
  background: rgba(255, 255, 255, 0.2);
}

.view-btn.active {
  background: rgba(102, 126, 234, 0.3);
  border-color: rgba(102, 126, 234, 0.5);
}

.gallery-content {
  display: grid;
  gap: 1.5rem;
  width: 100%;
}

.gallery-content.grid {
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
}

.gallery-content.list {
  grid-template-columns: 1fr;
  max-width: 800px;
  margin: 0 auto;
}

.gallery-item {
  cursor: pointer;
  transition: transform 0.2s;
}

.gallery-item:hover {
  transform: translateY(-4px);
}

.image-card {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  transition: all 0.3s;
}

.image-card:hover {
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.15);
}

.image-container {
  position: relative;
  aspect-ratio: 16/9;
  overflow: hidden;
}

.gallery-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s;
}

.gallery-item:hover .gallery-image {
  transform: scale(1.05);
}

.metadata-badge,
.edited-badge {
  position: absolute;
  top: 0.5rem;
  right: 0.5rem;
  background: rgba(0, 0, 0, 0.7);
  color: white;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
}

.image-info {
  padding: 1rem;
}

.image-title {
  font-size: 1rem;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 0.5rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.image-category {
  color: #6b7280;
  font-size: 0.875rem;
  margin-bottom: 0.5rem;
}

.image-details {
  margin-top: 0.5rem;
}

.image-description {
  color: #4b5563;
  font-size: 0.875rem;
  line-height: 1.4;
  margin-bottom: 0.5rem;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.image-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
  margin-bottom: 0.5rem;
}

.image-tag {
  background: #e5e7eb;
  color: #374151;
  padding: 0.125rem 0.5rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 500;
}

.tag-more {
  color: #6b7280;
  font-size: 0.75rem;
  font-style: italic;
}

.image-meta {
  display: flex;
  justify-content: space-between;
  color: #9ca3af;
  font-size: 0.75rem;
}

.load-more-section {
  text-align: center;
  margin-top: 2rem;
}

.load-more-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  padding: 1rem 2rem;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.load-more-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
}

.load-more-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.error-state,
.gallery-loading,
.gallery-empty {
  text-align: center;
  padding: 3rem;
  color: white;
}

.error-content h3 {
  font-size: 1.5rem;
  margin-bottom: 1rem;
}

.error-content p {
  margin-bottom: 1.5rem;
  opacity: 0.8;
}

.retry-button {
  background: rgba(255, 255, 255, 0.2);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.3);
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.retry-button:hover {
  background: rgba(255, 255, 255, 0.3);
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid rgba(255, 255, 255, 0.3);
  border-top: 4px solid white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.empty-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
}

.gallery-empty h3 {
  font-size: 1.5rem;
  margin-bottom: 0.5rem;
}

.gallery-empty p {
  opacity: 0.8;
}

/* Mobile responsiveness */
@media (max-width: 768px) {
  .gallery-container {
    padding: 1rem;
  }
  
  .gallery-header {
    flex-direction: column;
    align-items: stretch;
    gap: 1rem;
  }
  
  .gallery-info h2 {
    font-size: 1.3rem;
  }
  
  .gallery-info p {
    font-size: 0.8rem;
  }
  
  .gallery-controls {
    justify-content: center;
  }
  
  .gallery-content {
    gap: 1rem;
  }
  
  .gallery-content.grid {
    grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  }
  
  .image-card {
    border-radius: 8px;
  }
  
  .image-info {
    padding: 0.75rem;
  }
  
  .image-title {
    font-size: 0.9rem;
  }
  
  .image-category {
    font-size: 0.8rem;
  }
  
  .load-more-btn {
    padding: 0.75rem 1.5rem;
    font-size: 0.9rem;
  }
}

@media (max-width: 480px) {
  .gallery-container {
    padding: 0.75rem;
  }
  
  .gallery-header {
    padding: 0.75rem;
  }
  
  .gallery-info h2 {
    font-size: 1.2rem;
  }
  
  .gallery-info p {
    font-size: 0.75rem;
  }
  
  .gallery-content {
    gap: 0.75rem;
  }
  
  .gallery-content.grid {
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  }
  
  .image-info {
    padding: 0.5rem;
  }
  
  .image-title {
    font-size: 0.8rem;
  }
  
  .image-category {
    font-size: 0.75rem;
  }
  
  .image-description {
    font-size: 0.8rem;
  }
  
  .image-tag {
    font-size: 0.7rem;
    padding: 0.1rem 0.4rem;
  }
  
  .image-meta {
    font-size: 0.7rem;
  }
  
  .load-more-btn {
    padding: 0.6rem 1.2rem;
    font-size: 0.8rem;
  }
  
  .error-content h3 {
    font-size: 1.2rem;
  }
  
  .error-content p {
    font-size: 0.9rem;
  }
  
  .retry-button {
    padding: 0.6rem 1.2rem;
    font-size: 0.9rem;
  }
}

/* Tablet responsiveness */
@media (min-width: 769px) and (max-width: 1024px) {
  .gallery-content.grid {
    grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  }
}

/* Large desktop */
@media (min-width: 1400px) {
  .gallery-content.grid {
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  }
}

/* Ultra-wide screens */
@media (min-width: 1920px) {
  .gallery-content.grid {
    grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  }
}
</style>
