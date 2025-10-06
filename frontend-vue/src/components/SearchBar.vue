<template>
  <div class="search-container">
    <div class="search-header">
      <h3>Search & Filter</h3>
      <button 
        class="filters-toggle-btn"
        @click="showFilters = !showFilters"
      >
        {{ showFilters ? 'Hide Filters' : 'Show Filters' }}
      </button>
    </div>

    <!-- Search Input -->
    <div class="search-input-container">
      <div class="search-input-wrapper">
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Search images by name, description, or tags..."
          class="search-input"
          @keypress.enter="handleSearch"
          @focus="searchFocused = true"
          @blur="searchFocused = false"
        />
        <button 
          v-if="searchQuery"
          class="clear-search-btn"
          @click="handleClearSearch"
          title="Clear search"
        >
          ×
        </button>
        <button 
          class="search-btn"
          @click="handleSearch"
          :disabled="loading"
        >
          {{ loading ? 'Searching...' : 'Search' }}
        </button>
      </div>
    </div>

    <!-- Advanced Filters -->
    <div v-if="showFilters" class="filters-section">
      <div class="filters-grid">
        <!-- Categories Filter -->
        <div class="filter-group">
          <label>Categories</label>
          <div class="dropdown-container">
            <div 
              class="dropdown-trigger"
              @click="handleCategoryDropdownToggle"
            >
              <span class="dropdown-text">{{ getCategoryDisplayText() }}</span>
              <span class="dropdown-arrow">▼</span>
            </div>
            <div v-if="categoryDropdownOpen" class="dropdown-menu">
              <div class="dropdown-search">
                <input
                  v-model="categorySearch"
                  type="text"
                  placeholder="Search categories..."
                  class="dropdown-search-input"
                />
              </div>
              <div class="dropdown-options">
                <div 
                  class="dropdown-option all-option"
                  @click="handleAllCategories"
                >
                  <div class="all-option-content">
                    <span class="all-icon">🏠</span>
                    <span class="option-text">All Categories</span>
                    <span class="option-count">({{ getTotalCategoryCount() }})</span>
                  </div>
                </div>
                <div 
                  v-for="category in filteredCategories" 
                  :key="category.id"
                  class="dropdown-option"
                  :class="{ 'selected': selectedCategories.includes(category.id) }"
                  @click="handleCategoryToggle(category.id)"
                >
                  <span class="option-text">{{ category.name }}</span>
                  <span class="option-count">({{ category.usage_count }})</span>
                  <span v-if="selectedCategories.includes(category.id)" class="selected-icon">✓</span>
                </div>
                <div v-if="filteredCategories.length === 0" class="dropdown-empty">
                  No categories found
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Tags Filter -->
        <div class="filter-group">
          <label>Tags</label>
          <div class="dropdown-container">
            <div 
              class="dropdown-trigger"
              @click="handleTagDropdownToggle"
            >
              <span class="dropdown-text">{{ getTagDisplayText() }}</span>
              <span class="dropdown-arrow">▼</span>
            </div>
            <div v-if="tagDropdownOpen" class="dropdown-menu">
              <div class="dropdown-search">
                <input
                  v-model="tagSearch"
                  type="text"
                  placeholder="Search tags..."
                  class="dropdown-search-input"
                />
              </div>
              <div class="dropdown-options">
                <div 
                  class="dropdown-option all-option"
                  @click="handleAllTags"
                >
                  <div class="all-option-content">
                    <span class="all-icon">🏷️</span>
                    <span class="option-text">All Tags</span>
                    <span class="option-count">({{ getTotalTagCount() }})</span>
                  </div>
                </div>
                <div 
                  v-for="tag in filteredTags" 
                  :key="tag.tag"
                  class="dropdown-option"
                  :class="{ 'selected': selectedTags.includes(tag.tag) }"
                  @click="handleTagToggle(tag.tag)"
                >
                  <span class="option-text">{{ tag.tag }}</span>
                  <span class="option-count">({{ tag.count }})</span>
                  <span v-if="selectedTags.includes(tag.tag)" class="selected-icon">✓</span>
                </div>
                <div v-if="filteredTags.length === 0" class="dropdown-empty">
                  No tags found
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Sort Options -->
        <div class="filter-group">
          <label>Sort By</label>
          <div class="dropdown-container">
            <div 
              class="dropdown-trigger"
              @click="handleSortByDropdownToggle"
            >
              <span>{{ getSortByLabel(sortBy) }}</span>
              <span class="dropdown-arrow">▼</span>
            </div>
            <div v-if="sortByDropdownOpen" class="dropdown-menu">
              <div 
                v-for="option in sortByOptions" 
                :key="option.value"
                class="dropdown-option"
                :class="{ active: sortBy === option.value }"
                @click="selectSortBy(option.value)"
              >
                {{ option.label }}
              </div>
            </div>
          </div>
        </div>

        <div class="filter-group">
          <label>Order</label>
          <div class="dropdown-container">
            <div 
              class="dropdown-trigger"
              @click="handleSortOrderDropdownToggle"
            >
              <span>{{ getSortOrderLabel(sortOrder) }}</span>
              <span class="dropdown-arrow">▼</span>
            </div>
            <div v-if="sortOrderDropdownOpen" class="dropdown-menu">
              <div 
                v-for="option in sortOrderOptions" 
                :key="option.value"
                class="dropdown-option"
                :class="{ active: sortOrder === option.value }"
                @click="selectSortOrder(option.value)"
              >
                {{ option.label }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import axios from 'axios'

export default {
  name: 'SearchBar',
  props: {
    initialQuery: {
      type: String,
      default: ''
    },
    initialFilters: {
      type: Object,
      default: () => ({})
    },
    categories: {
      type: Array,
      default: () => []
    }
  },
  emits: ['search', 'filter-change'],
  setup(props, { emit }) {
    const searchQuery = ref(props.initialQuery)
    const showFilters = ref(true) // Show filters by default
    const searchFocused = ref(false)
    const loading = ref(false)
    
    // Filter states
    const selectedCategories = ref([])
    const selectedTags = ref([])
    const sortBy = ref('created_at')
    const sortOrder = ref('desc')
    
    // Dropdown states
    const categoryDropdownOpen = ref(false)
    const tagDropdownOpen = ref(false)
    const sortByDropdownOpen = ref(false)
    const sortOrderDropdownOpen = ref(false)
    const categorySearch = ref('')
    const tagSearch = ref('')
    
    // Available tags
    const availableTags = ref([])

    // Sort options
    const sortByOptions = ref([
      { value: 'created_at', label: 'Upload Date' },
      { value: 'file_size', label: 'File Size' },
      { value: 'original_filename', label: 'Filename' },
      { value: 'user_name', label: 'Name' }
    ])

    const sortOrderOptions = ref([
      { value: 'desc', label: 'Newest First' },
      { value: 'asc', label: 'Oldest First' }
    ])

    // Computed properties
    const filteredCategories = computed(() => {
      let filtered = props.categories.filter(cat => cat.usage_count > 0)
      
      if (categorySearch.value) {
        filtered = filtered.filter(cat => 
          cat.name.toLowerCase().includes(categorySearch.value.toLowerCase())
        )
      }
      
      return filtered
    })

    const filteredTags = computed(() => {
      let filtered = availableTags.value.filter(tag => tag.count > 0)
      
      if (tagSearch.value) {
        filtered = filtered.filter(tag => 
          tag.tag.toLowerCase().includes(tagSearch.value.toLowerCase())
        )
      }
      
      return filtered
    })

    // Methods
    const loadTags = async () => {
      try {
        // Use the same endpoint as the legacy frontend
        const response = await axios.get('http://localhost:8002/api/search/stats')
        availableTags.value = response.data.top_tags || []
        console.log('Tags loaded from stats endpoint:', availableTags.value)
      } catch (error) {
        console.error('Error loading tags from stats endpoint:', error)
        availableTags.value = []
      }
    }

    const handleSearch = () => {
      const filters = {
        query: searchQuery.value,
        category_id: selectedCategories.value,
        tags: selectedTags.value,
        sort_by: sortBy.value,
        sort_order: sortOrder.value
      }
      
      console.log('SearchBar: Emitting search with filters:', filters)
      emit('search', filters)
    }

    const handleClearSearch = () => {
      searchQuery.value = ''
      selectedCategories.value = []
      selectedTags.value = []
      handleSearch()
    }

    const handleCategoryToggle = (categoryId) => {
      const index = selectedCategories.value.indexOf(categoryId)
      if (index > -1) {
        selectedCategories.value.splice(index, 1)
      } else {
        selectedCategories.value.push(categoryId)
      }
      // Don't close dropdown or search immediately - let user make multiple selections
    }

    const handleCategoryDropdownToggle = () => {
      // Close all other dropdowns first
      closeAllDropdowns()
      
      // Toggle current dropdown
      categoryDropdownOpen.value = !categoryDropdownOpen.value
      if (!categoryDropdownOpen.value) {
        categorySearch.value = ''
      }
    }

    const handleTagDropdownToggle = () => {
      // Close all other dropdowns first
      closeAllDropdowns()
      
      // Toggle current dropdown
      tagDropdownOpen.value = !tagDropdownOpen.value
      if (!tagDropdownOpen.value) {
        tagSearch.value = ''
      }
    }

    const handleTagToggle = (tag) => {
      const index = selectedTags.value.indexOf(tag)
      if (index > -1) {
        selectedTags.value.splice(index, 1)
      } else {
        selectedTags.value.push(tag)
      }
      // Don't close dropdown or search immediately - let user make multiple selections
    }

    const handleSortByDropdownToggle = () => {
      // Close all other dropdowns first
      closeAllDropdowns()
      
      // Toggle current dropdown
      sortByDropdownOpen.value = !sortByDropdownOpen.value
    }

    const handleSortOrderDropdownToggle = () => {
      // Close all other dropdowns first
      closeAllDropdowns()
      
      // Toggle current dropdown
      sortOrderDropdownOpen.value = !sortOrderDropdownOpen.value
    }

    const selectSortBy = (value) => {
      sortBy.value = value
      closeAllDropdowns()
      handleSearch()
    }

    const selectSortOrder = (value) => {
      sortOrder.value = value
      closeAllDropdowns()
      handleSearch()
    }

    const getSortByLabel = (value) => {
      const option = sortByOptions.value.find(opt => opt.value === value)
      return option ? option.label : 'Upload Date'
    }

    const getSortOrderLabel = (value) => {
      const option = sortOrderOptions.value.find(opt => opt.value === value)
      return option ? option.label : 'Newest First'
    }

    const handleAllCategories = () => {
      selectedCategories.value = []
      closeAllDropdowns()
      handleSearch()
    }

    const handleAllTags = () => {
      selectedTags.value = []
      closeAllDropdowns()
      handleSearch()
    }

    const getCategoryDisplayText = () => {
      if (selectedCategories.value.length === 0) {
        return 'All Categories'
      }
      if (selectedCategories.value.length === 1) {
        const category = props.categories.find(c => c.id === selectedCategories.value[0])
        return category ? category.name : 'All Categories'
      }
      return `${selectedCategories.value.length} Categories Selected`
    }

    const getTagDisplayText = () => {
      if (selectedTags.value.length === 0) {
        return 'All Tags'
      }
      if (selectedTags.value.length === 1) {
        return selectedTags.value[0]
      }
      return `${selectedTags.value.length} Tags Selected`
    }

    const getTotalCategoryCount = () => {
      return props.categories.reduce((sum, cat) => sum + cat.usage_count, 0)
    }

    const getTotalTagCount = () => {
      return availableTags.value.filter(tag => tag.count > 0).length
    }

    // Function to close all dropdowns
    const closeAllDropdowns = () => {
      categoryDropdownOpen.value = false
      tagDropdownOpen.value = false
      sortByDropdownOpen.value = false
      sortOrderDropdownOpen.value = false
      categorySearch.value = ''
      tagSearch.value = ''
    }

    // Click outside to close dropdowns
    const handleClickOutside = (event) => {
      // If clicking outside any dropdown container, close all dropdowns
      if (!event.target.closest('.dropdown-container')) {
        closeAllDropdowns()
      }
    }

    // Initialize from props
    const initializeFromProps = () => {
      if (props.initialFilters) {
        selectedCategories.value = props.initialFilters.category_id || []
        selectedTags.value = props.initialFilters.tag || []
        sortBy.value = props.initialFilters.sort_by || 'created_at'
        sortOrder.value = props.initialFilters.sort_order || 'desc'
      }
    }

    // Watch for changes
    watch([sortBy, sortOrder], () => {
      handleSearch()
    })

    // Lifecycle
    onMounted(() => {
      loadTags()
      initializeFromProps()
      document.addEventListener('click', handleClickOutside)
    })

    onUnmounted(() => {
      document.removeEventListener('click', handleClickOutside)
    })

    return {
      searchQuery,
      showFilters,
      searchFocused,
      loading,
      selectedCategories,
      selectedTags,
      sortBy,
      sortOrder,
      categoryDropdownOpen,
      tagDropdownOpen,
      sortByDropdownOpen,
      sortOrderDropdownOpen,
      categorySearch,
      tagSearch,
      availableTags,
      filteredCategories,
      filteredTags,
      sortByOptions,
      sortOrderOptions,
      handleSearch,
      handleClearSearch,
      handleCategoryToggle,
      handleTagToggle,
      handleSortByDropdownToggle,
      handleSortOrderDropdownToggle,
      selectSortBy,
      selectSortOrder,
      getSortByLabel,
      getSortOrderLabel,
      handleCategoryDropdownToggle,
      handleTagDropdownToggle,
      handleAllCategories,
      handleAllTags,
      closeAllDropdowns,
      getCategoryDisplayText,
      getTagDisplayText,
      getTotalCategoryCount,
      getTotalTagCount
    }
  }
}
</script>

<style scoped>
.search-container {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 1.5rem;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  position: relative;
  z-index: 10;
  margin-bottom: 2rem;
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
}

.search-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.search-header h3 {
  color: white;
  font-size: 1.2rem;
  margin: 0;
}

.filters-toggle-btn {
  background: rgba(255, 255, 255, 0.1);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.2);
  padding: 0.5rem 1rem;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.filters-toggle-btn:hover {
  background: rgba(255, 255, 255, 0.2);
}

.search-input-container {
  margin-bottom: 1rem;
}

.search-input-wrapper {
  position: relative;
  display: flex;
  gap: 0.5rem;
}

.search-input {
  flex: 1;
  padding: 0.75rem 1rem;
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.1);
  color: white;
  font-size: 1rem;
  transition: all 0.2s;
}

