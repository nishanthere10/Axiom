const fs = require('fs');
const path = require('path');

const appDir = path.join(__dirname, 'app');
const workspaceDir = path.join(appDir, '(workspace)');

if (!fs.existsSync(workspaceDir)) {
  fs.mkdirSync(workspaceDir);
}

const dirsToMove = ['research', 'research-documents', 'memory', 'compare', 'settings'];

dirsToMove.forEach(dir => {
  const source = path.join(appDir, dir);
  const dest = path.join(workspaceDir, dir);
  if (fs.existsSync(source)) {
    try {
      fs.renameSync(source, dest);
      console.log(`Moved ${dir}`);
    } catch (e) {
      console.error(`Failed to move ${dir}:`, e);
    }
  } else {
    console.log(`Directory ${dir} not found`);
  }
});
