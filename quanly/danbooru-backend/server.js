const express = require('express');
const cors = require('cors');
const fs = require('fs');
const path = require('path');
const sqlite3 = require('sqlite3').verbose();

const app = express();
const PORT = 5000;

app.use(cors());
app.use(express.json());

// ===== ĐỊNH NGHĨA PATHS =====
const DATAPATH = path.join(__dirname, 'data'); // Thêm dòng này
const IMAGESPATH = path.join(DATAPATH, 'images');
const FAVOPATH = path.join(DATAPATH, 'favo');
const DBPATH = path.join(__dirname, 'danbooru.db');

// Tạo folders nếu chưa có
if (!fs.existsSync(DATAPATH)) {
  fs.mkdirSync(DATAPATH, { recursive: true });
}
if (!fs.existsSync(FAVOPATH)) {
  fs.mkdirSync(FAVOPATH, { recursive: true });
  console.log('✅ Created favo folder:', FAVOPATH);
}

// Serve static files
app.use('/favo', express.static(FAVOPATH));

// Load tags
let allTags = [];
let imageDatabase = [];

// SQLite database
const db = new sqlite3.Database(DBPATH, (err) => {
  if (err) {
    console.error('❌ Database error:', err);
  } else {
    console.log('✅ Connected to SQLite database');
    initDatabase();
  }
});

// Khởi tạo tables
function initDatabase() {
  db.run(`
    CREATE TABLE IF NOT EXISTS folders (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      path TEXT UNIQUE NOT NULL,
      name TEXT NOT NULL,
      image_count INTEGER DEFAULT 0,
      last_scan DATETIME,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
  `);
  
  db.run(`
    CREATE TABLE IF NOT EXISTS favorites (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      image_path TEXT UNIQUE NOT NULL,
      filename TEXT NOT NULL,
      tags TEXT,
      added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      display_order INTEGER
    )
  `);

  // Thêm cột isFavorite nếu chưa có
  db.run(`ALTER TABLE favorites ADD COLUMN isFavorite INTEGER DEFAULT 1`, (err) => {
    if (err && !err.message.includes('duplicate column')) {
      console.error('Note: isFavorite column may already exist');
    }
  });
}

function loadTags() {
  const files = ['general.txt', 'large.txt', 'eva02.txt'];
  const tags = new Set();
  
  files.forEach(file => {
    const filePath = path.join(__dirname, file);
    if (fs.existsSync(filePath)) {
      const content = fs.readFileSync(filePath, 'utf-8');
      content.split('\r\n').forEach(tag => {
        if (tag.trim()) tags.add(tag.trim());
      });
    }
  });
  
  allTags = Array.from(tags).sort();
  console.log(`✅ Loaded ${allTags.length} tags`);
}

loadTags();

// ==================== ROUTES ====================

app.get('/', (req, res) => {
  res.json({ 
    message: 'Backend API đang chạy!',
    endpoints: [
      '/api/health',
      '/api/tags/search',
      '/api/folders',
      '/api/images',
      '/api/favorites',
      '/api/source-folders',
      '/api/images/by-folder'
    ]
  });
});

app.get('/api/health', (req, res) => {
  res.json({ 
    ok: true, 
    message: 'Backend is running',
    totalTags: allTags.length,
    totalImages: imageDatabase.length
  });
});

app.get('/api/tags/search', (req, res) => {
  const query = (req.query.q || '').toLowerCase();
  
  if (!query) {
    return res.json({ results: [] });
  }
  
  const matches = allTags
    .filter(tag => tag.toLowerCase().startsWith(query))
    .slice(0, 20);
  
  res.json({ results: matches });
});

// ==================== FOLDER MANAGEMENT ====================

app.get('/api/folders', (req, res) => {
  db.all('SELECT * FROM folders ORDER BY created_at DESC', (err, rows) => {
    if (err) {
      return res.status(500).json({ error: err.message });
    }
    
    const foldersWithStatus = rows.map(folder => ({
      ...folder,
      exists: fs.existsSync(folder.path)
    }));
    
    res.json({ folders: foldersWithStatus });
  });
});

