<template>
  <div class="main-page">
    <div class="main-header">
      <h1>Photo Gallery - Vue.js</h1>
      <button 
        class="upload-toggle-btn"
        @click="showUpload = !showUpload"
      >
        {{ showUpload ? 'Hide Upload' : 'Show Upload' }}
      </button>
    </div>

    <!-- Upload Results -->
    <div v-if="uploadResults.length > 0" class="upload-results">
      <div 
        v-for="(result, index) in uploadResults" 
        :key="index" 
        :class="['upload-result', result.type]"
      >
        {{ result.message }}
      </div>
    </div>

    <!-- Upload Section -->
    <div v-if="showUpload" class="upload-section">
      <FileUpload
        @upload="handleSingleUpload"
        @batch-upload="handleUploadComplete"
        :multiple="true"
      />
    </div>

    <!-- Search Section -->
    <div class="search-section">
      <SearchBar
        @search="handleSearch"
        @filter-change="handleSearch"
        :initial-query="searchParams.query"
        :initial-filters="searchParams"
        :categories="categories"
      />
    </div>

    <!-- Gallery Section -->
    <div class="gallery-section">
      <Gallery
        :images="images"
        :loading="loading"
        :error="error"
        :pagination="pagination"
        @image-click="handleImageClick"
        @load-more="handleLoadMore"
        @retry="handleRetry"
      />
    </div>

    <!-- Modal -->
    <ImageModal
      v-if="isModalOpen && selectedImage"
      :key="selectedImage.id + '_' + (selectedImage.updated_at || selectedImage.created_at)"
      :image="selectedImage"
      :categories="categories"
      @close="handleModalClose"
      @save="handleSave"
      @reset="handleReset"
      @reanalyze="handleReanalyze"
      @delete="handleDelete"
    />
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import axios from 'axios'
import SearchBar from '../components/SearchBar.vue'
import Gallery from '../components/Gallery.vue'
import FileUpload from '../components/FileUpload.vue'
import ImageModal from '../components/ImageModal.vue'

