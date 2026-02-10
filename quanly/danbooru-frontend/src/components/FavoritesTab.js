import React, { useState, useEffect, useCallback, useRef } from 'react';
import axios from 'axios';
import TagAutocomplete from './TagAutocomplete';
import ImageDetailPanel from './ImageDetailPanel';
import './FavoritesTab.css';

function FavoritesTab() {
  const [favorites, setFavorites] = useState([]);
  
  const [currentTags, setCurrentTags] = useState(() => {
    const saved = localStorage.getItem('favoritesTags');
    return saved ? JSON.parse(saved) : [];
  });
  
  const [loading, setLoading] = useState(false);
  const [selectedImage, setSelectedImage] = useState(null);
  
  // ✅ THÊM: Multi-select state
  const [isMultiSelectMode, setIsMultiSelectMode] = useState(false);
  const [selectedFavorites, setSelectedFavorites] = useState(new Set());
  
  const [currentPage, setCurrentPage] = useState(() => {
    const saved = localStorage.getItem('favoritesPage');
    return saved ? parseInt(saved) : 1;
  });
  
  const [totalPages, setTotalPages] = useState(1);
  const [totalResults, setTotalResults] = useState(0);
  const [favoritesPerPage] = useState(50);
  
  const hasLoadedFavorites = useRef(false);
  const debounceTimerRef = useRef(null);
  const cancelTokenRef = useRef(null);

  useEffect(() => {
    if (!hasLoadedFavorites.current) {
      console.log('🟡 Loading Favorites initial data, page:', currentPage);
      loadFavorites(currentTags, currentPage);
      hasLoadedFavorites.current = true;
    }
  }, []);

  useEffect(() => {
    const handleFavoritesUpdated = () => {
      console.log('🔄 Favorites updated, reloading...');
      loadFavorites(currentTags, currentPage);
    };

    window.addEventListener('favoritesUpdated', handleFavoritesUpdated);
    
    return () => {
      window.removeEventListener('favoritesUpdated', handleFavoritesUpdated);
    };
  }, [currentTags, currentPage]);

  const loadFavorites = useCallback(async (tags, page) => {
    if (cancelTokenRef.current) {
      cancelTokenRef.current.cancel();
    }

    cancelTokenRef.current = axios.CancelToken.source();
    setLoading(true);

    try {
      const tagsQuery = tags.join(',');
      const res = await axios.get(
        `http://localhost:5000/api/favorites?tags=${tagsQuery}&page=${page}&limit=${favoritesPerPage}`,
        { cancelToken: cancelTokenRef.current.token }
      );
      
      const favoritesWithTags = res.data.favorites.map(fav => ({
        ...fav,
        tags: fav.tags ? fav.tags.split(',').map(t => t.trim()) : []
      }));
      
      setFavorites(favoritesWithTags);
      setTotalPages(res.data.totalPages || 1);
      setTotalResults(res.data.total || 0);
      setCurrentPage(page);
      
      localStorage.setItem('favoritesPage', page.toString());
      localStorage.setItem('favoritesTags', JSON.stringify(tags));
      
      console.log(`✅ Favorites loaded: ${res.data.total} items`);
      
      setTimeout(() => {
        const favoritesSection = document.querySelector('.favorites-section');
        if (favoritesSection) {
          favoritesSection.scrollTo({ top: 0, behavior: 'smooth' });
        }
      }, 100);
    } catch (error) {
      if (!axios.isCancel(error)) {
        console.error('Error loading favorites:', error);
      }
    } finally {
      setLoading(false);
    }
  }, [favoritesPerPage]);

  const loadFavoritesDebounced = useCallback((tags, page) => {
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }

    debounceTimerRef.current = setTimeout(() => {
      loadFavorites(tags, page);
    }, 500);
  }, [loadFavorites]);

  const handleTagsChange = (tags) => {
    setCurrentTags(tags);
    setSelectedFavorites(new Set()); // Clear selection
    setIsMultiSelectMode(false);
    loadFavoritesDebounced(tags, 1);
  };

  const handlePageChange = (newPage) => {
    if (newPage >= 1 && newPage <= totalPages) {
      setSelectedFavorites(new Set()); // Clear selection
      setIsMultiSelectMode(false);
      loadFavorites(currentTags, newPage);
    }
  };

  // ✅ TOGGLE SELECT FAVORITE
  const toggleSelectFavorite = (favoriteId) => {
    const newSelected = new Set(selectedFavorites);
    if (newSelected.has(favoriteId)) {
      newSelected.delete(favoriteId);
      console.log('➖ Deselected favorite:', favoriteId);
    } else {
      newSelected.add(favoriteId);
      console.log('➕ Selected favorite:', favoriteId);
    }
    setSelectedFavorites(newSelected);
  };

  // ✅ SELECT ALL
  const selectAll = () => {
    const allIds = new Set(favorites.map(fav => fav.id));
    setSelectedFavorites(allIds);
    console.log(`✅ Selected all ${allIds.size} favorites`);
  };

  // ✅ DESELECT ALL
  const deselectAll = () => {
    setSelectedFavorites(new Set());
    console.log('❌ Deselected all favorites');
  };

  // ✅ TOGGLE MULTI-SELECT MODE
  const toggleMultiSelectMode = () => {
    const newMode = !isMultiSelectMode;
    
    if (!newMode && selectedFavorites.size > 0) {
      if (!window.confirm(`Bạn đang chọn ${selectedFavorites.size} ảnh. Tắt chế độ chọn nhiều?`)) {
        return;
      }
    }
    
    setIsMultiSelectMode(newMode);
    
    if (!newMode) {
      setSelectedFavorites(new Set());
      console.log('✖️ Multi-select mode OFF');
    } else {
      setSelectedImage(null); // Close detail panel
      console.log('✅ Multi-select mode ON');
    }
  };

  // ✅ DELETE MULTIPLE FAVORITES
  const deleteMultipleFavorites = async () => {
    if (selectedFavorites.size === 0) {
      alert('⚠️ Vui lòng chọn ít nhất 1 ảnh!');
      return;
    }

    if (!window.confirm(`Xóa ${selectedFavorites.size} ảnh khỏi favorites?`)) {
      return;
    }

    setLoading(true);
    let successCount = 0;
    let errorCount = 0;

    try {
      // Delete từng ảnh
      for (const favoriteId of selectedFavorites) {
        try {
          await axios.delete(`http://localhost:5000/api/favorites/${favoriteId}`);
          successCount++;
          console.log('✅ Deleted favorite:', favoriteId);
        } catch (err) {
          errorCount++;
          console.error('❌ Failed to delete:', favoriteId, err);
        }
      }

      alert(`✅ Đã xóa ${successCount} ảnh${errorCount > 0 ? ` (${errorCount} lỗi)` : ''}`);
      
      // Reset state
      setSelectedFavorites(new Set());
      setIsMultiSelectMode(false);
      
      // Reload favorites
      loadFavorites(currentTags, currentPage);
    } catch (error) {
      alert('❌ Lỗi: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleRemoveFromFavorites = async (favoriteId) => {
    if (!window.confirm('Xóa ảnh này khỏi favorites?')) return;

    try {
      await axios.delete(`http://localhost:5000/api/favorites/${favoriteId}`);
      loadFavorites(currentTags, currentPage);
      setSelectedImage(null);
      console.log('✅ Removed from favorites:', favoriteId);
    } catch (error) {
      alert('❌ Lỗi: ' + (error.response?.data?.error || error.message));
    }
  };

  const handleClearAllFavorites = async () => {
    if (!window.confirm(`⚠️ XÓA TẤT CẢ ${totalResults} favorites? Hành động này KHÔNG THỂ hoàn tác!`)) {
      return;
    }

    if (!window.confirm('Bạn chắc chắn 100%? Nhấn OK để xóa hết!')) {
      return;
    }

    setLoading(true);
    try {
      const res = await axios.delete('http://localhost:5000/api/favorites');
      alert(`✅ ${res.data.message}`);
      
      setFavorites([]);
      setTotalResults(0);
      setTotalPages(1);
      setCurrentPage(1);
      setSelectedImage(null);
      setSelectedFavorites(new Set());
      setIsMultiSelectMode(false);
      
      console.log('🗑️ Cleared all favorites');
    } catch (error) {
      alert('❌ Lỗi: ' + (error.response?.data?.error || error.message));
    } finally {
      setLoading(false);
    }
  };

  const handleImageClick = (favorite) => {
    if (isMultiSelectMode) {
      toggleSelectFavorite(favorite.id);
    } else {
      setSelectedImage(favorite);
    }
  };

  useEffect(() => {
    return () => {
      if (cancelTokenRef.current) {
        cancelTokenRef.current.cancel();
      }
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, []);

  return (
    <div className="favorites-split-view">
      <div className={`favorites-section ${selectedImage ? 'with-panel' : ''}`}>
        <div className="favorites-tab">
          <div className="sticky-favorites-search">
            <div className="favorites-search">
              <TagAutocomplete 
                onTagsChange={handleTagsChange}
                initialTags={currentTags}
              />
            </div>
          </div>

          {/* ✅ TOOLBAR: Multi-select actions */}
          <div className="favorites-toolbar">
            <button
              className={`btn-toolbar ${isMultiSelectMode ? 'active' : ''}`}
              onClick={toggleMultiSelectMode}
            >
              {isMultiSelectMode ? '✖️ Tắt chọn nhiều' : '✅ Chọn nhiều'}
            </button>

            {isMultiSelectMode && (
              <>
                <button className="btn-toolbar" onClick={selectAll}>
                  ☑️ Chọn tất cả ({favorites.length})
                </button>
                
                {selectedFavorites.size > 0 && (
                  <button 
                    className="btn-toolbar btn-warning" 
                    onClick={deselectAll}
                  >
                    ⬜ Bỏ chọn ({selectedFavorites.size})
                  </button>
                )}
                
                <button 
                  className="btn-toolbar btn-delete-multi"
                  onClick={deleteMultipleFavorites}
                  disabled={selectedFavorites.size === 0}
                >
                  🗑️ Xóa {selectedFavorites.size} ảnh
                </button>
              </>
            )}
          </div>

          <div className="favorites-header">
            <h2 className="favorites-title">
              ⭐ Favorites {totalResults > 0 && `(${totalResults})`}
            </h2>
            
            <div className="favorites-actions">
              {loading && <span className="loading-indicator">⏳ Loading...</span>}
              
              {totalResults > 0 && !isMultiSelectMode && (
                <button 
                  className="btn-clear-all"
                  onClick={handleClearAllFavorites}
                  disabled={loading}
                >
                  🗑️ Xóa hết ({totalResults})
                </button>
              )}
            </div>
          </div>

          {!loading && favorites.length === 0 && (
            <div className="empty-state">
              <div className="empty-icon">⭐</div>
              <h3>Chưa có favorites</h3>
              <p>Thêm ảnh yêu thích từ Gallery để xem tại đây</p>
            </div>
          )}

          <div className="favorites-grid">
            {favorites.map((fav) => (
              <div 
                key={fav.id} 
                className={`favorite-card ${selectedImage?.id === fav.id ? 'selected' : ''} ${selectedFavorites.has(fav.id) ? 'multi-selected' : ''}`}
                onClick={() => handleImageClick(fav)}
              >
                {/* ✅ CHECKBOX cho multi-select */}
                {isMultiSelectMode && (
                  <div className="favorite-checkbox-wrapper">
                    <input
                      type="checkbox"
                      className="favorite-checkbox"
                      checked={selectedFavorites.has(fav.id)}
                      onChange={(e) => {
                        e.stopPropagation();
                        toggleSelectFavorite(fav.id);
                      }}
                      onClick={(e) => e.stopPropagation()}
                    />
                  </div>
                )}

                <div className="favorite-image-wrapper">
                  <img 
                    src={`http://localhost:5000/api/favorites/image/${fav.id}`}
                    alt={fav.filename}
                    loading="lazy"
                    className="favorite-image"
                  />
                  
                  {/* Chỉ hiện overlay khi KHÔNG ở multi-select mode */}
                  {!isMultiSelectMode && (
                    <div className="favorite-overlay">
                      <div className="favorite-tags">
                        {fav.tags.slice(0, 2).map((tag, i) => (
                          <span key={i} className="mini-tag">{tag}</span>
                        ))}
                        {fav.tags.length > 2 && (
                          <span className="mini-tag">+{fav.tags.length - 2}</span>
                        )}
                      </div>
                      <button 
                        className="btn-remove-favorite"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleRemoveFromFavorites(fav.id);
                        }}
                      >
                        🗑️ Remove
                      </button>
                    </div>
                  )}
                </div>
                <div className="favorite-info">
                  <p className="favorite-filename">{fav.filename}</p>
                  <p className="favorite-date">
                    {new Date(fav.added_at).toLocaleDateString('vi-VN')}
                  </p>
                </div>
              </div>
            ))}
          </div>

          {totalPages > 1 && (
            <div className="favorites-pagination">
              <button
                className="pagination-btn"
                onClick={() => handlePageChange(1)}
                disabled={currentPage === 1 || loading}
              >
                ⏮️ First
              </button>
              <button
                className="pagination-btn"
                onClick={() => handlePageChange(currentPage - 1)}
                disabled={currentPage === 1 || loading}
              >
                ◀️ Prev
              </button>
              
              <div className="pagination-info">
                <span className="page-number">
                  Page {currentPage} of {totalPages}
                </span>
                <span className="page-stats">
                  ({totalResults} favorites)
                </span>
              </div>
              
              <button
                className="pagination-btn"
                onClick={() => handlePageChange(currentPage + 1)}
                disabled={currentPage === totalPages || loading}
              >
                Next ▶️
              </button>
              <button
                className="pagination-btn"
                onClick={() => handlePageChange(totalPages)}
                disabled={currentPage === totalPages || loading}
              >
                Last ⏭️
              </button>
            </div>
          )}
        </div>
      </div>

      {selectedImage && !isMultiSelectMode && (
        <div className="detail-section">
          <ImageDetailPanel
            image={selectedImage}
            imageUrl={`http://localhost:5000/api/favorites/image/${selectedImage.id}`}
            onClose={() => setSelectedImage(null)}
            onRemoveFromFavorites={handleRemoveFromFavorites}
            isFavorite={true}
          />
        </div>
      )}
    </div>
  );
}

export default FavoritesTab;
