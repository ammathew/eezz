"""Utility functions for dream interpretation"""
from django.db.models import Q
from .models import DreamSymbol


def get_dream_symbols(keywords):
    """
    Query database for dream symbols matching keywords (case-insensitive)
    
    Args:
        keywords: List of keyword strings
        
    Returns:
        dict: Dictionary mapping keywords to list of interpretations
    """
    if not keywords:
        return {}

    # Build query for case-insensitive keyword matching
    query = Q()
    for keyword in keywords:
        query |= Q(keyword__icontains=keyword)

    # Get matching symbols
    symbols = DreamSymbol.objects.filter(query).values('keyword', 'interpretation', 'source')

    # Group interpretations by keyword
    result = {}
    for symbol in symbols:
        keyword = symbol['keyword']
        if keyword not in result:
            result[keyword] = []
        result[keyword].append({
            'interpretation': symbol['interpretation'],
            'source': symbol['source']
        })

    return result