.search-input::placeholder {
  color: rgba(255, 255, 255, 0.6);
}

.search-input:focus {
  outline: none;
  border-color: #667eea;
  background: rgba(255, 255, 255, 0.15);
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.clear-search-btn {
  position: absolute;
  right: 4rem;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  color: rgba(255, 255, 255, 0.6);
  cursor: pointer;
  font-size: 1.2rem;
  padding: 0.25rem;
  border-radius: 50%;
  transition: all 0.2s;
}

.clear-search-btn:hover {
  color: white;
  background: rgba(255, 255, 255, 0.1);
}

.search-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.search-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.search-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.filters-section {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  animation: slideDown 0.3s ease-out;
}

.filters-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.filter-group label {
  color: white;
  font-weight: 500;
  font-size: 0.9rem;
}

.form-select {
  padding: 0.5rem;
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.1);
  color: white;
  font-size: 0.9rem;
  appearance: none;
  -webkit-appearance: none;
  -moz-appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 20 20' fill='white'%3E%3Cpath fill-rule='evenodd' d='M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z' clip-rule='evenodd'%3E%3C/path%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 0.5rem center;
  background-size: 1.2em;
  padding-right: 2rem;
  min-height: 40px;
  display: flex;
  align-items: center;
  cursor: pointer;
  transition: all 0.2s;
}