app.post('/api/folders/add', (req, res) => {
  const { folderPath } = req.body;
  
  if (!folderPath) {
    return res.status(400).json({ error: 'Folder path is required' });
  }
  
  if (!fs.existsSync(folderPath)) {
    return res.status(400).json({ error: 'Folder không tồn tại' });
  }

  const folderName = path.basename(folderPath);
  
  db.run(
    'INSERT INTO folders (path, name) VALUES (?, ?)',
    [folderPath, folderName],
    function(err) {
      if (err) {
        if (err.message.includes('UNIQUE')) {
          return res.status(400).json({ error: 'Folder đã tồn tại trong database' });
        }
        return res.status(500).json({ error: err.message });
      }
      
      res.json({ 
        success: true, 
        id: this.lastID,
        message: 'Đã thêm folder'
      });
    }
  );
});

app.post('/api/folders/:id/scan', (req, res) => {
  const folderId = req.params.id;
  
  db.get('SELECT * FROM folders WHERE id = ?', [folderId], (err, folder) => {
    if (err) {
      return res.status(500).json({ error: err.message });
    }
    
    if (!folder) {
      return res.status(404).json({ error: 'Folder not found' });
    }
    
    if (!fs.existsSync(folder.path)) {
      return res.status(400).json({ error: 'Folder không tồn tại trên disk' });
    }

    try {
      const images = scanFolder(folder.path);
      imageDatabase = [...imageDatabase, ...images];
      
      imageDatabase = imageDatabase.filter((img, index, self) =>
        index === self.findIndex(t => t.path === img.path)
      );
      
      db.run(
        'UPDATE folders SET image_count = ?, last_scan = CURRENT_TIMESTAMP WHERE id = ?',
        [images.length, folderId]
      );
      
      res.json({ 
        success: true, 
        count: images.length,
        message: `Đã scan ${images.length} ảnh từ ${folder.name}`
      });
    } catch (error) {
      res.status(500).json({ error: error.message });
    }
  });
});

app.delete('/api/folders/:id', (req, res) => {
  const folderId = req.params.id;
  
  db.run('DELETE FROM folders WHERE id = ?', [folderId], function(err) {
    if (err) {
      return res.status(500).json({ error: err.message });
    }
    
    if (this.changes === 0) {
      return res.status(404).json({ error: 'Folder not found' });
    }
    
    res.json({ 
      success: true, 
      message: 'Đã xóa folder'
    });
  });
});

app.post('/api/folders/scan-all', (req, res) => {
  db.all('SELECT * FROM folders', (err, folders) => {
    if (err) {
      return res.status(500).json({ error: err.message });
    }
    
    let totalImages = 0;
    let scannedFolders = 0;
    
    folders.forEach(folder => {
      if (fs.existsSync(folder.path)) {
        const images = scanFolder(folder.path);
        imageDatabase = [...imageDatabase, ...images];
        totalImages += images.length;
        scannedFolders++;
        
        db.run(
          'UPDATE folders SET image_count = ?, last_scan = CURRENT_TIMESTAMP WHERE id = ?',
          [images.length, folder.id]
        );
      }
    });
    
    imageDatabase = imageDatabase.filter((img, index, self) =>
      index === self.findIndex(t => t.path === img.path)
    );
    
    res.json({ 
      success: true, 
      scannedFolders,
      totalImages: imageDatabase.length,
      message: `Đã scan ${scannedFolders} folders, tổng ${imageDatabase.length} ảnh`
    });
  });
});

// ==================== IMAGE ROUTES ====================

function scanFolder(folderPath) {
  const images = [];
  
  function scanRecursive(dir) {
    const items = fs.readdirSync(dir);
    
    items.forEach(item => {
      const fullPath = path.join(dir, item);
      const stat = fs.statSync(fullPath);
      
      if (stat.isDirectory()) {
        scanRecursive(fullPath);
      } else if (stat.isFile()) {
        const ext = path.extname(item).toLowerCase();
        if (['.jpg', '.jpeg', '.png', '.webp', '.gif'].includes(ext)) {
          const txtPath = fullPath.replace(ext, '.txt');
          let tags = [];
          
          if (fs.existsSync(txtPath)) {
            const content = fs.readFileSync(txtPath, 'utf-8');
            tags = content.split(',').map(t => t.trim()).filter(t => t);
          }
          
          images.push({
            id: Date.now() + Math.random(),
            filename: item,
            path: fullPath,
            relativePath: path.relative(folderPath, fullPath),
            tags: tags,
            folder: path.dirname(fullPath)
          });
        }
      }
    });
  }
  
  scanRecursive(folderPath);
  return images;
}

