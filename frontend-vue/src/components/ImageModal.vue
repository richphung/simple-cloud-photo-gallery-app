<template>
  <div class="modal-overlay" @click="handleClose">
    <div class="modal-content" @click.stop>
      <div class="modal-header">
        <h2>Edit Image Metadata</h2>
        <button class="close-button" @click="handleClose">×</button>
      </div>

      <div class="modal-body">
        <!-- Image Preview -->
        <div class="image-preview">
          <img :src="getImageUrl()" :alt="image.original_filename" />
          <div class="image-info">
            <h3>{{ image.original_filename }}</h3>
            <p>File size: {{ formatFileSize(image.file_size) }} MB</p>
            <p>Uploaded: {{ formatDate(image.created_at) }}</p>
          </div>
        </div>

        <!-- Form Fields -->
        <div class="form-fields">

          <!-- Name Field -->
          <div class="form-group">
            <label>Image Name</label>
            <input
              v-model="formData.user_name"
              type="text"
              placeholder="Enter a name for this image"
              class="form-input"
            />
          </div>

          <!-- Description Field -->
          <div class="form-group">
            <label>Description</label>
            <textarea
              v-model="formData.user_description"
              placeholder="Describe what's in this image"
              rows="3"
              class="form-textarea"
            ></textarea>
          </div>

          <!-- Category Field -->
          <div class="form-group">
            <label>Category</label>
            <select v-model="formData.user_category_id" class="form-select">
              <option value="">Select a category</option>
              <option 
                v-for="category in categories" 
                :key="category.id" 
                :value="category.id"
              >
                {{ category.name }} ({{ category.usage_count }})
              </option>
            </select>
          </div>

          <!-- Tags Field -->
          <div class="form-group">
            <label>Tags</label>
            <div class="tag-input-container">
              <input
                v-model="tagInput"
                type="text"
                placeholder="Add a tag and press Enter"
                class="form-input"
                @keypress.enter="handleTagAdd"
              />
              <button
                type="button"
                @click="handleTagAdd"
                class="add-tag-button"
                :disabled="!tagInput.trim()"
              >
                Add
              </button>
            </div>
            
            <!-- Current Tags -->
            <div class="current-tags">
              <span 
                v-for="(tag, index) in formData.user_tags" 
                :key="index" 
                class="tag"
              >
                {{ tag }}
                <button
                  type="button"
                  @click="handleTagRemove(tag)"
                  class="remove-tag"
                >
                  ×
                </button>
              </span>
              <p v-if="formData.user_tags.length === 0" class="no-tags">
                No tags added yet
              </p>
            </div>
          </div>
        </div>
      </div>

      <!-- AI Data Display -->
      <div v-if="image.ai_name || image.ai_description" class="ai-data-section">
        <h4>AI Analysis</h4>
        <div class="ai-data">
          <div v-if="image.ai_name" class="ai-field">
            <strong>AI Name:</strong> {{ image.ai_name }}
          </div>
          <div v-if="image.ai_description" class="ai-field">
            <strong>AI Description:</strong> {{ image.ai_description }}
          </div>
          <div v-if="image.ai_category_name" class="ai-field">
            <strong>AI Category:</strong> {{ image.ai_category_name }}
          </div>
          <div v-if="image.ai_tags && image.ai_tags.length > 0" class="ai-field">
            <strong>AI Tags:</strong> {{ image.ai_tags.join(', ') }}
          </div>
          <div v-if="image.ai_confidence_score" class="ai-field">
            <strong>Confidence:</strong> {{ Math.round(image.ai_confidence_score * 100) }}%
          </div>
        </div>
      </div>

      <!-- Error Display -->
      <div v-if="error" class="error-message">
        {{ error }}
      </div>

      <!-- Modal Actions -->
      <div class="modal-actions">
        <div class="action-group">
          <button
            v-if="image.ai_processing_status === 'failed' || image.ai_processing_status === 'in_progress'"
            @click="handleReanalyze"
            :disabled="loading || image.ai_processing_status === 'in_progress'"
            class="action-button secondary"
          >
            {{ loading || image.ai_processing_status === 'in_progress' ? 'Processing...' : '🤖 Re-analyze with AI' }}
          </button>
          <button
            v-if="hasUserData"
            @click="handleReset"
            :disabled="loading"
            class="action-button warning"
          >
            🔄 Clear All User Data
          </button>
        </div>
        
        <div class="action-group">
          <button
            @click="handleDelete"
            :disabled="loading"
            class="action-button danger"
          >
            Delete Image
          </button>
          <button
            @click="handleClose"
            :disabled="loading"
            class="action-button secondary"
          >
            Cancel
          </button>
          <button
            @click="handleSave"
            :disabled="loading || !hasChanges"
            class="action-button primary"
          >
            {{ loading ? 'Saving...' : 'Save Changes' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive, computed, watch } from 'vue'

export default {
  name: 'ImageModal',
  props: {
    image: {
      type: Object,
      required: true
    },
    categories: {
      type: Array,
      default: () => []
    }
  },
  emits: ['close', 'save', 'reset', 'reanalyze', 'delete'],
  setup(props, { emit }) {
    const loading = ref(false)
    const error = ref(null)
    const tagInput = ref('')

    const formData = reactive({
      user_name: '',
      user_description: '',
      user_tags: [],
      user_category_id: null
    })

    // Initialize form data
    const initializeForm = () => {
      console.log('Initializing form with image:', props.image)
      formData.user_name = props.image.user_name || props.image.ai_name || ''
      formData.user_description = props.image.user_description || props.image.ai_description || ''
      
      // Handle tags properly - use user tags if available, otherwise use AI tags
      if (props.image.user_tags && Array.isArray(props.image.user_tags) && props.image.user_tags.length > 0) {
        formData.user_tags = [...props.image.user_tags]
        console.log('Using user tags:', formData.user_tags)
      } else if (props.image.ai_tags && Array.isArray(props.image.ai_tags) && props.image.ai_tags.length > 0) {
        formData.user_tags = [...props.image.ai_tags]
        console.log('Using AI tags:', formData.user_tags)
      } else {
        formData.user_tags = []
        console.log('No tags available')
      }
      
      formData.user_category_id = props.image.user_category_id || props.image.ai_category_id || null
      
      console.log('Form initialized with:', {
        user_name: formData.user_name,
        user_description: formData.user_description,
        user_tags: formData.user_tags,
        user_category_id: formData.user_category_id
      })
    }

    // Initialize on mount
    initializeForm()

    // Watch for image changes
    watch(() => props.image, (newImage, oldImage) => {
      console.log('Image prop changed in modal:', { newImage, oldImage })
      // Force re-initialization with a small delay to ensure data is updated
      setTimeout(() => {
        initializeForm()
        console.log('Form re-initialized after image change:', formData)
      }, 100)
    }, { deep: true })

    const hasChanges = computed(() => {
      return formData.user_name !== (props.image.user_name || props.image.ai_name || '') ||
             formData.user_description !== (props.image.user_description || props.image.ai_description || '') ||
             JSON.stringify(formData.user_tags) !== JSON.stringify(props.image.user_tags || props.image.ai_tags || []) ||
             formData.user_category_id !== (props.image.user_category_id || props.image.ai_category_id || null)
    })

    const hasUserData = computed(() => {
      const hasUser = !!(props.image.user_name || props.image.user_description || 
                        (props.image.user_tags && props.image.user_tags.length > 0) || 
                        props.image.user_category_id)
      console.log('hasUserData computed:', hasUser, {
        user_name: props.image.user_name,
        user_description: props.image.user_description,
        user_tags: props.image.user_tags,
        user_category_id: props.image.user_category_id,
        fullImage: props.image
      })
      return hasUser
    })

    const hasAIData = computed(() => {
      return !!(props.image.ai_name || props.image.ai_description || 
               (props.image.ai_tags && props.image.ai_tags.length > 0) || 
               props.image.ai_category_id)
    })

    const handleTagAdd = () => {
      const trimmedTag = tagInput.value.trim()
      if (trimmedTag && !formData.user_tags.includes(trimmedTag)) {
        formData.user_tags.push(trimmedTag)
        tagInput.value = ''
      }
    }

    const handleTagRemove = (tagToRemove) => {
      const index = formData.user_tags.indexOf(tagToRemove)
      if (index > -1) {
        formData.user_tags.splice(index, 1)
      }
    }

    const handleSave = async () => {
      loading.value = true
      error.value = null
      
      try {
        await emit('save', props.image.id, formData)
      } catch (err) {
        error.value = err.message || 'Failed to save metadata'
      } finally {
        loading.value = false
      }
    }

    const handleDelete = async () => {
      if (confirm('Are you sure you want to delete this image? This action cannot be undone.')) {
        loading.value = true
        error.value = null
        
        try {
          await emit('delete', props.image.id)
        } catch (err) {
          error.value = err.message || 'Failed to delete image'
        } finally {
          loading.value = false
        }
      }
    }

    const handleReanalyze = async () => {
      loading.value = true
      error.value = null
      
      try {
        await emit('reanalyze', props.image.id)
      } catch (err) {
        error.value = err.message || 'Failed to trigger re-analysis'
      } finally {
        loading.value = false
      }
    }

    const handleClose = () => {
      emit('close')
    }


    const handleReset = async () => {
      if (confirm('Are you sure you want to clear all user data and revert to AI data? This will remove all manual edits.')) {
        loading.value = true
        error.value = null
        
        try {
          await emit('reset', props.image.id)
          // Wait for the parent to update the image data
          await new Promise(resolve => setTimeout(resolve, 200))
          
          // Force update the form data to show AI data
          formData.user_name = props.image.ai_name || ''
          formData.user_description = props.image.ai_description || ''
          
          // Use AI tags for reset
          if (props.image.ai_tags && Array.isArray(props.image.ai_tags) && props.image.ai_tags.length > 0) {
            formData.user_tags = [...props.image.ai_tags]
            console.log('Reset: Using AI tags:', formData.user_tags)
          } else {
            formData.user_tags = []
            console.log('Reset: No AI tags available')
          }
          
          formData.user_category_id = props.image.ai_category_id || null
          
          console.log('Reset completed, form now shows AI data:', formData)
          console.log('hasUserData after reset:', hasUserData.value)
        } catch (err) {
          error.value = err.message || 'Failed to reset metadata'
        } finally {
          loading.value = false
        }
      }
    }

    const getImageUrl = () => {
      return `http://localhost:8002/${props.image.file_path}`
    }

    const formatFileSize = (bytes) => {
      return (bytes / 1024 / 1024).toFixed(2)
    }

    const formatDate = (dateString) => {
      return new Date(dateString).toLocaleDateString()
    }

    return {
      loading,
      error,
      tagInput,
      formData,
      hasChanges,
      hasUserData,
      hasAIData,
      handleTagAdd,
      handleTagRemove,
      handleSave,
      handleDelete,
      handleReanalyze,
      handleClose,
      handleReset,
      getImageUrl,
      formatFileSize,
      formatDate
    }
  }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  animation: fadeIn 0.2s ease-out;
}

.modal-content {
  background: white;
  border-radius: 12px;
  max-width: 800px;
  max-height: 90vh;
  width: 90%;
  overflow: hidden;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
  animation: slideIn 0.3s ease-out;
  display: flex;
  flex-direction: column;
}

.modal-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 1.5rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-header h2 {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 600;
}

.close-button {
  background: none;
  border: none;
  color: white;
  font-size: 24px;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.close-button:hover {
  background: rgba(255, 255, 255, 0.2);
}

.modal-body {
  padding: 2rem;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
  flex: 1;
  overflow-y: auto;
}

.image-preview {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.image-preview img {
  width: 100%;
  max-height: 200px;
  object-fit: cover;
  border-radius: 8px;
}

.image-info h3 {
  margin: 0 0 0.5rem 0;
  color: #333;
  font-size: 1.1rem;
}

.image-info p {
  margin: 0.25rem 0;
  color: #666;
  font-size: 0.9rem;
}

.form-fields {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-group label {
  font-weight: 600;
  color: #374151;
  font-size: 0.9rem;
}

.form-input,
.form-textarea,
.form-select {
  padding: 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 0.9rem;
  transition: border-color 0.2s;
}

.form-input:focus,
.form-textarea:focus,
.form-select:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.form-textarea {
  resize: vertical;
  min-height: 80px;
}

.tag-input-container {
  display: flex;
  gap: 0.5rem;
}

.tag-input-container .form-input {
  flex: 1;
}

.add-tag-button {
  background: #667eea;
  color: white;
  border: none;
  padding: 0.75rem 1rem;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  transition: background-color 0.2s;
}

.add-tag-button:hover:not(:disabled) {
  background: #5a67d8;
}

.add-tag-button:disabled {
  background: #9ca3af;
  cursor: not-allowed;
}

.current-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-top: 0.5rem;
  min-height: 2rem;
  align-items: flex-start;
}

.tag {
  background: #dbeafe;
  color: #1e40af;
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.8rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  border: 1px solid #93c5fd;
  font-weight: 500;
}

.remove-tag {
  background: none;
  border: none;
  color: #6b7280;
  cursor: pointer;
  font-size: 1rem;
  padding: 0;
  width: 16px;
  height: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: background-color 0.2s;
}

.remove-tag:hover {
  background: #d1d5db;
}

.no-tags {
  color: #6b7280;
  font-style: italic;
  font-size: 0.875rem;
  padding: 0.5rem;
  background: #f9fafb;
  border-radius: 6px;
  border: 1px dashed #d1d5db;
  text-align: center;
  width: 100%;
  margin: 0;
}

.ai-data-section {
  grid-column: 1 / -1;
  background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%);
  padding: 1.5rem;
  border-radius: 8px;
  margin-top: 1rem;
}

.ai-data-section h4 {
  margin: 0 0 1rem 0;
  color: #374151;
  font-size: 1.1rem;
}

.ai-data {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.ai-field {
  font-size: 0.9rem;
  line-height: 1.4;
}

.ai-field strong {
  color: #374151;
  display: block;
  margin-bottom: 0.25rem;
}

.error-message {
  grid-column: 1 / -1;
  background: #fef2f2;
  color: #dc2626;
  padding: 1rem;
  border-radius: 6px;
  border: 1px solid #fecaca;
  margin-top: 1rem;
}

.modal-actions {
  background: #f8f9fa;
  padding: 1.5rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  flex-shrink: 0;
  border-top: 1px solid #e5e7eb;
}

.action-group {
  display: flex;
  gap: 0.75rem;
}

.action-button {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.action-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.action-button.primary {
  background: #667eea;
  color: white;
}

.action-button.primary:hover:not(:disabled) {
  background: #5a67d8;
  transform: translateY(-1px);
}

.action-button.secondary {
  background: #6b7280;
  color: white;
}

.action-button.secondary:hover:not(:disabled) {
  background: #4b5563;
}

.action-button.danger {
  background: #dc2626;
  color: white;
}

.action-button.danger:hover:not(:disabled) {
  background: #b91c1c;
}

.action-button.warning {
  background: #f59e0b;
  color: white;
}

.action-button.warning:hover:not(:disabled) {
  background: #d97706;
}


@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideIn {
  from { 
    opacity: 0;
    transform: scale(0.9) translateY(-20px);
  }
  to { 
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

/* Mobile responsiveness */
@media (max-width: 768px) {
  .modal-content {
    width: 95%;
    max-height: 95vh;
    margin: 1rem;
    display: flex;
    flex-direction: column;
  }
  
  .modal-header {
    padding: 1rem;
  }
  
  .modal-header h2 {
    font-size: 1.3rem;
  }
  
  .modal-body {
    grid-template-columns: 1fr;
    padding: 1rem;
    gap: 1rem;
    flex: 1;
    overflow-y: auto;
  }
  
  .image-preview img {
    max-height: 150px;
  }
  
  .image-info h3 {
    font-size: 1rem;
  }
  
  .image-info p {
    font-size: 0.8rem;
  }
  
  .form-fields {
    gap: 1rem;
  }
  
  .form-group label {
    font-size: 0.8rem;
  }
  
  .form-input,
  .form-textarea,
  .form-select {
    font-size: 0.8rem;
    padding: 0.6rem;
  }
  
  .form-textarea {
    min-height: 60px;
  }
  
  .tag-input-container {
    flex-direction: column;
    gap: 0.5rem;
  }
  
  .add-tag-button {
    padding: 0.6rem;
    font-size: 0.8rem;
  }
  
  .tag {
    font-size: 0.7rem;
    padding: 0.2rem 0.6rem;
  }
  
  .remove-tag {
    width: 14px;
    height: 14px;
    font-size: 0.8rem;
  }
  
  .ai-data-section {
    padding: 1rem;
  }
  
  .ai-data-section h4 {
    font-size: 1rem;
  }
  
  .ai-data {
    grid-template-columns: 1fr;
    gap: 0.75rem;
  }
  
  .ai-field {
    font-size: 0.8rem;
  }
  
  .modal-actions {
    flex-direction: column;
    align-items: stretch;
    padding: 1rem;
    gap: 0.75rem;
    flex-shrink: 0;
  }
  
  .action-group {
    justify-content: center;
    flex-wrap: wrap;
  }
  
  .action-button {
    padding: 0.6rem 1rem;
    font-size: 0.8rem;
    flex: 1;
    min-width: 120px;
  }
}

@media (max-width: 480px) {
  .modal-content {
    width: 98%;
    max-height: 98vh;
    margin: 0.5rem;
    display: flex;
    flex-direction: column;
  }
  
  .modal-header {
    padding: 0.75rem;
  }
  
  .modal-header h2 {
    font-size: 1.2rem;
  }
  
  .close-button {
    font-size: 20px;
    padding: 0.4rem;
  }
  
  .modal-body {
    padding: 0.75rem;
    gap: 0.75rem;
    flex: 1;
    overflow-y: auto;
  }
  
  .image-preview img {
    max-height: 120px;
  }
  
  .image-info h3 {
    font-size: 0.9rem;
  }
  
  .image-info p {
    font-size: 0.75rem;
  }
  
  .form-fields {
    gap: 0.75rem;
  }
  
  .form-group label {
    font-size: 0.75rem;
  }
  
  .form-input,
  .form-textarea,
  .form-select {
    font-size: 0.75rem;
    padding: 0.5rem;
  }
  
  .form-textarea {
    min-height: 50px;
  }
  
  .add-tag-button {
    padding: 0.5rem;
    font-size: 0.75rem;
  }
  
  .tag {
    font-size: 0.65rem;
    padding: 0.15rem 0.5rem;
  }
  
  .remove-tag {
    width: 12px;
    height: 12px;
    font-size: 0.7rem;
  }
  
  .ai-data-section {
    padding: 0.75rem;
  }
  
  .ai-data-section h4 {
    font-size: 0.9rem;
  }
  
  .ai-field {
    font-size: 0.75rem;
  }
  
  .modal-actions {
    padding: 0.75rem;
    gap: 0.5rem;
    flex-shrink: 0;
  }
  
  .action-button {
    padding: 0.5rem 0.75rem;
    font-size: 0.75rem;
    min-width: 100px;
  }
}

/* Tablet responsiveness */
@media (min-width: 769px) and (max-width: 1024px) {
  .modal-content {
    width: 90%;
    max-width: 700px;
  }
  
  .modal-body {
    grid-template-columns: 1fr 1fr;
    gap: 1.5rem;
  }
  
  .ai-data {
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  }
}

/* Large desktop */
@media (min-width: 1400px) {
  .modal-content {
    max-width: 900px;
  }
  
  .modal-body {
    gap: 2rem;
  }
  
  .ai-data {
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  }
}
</style>