export default {
  name: 'MainPage',
  components: {
    SearchBar,
    Gallery,
    FileUpload,
    ImageModal
  },
  setup() {
    // State
    const images = ref([])
    const loading = ref(false)
    const error = ref(null)
    const pagination = ref({})
    const categories = ref([])
    const selectedImage = ref(null)
    const isModalOpen = ref(false)
    const uploadResults = ref([])
    const showUpload = ref(false)

    const searchParams = reactive({
      query: '',
      category_id: [],
      tag: [],
      date_from: null,
      date_to: null,
      sort_by: 'created_at',
      sort_order: 'desc',
      page: 1,
      limit: 20
    })

    // Load gallery data
    const loadGallery = async (params = searchParams, append = false) => {
      loading.value = true
      error.value = null
      
      try {
        const queryParams = new URLSearchParams()
        
        if (params.query) queryParams.append('query', params.query)
        if (params.category_id && params.category_id.length > 0) {
          params.category_id.forEach(id => queryParams.append('category_id', id))
        }
        if (params.tags && params.tags.length > 0) {
          params.tags.forEach(tag => queryParams.append('tags', tag))
        }
        if (params.date_from) queryParams.append('date_from', params.date_from)
        if (params.date_to) queryParams.append('date_to', params.date_to)
        if (params.sort_by) queryParams.append('sort_by', params.sort_by)
        if (params.sort_order) queryParams.append('sort_order', params.sort_order)
        if (params.page) queryParams.append('page', params.page)
        if (params.limit) queryParams.append('limit', params.limit)

        const response = await axios.get(`http://localhost:8002/api/search/gallery?${queryParams}`)
        const data = response.data
        
        if (append) {
          images.value = [...images.value, ...data.images]
        } else {
          images.value = data.images || []
          categories.value = data.categories || []
        }
        
        pagination.value = data.pagination || {
          totalCount: 0,
          hasMore: false,
          currentPage: 1,
          totalPages: 1
        }
      } catch (err) {
        console.error('Error loading gallery:', err)
        error.value = err.response?.data?.detail || err.message || 'Failed to load images'
        // Reset data on error
        if (!append) {
          images.value = []
          categories.value = []
          pagination.value = {
            totalCount: 0,
            hasMore: false,
            currentPage: 1,
            totalPages: 1
          }
        }
      } finally {
        loading.value = false
      }
    }

    // Handle search
    const handleSearch = (newParams) => {
      console.log('MainPage: Received search params:', newParams)
      Object.assign(searchParams, newParams)
      searchParams.page = 1
      console.log('MainPage: Updated searchParams:', searchParams)
      loadGallery(searchParams, false)
    }

    // Handle load more
    const handleLoadMore = () => {
      const nextPage = pagination.value.current_page + 1
      if (nextPage <= pagination.value.total_pages) {
        searchParams.page = nextPage
        loadGallery(searchParams, true)
      }
    }

    // Handle retry
    const handleRetry = () => {
      loadGallery()
    }

    // Handle image click - SIMPLE AND RELIABLE
    const handleImageClick = (image) => {
      console.log('🎯 VUE IMAGE CLICK:', image.original_filename)
      selectedImage.value = image
      isModalOpen.value = true
    }

    // Handle modal close
    const handleModalClose = () => {
      console.log('🔒 VUE MODAL CLOSE')
      isModalOpen.value = false
      selectedImage.value = null
    }

    // Handle single upload
    const handleSingleUpload = (result) => {
      console.log('Single upload result:', result)
      if (result.success) {
        uploadResults.value.push({ 
          type: 'success', 
          message: `✅ ${result.data.original_filename} uploaded successfully` 
        })
        setTimeout(() => showUpload.value = false, 2000)
        setTimeout(() => loadGallery(), 1000)
      } else {
        uploadResults.value.push({ 
          type: 'error', 
          message: `❌ Upload failed: ${result.error}` 
        })
      }
    }

    // Handle batch upload
    const handleUploadComplete = (results) => {
      console.log('Batch upload results:', results)
      const successCount = results.filter(r => r.success).length
      const errorCount = results.filter(r => !r.success).length
      
      if (successCount > 0) {
        uploadResults.value.push({ 
          type: 'success', 
          message: `✅ ${successCount} image(s) uploaded successfully` 
        })
      }
      
      if (errorCount > 0) {
        uploadResults.value.push({ 
          type: 'error', 
          message: `❌ ${errorCount} image(s) failed to upload` 
        })
      }
      
      setTimeout(() => showUpload.value = false, 2000)
      setTimeout(() => loadGallery(), 1000)
    }

    // Modal handlers
    const handleSave = async (imageId, formData) => {
      try {
        const response = await axios.put(`http://localhost:8002/api/metadata/${imageId}`, formData)
        console.log('Metadata saved successfully:', response.data)
        await loadGallery() // Refresh gallery
        
        // Update the selected image with the new data
        if (selectedImage.value && selectedImage.value.id === imageId) {
          const updatedImage = images.value.find(img => img.id === imageId)
          if (updatedImage) {
            selectedImage.value = updatedImage
            console.log('Updated selected image:', selectedImage.value)
          }
        }
      } catch (err) {
        console.error('Error saving metadata:', err)
        throw new Error(err.response?.data?.detail || err.message || 'Failed to save metadata')
      }
    }

    const handleReset = async (imageId) => {
      try {
        await axios.delete(`http://localhost:8002/api/metadata/${imageId}`)
        await loadGallery() // Refresh gallery
        
        // Force update the selected image data
        if (selectedImage.value && selectedImage.value.id === imageId) {
          const updatedImage = images.value.find(img => img.id === imageId)
          if (updatedImage) {
            selectedImage.value = updatedImage
          }
        }
      } catch (err) {
        throw new Error(err.response?.data?.detail || 'Failed to reset metadata')
      }
    }

    const handleReanalyze = async (imageId) => {
      try {
        await axios.post(`http://localhost:8002/api/metadata/${imageId}/reanalyze`)
        await loadGallery() // Refresh gallery
      } catch (err) {
        throw new Error(err.response?.data?.detail || 'Failed to trigger re-analysis')
      }
    }

    const handleDelete = async (imageId) => {
      try {
        await axios.delete(`http://localhost:8002/api/files/${imageId}`)
        await loadGallery() // Refresh gallery
        handleModalClose()
      } catch (err) {
        throw new Error(err.response?.data?.detail || 'Failed to delete image')
      }
    }

    // Load initial data
    onMounted(() => {
      loadGallery()
    })

    return {
      images,
      loading,
      error,
      pagination,
      categories,
      selectedImage,
      isModalOpen,
      uploadResults,
      showUpload,
      searchParams,
      handleSearch,
      handleLoadMore,
      handleRetry,
      handleImageClick,
      handleModalClose,
      handleSingleUpload,
      handleUploadComplete,
      handleSave,
      handleReset,
      handleReanalyze,
      handleDelete
    }
  }
}
</script>

