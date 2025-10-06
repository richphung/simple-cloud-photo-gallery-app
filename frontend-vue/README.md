# Photo Gallery - Vue.js Frontend

A modern, responsive photo gallery application built with Vue.js 3 and Vite.

## Features

- **Reliable Event System**: Built with Vue.js for stable event handling
- **Modern UI**: Beautiful, responsive design with glassmorphism effects
- **Image Upload**: Drag & drop or click to upload multiple images
- **AI-Powered Search**: Search by name, description, tags, or categories
- **Advanced Filtering**: Filter by categories, tags, date ranges
- **Image Management**: Edit metadata, delete images, AI re-analysis
- **Real-time Updates**: Live status updates for AI processing

## Quick Start

1. **Install Dependencies**
   ```bash
   cd frontend-vue
   npm install
   ```

2. **Start Development Server**
   ```bash
   npm run dev
   ```

3. **Open in Browser**
   - Navigate to `http://localhost:3001`
   - Make sure the backend is running on `http://localhost:8002`

## Project Structure

```
frontend-vue/
├── src/
│   ├── components/
│   │   ├── Gallery.vue          # Image gallery display
│   │   ├── ImageModal.vue       # Image editing modal
│   │   ├── FileUpload.vue      # File upload component
│   │   └── SearchBar.vue        # Search and filter component
│   ├── views/
│   │   └── MainPage.vue         # Main application page
│   ├── router/
│   │   └── index.js             # Vue Router configuration
│   ├── App.vue                  # Root component
│   └── main.js                  # Application entry point
├── index.html                   # HTML template
├── package.json                 # Dependencies
├── vite.config.js              # Vite configuration
└── README.md                   # This file
```

## Key Features

### ✅ **Reliable Event System**
- Vue's event system provides stable event handling
- No double-click or modal flickering problems
- Clean, predictable event handling

### ✅ **Intuitive State Management**
- Vue's reactive system is easy to understand
- No complex dependency management
- Automatic reactivity without manual tracking

### ✅ **Optimized Performance**
- Vue's reactivity system is highly efficient
- No unnecessary re-renders
- Optimized component updates

### ✅ **Clean Code Structure**
- Minimal boilerplate code
- Readable component structure
- Clear separation of concerns

## API Integration

The Vue frontend connects to the FastAPI backend:

- **Backend URL**: `http://localhost:8002`
- **API Endpoints**: Full REST API integration
- **Authentication**: None required for local development
- **CORS**: Configured for local development

## Development

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build

### Key Features

1. **Single Page Application**
   - All functionality in one page
   - No complex routing
   - Simple navigation

2. **Responsive Design**
   - Works on desktop and mobile
   - Adaptive layouts
   - Touch-friendly interface

3. **Modern UI Components**
   - Glassmorphism effects
   - Smooth animations
   - Intuitive interactions

4. **Real-time Updates**
   - Live AI processing status
   - Automatic gallery refresh
   - Progress indicators

## Troubleshooting

### Common Issues

1. **Backend Connection**
   - Ensure backend is running on port 8002
   - Check API health endpoint
   - Verify CORS configuration

2. **Image Upload**
   - Check file size limits
   - Verify supported formats
   - Monitor upload progress

3. **Search Issues**
   - Clear search filters
   - Check API response
   - Verify category/tag data

### Debug Mode

Enable debug logging by opening browser console and looking for:
- `🎯 VUE IMAGE CLICK:` - Image click events
- `🔒 VUE MODAL CLOSE` - Modal close events
- API request/response logs

## Production Deployment

1. **Build the Application**
   ```bash
   npm run build
   ```

2. **Deploy to Server**
   - Copy `dist/` folder to web server
   - Configure reverse proxy for API
   - Set up HTTPS for production

3. **Environment Variables**
   - Update API base URL
   - Configure production backend
   - Set up monitoring

## Support

This Vue.js frontend provides a modern, efficient interface for the photo gallery application with reliable event handling and intuitive state management.

For backend setup and API documentation, refer to the main project README.
