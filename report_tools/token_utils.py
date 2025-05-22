"""Utilities for token counting and estimation."""

import logging

def count_tokens(text, model="gpt-4"):
    """
    Count tokens in text using tiktoken if available, otherwise estimate.
    
    Args:
        text: The text to count tokens for
        model: The model to use for counting (affects tokenization)
        
    Returns:
        int: Token count or estimate
    """
    # Calculate word count for estimation fallback
    word_count = len(text.split())
    
    try:
        import tiktoken
        encoder = tiktoken.encoding_for_model(model)
        token_count = len(encoder.encode(text))
        return token_count, word_count, True  # Return actual count and whether tiktoken was used
    except ImportError:
        # Fallback estimation if tiktoken is not available
        estimated_tokens = int(word_count * 1.33)  # Rough approximation
        logging.warning("Tiktoken not available, using estimated token count")
        return estimated_tokens, word_count, False  # Return estimate and flag it's an estimate

def format_stack_summary(stack_name, file_count, stack_text):
    """
    Format a single-line summary of a stack for console output.
    
    Args:
        stack_name: Name of the stack
        file_count: Number of files in the stack
        stack_text: Full text content of the stack
        
    Returns:
        str: Formatted summary line
    """
    tokens, words, is_accurate = count_tokens(stack_text)
    
    if is_accurate:
        return f"Stack: {stack_name} [{file_count} files, {words:,} words, {tokens:,} tokens]"
    else:
        return f"Stack: {stack_name} [{file_count} files, {words:,} words, est. ~{tokens:,} tokens]"