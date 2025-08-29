"""
Question Generation Prompts

Type-to-prompt mapping system for generating different types of trivia questions
based on document content and structure.
"""

from typing import List


class SmitePrompts:
    """
    Prompt templates for Smite game data question generation.
    Maps document types to specialized prompts for creating engaging trivia questions.
    """
    
    # Core prompts for each document type
    BASE_PROMPTS = {
        "god": """
        Create trivia questions about this Smite god based on the following information:
        {content}
        
        Focus on:
        - God stats (health, mana, protections, attack speed)
        - Pantheon and lore (Greek, Egyptian, etc.)
        - Role and gameplay (Solo, Support, etc.)
        - Abilities mentioned
        - Title and characteristics
        
        Generate {question_count} {question_type} questions.
        Make questions challenging but fair for Smite players.
        """,
        
        "ability": """
        Create trivia questions about this Smite ability:
        {content}
        
        Focus on:
        - Ability mechanics and effects
        - Damage values and scaling
        - Cooldowns and mana costs
        - Range and area of effect
        - Special interactions or notes
        - Which god owns this ability
        
        Generate {question_count} {question_type} questions.
        Include specific numerical values when available.
        """,
        
        "patch": """
        Create trivia questions about this Smite patch:
        {content}
        
        Focus on:
        - Which gods were changed in this patch
        - Major features or updates introduced
        - Patch number and naming
        - Timeline and release information
        
        Generate {question_count} {question_type} questions.
        Test knowledge of patch history and changes.
        """,
        
        "god_change": """
        Create trivia questions about this specific god balance change:
        {content}
        
        Focus on:
        - What specific changes were made (buffs/nerfs)
        - Exact numerical changes (before vs after values)
        - Which patch the change occurred in
        - Impact on gameplay
        - Ability or stat affected
        
        Generate {question_count} {question_type} questions.
        Include precise details about the changes.
        """,
        
        "item": """
        Create trivia questions about this Smite item:
        {content}
        
        Focus on:
        - Item effects and passive abilities
        - Active abilities and cooldowns
        - Item cost and type (Relic, etc.)
        - Usage scenarios and strategies
        - Item statistics and bonuses
        
        Generate {question_count} {question_type} questions.
        Test knowledge of item mechanics and usage.
        """
    }
    
    # Question type specific instructions
    QUESTION_TYPE_INSTRUCTIONS = {
        "multiple_choice": """
        Format: Multiple choice with 4 options (A, B, C, D).
        - One correct answer, three plausible incorrect answers
        - Make incorrect options challenging but clearly wrong to experts
        - Include numerical distractors that are close but not exact
        - Format as JSON: {"question": "...", "options": ["A", "B", "C", "D"], "correct_answer": "B", "type": "multiple_choice"}
        """,
        
        "true_false": """
        Format: True/False questions.
        - Create statements that can be definitively true or false
        - Avoid ambiguous wording
        - Test specific facts and details
        - Format as JSON: {"question": "...", "correct_answer": "true", "type": "true_false"}
        """,
        
        "open_ended": """
        Format: Open-ended questions requiring specific answers.
        - Questions should have clear, unambiguous correct answers
        - Ideal for names, numbers, or short phrases
        - Consider common alternative spellings/formats
        - Format as JSON: {"question": "...", "correct_answer": "exact answer", "type": "open_ended"}
        """
    }
    
    # Additional context for better questions
    CONTEXT_PROMPTS = {
        "difficulty_easy": "Make questions accessible to casual Smite players.",
        "difficulty_medium": "Target questions at regular Smite players with moderate game knowledge.",
        "difficulty_hard": "Create challenging questions for dedicated Smite enthusiasts and competitive players.",
        
        "focus_numbers": "Emphasize specific numerical values, statistics, and precise measurements.",
        "focus_lore": "Focus on mythology, backstory, and thematic elements.",
        "focus_mechanics": "Concentrate on gameplay mechanics, interactions, and strategic elements.",
        "focus_history": "Emphasize game development history, patches, and changes over time."
    }
    
    @classmethod
    def get_prompt(
        cls, 
        document_type: str, 
        question_type: str = "multiple_choice",
        question_count: int = 5,
        difficulty: str = "medium",
        focus: str = None
    ) -> str:
        """
        Generate a complete prompt for question generation.
        
        Args:
            document_type: Type of document ('god', 'ability', etc.)
            question_type: Type of questions to generate
            question_count: Number of questions to generate
            difficulty: Difficulty level (easy/medium/hard)
            focus: Optional focus area (numbers/lore/mechanics/history)
            
        Returns:
            Complete prompt string ready for LLM
        """
        if document_type not in cls.BASE_PROMPTS:
            raise ValueError(f"Unsupported document type: {document_type}")
        if question_type not in cls.QUESTION_TYPE_INSTRUCTIONS:
            raise ValueError(f"Unsupported question type: {question_type}")
            
        # Build the complete prompt
        base_prompt = cls.BASE_PROMPTS[document_type]
        type_instructions = cls.QUESTION_TYPE_INSTRUCTIONS[question_type]
        
        prompt_parts = [base_prompt]
        
        # Add difficulty context
        if difficulty in cls.CONTEXT_PROMPTS:
            prompt_parts.append(cls.CONTEXT_PROMPTS[f"difficulty_{difficulty}"])
            
        # Add focus context
        if focus and f"focus_{focus}" in cls.CONTEXT_PROMPTS:
            prompt_parts.append(cls.CONTEXT_PROMPTS[f"focus_{focus}"])
            
        # Add question type instructions
        prompt_parts.append(type_instructions)
        
        # Add JSON formatting reminder
        prompt_parts.append("""
        IMPORTANT: 
        - Return only valid JSON array of question objects
        - No additional text or explanation
        - Ensure all JSON is properly formatted and escaped
        - Double-check numerical accuracy against the source content
        """)
        
        final_prompt = "\n\n".join(prompt_parts)
        
        # Replace template variables (content will be filled later by the generator)
        final_prompt = final_prompt.replace("{question_count}", str(question_count))
        final_prompt = final_prompt.replace("{question_type}", question_type.replace('_', ' '))
        
        return final_prompt
    
    @classmethod
    def get_available_types(cls) -> List[str]:
        """Get list of available document types."""
        return list(cls.BASE_PROMPTS.keys())
    
    @classmethod 
    def get_available_question_types(cls) -> List[str]:
        """Get list of available question types."""
        return list(cls.QUESTION_TYPE_INSTRUCTIONS.keys())