app.get('/api/images', (req, res) => {
  const { tags, page = 1, limit = 50 } = req.query;
  
  let filteredImages = imageDatabase;
  
  if (tags && tags.trim()) {
    const searchTags = tags.split(',').map(t => t.trim().toLowerCase()).filter(t => t);
    const positiveTags = searchTags.filter(t => !t.startsWith('-'));
    const negativeTags = searchTags.filter(t => t.startsWith('-')).map(t => t.substring(1));
    
    filteredImages = imageDatabase.filter(img => {
      const imgTags = img.tags.map(t => t.toLowerCase());
      
      const hasAllPositive = positiveTags.length === 0 || positiveTags.every(tag => 
        imgTags.some(imgTag => imgTag.includes(tag))
      );
      
      const hasNoNegative = !negativeTags.some(tag => 
        imgTags.some(imgTag => imgTag.includes(tag))
      );
      
      return hasAllPositive && hasNoNegative;
    });
  }
  
  const pageNum = parseInt(page);
  const limitNum = parseInt(limit);
  const start = (pageNum - 1) * limitNum;
  const end = start + limitNum;
  const paginatedImages = filteredImages.slice(start, end);
  
  res.json({
    images: paginatedImages,
    total: filteredImages.length,
    page: pageNum,
    limit: limitNum,
    totalPages: Math.ceil(filteredImages.length / limitNum),
    hasMore: end < filteredImages.length
  });
});

app.get('/api/image/:id', (req, res) => {
  const image = imageDatabase.find(img => img.id == req.params.id);
  
  if (!image || !fs.existsSync(image.path)) {
    return res.status(404).json({ error: 'Image not found' });
  }
  
  res.sendFile(image.path);
});

// ==================== FAVORITES API (MỚI) ====================

// Helper: Tìm image trong imageDatabase
function findImageByFilename(filename) {
  return imageDatabase.find(img => img.filename === filename);
}

// GET: Danh sách favorites
app.get('/api/favorites', (req, res) => {
  const { tags, page = 1, limit = 50 } = req.query;
  
  db.all('SELECT * FROM favorites ORDER BY display_order DESC, added_at DESC', (err, rows) => {
    if (err) {
      return res.status(500).json({ error: err.message });
    }
    
    let filtered = rows;
    
    if (tags && tags.trim()) {
      const searchTags = tags.split(',').map(t => t.trim().toLowerCase()).filter(t => t);
      const positiveTags = searchTags.filter(t => !t.startsWith('-'));
      const negativeTags = searchTags.filter(t => t.startsWith('-')).map(t => t.substring(1));
      
      filtered = rows.filter(fav => {
        const favTags = fav.tags ? fav.tags.toLowerCase().split(',').map(t => t.trim()) : [];
        
        const hasAllPositive = positiveTags.length === 0 || positiveTags.every(tag => 
          favTags.some(favTag => favTag.includes(tag))
        );
        
        const hasNoNegative = !negativeTags.some(tag => 
          favTags.some(favTag => favTag.includes(tag))
        );
        
        return hasAllPositive && hasNoNegative;
      });
    }
    
    const pageNum = parseInt(page);
    const limitNum = parseInt(limit);
    const start = (pageNum - 1) * limitNum;
    const end = start + limitNum;
    const paginated = filtered.slice(start, end);
    
    res.json({
      favorites: paginated,
      total: filtered.length,
      page: pageNum,
      limit: limitNum,
      totalPages: Math.ceil(filtered.length / limitNum),
      hasMore: end < filtered.length
    });
  });
});

// POST: Thêm 1 ảnh vào favorites (từ imageId)
app.post('/api/favorites/add', (req, res) => {
  const { imageId } = req.body;
  
  const image = imageDatabase.find(img => img.id == imageId);
  if (!image) {
    return res.status(404).json({ error: 'Image not found' });
  }
  
  db.get('SELECT MAX(display_order) as maxOrder FROM favorites', (err, row) => {
    const nextOrder = (row && row.maxOrder) ? row.maxOrder + 1 : 1;
    
    db.run(
      'INSERT INTO favorites (image_path, filename, tags, display_order) VALUES (?, ?, ?, ?)',
      [image.path, image.filename, image.tags.join(', '), nextOrder],
      function(err) {
        if (err) {
          if (err.message.includes('UNIQUE')) {
            return res.status(400).json({ error: 'Ảnh đã có trong favorites' });
          }
          return res.status(500).json({ error: err.message });
        }
        
        res.json({ 
          success: true, 
          id: this.lastID,
          message: 'Đã thêm vào favorites' 
        });
      }
    );
  });
});