.form-select:hover {
  background: rgba(255, 255, 255, 0.15);
  border-color: rgba(255, 255, 255, 0.4);
}

.form-select option {
  background: #1f2937;
  color: white;
  padding: 0.5rem;
}

.form-select:focus {
  outline: none;
  border-color: #667eea;
  background: rgba(255, 255, 255, 0.15);
}

.dropdown-container {
  position: relative;
  z-index: 1000;
}

.dropdown-trigger {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem;
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.1);
  color: white;
  cursor: pointer;
  transition: all 0.2s;
  min-height: 40px;
}

.dropdown-trigger:hover {
  background: rgba(255, 255, 255, 0.15);
}

.dropdown-text {
  flex: 1;
  text-align: left;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.dropdown-arrow {
  font-size: 0.8rem;
  transition: transform 0.2s;
  margin-left: 0.5rem;
}

.dropdown-container:has(.dropdown-menu) .dropdown-arrow {
  transform: rotate(180deg);
}

.dropdown-menu {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 1000;
  max-height: 200px;
  overflow-y: auto;
  margin-top: 4px;
  display: block !important;
  visibility: visible !important;
  opacity: 1 !important;
}

.dropdown-search {
  padding: 0.5rem;
  border-bottom: 1px solid #e5e7eb;
}

.dropdown-search-input {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  font-size: 0.9rem;
  color: #374151;
  background: white;
}

.dropdown-options {
  max-height: 150px;
  overflow-y: auto;
}

.dropdown-option {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem;
  cursor: pointer;
  transition: background-color 0.2s;
  color: #374151;
}

.dropdown-option:hover {
  background: #f3f4f6;
}

.dropdown-option.selected {
  background-color: #dbeafe;
  color: #1e40af;
  font-weight: 500;
}

.dropdown-option.selected:hover {
  background-color: #bfdbfe;
}

.selected-icon {
  color: #059669;
  font-weight: bold;
  margin-left: 0.5rem;
}

.dropdown-option.all-option {
  border-bottom: 1px solid #e5e7eb;
  font-weight: 600;
}

.all-option-content {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  width: 100%;
}

.all-icon {
  font-size: 1rem;
}

.option-text {
  flex: 1;
  color: #374151;
}

.option-count {
  color: #6b7280;
  font-size: 0.8rem;
}

.dropdown-empty {
  padding: 1rem;
  text-align: center;
  color: #6b7280;
  font-style: italic;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Mobile responsiveness */
@media (max-width: 768px) {
  .search-container {
    padding: 1rem;
  }
  
  .search-header {
    flex-direction: column;
    align-items: stretch;
    gap: 0.75rem;
  }
  
  .search-header h3 {
    font-size: 1.1rem;
    text-align: center;
  }
  
  .filters-toggle-btn {
    width: 100%;
    padding: 0.6rem;
    font-size: 0.9rem;
  }
  
  .search-input-wrapper {
    flex-direction: column;
    gap: 0.5rem;
  }
  
  .search-input {
    font-size: 0.9rem;
    padding: 0.6rem 0.8rem;
  }
  
  .search-btn {
    width: 100%;
    padding: 0.6rem;
    font-size: 0.9rem;
  }
  
  .filters-grid {
    grid-template-columns: 1fr;
    gap: 0.75rem;
  }
  
  .filter-group label {
    font-size: 0.8rem;
  }
  
  .form-select {
    font-size: 0.8rem;
    padding: 0.4rem;
  }
  
  .dropdown-trigger {
    font-size: 0.8rem;
    padding: 0.4rem;
  }
  
  .dropdown-option {
    padding: 0.4rem;
    font-size: 0.8rem;
  }
  
  .option-text {
    font-size: 0.8rem;
  }
  
  .option-count {
    font-size: 0.7rem;
  }
}

@media (max-width: 480px) {
  .search-container {
    padding: 0.75rem;
  }
  
  .search-header {
    padding: 0.75rem;
  }
  
  .search-header h3 {
    font-size: 1rem;
  }
  
  .filters-toggle-btn {
    padding: 0.5rem;
    font-size: 0.8rem;
  }
  
  .search-input {
    font-size: 0.8rem;
    padding: 0.5rem 0.7rem;
  }
  
  .search-btn {
    padding: 0.5rem;
    font-size: 0.8rem;
  }
  
  .filters-grid {
    gap: 0.5rem;
  }
  
  .filter-group label {
    font-size: 0.75rem;
  }
  
  .form-select {
    font-size: 0.75rem;
    padding: 0.35rem;
  }
  
  .dropdown-trigger {
    font-size: 0.75rem;
    padding: 0.35rem;
  }
  
  .dropdown-option {
    padding: 0.35rem;
    font-size: 0.75rem;
  }
  
  .option-text {
    font-size: 0.75rem;
  }
  
  .option-count {
    font-size: 0.65rem;
  }
  
  .dropdown-menu {
    max-height: 150px;
  }
}

/* Tablet responsiveness */
@media (min-width: 769px) and (max-width: 1024px) {
  .filters-grid {
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  }
}

/* Large desktop */
@media (min-width: 1400px) {
  .filters-grid {
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  }
}
</style>
