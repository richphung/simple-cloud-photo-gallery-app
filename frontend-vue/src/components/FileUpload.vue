<template>
  <div class="upload-container">
    <div 
      :class="['drag-drop-area', { 'drag-active': isDragOver }]"
      @dragover.prevent="handleDragOver"
      @dragleave.prevent="handleDragLeave"
      @drop.prevent="handleDrop"
      @click="triggerFileInput"
    >
      <div class="upload-icon">📁</div>
      <div class="upload-text">
        <strong>Drag & drop images here or click to browse</strong>
        <p>Supports JPG, PNG, GIF, WebP, and more</p>
      </div>
      <input
        ref="fileInput"
        type="file"
        multiple
        accept="image/*"
        @change="handleFileSelect"
        style="display: none"
      />
    </div>

    <!-- Upload Progress -->
    <div v-if="uploading" class="upload-progress">
      <div class="progress-bar">
        <div class="progress-fill" :style="{ width: uploadProgress + '%' }"></div>
      </div>
      <p>{{ uploadStatus }}</p>
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
  </div>
</template>

<script>
import { ref } from 'vue'
import axios from 'axios'

export default {
  name: 'FileUpload',
  props: {
    multiple: {
      type: Boolean,
      default: true
    }
  },
  emits: ['upload', 'batch-upload'],
  setup(props, { emit }) {
    const fileInput = ref(null)
    const isDragOver = ref(false)
    const uploading = ref(false)
    const uploadProgress = ref(0)
    const uploadStatus = ref('')
    const uploadResults = ref([])

    const triggerFileInput = () => {
      fileInput.value?.click()
    }

    const handleDragOver = (e) => {
      e.preventDefault()
      isDragOver.value = true
    }

    const handleDragLeave = (e) => {
      e.preventDefault()
      isDragOver.value = false
    }

    const handleDrop = (e) => {
      e.preventDefault()
      isDragOver.value = false
      
      const files = Array.from(e.dataTransfer.files)
      handleFiles(files)
    }

    const handleFileSelect = (e) => {
      const files = Array.from(e.target.files)
      handleFiles(files)
    }

    const handleFiles = async (files) => {
      if (files.length === 0) return

      // Filter for image files and validate
      const imageFiles = files.filter(file => {
        const isValidImage = file.type.startsWith('image/')
        const isValidSize = file.size <= 50 * 1024 * 1024 // 50MB limit
        const hasValidName = file.name.length > 0
        
        if (!isValidImage) {
          console.warn(`File ${file.name} is not an image`)
        }
        if (!isValidSize) {
          console.warn(`File ${file.name} is too large (${(file.size / 1024 / 1024).toFixed(2)}MB)`)
        }
        if (!hasValidName) {
          console.warn(`File has invalid name`)
        }
        
        return isValidImage && isValidSize && hasValidName
      })
      
      if (imageFiles.length === 0) {
        uploadResults.value.push({
          type: 'error',
          message: '❌ No valid image files selected. Please select image files under 50MB.'
        })
        return
      }

      if (imageFiles.length === 1) {
        await uploadSingleFile(imageFiles[0])
      } else {
        await uploadMultipleFiles(imageFiles)
      }
    }

    const uploadSingleFile = async (file) => {
      uploading.value = true
      uploadProgress.value = 0
      uploadStatus.value = `Uploading ${file.name}...`
      uploadResults.value = []

      try {
        const formData = new FormData()
        formData.append('file', file)

        const response = await axios.post('http://localhost:8002/api/upload/single', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          },
          onUploadProgress: (progressEvent) => {
            uploadProgress.value = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          }
        })

        uploadResults.value.push({
          type: 'success',
          message: `✅ ${file.name} uploaded successfully`
        })

        emit('upload', { success: true, data: response.data })
      } catch (error) {
        console.error('Upload error:', error)
        uploadResults.value.push({
          type: 'error',
          message: `❌ Failed to upload ${file.name}: ${error.response?.data?.detail || error.message}`
        })
        emit('upload', { success: false, error: error.response?.data?.detail || error.message })
      } finally {
        uploading.value = false
        uploadProgress.value = 0
        uploadStatus.value = ''
      }
    }

    const uploadMultipleFiles = async (files) => {
      uploading.value = true
      uploadProgress.value = 0
      uploadStatus.value = `Uploading ${files.length} files...`
      uploadResults.value = []

      try {
        const formData = new FormData()
        files.forEach(file => {
          formData.append('files', file)
        })

        const response = await axios.post('http://localhost:8002/api/upload/multiple', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          },
          onUploadProgress: (progressEvent) => {
            uploadProgress.value = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          }
        })

        const results = response.data.results || []
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

        emit('batch-upload', results)
      } catch (error) {
        console.error('Batch upload error:', error)
        uploadResults.value.push({
          type: 'error',
          message: `❌ Batch upload failed: ${error.response?.data?.detail || error.message}`
        })
        emit('batch-upload', [])
      } finally {
        uploading.value = false
        uploadProgress.value = 0
        uploadStatus.value = ''
      }
    }

    return {
      fileInput,
      isDragOver,
      uploading,
      uploadProgress,
      uploadStatus,
      uploadResults,
      triggerFileInput,
      handleDragOver,
      handleDragLeave,
      handleDrop,
      handleFileSelect
    }
  }
}
</script>