// POST: Thêm NHIỀU ảnh vào favorites (từ filenames array)
app.post('/api/favorites', async (req, res) => {
  const { filenames } = req.body;
  
  if (!Array.isArray(filenames) || filenames.length === 0) {
    return res.status(400).json({ error: 'filenames array is required' });
  }

  let successCount = 0;
  let errorCount = 0;

  for (const filename of filenames) {
    try {
      const image = findImageByFilename(filename);
      if (!image) {
        throw new Error('Image not found in database');
      }

      const sourceImage = image.path;
      const sourceTxt = sourceImage.replace(/\.(png|jpg|jpeg|webp|gif)$/i, '.txt');

      const destImage = path.join(FAVOPATH, path.basename(filename));
      const destTxt = destImage.replace(/\.(png|jpg|jpeg|webp|gif)$/i, '.txt');

      // Copy ảnh
      if (fs.existsSync(sourceImage)) {
        fs.copyFileSync(sourceImage, destImage);
      }

      // Copy txt
      if (fs.existsSync(sourceTxt)) {
        fs.copyFileSync(sourceTxt, destTxt);
      }

      // Thêm vào database favorites
      await new Promise((resolve, reject) => {
        db.run(
          'INSERT OR IGNORE INTO favorites (image_path, filename, tags, display_order) VALUES (?, ?, ?, ?)',
          [destImage, filename, image.tags.join(', '), Date.now()],
          (err) => {
            if (err) reject(err);
            else resolve();
          }
        );
      });

      successCount++;
      console.log(`✅ Added to favo: ${filename}`);
    } catch (err) {
      console.error(`❌ Error: ${filename}`, err.message);
      errorCount++;
    }
  }

  res.json({ 
    success: true, 
    message: `Added ${successCount} images (${errorCount} failed)`,
    successCount,
    errorCount
  });
});

// DELETE: Xóa 1 favorite
app.delete('/api/favorites/:id', (req, res) => {
  db.get('SELECT * FROM favorites WHERE id = ?', [req.params.id], (err, fav) => {
    if (err || !fav) {
      return res.status(404).json({ error: 'Favorite not found' });
    }

    // Xóa file trong FAVOPATH
    const favoImage = path.join(FAVOPATH, fav.filename);
    const favoTxt = favoImage.replace(/\.(png|jpg|jpeg|webp|gif)$/i, '.txt');

    if (fs.existsSync(favoImage)) fs.unlinkSync(favoImage);
    if (fs.existsSync(favoTxt)) fs.unlinkSync(favoTxt);

    // Xóa khỏi database
    db.run('DELETE FROM favorites WHERE id = ?', [req.params.id], function(err) {
      if (err) {
        return res.status(500).json({ error: err.message });
      }
      
      res.json({ success: true, message: 'Đã xóa khỏi favorites' });
    });
  });
});

// Serve favorite image
app.get('/api/favorites/image/:id', (req, res) => {
  db.get('SELECT * FROM favorites WHERE id = ?', [req.params.id], (err, fav) => {
    if (err || !fav) {
      return res.status(404).json({ error: 'Favorite not found' });
    }
    
    // Check trong FAVOPATH trước
    const favoPath = path.join(FAVOPATH, fav.filename);
    if (fs.existsSync(favoPath)) {
      return res.sendFile(favoPath);
    }

    // Fallback: check original path
    if (fs.existsSync(fav.image_path)) {
      return res.sendFile(fav.image_path);
    }
    
    res.status(404).json({ error: 'Image file not found' });
  });
});

// ==================== API LỌC THEO FOLDER ====================

app.get('/api/source-folders', (req, res) => {
  const folders = [...new Set(imageDatabase.map(img => img.folder))].sort();
  res.json({ folders });
});

app.get('/api/images/by-folder', (req, res) => {
  const { folder } = req.query;
  
  if (!folder) {
    return res.status(400).json({ error: 'folder parameter required' });
  }

  const filtered = imageDatabase.filter(img => img.folder === folder);
  
  res.json({ results: filtered, folder });
});

// ==================== START SERVER ====================

app.listen(PORT, () => {
  console.log('===========================================');
  console.log(`🚀 Backend started on port ${PORT}`);
  console.log(`📂 Data: ${DATAPATH}`);
  console.log(`⭐ Favorites: ${FAVOPATH}`);
  console.log(`💾 Database: ${DBPATH}`);
  console.log('===========================================');
});

process.on('SIGINT', () => {
  db.close((err) => {
    if (err) console.error(err);
    console.log('Database closed');
    process.exit(0);
  });
});
