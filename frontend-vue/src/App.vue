<template>
  <div class="app">
    <header class="app-header">
      <div class="header-content">
        <h1>📸 Photo Gallery - Vue.js</h1>
        <p>Upload, search, and manage your photos with AI-powered metadata</p>
      </div>
      <div class="api-status">
        <span :class="['status-indicator', apiStatus === 'connected' ? 'connected' : 'disconnected']">
          API: {{ apiStatus }}
        </span>
        <span v-if="apiError" class="error-message">({{ apiError }})</span>
      </div>
    </header>
    <main>
      <router-view />
    </main>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import axios from 'axios'

export default {
  name: 'App',
  setup() {
    const apiStatus = ref('checking...')
    const apiError = ref(null)

    const testConnection = async () => {
      try {
        const response = await axios.get('http://localhost:8002/health', {
          timeout: 5000 // 5 second timeout
        })
        apiStatus.value = 'connected'
        apiError.value = null
        console.log('Backend connection successful:', response.data)
      } catch (error) {
        apiStatus.value = 'disconnected'
        apiError.value = error.code === 'ECONNABORTED' ? 'Connection timeout' : error.message
        console.error('Backend connection failed:', error)
      }
    }

    onMounted(() => {
      testConnection()
      
      // Set up global axios error handler
      axios.interceptors.response.use(
        response => response,
        error => {
          console.error('Axios error:', error)
          return Promise.reject(error)
        }
      )
    })

    return {
      apiStatus,
      apiError
    }
  }
}
</script>

<style scoped>
.app {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  flex-direction: column;
}

.app-header {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  padding: 1.5rem 2rem;
  text-align: center;
  color: white;
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  flex-shrink: 0;
}

.header-content {
  margin-bottom: 1rem;
}

.header-content h1 {
  font-size: clamp(1.8rem, 4vw, 2.5rem);
  margin-bottom: 0.5rem;
  font-weight: 700;
  line-height: 1.2;
}

.header-content p {
  font-size: clamp(0.9rem, 2vw, 1.1rem);
  opacity: 0.9;
  margin: 0;
  line-height: 1.4;
}

.api-status {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.status-indicator {
  padding: 0.5rem 1rem;
  border-radius: 20px;
  font-weight: 600;
  font-size: 0.9rem;
  white-space: nowrap;
}

.status-indicator.connected {
  background: rgba(34, 197, 94, 0.2);
  color: #22c55e;
  border: 1px solid rgba(34, 197, 94, 0.3);
}

.status-indicator.disconnected {
  background: rgba(239, 68, 68, 0.2);
  color: #ef4444;
  border: 1px solid rgba(239, 68, 68, 0.3);
}

.error-message {
  color: #fca5a5;
  font-size: 0.9rem;
  word-break: break-word;
}

main {
  padding: 1rem;
  flex: 1;
  display: flex;
  flex-direction: column;
}

/* Mobile responsiveness */
@media (max-width: 768px) {
  .app-header {
    padding: 1rem;
  }
  
  .header-content h1 {
    font-size: 1.8rem;
  }
  
  .header-content p {
    font-size: 0.9rem;
  }
  
  .api-status {
    flex-direction: column;
    gap: 0.25rem;
  }
  
  main {
    padding: 0.5rem;
  }
}

@media (max-width: 480px) {
  .app-header {
    padding: 0.75rem;
  }
  
  .header-content h1 {
    font-size: 1.5rem;
  }
  
  .header-content p {
    font-size: 0.8rem;
  }
  
  .status-indicator {
    padding: 0.4rem 0.8rem;
    font-size: 0.8rem;
  }
  
  main {
    padding: 0.25rem;
  }
}
</style>
