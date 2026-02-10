import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import './TagAutocomplete.css';

function TagAutocomplete({ onTagsChange, initialTags = [] }) {
  const [tagInput, setTagInput] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [selectedTags, setSelectedTags] = useState(initialTags);
  const [highlightedIndex, setHighlightedIndex] = useState(0);
  const [isNegative, setIsNegative] = useState(false);
  
  const inputRef = useRef(null);
  const debounceTimerRef = useRef(null);
  const cancelTokenRef = useRef(null);

  // Chỉ notify parent khi tags thay đổi
  useEffect(() => {
    onTagsChange(selectedTags);
  }, [selectedTags]); // KHÔNG thêm onTagsChange vào dependencies

  // Tìm gợi ý tags với debounce
  const searchTags = async (searchQuery) => {
    // Cancel request cũ
    if (cancelTokenRef.current) {
      cancelTokenRef.current.cancel();
    }

    if (searchQuery.length === 0) {
      setSuggestions([]);
      return;
    }

    try {
      cancelTokenRef.current = axios.CancelToken.source();
      const res = await axios.get(
        `http://localhost:5000/api/tags/search?q=${searchQuery}`,
        { cancelToken: cancelTokenRef.current.token }
      );
      setSuggestions(res.data.results);
      setHighlightedIndex(0);
    } catch (error) {
      if (!axios.isCancel(error)) {
        setSuggestions([]);
      }
    }
  };

  const handleTagInput = (value) => {
    setTagInput(value);

    // Kiểm tra dấu -
    let searchQuery = value;
    let hasNegative = false;
    
    if (value.startsWith('-')) {
      hasNegative = true;
      searchQuery = value.substring(1);
    }
    
    setIsNegative(hasNegative);

    // Clear timeout cũ
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }

    // Debounce search (chờ 300ms)
    debounceTimerRef.current = setTimeout(() => {
      searchTags(searchQuery);
    }, 300);
  };

  const addTag = (tag) => {
    const finalTag = isNegative ? `-${tag}` : tag;
    
    if (!selectedTags.includes(finalTag)) {
      setSelectedTags([...selectedTags, finalTag]);
    }
    setTagInput('');
    setSuggestions([]);
    setIsNegative(false);
    inputRef.current.focus();
  };

  const removeTag = (tag) => {
    setSelectedTags(selectedTags.filter(t => t !== tag));
  };

  const handleKeyDown = (e) => {
    if (suggestions.length === 0) return;

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setHighlightedIndex((prev) => 
          prev < suggestions.length - 1 ? prev + 1 : 0
        );
        break;

      case 'ArrowUp':
        e.preventDefault();
        setHighlightedIndex((prev) => 
          prev > 0 ? prev - 1 : suggestions.length - 1
        );
        break;

      case 'Enter':
      case 'Tab':
        e.preventDefault();
        if (suggestions[highlightedIndex]) {
          addTag(suggestions[highlightedIndex]);
        }
        break;

      case 'Escape':
        setSuggestions([]);
        break;

      default:
        break;
    }
  };

  // Cleanup
  useEffect(() => {
    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
      if (cancelTokenRef.current) {
        cancelTokenRef.current.cancel();
      }
    };
  }, []);

  return (
    <div className="tag-autocomplete">
      <div className="input-wrapper">
        <input
          ref={inputRef}
          type="text"
          value={tagInput}
          onChange={(e) => handleTagInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Gõ tag hoặc -tag để loại trừ (↑↓ Enter/Tab)"
          className="tag-input"
        />

        {isNegative && tagInput.length > 1 && (
          <div className="negative-hint">
            🚫 Negative tag mode
          </div>
        )}

        {suggestions.length > 0 && (
          <div className="suggestions-dropdown">
            {suggestions.map((tag, index) => (
              <div
                key={index}
                onClick={() => addTag(tag)}
                className={`suggestion-item ${index === highlightedIndex ? 'highlighted' : ''}`}
              >
                {isNegative && <span className="negative-prefix">-</span>}
                {tag}
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="selected-tags">
        {selectedTags.map((tag, index) => {
          const isNegativeTag = tag.startsWith('-');
          const displayTag = isNegativeTag ? tag.substring(1) : tag;
          
          return (
            <span 
              key={index} 
              className={`tag-chip ${isNegativeTag ? 'negative' : 'positive'}`}
            >
              {isNegativeTag && <span className="tag-prefix">-</span>}
              {displayTag}
              <button
                onClick={() => removeTag(tag)}
                className="tag-remove"
                aria-label="Remove tag"
              >
                ×
              </button>
            </span>
          );
        })}
      </div>
    </div>
  );
}

export default TagAutocomplete;
