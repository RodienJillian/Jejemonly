from J3jemonly.jejemon_normalizer import JejemonNormalizer

def main():
    normalizer = JejemonNormalizer()
    
    print("Jejemon Text Normalizer")
    print("-" * 40)
    
    while True:
        user_input = input("\nEnter jejemon text: ").strip()
        
        if user_input.lower() == 'bye':
            break
        
        if not user_input:
            continue
        
        result = normalizer.normalize_text(user_input)
        
        print(f"\nStep-by-step normalization:")
        print(f"1. Original text: {result['original']}")
        print(f"2. After punctuation processing: {result['punctuation_evaluated']}")
        print(f"3. After character replacement: {result['character_replaced']}")
        
        # Only show tokenized step if you implemented the new flow
        if 'tokenized' in result:
            print(f"4. After tokenization: {result['tokenized']}")
            print(f"5. Final normalized text: {result['normalized']}")
        else:
            print(f"4. Final normalized text: {result['normalized']}")
        
        # Show what actually changed
        if result['original'] != result['normalized']:
            print(f"\n✓ Text was normalized successfully!")
        else:
            print(f"\n→ No changes needed (text was already normal)")
        
        # Uncomment if you want confidence scoring
        # confidence = normalizer.get_normalization_confidence(
        #     result['original'], result['normalized']
        # )
        # print(f"Confidence: {confidence:.2%}")

if __name__ == "__main__":
    main()