<style scoped>
.upload-container {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 1.5rem;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.drag-drop-area {
  border: 2px dashed rgba(255, 255, 255, 0.3);
  border-radius: 12px;
  padding: 3rem 2rem;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  background: rgba(255, 255, 255, 0.05);
}

.drag-drop-area:hover {
  border-color: rgba(255, 255, 255, 0.6);
  background: rgba(255, 255, 255, 0.1);
  transform: translateY(-2px);
}

.drag-drop-area.drag-active {
  border-color: #667eea;
  background: rgba(102, 126, 234, 0.1);
  transform: scale(1.02);
}

.upload-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
  opacity: 0.8;
}

.upload-text {
  color: white;
}

.upload-text strong {
  display: block;
  font-size: 1.2rem;
  margin-bottom: 0.5rem;
}

.upload-text p {
  opacity: 0.8;
  font-size: 0.9rem;
  margin: 0;
}

.upload-progress {
  margin-top: 1rem;
  text-align: center;
}

.progress-bar {
  width: 100%;
  height: 8px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 0.5rem;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
  transition: width 0.3s ease;
}

.upload-progress p {
  color: white;
  font-size: 0.9rem;
  margin: 0;
}

.upload-results {
  margin-top: 1rem;
}

.upload-result {
  padding: 0.75rem;
  border-radius: 6px;
  margin-bottom: 0.5rem;
  font-size: 0.9rem;
  font-weight: 500;
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

/* Mobile responsiveness */
@media (max-width: 768px) {
  .upload-container {
    padding: 1rem;
  }
  
  .drag-drop-area {
    padding: 2rem 1rem;
  }
  
  .upload-icon {
    font-size: 2.5rem;
  }
  
  .upload-text strong {
    font-size: 1.1rem;
  }
  
  .upload-text p {
    font-size: 0.8rem;
  }
  
  .upload-progress p {
    font-size: 0.8rem;
  }
  
  .upload-result {
    padding: 0.75rem;
    font-size: 0.9rem;
  }
}

@media (max-width: 480px) {
  .upload-container {
    padding: 0.75rem;
  }
  
  .drag-drop-area {
    padding: 1.5rem 0.75rem;
  }
  
  .upload-icon {
    font-size: 2rem;
  }
  
  .upload-text strong {
    font-size: 1rem;
  }
  
  .upload-text p {
    font-size: 0.75rem;
  }
  
  .upload-progress p {
    font-size: 0.75rem;
  }
  
  .upload-result {
    padding: 0.6rem;
    font-size: 0.8rem;
  }
}

/* Tablet responsiveness */
@media (min-width: 769px) and (max-width: 1024px) {
  .drag-drop-area {
    padding: 2.5rem 1.5rem;
  }
  
  .upload-icon {
    font-size: 2.8rem;
  }
}

/* Large desktop */
@media (min-width: 1400px) {
  .drag-drop-area {
    padding: 3.5rem 2.5rem;
  }
  
  .upload-icon {
    font-size: 3.5rem;
  }
}
</style>
