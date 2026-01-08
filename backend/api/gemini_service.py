import google.generativeai as genai
from decouple import config
import json
import logging

logger = logging.getLogger(__name__)


class GeminiService:
    """
    Service to interact with Google's Gemini API for dream interpretation.

    Uses two separate model instances:
    1. Keyword Extractor: Extracts dream symbols from text (returns JSON)
    2. Dream Interpreter: Generates dream interpretations (has specialized system prompt)
    """

    MODEL_NAME = 'gemini-2.5-flash'
    DREAM_INTERPRETER_PROMPT = "You are a master dream interpreter. Interpret the user's dreams and answer any followup questions in a direct and professional way. If an exact match for relevant keywords are not found, fall back on your general knowledge for interpretation. Prioritize the keyword symbols if provided."

    def __init__(self):
        """Initialize Gemini API and create model instances"""
        api_key = config('GEMINI_API_KEY', default='')
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY not found in environment variables. "
                "Please add it to your .env file or set it as an environment variable."
            )
        genai.configure(api_key=api_key)

        logger.info("=== GeminiService initialized ===")

        # Initialize both models
        self._keyword_extractor = self._create_keyword_extractor()
        self._dream_interpreter = self._create_dream_interpreter()

    def _create_keyword_extractor(self):
        """Create model for extracting keywords (no system instruction needed)"""
        model = genai.GenerativeModel(self.MODEL_NAME)
        logger.info("Keyword extractor model created")
        return model

    def _create_dream_interpreter(self):
        """Create model for dream interpretation with specialized system prompt"""
        model = genai.GenerativeModel(
            self.MODEL_NAME,
            system_instruction=self.DREAM_INTERPRETER_PROMPT
        )
        logger.info("Dream interpreter model created with system instruction")
        return model

    def extract_dream_keywords(self, message):
        """
        Use LLM to extract dream-related keywords from user message

        Args:
            message: The user's message

        Returns:
            list: List of extracted keywords
        """
        try:
            prompt = f"""Extract dream symbol keywords from the following message.
Return ONLY a JSON array of keywords (nouns/objects/concepts that appear in the dream).
Do not include common words like 'dream', 'I', 'saw', etc.
Focus on concrete objects, people, animals, places, colors, emotions, and actions.

IMPORTANT: For compound words, include BOTH variations:
- Separated with spaces: "water skiing"
- Combined as one word: "waterskiing"

Message: {message}

Return format: ["keyword1", "keyword2", "keyword3"]
"""
            logger.info(f"[KEYWORD EXTRACTION] Starting for message: {message[:100]}...")
            logger.debug(f"[KEYWORD EXTRACTION] Full prompt: {prompt}")

            response = self._keyword_extractor.generate_content(prompt)

            logger.info(f"[KEYWORD EXTRACTION] Raw response: {response.text}")

            # Parse the JSON response
            keywords_text = response.text.strip()
            # Remove markdown code blocks if present
            if keywords_text.startswith('```'):
                keywords_text = keywords_text.split('\n', 1)[1]
                keywords_text = keywords_text.rsplit('```', 1)[0]

            keywords = json.loads(keywords_text)
            logger.info(f"[KEYWORD EXTRACTION] Extracted keywords: {keywords}")
            return keywords if isinstance(keywords, list) else []
        except Exception as e:
            logger.error(f"[KEYWORD EXTRACTION] Error extracting keywords: {str(e)}", exc_info=True)
            return []

    def generate_response(self, messages, dream_symbols=None):
        """
        Generate a response from Gemini based on conversation history

        Args:
            messages: List of dicts with 'role' and 'content' keys
            dream_symbols: Optional dict of dream symbols and interpretations

        Returns:
            str: The generated response text
        """
        try:
            logger.info(f"[DREAM INTERPRETATION] Starting response generation")
            logger.debug(f"[DREAM INTERPRETATION] Message count: {len(messages)}")
            logger.debug(f"[DREAM INTERPRETATION] Dream symbols provided: {bool(dream_symbols)}")

            # Convert messages to Gemini format
            chat_history = []

            for msg in messages[:-1]:  # All except the last message
                role = 'user' if msg['role'] == 'user' else 'model'
                chat_history.append({
                    'role': role,
                    'parts': [msg['content']]
                })

            logger.debug(f"[DREAM INTERPRETATION] Chat history length: {len(chat_history)}")

            # Start a chat session with history using the dream interpreter model
            chat = self._dream_interpreter.start_chat(history=chat_history)

            # Prepare the latest message
            latest_message = messages[-1]['content']
            logger.info(f"[DREAM INTERPRETATION] User message: {latest_message[:200]}...")

            # Add dream symbols context if provided
            if dream_symbols:
                context = "\n\n--- DATABASE DREAM SYMBOL INTERPRETATIONS ---\n"
                context += "Use the following dream symbol interpretations to help interpret the user's dream:\n\n"

                for keyword, interpretations in dream_symbols.items():
                    context += f"**{keyword}**:\n"
                    for interp in interpretations:
                        context += f"  • {interp['interpretation']}\n"
                    context += "\n"

                context += "--- END DATABASE DREAM SYMBOL INTERPRETATIONS ---\n\n"
                context += "Based on these interpretations and the user's dream description, provide a thoughtful and personalized dream interpretation. Only reference above dream symbols if applicable. If not, fall back on your general knowledge. Do not mention 'provided symbols' be seamless in your response.\n\n"

                logger.info(f"[DREAM INTERPRETATION] Added symbol context for keywords: {list(dream_symbols.keys())}")
                latest_message = latest_message + context


            logger.debug(f"[DREAM INTERPRETATION] Final message length: {len(latest_message)} chars")
            logger.info(f"[DREAM INTERPRETATION] FULL PROMPT BEING SENT:\n{'-'*80}\n{latest_message}\n{'-'*80}")

            response = chat.send_message(latest_message)

            logger.info(f"[DREAM INTERPRETATION] Response generated successfully")
            logger.debug(f"[DREAM INTERPRETATION] Response preview: {response.text[:200]}...")

            return response.text

        except Exception as e:
            logger.error(f"[DREAM INTERPRETATION] Error generating response: {str(e)}", exc_info=True)
            raise Exception(f"Error generating response from Gemini: {str(e)}")

    def generate_simple_response(self, prompt):
        """
        Generate a simple response without conversation history

        Args:
            prompt: The user's message

        Returns:
            str: The generated response text
        """
        try:
            logger.info(f"[SIMPLE RESPONSE] Generating response for prompt: {prompt[:100]}...")
            response = self._keyword_extractor.generate_content(prompt)
            logger.info(f"[SIMPLE RESPONSE] Response generated: {response.text[:200]}...")
            return response.text
        except Exception as e:
            logger.error(f"[SIMPLE RESPONSE] Error: {str(e)}", exc_info=True)
            raise Exception(f"Error generating response from Gemini: {str(e)}")

    def _parse_json_response(self, response_text):
        cleaned = response_text.strip()
        if cleaned.startswith('```'):
            cleaned = cleaned.split('\n', 1)[1]
            cleaned = cleaned.rsplit('```', 1)[0]
        start = cleaned.find('{')
        end = cleaned.rfind('}')
        if start != -1 and end != -1:
            cleaned = cleaned[start:end + 1]
        return json.loads(cleaned)

    def generate_ad_copy(self, brief):
        """
        Generate ad copy and overlay text for a square Facebook post.

        Args:
            brief: dict with product, audience, offer, proof, tone, cta

        Returns:
            dict: {primary_text, headline, cta, image_text}
        """
        prompt = f"""You are a senior performance marketer.
Generate concise Facebook ad copy for a single square image post with black background and white text.

Brand/product: {brief.get('product')}
Audience: {brief.get('audience')}
Offer/outcome: {brief.get('offer')}
Proof/credibility: {brief.get('proof')}
Tone: {brief.get('tone')}
CTA preference: {brief.get('cta')}

Return ONLY JSON with:
- "primary_text": 1-2 sentences, <= 280 chars
- "headline": 3-7 words
- "cta": one of ["Learn More","Get Demo","Start Free","Sign Up","Book Call","Download"]
- "image_text": 3-7 words, punchy, title case
Avoid emojis and hashtags.
"""
        try:
            response = self._keyword_extractor.generate_content(prompt)
            payload = self._parse_json_response(response.text)
            return {
                "primary_text": str(payload.get("primary_text", "")).strip(),
                "headline": str(payload.get("headline", "")).strip(),
                "cta": str(payload.get("cta", "")).strip(),
                "image_text": str(payload.get("image_text", "")).strip(),
            }
        except Exception as e:
            logger.error(f"[AD COPY] Error: {str(e)}", exc_info=True)
            raise Exception(f"Error generating ad copy from Gemini: {str(e)}")
