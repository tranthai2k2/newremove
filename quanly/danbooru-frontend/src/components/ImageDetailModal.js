import React from 'react';
import './ImageDetailModal.css';

function ImageDetailModal({ image, imageUrl, onClose, onAddToFavorites, onRemoveFromFavorites, isFavorite }) {
  if (!image) return null;

  const handleBackdropClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <div className="modal-backdrop" onClick={handleBackdropClick}>
      <div className="modal-content">
        <button className="modal-close" onClick={onClose}>✕</button>
        
        <div className="modal-body">
          {/* Image Preview */}
          <div className="modal-image-section">
            <img 
              src={imageUrl} 
              alt={image.filename} 
              className="modal-image"
            />
          </div>

          {/* Image Details */}
          <div className="modal-details-section">
            <h2 className="modal-title">{image.filename}</h2>
            
            <div className="detail-group">
              <label>📁 Path:</label>
              <div className="detail-value path">{image.path || image.image_path}</div>
            </div>

            <div className="detail-group">
              <label>🏷️ Tags ({image.tags?.length || 0}):</label>
              <div className="tags-container">
                {image.tags && image.tags.length > 0 ? (
                  image.tags.map((tag, i) => (
                    <span key={i} className="tag-badge">{tag}</span>
                  ))
                ) : (
                  <span className="no-tags">No tags</span>
                )}
              </div>
            </div>

            <div className="detail-group">
              <label>📄 Full Tags Text:</label>
              <textarea 
                className="tags-textarea"
                value={image.tags?.join(', ') || ''}
                readOnly
                rows={8}
              />
            </div>

            <div className="modal-actions">
              {!isFavorite ? (
                <button 
                  className="btn-modal btn-favorite"
                  onClick={() => onAddToFavorites(image.id)}
                >
                  ⭐ Add to Favorites
                </button>
              ) : (
                <button 
                  className="btn-modal btn-remove"
                  onClick={() => onRemoveFromFavorites(image.id)}
                >
                  🗑️ Remove from Favorites
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ImageDetailModal;
