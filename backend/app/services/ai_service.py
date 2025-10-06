"""
AI service for image analysis using OpenRouter API with Claude 3.5 Sonnet Vision.
"""

import base64
import json
import asyncio
from typing import Dict, List, Optional, Any, Tuple
import httpx
from ..config import settings
import logging

logger = logging.getLogger(__name__)

class AIService:
    """
    Service for AI-powered image analysis using OpenRouter API.
    """
    
    def __init__(self):
        self.api_key = settings.OPENROUTER_API_KEY
        self.base_url = "https://openrouter.ai/api/v1"
        self.model = "anthropic/claude-3.5-sonnet"
        self.max_retries = 3
        self.retry_delay = 1.0
        
        if not self.api_key:
            logger.warning("OpenRouter API key not found. AI analysis will be disabled.")
    
    def encode_image_to_base64(self, image_path: str) -> str:
        """
        Encode image file to base64 string for API transmission.
        Convert to JPEG if needed for AI API compatibility.
        Compress image to stay under 5MB limit.
        """
        try:
            from PIL import Image
            import io
            
            # Open image and convert to RGB if needed
            with Image.open(image_path) as img:
                # Convert to RGB if the image has transparency or is in a format not supported by AI APIs
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Start with reasonable size and quality
                max_size = 1024  # Start smaller
                quality = 80  # Start with good quality
                
                # Iteratively reduce size/quality until under 5MB limit
                for attempt in range(5):  # Max 5 attempts
                    # Resize if image is too large
                    if max(img.size) > max_size:
                        img_copy = img.copy()
                        img_copy.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                    else:
                        img_copy = img.copy()
                    
                    # Save as JPEG in memory with current quality
                    img_buffer = io.BytesIO()
                    img_copy.save(img_buffer, format='JPEG', quality=quality, optimize=True)
                    img_buffer.seek(0)
                    image_bytes = img_buffer.getvalue()
                    
                    # Check if under 5MB limit (5,242,880 bytes)
                    if len(image_bytes) <= 5242880:
                        logger.info(f"Image compressed successfully: {len(image_bytes)} bytes (attempt {attempt + 1})")
                        return base64.b64encode(image_bytes).decode('utf-8')
                    
                    # Reduce size and quality for next attempt
                    max_size = int(max_size * 0.8)  # Reduce size by 20%
                    quality = max(quality - 10, 30)  # Reduce quality by 10, minimum 30
                    logger.warning(f"Image too large ({len(image_bytes)} bytes), retrying with size {max_size}px, quality {quality}%")
                
                # If still too large after all attempts, use minimum settings
                logger.warning("Image still too large after compression attempts, using minimum settings")
                img.thumbnail((512, 512), Image.Resampling.LANCZOS)
                img_buffer = io.BytesIO()
                img.save(img_buffer, format='JPEG', quality=30, optimize=True)
                img_buffer.seek(0)
                image_bytes = img_buffer.getvalue()
                
                return base64.b64encode(image_bytes).decode('utf-8')
                
        except Exception as e:
            logger.error(f"Error encoding image {image_path}: {e}")
            # Fallback to original method
            try:
                with open(image_path, "rb") as image_file:
                    encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                    return encoded_string
            except Exception as e2:
                logger.error(f"Fallback encoding also failed for {image_path}: {e2}")
                raise
    
    def get_image_mime_type(self, image_path: str) -> str:
        """
        Get MIME type for the image file.
        Since we convert all images to JPEG for AI API compatibility, always return image/jpeg.
        """
        return 'image/jpeg'
    
    def create_analysis_prompt(self, existing_categories: List[Dict]) -> str:
        """
        Create the comprehensive prompt for AI image analysis.
        """
        categories_list = [cat['name'] for cat in existing_categories]
        categories_text = ", ".join(categories_list) if categories_list else "None"
        
        prompt = f"""
You are an expert image analyst. Analyze the provided image and return a comprehensive JSON response with the following structure:

{{
  "ai_name": "Descriptive name for the image",
  "ai_description": "Detailed description of what you see in the image",
  "ai_tags": ["tag1", "tag2", "tag3", "tag4", "tag5"],
  "ai_objects": ["object1", "object2", "object3"],
  "ai_scene_description": "Description of the overall scene and setting",
  "ai_color_palette": ["#color1", "#color2", "#color3", "#color4", "#color5"],
  "ai_emotions": ["emotion1", "emotion2", "emotion3"],
  "ai_confidence_score": 0.95,
  "ai_user_suggested_name": "User-friendly suggested name",
  "ai_user_suggested_description": "User-friendly description",
  "ai_user_suggested_tags": ["user_tag1", "user_tag2", "user_tag3"],
  "category_selection": {{
    "selected_category": "Category name from existing list or 'new'",
    "new_category_name": "Name if creating new category (only if selected_category is 'new')",
    "new_category_description": "Description if creating new category (only if selected_category is 'new')"
  }}
}}

EXISTING CATEGORIES: {categories_text}

INSTRUCTIONS:
1. Provide a detailed analysis of the image content
2. Extract 5-10 relevant tags that describe the image
3. Identify 3-5 main objects in the image
4. Describe the overall scene and setting
5. Extract 5 dominant colors in hex format
6. Identify 2-3 emotions or moods conveyed by the image
7. Provide a confidence score (0.0 to 1.0) for your analysis
8. Suggest user-friendly names, descriptions, and tags
9. Choose the most appropriate category from the existing list, or suggest a new one
10. If suggesting a new category, provide a name and description

IMPORTANT: Return ONLY valid JSON. No additional text or formatting.
"""
        return prompt
    
    async def analyze_image(self, image_path: str, existing_categories: List[Dict]) -> Dict[str, Any]:
        """
        Analyze a single image using Claude 3.5 Sonnet Vision.
        """
        if not self.api_key:
            return self._create_fallback_response("AI analysis disabled - no API key")
        
        try:
            # Encode image
            image_base64 = self.encode_image_to_base64(image_path)
            mime_type = self.get_image_mime_type(image_path)
            
            # Create prompt
            prompt = self.create_analysis_prompt(existing_categories)
            
            # Prepare request
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:3000",
                "X-Title": "Simple Cloud Photo Gallery"
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 2000,
                "temperature": 0.1
            }
            
            # Make API request with retries
            async with httpx.AsyncClient(timeout=60.0) as client:
                for attempt in range(self.max_retries):
                    try:
                        response = await client.post(
                            f"{self.base_url}/chat/completions",
                            headers=headers,
                            json=payload
                        )
                        
                        if response.status_code == 200:
                            result = response.json()
                            logger.info(f"OpenRouter API response: {result}")
                            
                            # Check if response has expected structure
                            if 'choices' not in result:
                                error_msg = f"Unexpected API response format: missing 'choices' key. Response: {result}"
                                logger.error(error_msg)
                                return self._create_fallback_response(error_msg)
                            
                            if not result['choices'] or len(result['choices']) == 0:
                                error_msg = f"Empty choices array in API response: {result}"
                                logger.error(error_msg)
                                return self._create_fallback_response(error_msg)
                            
                            if 'message' not in result['choices'][0] or 'content' not in result['choices'][0]['message']:
                                error_msg = f"Invalid message structure in API response: {result}"
                                logger.error(error_msg)
                                return self._create_fallback_response(error_msg)
                            
                            content = result['choices'][0]['message']['content']
                            
                            # Parse JSON response
                            try:
                                ai_data = json.loads(content)
                            except json.JSONDecodeError as e:
                                error_msg = f"Failed to parse JSON from AI response: {content}. Error: {e}"
                                logger.error(error_msg)
                                return self._create_fallback_response(error_msg)
                            
                            # Validate and clean the response
                            return self._validate_and_clean_response(ai_data)
                        
                        elif response.status_code == 429:
                            # Rate limited, wait and retry
                            wait_time = self.retry_delay * (2 ** attempt)
                            logger.warning(f"Rate limited, waiting {wait_time}s before retry {attempt + 1}")
                            await asyncio.sleep(wait_time)
                            continue
                        
                        else:
                            error_msg = f"API error {response.status_code}: {response.text}"
                            logger.error(error_msg)
                            if attempt == self.max_retries - 1:
                                return self._create_fallback_response(error_msg)
                            continue
                    
                    except httpx.TimeoutException:
                        logger.warning(f"Request timeout on attempt {attempt + 1}")
                        if attempt == self.max_retries - 1:
                            return self._create_fallback_response("Request timeout")
                        await asyncio.sleep(self.retry_delay * (2 ** attempt))
                        continue
                    
                    except KeyError as e:
                        error_msg = f"Missing key in API response: {e}. Response structure may have changed."
                        logger.error(error_msg)
                        if attempt == self.max_retries - 1:
                            return self._create_fallback_response(error_msg)
                        await asyncio.sleep(self.retry_delay * (2 ** attempt))
                        continue
                    
                    except Exception as e:
                        logger.error(f"Request error on attempt {attempt + 1}: {e}")
                        if attempt == self.max_retries - 1:
                            return self._create_fallback_response(f"Request error: {str(e)}")
                        await asyncio.sleep(self.retry_delay * (2 ** attempt))
                        continue
            
            return self._create_fallback_response("Max retries exceeded")
            
        except Exception as e:
            logger.error(f"Error analyzing image {image_path}: {e}")
            return self._create_fallback_response(f"Analysis error: {str(e)}")
    
    def _validate_and_clean_response(self, ai_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and clean the AI response data.
        """
        # Ensure all required fields exist
        cleaned_data = {
            "ai_name": ai_data.get("ai_name", ""),
            "ai_description": ai_data.get("ai_description", ""),
            "ai_tags": ai_data.get("ai_tags", []),
            "ai_objects": ai_data.get("ai_objects", []),
            "ai_scene_description": ai_data.get("ai_scene_description", ""),
            "ai_color_palette": ai_data.get("ai_color_palette", []),
            "ai_emotions": ai_data.get("ai_emotions", []),
            "ai_confidence_score": min(max(ai_data.get("ai_confidence_score", 0.5), 0.0), 1.0),
            "ai_user_suggested_name": ai_data.get("ai_user_suggested_name", ""),
            "ai_user_suggested_description": ai_data.get("ai_user_suggested_description", ""),
            "ai_user_suggested_tags": ai_data.get("ai_user_suggested_tags", []),
            "category_selection": ai_data.get("category_selection", {
                "selected_category": "Other",
                "new_category_name": "",
                "new_category_description": ""
            }),
            "analysis_success": True,
            "error_message": None
        }
        
        # Ensure lists are actually lists
        for field in ["ai_tags", "ai_objects", "ai_color_palette", "ai_emotions", "ai_user_suggested_tags"]:
            if not isinstance(cleaned_data[field], list):
                cleaned_data[field] = []
        
        return cleaned_data
    
    def _create_fallback_response(self, error_message: str) -> Dict[str, Any]:
        """
        Create a fallback response when AI analysis fails.
        """
        return {
            "ai_name": "",
            "ai_description": "",
            "ai_tags": [],
            "ai_objects": [],
            "ai_scene_description": "",
            "ai_color_palette": [],
            "ai_emotions": [],
            "ai_confidence_score": 0.0,
            "ai_user_suggested_name": "",
            "ai_user_suggested_description": "",
            "ai_user_suggested_tags": [],
            "category_selection": {
                "selected_category": "Other",
                "new_category_name": "",
                "new_category_description": ""
            },
            "analysis_success": False,
            "error_message": error_message
        }
    
    async def analyze_multiple_images(self, image_paths: List[str], existing_categories: List[Dict]) -> List[Dict[str, Any]]:
        """
        Analyze multiple images concurrently.
        """
        tasks = [
            self.analyze_image(image_path, existing_categories)
            for image_path in image_paths
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to error responses
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error analyzing image {image_paths[i]}: {result}")
                processed_results.append(self._create_fallback_response(f"Exception: {str(result)}"))
            else:
                processed_results.append(result)
        
        return processed_results
    
    def _format_tags_for_storage(self, tags: List[str]) -> str:
        """
        Format tags list for database storage as JSON string.
        """
        if not tags:
            return None
        return json.dumps(tags)
    
    def get_analysis_cost_estimate(self, num_images: int) -> Dict[str, Any]:
        """
        Get cost estimate for analyzing images.
        Based on OpenRouter pricing for Claude 3.5 Sonnet Vision.
        """
        # Approximate costs (as of 2024)
        cost_per_image = 0.01  # $0.01 per image (approximate)
        total_cost = num_images * cost_per_image
        
        return {
            "cost_per_image": cost_per_image,
            "total_cost": total_cost,
            "currency": "USD",
            "note": "Costs are approximate and may vary based on image complexity and API pricing changes"
        }
