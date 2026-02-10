import React, { useState, useEffect, useRef, useCallback } from 'react';
import axios from 'axios';
import TagAutocomplete from './components/TagAutocomplete';
import FolderManager from './components/FolderManager';
import FavoritesTab from './components/FavoritesTab';
import ImageDetailPanel from './components/ImageDetailPanel';
import './App.css';

function App() {
  const [activeTab, setActiveTab] = useState(() => {
    return localStorage.getItem('activeTab') || 'gallery';
  });

  // ===== STATE MỚI: FAVORITE & FOLDER FILTER =====
  const [selectedImages, setSelectedImages] = useState(new Set());
  const [sourceFolders, setSourceFolders] = useState([]);
  const [selectedFolder, setSelectedFolder] = useState(null);
  const [isMultiSelectMode, setIsMultiSelectMode] = useState(false);

  const [status, setStatus] = useState('Đang kết nối...');
  const [totalTags, setTotalTags] = useState(0);
  const [totalImages, setTotalImages] = useState(0);
  
  const [currentTags, setCurrentTags] = useState(() => {
    const saved = localStorage.getItem('galleryTags');
    return saved ? JSON.parse(saved) : [];
  });
  
  const [images, setImages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedImage, setSelectedImage] = useState(null);
  
  const [currentPage, setCurrentPage] = useState(() => {
    const saved = localStorage.getItem('galleryPage');
    return saved ? parseInt(saved) : 1;
  });
  
  const [totalPages, setTotalPages] = useState(1);
  const [totalResults, setTotalResults] = useState(0);
  const [imagesPerPage] = useState(50);
  
  const hasLoadedGallery = useRef(false);
  const cancelTokenRef = useRef(null);
  const debounceTimerRef = useRef(null);

  // Initial load
  useEffect(() => {
    checkBackendConnection();
    loadSourceFolders();
    if (!hasLoadedGallery.current) {
      console.log('🔵 Loading Gallery initial data, page:', currentPage);
      loadImages(currentTags, currentPage);
      hasLoadedGallery.current = true;
    }
  }, []);

  useEffect(() => {
    localStorage.setItem('activeTab', activeTab);
  }, [activeTab]);

  // ✅ DEBUG: Log state changes
  useEffect(() => {
    if (selectedImages.size > 0 || isMultiSelectMode) {
      console.log('📊 Selection State:', {
        selectedCount: selectedImages.size,
        isMultiSelectMode,
        selectedFolder: selectedFolder ? 'Yes' : 'No',
        totalImages: images.length
      });
    }
  }, [selectedImages, isMultiSelectMode, selectedFolder, images]);

  const checkBackendConnection = async () => {
    try {
      const response = await axios.get('http://localhost:5000/api/health');
      setStatus('✅ Kết nối thành công');
      setTotalTags(response.data.totalTags);
      setTotalImages(response.data.totalImages);
    } catch (error) {
      setStatus('❌ Lỗi kết nối Backend');
    }
  };

  const loadSourceFolders = async () => {
    try {
      const res = await axios.get('http://localhost:5000/api/source-folders');
      setSourceFolders(res.data.folders || []);
      console.log(`✅ Loaded ${res.data.folders?.length || 0} source folders`);
    } catch (error) {
      console.error('Error loading folders:', error);
    }
  };

  // ============================================
  // 🔴 FIX: loadImagesByFolder - Clear ảnh TRƯỚC API call
  // ============================================
  const loadImagesByFolder = useCallback(async (folder) => {
    console.log('🔄 Loading folder:', folder);
    
    // ✅ QUAN TRỌNG: Clear images NGAY LẬP TỨC (trước API call)
    setImages([]);
    setLoading(true);
    
    // ✅ Clear selection state
    setSelectedImages(new Set());
    setIsMultiSelectMode(false);
    setSelectedImage(null);
    
    // ✅ Update folder state
    setSelectedFolder(folder);
    setCurrentTags([]);
    setCurrentPage(1);
    
    // ✅ Cancel previous request nếu có
    if (cancelTokenRef.current) {
      cancelTokenRef.current.cancel();
    }
    
    cancelTokenRef.current = axios.CancelToken.source();
    
    try {
      const res = await axios.get(
        `http://localhost:5000/api/images/by-folder?folder=${encodeURIComponent(folder)}`,
        { cancelToken: cancelTokenRef.current.token }
      );
      
      const results = res.data.results || [];
      
      // ✅ Update images (list đã clear ở trên, nên không bị trộn)
      setImages(results);
      setTotalResults(results.length);
      setTotalPages(1);
      
      console.log(`✅ Loaded ${results.length} images from folder`);
      
      // Scroll lên đầu
      setTimeout(() => {
        const gallerySection = document.querySelector('.gallery-section');
        if (gallerySection) {
          gallerySection.scrollTo({ top: 0, behavior: 'smooth' });
        }
      }, 100);
    } catch (error) {
      // ✅ Ignore cancelled requests
      if (!axios.isCancel(error)) {
        console.error('❌ Error loading folder images:', error);
        setImages([]);
        alert('Lỗi khi load folder: ' + (error.response?.data?.error || error.message));
      }
    } finally {
      setLoading(false);
    }
  }, []);

  const loadImages = useCallback(async (tags, page) => {
    console.log('🔄 Loading images, page:', page, 'tags:', tags);
    
    if (cancelTokenRef.current) {
      cancelTokenRef.current.cancel();
    }

    cancelTokenRef.current = axios.CancelToken.source();
    setLoading(true);
    
    // ✅ CLEAR STATE NGAY LẬP TỨC
    setSelectedFolder(null);
    setSelectedImages(new Set());
    setIsMultiSelectMode(false);
    setSelectedImage(null);
    
    try {
      const tagsQuery = tags.join(',');
      const res = await axios.get(
        `http://localhost:5000/api/images?tags=${tagsQuery}&page=${page}&limit=${imagesPerPage}`,
        { cancelToken: cancelTokenRef.current.token }
      );
      
      setImages(res.data.images);
      setTotalPages(res.data.totalPages);
      setTotalResults(res.data.total);
      setCurrentPage(page);
      
      localStorage.setItem('galleryPage', page.toString());
      localStorage.setItem('galleryTags', JSON.stringify(tags));
      
      console.log(`✅ Gallery loaded: page ${page}, total: ${res.data.total}`);
      
      setTimeout(() => {
        const gallerySection = document.querySelector('.gallery-section');
        if (gallerySection) {
          gallerySection.scrollTo({ top: 0, behavior: 'smooth' });
        }
      }, 100);
    } catch (error) {
      if (!axios.isCancel(error)) {
        console.error('❌ Error loading images:', error);
      }
    } finally {
      setLoading(false);
    }
  }, [imagesPerPage]);

  const loadImagesDebounced = useCallback((tags, page) => {
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }

    debounceTimerRef.current = setTimeout(() => {
      loadImages(tags, page);
    }, 500);
  }, [loadImages]);

  const handleTagsChange = (tags) => {
    console.log('🔄 Tags changed:', tags);
    setCurrentTags(tags);
    setSelectedImages(new Set());
    setIsMultiSelectMode(false);
    setSelectedImage(null);
    loadImagesDebounced(tags, 1);
  };

  const handlePageChange = (newPage) => {
    if (newPage >= 1 && newPage <= totalPages) {
      console.log('🔄 Page changed to:', newPage);
      setSelectedImages(new Set());
      setIsMultiSelectMode(false);
      setSelectedImage(null);
      loadImages(currentTags, newPage);
    }
  };

  const toggleSelectImage = (imageId) => {
    const newSelected = new Set(selectedImages);
    if (newSelected.has(imageId)) {
      newSelected.delete(imageId);
      console.log('➖ Deselected:', imageId);
    } else {
      newSelected.add(imageId);
      console.log('➕ Selected:', imageId);
    }
    setSelectedImages(newSelected);
  };

  const selectAll = () => {
    const allIds = new Set(images.map(img => img.id));
    setSelectedImages(allIds);
    console.log(`✅ Selected all ${allIds.size} images`);
  };

  const deselectAll = () => {
    setSelectedImages(new Set());
    console.log('❌ Deselected all');
  };

  const addMultipleToFavorites = async () => {
    if (selectedImages.size === 0) {
      alert('⚠️ Vui lòng chọn ít nhất 1 ảnh!');
      return;
    }

    if (!window.confirm(`Thêm ${selectedImages.size} ảnh vào Favorites?`)) {
      return;
    }

    setLoading(true);
    try {
      const selectedFilenames = images
        .filter(img => selectedImages.has(img.id))
        .map(img => img.filename);

      console.log('📤 Adding to favorites:', selectedFilenames);

      const res = await axios.post('http://localhost:5000/api/favorites', {
        filenames: selectedFilenames
      });

      alert(`✅ ${res.data.message}`);
      
      // Clear selection sau khi thành công
      setSelectedImages(new Set());
      setIsMultiSelectMode(false);
      
      // Reload
      if (selectedFolder) {
        loadImagesByFolder(selectedFolder);
      } else {
        loadImages(currentTags, currentPage);
      }
    } catch (error) {
      console.error('❌ Error adding to favorites:', error);
      alert('❌ Lỗi: ' + (error.response?.data?.error || error.message));
    } finally {
      setLoading(false);
    }
  };

  const handleAddToFavorites = async (imageId) => {
    try {
      await axios.post('http://localhost:5000/api/favorites/add', { imageId });
      alert('✅ Đã thêm vào favorites!');
    } catch (error) {
      alert('❌ ' + (error.response?.data?.error || error.message));
    }
  };

  const handleImageClick = (image) => {
    if (isMultiSelectMode) {
      toggleSelectImage(image.id);
    } else {
      setSelectedImage(image);
    }
  };

  const handleTabChange = (tab) => {
    console.log('🔄 Switch tab to:', tab);
    setActiveTab(tab);
    setSelectedImage(null);
    setIsMultiSelectMode(false);
    setSelectedImages(new Set());
  };

  // ✅ TOGGLE MULTI-SELECT MODE
  const toggleMultiSelectMode = () => {
    const newMode = !isMultiSelectMode;
    
    if (!newMode && selectedImages.size > 0) {
      // Tắt mode và đang có ảnh được chọn
      if (!window.confirm(`Bạn đang chọn ${selectedImages.size} ảnh. Tắt chế độ chọn nhiều?`)) {
        return;
      }
    }
    
    setIsMultiSelectMode(newMode);
    
    if (!newMode) {
      // Clear selection khi tắt mode
      setSelectedImages(new Set());
      console.log('✖️ Multi-select mode OFF, cleared selection');
    } else {
      console.log('✅ Multi-select mode ON');
    }
  };

  // ✅ RESET TO ALL FOLDERS
  const resetToAllFolders = () => {
    console.log('🔄 Reset to all folders');
    setSelectedFolder(null);
    setSelectedImages(new Set());
    setIsMultiSelectMode(false);
    setSelectedImage(null);
    setCurrentPage(1);
    loadImages(currentTags, 1);
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
    <div className="app-container">
      {/* Header */}
      <header className="app-header">
        <div className="header-content">
          <div className="header-left">
            <h1 className="app-title">🎨 Danbooru Manager</h1>
            <div className="status-badge">
              <span className="status-dot"></span>
              {status}
            </div>
          </div>
          
          <div className="header-stats">
            <div className="stat-pill">
              <span className="stat-icon">🏷️</span>
              <span className="stat-text">{totalTags.toLocaleString()} tags</span>
            </div>
            <div className="stat-pill">
              <span className="stat-icon">🖼️</span>
              <span className="stat-text">{totalImages} images</span>
            </div>
            <div className="stat-pill">
              <span className="stat-icon">✨</span>
              <span className="stat-text">{currentTags.length} selected</span>
            </div>
            {selectedImages.size > 0 && (
              <div className="stat-pill stat-pill-highlight">
                <span className="stat-icon">✅</span>
                <span className="stat-text">{selectedImages.size} chọn</span>
              </div>
            )}
          </div>
        </div>

        {/* Tabs Navigation */}
        <div className="tabs-nav">
          <button 
            className={`tab-btn ${activeTab === 'gallery' ? 'active' : ''}`}
            onClick={() => handleTabChange('gallery')}
          >
            <span className="tab-icon">🖼️</span>
            Gallery
            {currentPage > 1 && (
              <span className="tab-badge">p.{currentPage}</span>
            )}
          </button>
          <button 
            className={`tab-btn ${activeTab === 'favorites' ? 'active' : ''}`}
            onClick={() => handleTabChange('favorites')}
          >
            <span className="tab-icon">⭐</span>
            Favorites
          </button>
          <button 
            className={`tab-btn ${activeTab === 'settings' ? 'active' : ''}`}
            onClick={() => handleTabChange('settings')}
          >
            <span className="tab-icon">⚙️</span>
            Settings
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="main-content">
        {/* Gallery Tab */}
        <div className={`tab-content ${activeTab === 'gallery' ? 'active' : ''}`}>
          <div className="split-view">
            <div className={`gallery-section ${selectedImage ? 'with-panel' : ''}`}>
              <div className="gallery-content">
                <div className="sticky-search-wrapper">
                  <div className="search-section">
                    <TagAutocomplete 
                      onTagsChange={handleTagsChange}
                      initialTags={currentTags}
                    />
                  </div>
                </div>

                {/* TOOLBAR ACTIONS */}
                <div className="toolbar-actions">
                  <div className="toolbar-left">
                    <button
                      className={`btn-toolbar ${isMultiSelectMode ? 'active' : ''}`}
                      onClick={toggleMultiSelectMode}
                    >
                      {isMultiSelectMode ? '✖️ Tắt chọn nhiều' : '✅ Chọn nhiều'}
                    </button>

                    {isMultiSelectMode && (
                      <>
                        <button className="btn-toolbar" onClick={selectAll}>
                          ☑️ Chọn tất cả ({images.length})
                        </button>
                        
                        {selectedImages.size > 0 && (
                          <button 
                            className="btn-toolbar btn-warning" 
                            onClick={deselectAll}
                            style={{ background: '#ff9800' }}
                          >
                            ⬜ Bỏ chọn ({selectedImages.size})
                          </button>
                        )}
                        
                        <button 
                          className="btn-toolbar btn-favo"
                          onClick={addMultipleToFavorites}
                          disabled={selectedImages.size === 0}
                        >
                          ⭐ Add {selectedImages.size} vào Favo
                        </button>
                      </>
                    )}
                  </div>
                </div>

                {/* FOLDER FILTER */}
                {sourceFolders.length > 0 && (
                  <div className="folder-filter-section">
                    <h3 className="filter-title">📁 Lọc theo Folder: ({sourceFolders.length})</h3>
                    <div className="folder-buttons">
                      <button
                        className={`folder-btn ${!selectedFolder ? 'active' : ''}`}
                        onClick={resetToAllFolders}
                      >
                        📂 Tất cả
                      </button>
                      {sourceFolders.map((folder, idx) => {
                        const displayName = typeof folder === 'string' 
                          ? folder.split('\\').pop() || folder 
                          : folder.name || folder.path?.split('\\').pop() || 'Unknown';
                        const folderPath = typeof folder === 'string' ? folder : folder.path;
                        
                        return (
                          <button
                            key={idx}
                            className={`folder-btn ${selectedFolder === folderPath ? 'active' : ''}`}
                            onClick={() => loadImagesByFolder(folderPath)}
                            title={folderPath}
                          >
                            📁 {displayName}
                          </button>
                        );
                      })}
                    </div>
                  </div>
                )}

                <div className="gallery-controls">
                  <h2 className="gallery-title">
                    {selectedFolder ? `📁 ${selectedFolder.split('\\').pop()}` : 'Gallery'} 
                    {totalResults > 0 && ` (${totalResults})`}
                  </h2>
                  {loading && <span className="loading-indicator">⏳ Loading...</span>}
                </div>

                {!loading && images.length === 0 && (
                  <div className="empty-state">
                    <div className="empty-icon">📂</div>
                    <h3>Chưa có ảnh</h3>
                    <p>Vào tab <strong>Settings</strong> để scan folder</p>
                    <button 
                      className="btn-primary"
                      onClick={() => handleTabChange('settings')}
                    >
                      Đi tới Settings
                    </button>
                  </div>
                )}

                <div className="image-grid">
                  {images.map((img) => (
                    <div 
                      key={img.id} 
                      className={`image-card ${selectedImage?.id === img.id ? 'selected' : ''} ${selectedImages.has(img.id) ? 'multi-selected' : ''}`}
                      onClick={() => handleImageClick(img)}
                    >
                      {isMultiSelectMode && (
                        <div className="image-checkbox-wrapper">
                          <input
                            type="checkbox"
                            className="image-checkbox"
                            checked={selectedImages.has(img.id)}
                            onChange={(e) => {
                              e.stopPropagation();
                              toggleSelectImage(img.id);
                            }}
                            onClick={(e) => e.stopPropagation()}
                          />
                        </div>
                      )}

                      {img.isFavorite === 1 && (
                        <div className="favo-badge">⭐</div>
                      )}

                      <div className="image-wrapper">
                        <img 
                          src={`http://localhost:5000/api/image/${img.id}`} 
                          alt={img.filename}
                          loading="lazy"
                        />
                        <div className="image-overlay">
                          <div className="image-tags">
                            {img.tags.slice(0, 3).map((tag, i) => (
                              <span key={i} className="mini-tag">{tag}</span>
                            ))}
                            {img.tags.length > 3 && (
                              <span className="mini-tag">+{img.tags.length - 3}</span>
                            )}
                          </div>
                        </div>
                      </div>
                      <div className="image-info">
                        <p className="image-filename">{img.filename}</p>
                      </div>
                    </div>
                  ))}
                </div>

                {totalPages > 1 && !selectedFolder && (
                  <div className="pagination">
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
                        ({totalResults} images)
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
                  imageUrl={`http://localhost:5000/api/image/${selectedImage.id}`}
                  onClose={() => setSelectedImage(null)}
                  onAddToFavorites={handleAddToFavorites}
                  isFavorite={false}
                />
              </div>
            )}
          </div>
        </div>

        {/* Favorites Tab */}
        <div className={`tab-content ${activeTab === 'favorites' ? 'active' : ''}`}>
          <FavoritesTab />
        </div>

        {/* Settings Tab */}
        <div className={`tab-content ${activeTab === 'settings' ? 'active' : ''}`}>
          <div className="tab-panel">
            <div className="settings-container">
              <h2 className="section-title">⚙️ Settings</h2>
              
              <div className="settings-section">
                <h3>📂 Folder Management</h3>
                <p className="section-description">
                  Quản lý folders chứa ảnh. Folders sẽ được lưu vào database.
                </p>
                <FolderManager onFoldersChanged={() => {
                  checkBackendConnection();
                  loadSourceFolders();
                }} />
              </div>

              <div className="settings-section">
                <h3>ℹ️ Thông tin</h3>
                <div className="info-grid">
                  <div className="info-item">
                    <span className="info-label">Backend Status:</span>
                    <span className="info-value">{status}</span>
                  </div>
                  <div className="info-item">
                    <span className="info-label">Total Tags:</span>
                    <span className="info-value">{totalTags.toLocaleString()}</span>
                  </div>
                  <div className="info-item">
                    <span className="info-label">Total Images:</span>
                    <span className="info-value">{totalImages}</span>
                  </div>
                  <div className="info-item">
                    <span className="info-label">Source Folders:</span>
                    <span className="info-value">{sourceFolders.length}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;