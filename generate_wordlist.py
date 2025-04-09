#!/usr/bin/env python3
import argparse
import itertools
import os
import sys
from typing import List, Set

def read_base_words(file_path: str) -> List[str]:
    """Read base words from a file, one word per line."""
    with open(file_path, 'r') as f:
        return [line.strip() for line in f if line.strip()]

def generate_variations(base_words: List[str], max_length: int = 2) -> Set[str]:
    """Generate variations of base words with common patterns and combinations."""
    variations = set(base_words)
    
    # Add years
    years = [str(year) for year in range(2000, 2025)]
    for word in base_words:
        for year in years:
            variations.add(f"{word}{year}")
            variations.add(f"{word}_{year}")
            variations.add(f"{word}-{year}")
            
    # Add common numbers
    common_suffixes = ["123", "1234", "12345", "123456", "1", "01", "02", "2023", "2024"]
    for word in base_words:
        for suffix in common_suffixes:
            variations.add(f"{word}{suffix}")
            
    # Add character substitutions (leet speak)
    leet_map = {'a': '4', 'e': '3', 'i': '1', 'o': '0', 's': '5', 't': '7'}
    for word in base_words:
        # Generate all possible leet speak combinations
        chars = list(word)
        positions = [i for i, char in enumerate(chars) if char.lower() in leet_map]
        
        for r in range(1, min(len(positions) + 1, 4)):  # Limit combinations to avoid explosion
            for combo in itertools.combinations(positions, r):
                word_chars = chars.copy()
                for pos in combo:
                    char = word_chars[pos].lower()
                    if char in leet_map:
                        word_chars[pos] = leet_map[char]
                variations.add(''.join(word_chars))
    
    # Add common transformations
    for word in base_words:
        # Capitalize first letter
        variations.add(word.capitalize())
        # All uppercase
        variations.add(word.upper())
        # Add exclamation mark
        variations.add(f"{word}!")
        variations.add(f"{word.capitalize()}!")
        # Add @ symbol
        variations.add(f"{word}@")
        # Add common special character endings
        for char in "!@#$%^&*()":
            variations.add(f"{word}{char}")
    
    # Add common word combinations (up to max_length)
    if max_length >= 2:
        for combo in itertools.permutations(base_words, 2):
            variations.add(''.join(combo))
            variations.add('_'.join(combo))
            
    if max_length >= 3:
        # Limit to avoid combinatorial explosion
        sample_words = base_words[:min(len(base_words), 10)]
        for combo in itertools.permutations(sample_words, 3):
            variations.add(''.join(combo))
    
    return variations

def main():
    parser = argparse.ArgumentParser(description="Generate password variations for cracking")
    parser.add_argument("-i", "--input", required=True, help="Input file with base words")
    parser.add_argument("-o", "--output", required=True, help="Output file for generated passwords")
    parser.add_argument("-m", "--max-length", type=int, default=2, 
                        help="Maximum word combination length (default: 2)")
    parser.add_argument("-l", "--limit", type=int, default=None,
                        help="Limit output to this many passwords")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        print(f"Error: Input file not found: {args.input}")
        sys.exit(1)
    
    print(f"Reading base words from {args.input}...")
    base_words = read_base_words(args.input)
    print(f"Found {len(base_words)} base words")
    
    print("Generating variations...")
    variations = generate_variations(base_words, args.max_length)
    print(f"Generated {len(variations)} variations")
    
    # Apply limit if specified
    if args.limit and len(variations) > args.limit:
        print(f"Limiting output to {args.limit} passwords")
        variations = list(variations)[:args.limit]
    
    print(f"Writing output to {args.output}...")
    with open(args.output, 'w') as f:
        for variation in variations:
            f.write(f"{variation}\n")
    
    print(f"Done! Generated {len(variations)} passwords.")

if __name__ == "__main__":
    main() 