import React from 'react';
import './ImageDetailPanel.css';

function ImageDetailPanel({ image, imageUrl, onClose, onAddToFavorites, onRemoveFromFavorites, isFavorite }) {
  if (!image) {
    return (
      <div className="detail-panel empty">
        <div className="empty-detail">
          <span className="empty-icon">👆</span>
          <p>Chọn ảnh để xem chi tiết</p>
        </div>
      </div>
    );
  }

  return (
    <div className="detail-panel">
      {/* Close button */}
      <button className="panel-close" onClick={onClose} title="Đóng panel">
        ✕
      </button>

      {/* Image Preview */}
      <div className="panel-image-section">
        <img 
          src={imageUrl} 
          alt={image.filename} 
          className="panel-image"
        />
      </div>

      {/* Details */}
      <div className="panel-details">
        <h3 className="panel-title">{image.filename}</h3>
        
        <div className="detail-item">
          <label>📁 Path:</label>
          <div className="detail-text path">{image.path || image.image_path}</div>
        </div>

        <div className="detail-item">
          <label>🏷️ Tags ({image.tags?.length || 0}):</label>
          <div className="tags-scroll">
            {image.tags && image.tags.length > 0 ? (
              image.tags.map((tag, i) => (
                <span key={i} className="tag-pill">{tag}</span>
              ))
            ) : (
              <span className="no-data">No tags</span>
            )}
          </div>
        </div>

        <div className="detail-item">
          <label>📄 Full Tags:</label>
          <textarea 
            className="tags-text"
            value={image.tags?.join(', ') || ''}
            readOnly
            rows={6}
          />
        </div>

        {/* Actions */}
        <div className="panel-actions">
          {!isFavorite ? (
            <button 
              className="btn-panel btn-fav"
              onClick={() => onAddToFavorites(image.id)}
            >
              ⭐ Add to Favorites
            </button>
          ) : (
            <button 
              className="btn-panel btn-remove"
              onClick={() => onRemoveFromFavorites(image.id)}
            >
              🗑️ Remove
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

export default ImageDetailPanel;