<style scoped>
.main-page {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 1rem;
  flex: 1;
  display: flex;
  flex-direction: column;
}

.main-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  padding: 1.5rem;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  flex-wrap: wrap;
  gap: 1rem;
}

.main-header h1 {
  color: white;
  font-size: clamp(1.4rem, 3vw, 1.8rem);
  font-weight: 600;
  margin: 0;
  flex: 1;
  min-width: 200px;
}

.upload-toggle-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
  flex-shrink: 0;
}

.upload-toggle-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
}

.upload-results {
  margin-bottom: 1rem;
}

.upload-result {
  padding: 1rem;
  border-radius: 8px;
  margin-bottom: 0.5rem;
  font-weight: 500;
  word-break: break-word;
}

.upload-result.success {
  background: rgba(34, 197, 94, 0.1);
  color: #22c55e;
  border: 1px solid rgba(34, 197, 94, 0.2);
}

.upload-result.error {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
  border: 1px solid rgba(239, 68, 68, 0.2);
}

.upload-section,
.search-section,
.gallery-section {
  margin-bottom: 1.5rem;
  flex-shrink: 0;
}

.gallery-section {
  flex: 1;
  display: flex;
  flex-direction: column;
}

/* Mobile responsiveness */
@media (max-width: 768px) {
  .main-page {
    padding: 0 0.5rem;
  }
  
  .main-header {
    flex-direction: column;
    align-items: stretch;
    text-align: center;
    padding: 1rem;
  }
  
  .main-header h1 {
    font-size: 1.4rem;
    margin-bottom: 0.5rem;
  }
  
  .upload-toggle-btn {
    width: 100%;
    padding: 0.75rem;
  }
  
  .upload-section,
  .search-section,
  .gallery-section {
    margin-bottom: 1rem;
  }
}

@media (max-width: 480px) {
  .main-page {
    padding: 0 0.25rem;
  }
  
  .main-header {
    padding: 0.75rem;
  }
  
  .main-header h1 {
    font-size: 1.2rem;
  }
  
  .upload-toggle-btn {
    padding: 0.6rem 1rem;
    font-size: 0.9rem;
  }
  
  .upload-result {
    padding: 0.75rem;
    font-size: 0.9rem;
  }
}

/* Tablet responsiveness */
@media (min-width: 769px) and (max-width: 1024px) {
  .main-page {
    padding: 0 0.75rem;
  }
  
  .main-header {
    padding: 1.25rem;
  }
  
  .main-header h1 {
    font-size: 1.6rem;
  }
}

/* Large desktop */
@media (min-width: 1400px) {
  .main-page {
    padding: 0 2rem;
  }
}
</style>
